"""
PhotoVault Gallery Routes
Simple gallery blueprint for photo management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
import os

# Create the gallery blueprint
gallery_bp = Blueprint('gallery', __name__)

@gallery_bp.route('/dashboard')
@login_required
def dashboard():
    """Gallery dashboard"""
    try:
        from photovault.models import Photo
        photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc()).limit(12).all()
        total_photos = Photo.query.filter_by(user_id=current_user.id).count()
    except Exception as e:
        photos = []
        total_photos = 0
        flash('Photo database not ready yet.', 'info')
    
    return render_template('gallery/dashboard.html', photos=photos, total_photos=total_photos)

@gallery_bp.route('/photos')
@login_required
def photos():
    """All photos page"""
    try:
        from photovault.models import Photo
        page = request.args.get('page', 1, type=int)
        photos = Photo.query.filter_by(user_id=current_user.id)\
                          .order_by(Photo.created_at.desc())\
                          .paginate(page=page, per_page=20, error_out=False)
    except Exception as e:
        photos = None
        flash('Photo database not ready yet.', 'info')
    
    return render_template('gallery/photos.html', photos=photos, current_filter='all')

@gallery_bp.route('/albums')
@login_required
def albums():
    """Albums page"""
    try:
        from photovault.models import Album
        albums = Album.query.filter_by(user_id=current_user.id).order_by(Album.created_at.desc()).all()
    except Exception as e:
        albums = []
        flash('Album database not ready yet.', 'info')
    
    return render_template('gallery/albums.html', albums=albums)

@gallery_bp.route('/upload')
@login_required
def upload():
    """Upload page - redirect to main upload route"""
    return redirect(url_for('photo.upload_page'))

@gallery_bp.route('/photo/<int:photo_id>')
@login_required
def view_photo(photo_id):
    """View single photo"""
    try:
        from photovault.models import Photo
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
        return render_template('view_photo.html', photo=photo, tagged_people=[], all_people=[])
    except Exception as e:
        flash('Photo not found or database not ready.', 'error')
        return redirect(url_for('gallery.dashboard'))

@gallery_bp.route('/photo/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    """Delete a photo"""
    try:
        from photovault.models import Photo
        from photovault import db
        
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
        
        # Delete file from disk
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
        
        # Delete thumbnail if exists
        if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
            os.remove(photo.thumbnail_path)
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        
        flash('Photo deleted successfully.', 'success')
    except Exception as e:
        flash('Error deleting photo or database not ready.', 'error')
    
    return redirect(url_for('gallery.dashboard'))
@gallery_bp.route('/photos/originals')
@login_required
def originals():
    """Show only original photos (no edited versions)"""
    try:
        from photovault.models import Photo
        page = request.args.get('page', 1, type=int)
        photos = Photo.query.filter_by(user_id=current_user.id)\
                          .filter(Photo.edited_filename.is_(None))\
                          .order_by(Photo.created_at.desc())\
                          .paginate(page=page, per_page=20, error_out=False)
    except Exception as e:
        photos = None
        flash('Photo database not ready yet.', 'info')
    
    return render_template('gallery/originals.html', photos=photos)

@gallery_bp.route('/photos/edited')
@login_required
def edited():
    """Show only edited photos"""
    try:
        from photovault.models import Photo
        page = request.args.get('page', 1, type=int)
        photos = Photo.query.filter_by(user_id=current_user.id)\
                          .filter(Photo.edited_filename.isnot(None))\
                          .order_by(Photo.created_at.desc())\
                          .paginate(page=page, per_page=20, error_out=False)
    except Exception as e:
        photos = None
        flash('Photo database not ready.', 'info')
    
    return render_template('gallery/edited.html', photos=photos)
