"""
PhotoVault Gallery Routes
Simple gallery blueprint for photo management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, send_file, abort, current_app, Response, after_this_request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import zipfile
import io
import tempfile
from datetime import datetime
from photovault.utils.enhanced_file_handler import get_file_content, file_exists_enhanced

# Create the gallery blueprint
gallery_bp = Blueprint('gallery', __name__)

@gallery_bp.route('/gallery')
@login_required
def gallery():
    """Gallery index - redirect to photos"""
    return redirect(url_for('gallery.photos'))

@gallery_bp.route('/gallery/photos')
@login_required  
def gallery_photos():
    """Redirect gallery/photos to photos for compatibility"""
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

@gallery_bp.route('/download-all')
@login_required
def download_all_images():
    """Download all user images as a ZIP file (secure implementation)"""
    try:
        from photovault.models import Photo
        
        # Get all photos for the current user
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        
        if not photos:
            flash('No photos found to download.', 'warning')
            return redirect(url_for('gallery.photos'))
        
        # Create ZIP file in memory to avoid temp file management issues
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            added_files = set()  # Track added files to avoid duplicates
            
            for photo in photos:
                try:
                    # Get file content from App Storage first, then local
                    file_content = None
                    
                    # Use original_name if available, otherwise filename, but sanitize it
                    raw_filename = photo.original_name or photo.filename
                    # SECURITY: Sanitize filename to prevent zip-slip attacks
                    safe_filename = secure_filename(raw_filename)
                    # SECURITY: Strip any remaining path separators
                    safe_filename = safe_filename.replace('/', '_').replace('\\', '_')
                    
                    # If sanitization removed too much, use a fallback name
                    if not safe_filename or safe_filename == '':
                        safe_filename = f"photo_{photo.id}.jpg"
                    
                    # Try App Storage path first
                    app_storage_path = f"users/{current_user.id}/{photo.filename}"
                    if file_exists_enhanced(app_storage_path):
                        success, content = get_file_content(app_storage_path)
                        if success:
                            file_content = content
                    
                    # Fallback to local file system
                    if file_content is None and photo.file_path and os.path.exists(photo.file_path):
                        with open(photo.file_path, 'rb') as f:
                            file_content = f.read()
                    
                    # Add to ZIP if we have content
                    if file_content:
                        # Ensure unique filename in ZIP
                        base_name = safe_filename
                        counter = 1
                        while base_name in added_files:
                            name, ext = os.path.splitext(safe_filename)
                            if not ext:  # If no extension, add one
                                ext = '.jpg'
                            base_name = f"{name}_{counter}{ext}"
                            counter += 1
                        
                        # SECURITY: Final check - ensure no path traversal in ZIP entry name
                        zip_entry_name = os.path.basename(base_name)
                        zipf.writestr(zip_entry_name, file_content)
                        added_files.add(base_name)
                        current_app.logger.info(f"Added {zip_entry_name} to ZIP archive")
                
                except Exception as e:
                    current_app.logger.warning(f"Could not add photo {photo.filename} to ZIP: {str(e)}")
                    continue
        
        # Check if we have any content
        if len(added_files) == 0:
            flash('No photos could be packaged for download.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Prepare the file for download
        memory_file.seek(0)
        zip_filename = f"PhotoVault_{secure_filename(current_user.username)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        current_app.logger.info(f"Sending ZIP download: {zip_filename} ({len(added_files)} photos)")
        flash(f'Downloading {len(added_files)} photos as {zip_filename}', 'success')
        
        # Send the ZIP file directly from memory
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
            
    except Exception as e:
        current_app.logger.error(f"Error creating ZIP download for user {current_user.id}: {str(e)}")
        flash('Error creating download archive. Please try again.', 'error')
        return redirect(url_for('gallery.photos'))

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
            
            # First try to find by checking App Storage paths
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                potential_original = base_name + ext
                app_storage_original = f"users/{user_id}/{potential_original}"
                if file_exists_enhanced(app_storage_original):
                    original_filename = potential_original
                    break
            else:
                # Fallback to checking local filesystem
                for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    if os.path.exists(os.path.join(current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads'), str(user_id), base_name + ext)):
                        original_filename = base_name + ext
                        break
        
        photo = Photo.query.filter_by(user_id=user_id).filter(
            (Photo.filename == original_filename) | (Photo.edited_filename == original_filename)
        ).first()
        
        if not photo:
            abort(404)
            
        # Try to serve from App Storage first, then fallback to local filesystem
        
        # Check if this is likely an App Storage path (based on how we store photos)
        app_storage_path = f"users/{user_id}/{filename}"
        
        if file_exists_enhanced(app_storage_path):
            # Serve from App Storage
            success, file_content = get_file_content(app_storage_path)
            if success:
                # Determine content type
                import mimetypes
                content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                
                return Response(
                    file_content,
                    mimetype=content_type,
                    headers={'Content-Disposition': f'inline; filename="{filename}"'}
                )
            else:
                # App Storage exists check passed but download failed
                current_app.logger.error(f"App Storage download failed for {app_storage_path}: {file_content}")
                abort(404)
        
        # Fallback to local filesystem
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        uploads_dir = os.path.join(upload_folder, str(user_id))
        
        # Determine the actual file path to serve
        if photo.file_path:
            file_path = photo.file_path
            
            if os.path.isabs(file_path):
                # Use absolute path directly
                file_to_serve = file_path
            elif file_path.startswith(upload_folder + '/'):
                # Path already includes the upload folder root (e.g., "photovault/uploads/1/file.jpg")
                file_to_serve = file_path
            elif file_path.startswith('uploads/') or file_path.startswith('users/'):
                # App Storage style path - strip the storage prefix and use with upload folder
                # e.g., "uploads/123/file.jpg" -> "photovault/uploads/123/file.jpg"
                # or "users/123/file.jpg" -> "photovault/uploads/123/file.jpg"
                path_parts = file_path.split('/', 1)
                if len(path_parts) > 1:
                    relative_part = path_parts[1]  # "123/file.jpg"
                    file_to_serve = os.path.join(upload_folder, relative_part)
                else:
                    file_to_serve = os.path.join(uploads_dir, file_path)
            elif '/' in file_path and file_path.split('/')[0].isdigit():
                # Bare user-relative path like "123/file.jpg" - map to upload folder
                file_to_serve = os.path.join(upload_folder, file_path)
            else:
                # Relative path within user directory (e.g., "extracted_photos/file.jpg")
                file_to_serve = os.path.join(uploads_dir, file_path)
            
            if os.path.exists(file_to_serve):
                return send_file(file_to_serve)
            else:
                current_app.logger.error(f"File not found: {file_to_serve} (from photo.file_path: {file_path})")
                abort(404)
        else:
            # No stored file_path, use filename from URL
            return send_from_directory(uploads_dir, filename)
        
    except Exception as e:
        current_app.logger.error(f"Error serving file {filename} for user {user_id}: {e}")
        abort(404)
