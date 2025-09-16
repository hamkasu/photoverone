"""
PhotoVault Main Routes Blueprint
This should only contain routes, not a Flask app
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

# Create the main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    try:
        # Calculate photo statistics for the current user
        from photovault.models import Photo
        
        total_photos = Photo.query.filter_by(user_id=current_user.id).count()
        # For now, assume all photos are originals since there's no edited version tracking yet
        edited_photos = 0
        original_photos = total_photos
        
        # Calculate total storage used (in MB)
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        total_size_bytes = sum(photo.file_size or 0 for photo in photos)
        total_size_mb = round(total_size_bytes / 1024 / 1024, 2) if total_size_bytes > 0 else 0
        
        # Calculate storage usage percentage (assuming 1GB = 1024MB limit for demo)
        storage_limit_mb = 1024  # 1GB limit
        storage_usage_percent = (total_size_mb / storage_limit_mb * 100) if storage_limit_mb > 0 else 0
        
        stats = {
            'total_photos': total_photos,
            'edited_photos': edited_photos,
            'original_photos': original_photos,
            'total_size_mb': total_size_mb,
            'storage_usage_percent': storage_usage_percent
        }
        
        # Get recent photos for dashboard display (limit to 12 most recent)
        recent_photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc()).limit(12).all()
        
        return render_template('dashboard.html', stats=stats, photos=recent_photos)
    except Exception as e:
        # Simple fallback for errors - just log to console
        print(f"Dashboard error: {str(e)}")
        # Return simple stats in case of error
        stats = {'total_photos': 0, 'edited_photos': 0, 'original_photos': 0, 'total_size_mb': 0, 'storage_usage_percent': 0}
        return render_template('dashboard.html', stats=stats, photos=[])

@main_bp.route('/upload')
@login_required
def upload():
    """Upload page"""
    return render_template('upload.html', user=current_user)

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Initialize with defaults
    stats = {
        'total_photos': 0,
        'edited_photos': 0,
        'total_size': 0,
        'member_since': 'Unknown'
    }
    
    try:
        # Calculate user statistics
        from photovault.models import Photo
        from datetime import datetime
        
        # Get all photos for current user
        user_photos = Photo.query.filter_by(user_id=current_user.id).all()
        
        # Calculate statistics
        total_photos = len(user_photos)
        edited_photos = sum(1 for photo in user_photos if photo.edited_filename and photo.edited_filename.strip())
        total_size = sum(photo.file_size or 0 for photo in user_photos)
        
        # Format member since date
        if current_user.created_at:
            member_since = current_user.created_at.strftime('%B %Y')
        else:
            member_since = 'Unknown'
            
        stats = {
            'total_photos': total_photos,
            'edited_photos': edited_photos, 
            'total_size': total_size,
            'member_since': member_since
        }
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        # stats already initialized with defaults above
        
    return render_template('profile.html', user=current_user, stats=stats)

@main_bp.route('/gallery')
@login_required
def gallery():
    """Gallery page"""
    try:
        from photovault.models import Photo
        
        # Get all photos for the current user
        photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc()).all()
        
        return render_template('gallery/dashboard.html', photos=photos, total_photos=len(photos))
    except Exception as e:
        print(f"Gallery error: {str(e)}")
        return render_template('gallery/dashboard.html', photos=[], total_photos=0)

@main_bp.route('/photos/<int:photo_id>/edit')
@login_required
def edit_photo(photo_id):
    """Photo editor page"""
    try:
        from photovault.models import Photo
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return redirect(url_for('main.dashboard'))
            
        return render_template('editor.html', photo=photo)
    except Exception as e:
        print(f"Edit photo error: {str(e)}")
        return redirect(url_for('main.dashboard'))