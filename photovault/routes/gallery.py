"""
PhotoVault Gallery Routes
Simple gallery blueprint for photo management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, abort, current_app
from flask_login import login_required, current_user
import os

# Create the gallery blueprint
gallery_bp = Blueprint('gallery', __name__)

@gallery_bp.route('/gallery')
@login_required
def gallery():
    """Gallery index - redirect to photos"""
    return redirect(url_for('gallery.photos'))

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

@gallery_bp.route('/photos/compare')
@login_required
def compare_photos():
    """Show photos with side-by-side comparison of original and edited versions"""
    try:
        from photovault.models import Photo
        page = request.args.get('page', 1, type=int)
        photos = Photo.query.filter_by(user_id=current_user.id)\
                          .filter(Photo.edited_filename.isnot(None))\
                          .order_by(Photo.created_at.desc())\
                          .paginate(page=page, per_page=6, error_out=False)
    except Exception as e:
        photos = None
        flash('Photo database not ready.', 'info')
    
    return render_template('gallery/compare.html', photos=photos)

@gallery_bp.route('/photo/<int:photo_id>/compare')
@login_required
def compare_single_photo(photo_id):
    """View single photo with side-by-side original vs edited comparison"""
    try:
        from photovault.models import Photo
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first_or_404()
        
        # Ensure the photo has an edited version
        if not photo.edited_filename:
            flash('This photo does not have an edited version for comparison.', 'warning')
            return redirect(url_for('gallery.view_photo', photo_id=photo_id))
        
        return render_template('gallery/compare_single.html', photo=photo)
    except Exception as e:
        flash('Photo not found or database not ready.', 'error')
        return redirect(url_for('gallery.dashboard'))

@gallery_bp.route('/uploads/<int:user_id>/<path:filename>')
@login_required
def uploaded_file(user_id, filename):
    """Secure route for serving uploaded files with authentication checks"""
    # Security check: Users can only access their own files unless they're admin
    if current_user.id != user_id and not current_user.is_admin:
        abort(403)
    
    # Verify the file exists and belongs to the user
    try:
        from photovault.models import Photo
        
        # Handle thumbnail files by checking for original file
        original_filename = filename
        if filename.endswith('_thumb.jpg') or filename.endswith('_thumb.png') or filename.endswith('_thumb.jpeg'):
            # Extract original filename by removing _thumb suffix
            base_name = filename.rsplit('_thumb.', 1)[0]
            # Find the original extension
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                if os.path.exists(os.path.join(current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads'), str(user_id), base_name + ext)):
                    original_filename = base_name + ext
                    break
        
        photo = Photo.query.filter_by(user_id=user_id).filter(
            (Photo.filename == original_filename) | (Photo.edited_filename == original_filename)
        ).first()
        
        if not photo:
            abort(404)
            
        # Construct the file path
        uploads_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads'), str(user_id))
        
        return send_from_directory(uploads_dir, filename)
        
    except Exception as e:
        current_app.logger.error(f"Error serving file {filename} for user {user_id}: {e}")
        abort(404)
