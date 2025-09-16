"""
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
"""

# photovault/routes/admin.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, case, text
from photovault import db
from photovault.models import User, Photo
from datetime import datetime, timedelta
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def superuser_required(f):
    """Decorator to require superuser access"""
    def wrap(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superuser:
            logger.warning(f"Unauthorized superuser access attempt by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
            flash("You do not have permission to access that page.", "danger")
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__  # Important for endpoint naming
    return wrap

def admin_required(f):
    """Decorator to require either admin or superuser access"""
    def wrap(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_admin or current_user.is_superuser):
            logger.warning(f"Unauthorized admin access attempt by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
            flash("You do not have permission to access that page.", "danger")
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Enhanced admin dashboard with optimized queries"""
    try:
        # Optimized single query to get all user statistics - fixes N+1 problem
        users_with_stats = db.session.query(
            User,
            func.coalesce(func.count(Photo.id), 0).label('total_photos'),
            func.coalesce(
                func.sum(case((Photo.edited_filename.isnot(None), 1), else_=0)), 0
            ).label('edited_photos'),
            func.coalesce(func.sum(Photo.file_size), 0).label('total_size')
        ).outerjoin(Photo, User.id == Photo.user_id)\
         .group_by(User.id)\
         .order_by(User.created_at.desc())\
         .all()
        
        # Calculate totals efficiently in a single pass
        total_users = len(users_with_stats)
        total_photos_all = sum(row.total_photos for row in users_with_stats)
        total_edited_all = sum(row.edited_photos for row in users_with_stats)
        total_storage_all = sum(row.total_size for row in users_with_stats)
        
        # Overall statistics
        stats = {
            'total_users': total_users,
            'total_photos': total_photos_all,
            'total_edited': total_edited_all,
            'total_storage': total_storage_all,
            'total_storage_mb': round(total_storage_all / (1024 * 1024), 2) if total_storage_all else 0
        }
        
        # Convert to the format expected by the template
        users_with_stats_formatted = []
        for row in users_with_stats:
            user = row[0]  # User object
            total_photos = row.total_photos
            edited_photos = row.edited_photos
            total_size = row.total_size
            users_with_stats_formatted.append((user, total_photos, edited_photos, total_size))
        
        logger.info(f"Admin dashboard accessed by user {current_user.username} - {total_users} users, {total_photos_all} photos")
        
        return render_template('admin/dashboard.html', 
                             users_with_stats=users_with_stats_formatted, 
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        db.session.rollback()
        flash("Error loading dashboard. Please try again.", "danger")
        return redirect(url_for('main.dashboard'))

@admin_bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View detailed information about a specific user with optimized queries"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user's photos with single query
        photos = Photo.query.filter_by(user_id=user_id)\
                           .order_by(Photo.uploaded_at.desc())\
                           .all()
        
        # Calculate statistics efficiently
        total_photos = len(photos)
        edited_photos = sum(1 for photo in photos if photo.edited_filename is not None)
        total_size = sum(photo.file_size or 0 for photo in photos)
        
        user_stats = {
            'total_photos': total_photos,
            'edited_photos': edited_photos,
            'original_photos': total_photos - edited_photos,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size > 0 else 0,
            'avg_file_size': round(total_size / total_photos / 1024, 2) if total_photos > 0 else 0  # in KB
        }
        
        logger.info(f"User detail viewed for {user.username} by admin {current_user.username}")
        
        return render_template('admin/user_detail.html', 
                             user=user, 
                             photos=photos, 
                             user_stats=user_stats)
    
    except Exception as e:
        logger.error(f"Error loading user detail for user_id {user_id}: {str(e)}")
        flash("Error loading user details.", "danger")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user information with improved validation"""
    try:
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            new_username = request.form.get('username', '').strip()
            new_email = request.form.get('email', '').strip().lower()
            
            # Enhanced validation
            if not new_username or len(new_username) < 3:
                flash("Username must be at least 3 characters long.", "danger")
                return render_template('admin/edit_user.html', user=user)
            
            if not new_email:
                flash("Email address is required.", "danger")
                return render_template('admin/edit_user.html', user=user)
            
            # Check for email format
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
                flash("Please enter a valid email address.", "danger")
                return render_template('admin/edit_user.html', user=user)
            
            # Check if username or email is taken by another user
            existing_user = User.query.filter(
                User.id != user_id,
                (User.username == new_username) | (User.email == new_email)
            ).first()
            
            if existing_user:
                if existing_user.username == new_username:
                    flash("Username already exists.", "danger")
                else:
                    flash("Email address already exists.", "danger")
                return render_template('admin/edit_user.html', user=user)
            
            # Update user information
            old_username = user.username
            old_email = user.email
            user.username = new_username
            user.email = new_email
            
            db.session.commit()
            logger.info(f"User {old_username} updated by admin {current_user.username}: username={new_username}, email={new_email}")
            flash(f"User information updated successfully.", "success")
            return redirect(url_for('admin.user_detail', user_id=user_id))
        
        return render_template('admin/edit_user.html', user=user)
    
    except Exception as e:
        logger.error(f"Error editing user {user_id}: {str(e)}")
        db.session.rollback()
        flash("Error updating user information.", "danger")
        return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/user/<int:user_id>/reset-password', methods=['POST'])
@login_required
@superuser_required  # Only superusers can reset passwords
def reset_user_password(user_id):
    """Reset a user's password with enhanced validation"""
    try:
        user = User.query.get_or_404(user_id)
        
        new_password = request.form.get('new_password', '').strip()
        if not new_password:
            flash("New password is required.", "danger")
            return redirect(url_for('admin.user_detail', user_id=user_id))
        
        # Enhanced password validation
        if len(new_password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return redirect(url_for('admin.user_detail', user_id=user_id))
        
        # Check for basic password strength
        import re
        if not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
            flash("Password must contain both letters and numbers.", "danger")
            return redirect(url_for('admin.user_detail', user_id=user_id))
        
        user.set_password(new_password)
        db.session.commit()
        
        logger.warning(f"Password reset for user {user.username} by superuser {current_user.username}")
        flash(f"Password reset for user {user.username}.", "success")
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    except Exception as e:
        logger.error(f"Error resetting password for user {user_id}: {str(e)}")
        db.session.rollback()
        flash("Error resetting password.", "danger")
        return redirect(url_for('admin.user_detail', user_id=user_id))

@admin_bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@superuser_required # Only superusers can toggle admin status
def toggle_admin(user_id):
    """Toggle the admin status of a user with enhanced security"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent users from modifying superusers unless they are also superusers
        if user.is_superuser and not current_user.is_superuser:
            logger.warning(f"Attempt to modify superuser {user.username} by non-superuser {current_user.username}")
            flash("You cannot modify superuser accounts.", "danger")
            return redirect(url_for('admin.dashboard'))
        
        # Prevent self-modification of admin status
        if user.id == current_user.id:
            flash("You cannot modify your own admin status.", "warning")
            return redirect(url_for('admin.dashboard'))
            
        old_status = user.is_admin
        user.is_admin = not user.is_admin
        db.session.commit()
        
        status = "granted" if user.is_admin else "revoked"
        logger.warning(f"Admin status {status} for user {user.username} by superuser {current_user.username}")
        flash(f"Admin status {status} for user {user.username}.", "success")
        return redirect(url_for('admin.dashboard'))
    
    except Exception as e:
        logger.error(f"Error toggling admin status for user {user_id}: {str(e)}")
        db.session.rollback()
        flash("Error updating admin status.", "danger")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/toggle_superuser/<int:user_id>', methods=['POST'])
@login_required
@superuser_required # Only superusers can toggle superuser status
def toggle_superuser(user_id):
    """Toggle the superuser status of a user with enhanced security"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Critical: Prevent a superuser from removing their own superuser status
        if user.id == current_user.id:
            flash("You cannot change your own superuser status.", "warning")
            return redirect(url_for('admin.dashboard'))
        
        # Check if this would leave no superusers (safety check)
        if user.is_superuser:
            remaining_superusers = User.query.filter(
                User.is_superuser == True,
                User.id != user_id
            ).count()
            
            if remaining_superusers == 0:
                flash("Cannot revoke superuser status: at least one superuser must remain.", "danger")
                return redirect(url_for('admin.dashboard'))

        old_status = user.is_superuser
        user.is_superuser = not user.is_superuser
        db.session.commit()
        
        status = "granted" if user.is_superuser else "revoked"
        logger.critical(f"Superuser status {status} for user {user.username} by superuser {current_user.username}")
        flash(f"Superuser status {status} for user {user.username}.", "success")
        return redirect(url_for('admin.dashboard'))
    
    except Exception as e:
        logger.error(f"Error toggling superuser status for user {user_id}: {str(e)}")
        db.session.rollback()
        flash("Error updating superuser status.", "danger")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@superuser_required # Only superusers can delete users
def delete_user(user_id):
    """Delete a user and their photos with enhanced safety checks"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Enhanced security checks
        if user.is_superuser:
            flash("Superuser accounts cannot be deleted.", "danger")
            return redirect(url_for('admin.dashboard'))
            
        # Prevent users from deleting themselves
        if user.id == current_user.id:
            flash("You cannot delete your own account.", "danger")
            return redirect(url_for('admin.dashboard'))

        username = user.username
        photo_count = len(user.photos)
        
        # Delete user's photos from the filesystem
        deleted_files = 0
        failed_deletions = []
        
        for photo in user.photos:
            # Delete original file
            original_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
            if os.path.exists(original_filepath):
                try:
                    os.remove(original_filepath)
                    deleted_files += 1
                except OSError as e:
                    logger.error(f"Error deleting original file {original_filepath}: {e}")
                    failed_deletions.append(photo.filename)
            
            # Delete edited file if it exists
            if photo.edited_filename:
                edited_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.edited_filename)
                if os.path.exists(edited_filepath):
                    try:
                        os.remove(edited_filepath)
                        deleted_files += 1
                    except OSError as e:
                        logger.error(f"Error deleting edited file {edited_filepath}: {e}")
                        failed_deletions.append(photo.edited_filename)
        
        # Delete user from database
        db.session.delete(user)
        db.session.commit()
        
        # Log the deletion
        logger.critical(f"User {username} deleted by superuser {current_user.username} - {photo_count} photos, {deleted_files} files deleted")
        
        if failed_deletions:
            flash(f"User {username} deleted successfully, but {len(failed_deletions)} files could not be removed from disk.", "warning")
        else:
            flash(f"User {username} and all their photos deleted successfully.", "success")
        
        return redirect(url_for('admin.dashboard'))
    
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        db.session.rollback()
        flash("Error deleting user.", "danger")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/photo/<int:photo_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_photo(photo_id):
    """Delete a specific photo (admin can delete any photo) with enhanced logging"""
    try:
        photo = Photo.query.get_or_404(photo_id)
        user_id = photo.user_id
        filename = photo.original_filename
        owner = User.query.get(user_id)
        
        # Delete files from filesystem
        deleted_files = []
        failed_deletions = []
        
        original_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
        if os.path.exists(original_filepath):
            try:
                os.remove(original_filepath)
                deleted_files.append(photo.filename)
            except OSError as e:
                logger.error(f"Error deleting original file {original_filepath}: {e}")
                failed_deletions.append(photo.filename)
        
        if photo.edited_filename:
            edited_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.edited_filename)
            if os.path.exists(edited_filepath):
                try:
                    os.remove(edited_filepath)
                    deleted_files.append(photo.edited_filename)
                except OSError as e:
                    logger.error(f"Error deleting edited file {edited_filepath}: {e}")
                    failed_deletions.append(photo.edited_filename)
        
        db.session.delete(photo)
        db.session.commit()
        
        logger.info(f"Photo {filename} (owner: {owner.username if owner else 'unknown'}) deleted by admin {current_user.username}")
        
        if failed_deletions:
            flash(f"Photo deleted from database, but {len(failed_deletions)} files could not be removed from disk.", "warning")
        else:
            flash("Photo deleted successfully.", "success")
        
        return redirect(url_for('admin.user_detail', user_id=user_id))
    
    except Exception as e:
        logger.error(f"Error deleting photo {photo_id}: {str(e)}")
        db.session.rollback()
        flash("Error deleting photo.", "danger")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """View detailed system statistics with optimized queries"""
    try:
        # Optimize queries using aggregations
        
        # User statistics - single query
        user_stats = db.session.query(
            func.count(User.id).label('total_users'),
            func.sum(case((User.is_admin == True, 1), else_=0)).label('admin_users'),
            func.sum(case((User.is_superuser == True, 1), else_=0)).label('superusers')
        ).first()
        
        # Recent users (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        # Photo statistics - single query  
        photo_stats = db.session.query(
            func.count(Photo.id).label('total_photos'),
            func.sum(case((Photo.edited_filename.isnot(None), 1), else_=0)).label('edited_photos'),
            func.sum(Photo.file_size).label('total_size')
        ).first()
        
        # Recent uploads (last 30 days)
        recent_uploads = Photo.query.filter(Photo.uploaded_at >= thirty_days_ago).count()
        
        # Calculate derived statistics
        total_photos = photo_stats.total_photos or 0
        edited_photos = photo_stats.edited_photos or 0
        total_size = photo_stats.total_size or 0
        
        # Most active users - optimized query
        most_active_users = db.session.query(
            User.username,
            func.count(Photo.id).label('photo_count')
        ).join(Photo)\
         .group_by(User.id, User.username)\
         .order_by(func.count(Photo.id).desc())\
         .limit(10)\
         .all()
        
        # Format for template
        most_active_formatted = [(row.username, row.photo_count) for row in most_active_users]
        
        statistics = {
            'users': {
                'total': user_stats.total_users,
                'admins': user_stats.admin_users,
                'superusers': user_stats.superusers,
                'recent': recent_users
            },
            'photos': {
                'total': total_photos,
                'edited': edited_photos,
                'original_only': total_photos - edited_photos,
                'recent_uploads': recent_uploads
            },
            'storage': {
                'total_bytes': total_size,
                'total_mb': round(total_size / (1024 * 1024), 2),
                'total_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'avg_file_size_kb': round(total_size / total_photos / 1024, 2) if total_photos else 0
            },
            'most_active_users': most_active_formatted
        }
        
        logger.info(f"Statistics viewed by admin {current_user.username}")
        
        return render_template('admin/statistics.html', stats=statistics)
    
    except Exception as e:
        logger.error(f"Error loading statistics: {str(e)}")
        flash("Error loading statistics.", "danger")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/profile')
@login_required
@admin_required # Both admins and superusers can view their profile
def profile():
    """View admin/superuser profile"""
    return render_template('admin/profile.html', user=current_user)

# Error handlers for admin blueprint
@admin_bp.errorhandler(403)
def admin_forbidden(error):
    """Handle forbidden access in admin area"""
    logger.warning(f"403 error in admin area: {request.endpoint} by user {current_user.username if current_user.is_authenticated else 'anonymous'}")
    return render_template('errors/403.html'), 403

@admin_bp.errorhandler(404)
def admin_not_found(error):
    """Handle not found errors in admin area"""
    logger.info(f"404 error in admin area: {request.endpoint}")
    return render_template('errors/404.html'), 404

@admin_bp.errorhandler(500)
def admin_internal_error(error):
    """Handle internal errors in admin area"""
    logger.error(f"500 error in admin area: {request.endpoint} - {str(error)}")
    db.session.rollback()
    return render_template('errors/500.html'), 500