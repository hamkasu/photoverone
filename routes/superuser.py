"""
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
"""

# photovault/routes/superuser.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from photovault import db
from photovault.models import User
from datetime import datetime

superuser_bp = Blueprint('superuser', __name__, url_prefix='/superuser')

def superuser_required(f):
    """Decorator to require superuser access"""
    def wrap(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superuser:
            flash("Access denied. Superuser privileges required.", "danger")
            return redirect(url_for('main.index')) # Or redirect to login/dashboard
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@superuser_bp.route('/')
@superuser_bp.route('/dashboard')
@login_required
@superuser_required
def dashboard():
    """Superuser dashboard showing all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('superuser/dashboard.html', users=users)

@superuser_bp.route('/users/toggle_superuser/<int:user_id>', methods=['POST'])
@login_required
@superuser_required
def toggle_superuser(user_id):
    """Toggle the superuser status of a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent users from modifying their own superuser status via this route
    if user.id == current_user.id:
        flash("You cannot change your own superuser status here.", "warning")
        return redirect(url_for('superuser.dashboard'))

    user.is_superuser = not user.is_superuser
    db.session.commit()
    status = "granted" if user.is_superuser else "revoked"
    flash(f"Superuser status {status} for user {user.username}.", "success")
    return redirect(url_for('superuser.dashboard'))

@superuser_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@superuser_required
def delete_user(user_id):
    """Delete a user and their photos"""
    user = User.query.get_or_404(user_id)
    
    # Prevent users from deleting themselves
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for('superuser.dashboard'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f"User {username} deleted successfully.", "success")
    return redirect(url_for('superuser.dashboard'))
