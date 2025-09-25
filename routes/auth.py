"""
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from photovault.models import User, PasswordResetToken, db
from photovault.utils import safe_db_query, retry_db_operation, TransientDBError
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        # Try to find user by username or email with retry logic
        def find_user():
            return User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
        
        try:
            user = safe_db_query(find_user, operation_name="user lookup")
        except TransientDBError:
            flash('Temporary database issue. Please try again in a moment.', 'error')
            return render_template('login.html')
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            
            # Get next page from URL parameter
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page)
            else:
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Basic validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        # Username validation
        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'error')
            return render_template('register.html')
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username can only contain letters, numbers, and underscores.', 'error')
            return render_template('register.html')
        
        # Email validation
        if not validate_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('register.html')
        
        # Password validation
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        # Check if user already exists with retry logic
        def check_existing_user():
            return User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
        
        try:
            existing_user = safe_db_query(check_existing_user, operation_name="existing user check")
        except TransientDBError:
            flash('Temporary database issue. Please try again in a moment.', 'error')
            return render_template('register.html')
        
        if existing_user:
            if existing_user.username == username:
                flash('Username already exists. Please choose a different one.', 'error')
            else:
                flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html')
        
        @retry_db_operation(max_retries=3)
        def create_user():
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            return user
        
        try:
            create_user()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except TransientDBError:
            flash('Temporary database issue. Please try again in a moment.', 'error')
            return render_template('register.html')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {e}')
            # Check if it's a duplicate user error
            if 'unique constraint' in str(e).lower() or 'already exists' in str(e).lower():
                flash('Username or email already exists. Please try different values.', 'error')
            else:
                flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged-in users"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate current password
        if not current_password:
            flash('Current password is required.', 'error')
            return render_template('auth/change_password.html')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')
        
        # Validate new password
        if not new_password or not confirm_password:
            flash('Please enter and confirm your new password.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New password and confirmation do not match.', 'error')
            return render_template('auth/change_password.html')
        
        # Check if new password is same as current
        if current_user.check_password(new_password):
            flash('New password must be different from your current password.', 'error')
            return render_template('auth/change_password.html')
        
        # Validate password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/change_password.html')
        
        try:
            # Update password
            current_user.set_password(new_password)
            db.session.commit()
            
            # Clear session for security after password change
            session.clear()
            logout_user()
            
            flash('Password changed successfully! Please log in again with your new password.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while changing your password. Please try again.', 'error')
            return render_template('auth/change_password.html')
    
    return render_template('auth/change_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route"""
    try:
        # Store username before logout
        username = current_user.username if current_user.is_authenticated else None
        
        # Clear any sensitive session data
        session.clear()
        
        # Logout user
        logout_user()
        
        # Flash message with username if available
        if username:
            flash(f'Goodbye, {username}! You have been logged out successfully.', 'info')
        else:
            flash('You have been logged out successfully.', 'info')
        
        # Redirect to login page
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Logout error: {e}")
        
        # Force clear session and redirect
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        if not validate_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                # Clean up old tokens for this user
                old_tokens = PasswordResetToken.query.filter_by(user_id=user.id).all()
                for token in old_tokens:
                    db.session.delete(token)
                
                # Create new reset token
                reset_token = PasswordResetToken(user.id)
                db.session.add(reset_token)
                db.session.commit()
                
                # Send reset email
                email_sent = send_password_reset_email(user, reset_token.token)
                if not email_sent:
                    current_app.logger.warning(f"Failed to send reset email to user {user.id}")
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Password reset error: {str(e)}")
        
        # Always show success message for security (don't reveal if email exists)
        flash('If an account with that email exists, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Find and validate token
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid():
        flash('Password reset link is invalid or has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords
        if not new_password or not confirm_password:
            flash('Please enter and confirm your new password.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Password and confirmation do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Validate password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/reset_password.html', token=token)
        
        try:
            # Update user password
            user = reset_token.user
            user.set_password(new_password)
            
            # Mark token as used
            reset_token.mark_as_used()
            
            db.session.commit()
            
            flash('Your password has been reset successfully! You can now log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password reset error: {str(e)}")
            flash('An error occurred while resetting your password. Please try again.', 'error')
            return render_template('auth/reset_password.html', token=token)
    
    return render_template('auth/reset_password.html', token=token, user=reset_token.user)

def send_password_reset_email(user, token):
    """Send password reset email to user using SendGrid service"""
    try:
        # Import SendGrid service
        from photovault.services.sendgrid_service import send_password_reset_email as sendgrid_reset_email
        
        # Try SendGrid first
        if sendgrid_reset_email(user, token):
            current_app.logger.info(f"Password reset email sent successfully to {user.email} via SendGrid")
        else:
            # Log failure but proceed with fallback
            current_app.logger.error(f"SendGrid failed to send password reset email to {user.email}")
            
            # Fallback to console logging in development only
            if current_app.debug:
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                print(f"EMAIL TO {user.email}: Password reset link: {reset_url}")
                current_app.logger.info(f"Used console fallback for password reset to {user.email}")
        
        # Always return True to prevent email enumeration attacks
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send reset email: {str(e)}")
        # Still return True to avoid revealing whether email exists or not
        return True