"""
PhotoVault Gallery Routes
Simple gallery blueprint for photo management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, send_file, abort, current_app, Response, jsonify
from flask_login import login_required, current_user
import os
import zipfile
import tempfile
import time
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

@gallery_bp.route('/debug/file-diagnostics')
@login_required
def file_diagnostics():
    """Debug page for file integrity diagnostics"""
    # Temporarily allow all users for debugging (remove after fixing the issue)
    # if not current_user.is_admin:
    #     flash('Access denied. Admin privileges required.', 'error')
    #     return redirect(url_for('gallery.dashboard'))
    
    return render_template('debug/file_diagnostics.html')

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
        is_thumbnail_request = filename.endswith('_thumb.jpg') or filename.endswith('_thumb.png') or filename.endswith('_thumb.jpeg')
        
        if is_thumbnail_request:
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
                else:
                    # If original file not found for thumbnail, return placeholder
                    current_app.logger.warning(f"Thumbnail requested for missing original file: {filename}")
                    return redirect(url_for('static', filename='img/placeholder.png'))
        
        photo = Photo.query.filter_by(user_id=user_id).filter(
            (Photo.filename == original_filename) | (Photo.edited_filename == original_filename)
        ).first()
        
        if not photo:
            # If photo record not found but it's a thumbnail request, serve placeholder
            if is_thumbnail_request:
                current_app.logger.warning(f"Photo record not found for thumbnail: {filename}")
                return redirect(url_for('static', filename='img/placeholder.png'))
            else:
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
                # If it's a thumbnail request, serve placeholder instead of 404
                if is_thumbnail_request:
                    current_app.logger.warning(f"Serving placeholder for failed thumbnail: {filename}")
                    return redirect(url_for('static', filename='img/placeholder.png'))
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
                # If it's a thumbnail request, serve placeholder instead of 404
                if is_thumbnail_request:
                    current_app.logger.warning(f"Serving placeholder for missing thumbnail file: {file_to_serve}")
                    return redirect(url_for('static', filename='img/placeholder.png'))
                abort(404)
        else:
            # No stored file_path, use filename from URL
            file_path = os.path.join(uploads_dir, filename)
            if os.path.exists(file_path):
                return send_from_directory(uploads_dir, filename)
            else:
                current_app.logger.error(f"File not found in uploads directory: {file_path}")
                # If it's a thumbnail request, serve placeholder instead of 404
                if is_thumbnail_request:
                    current_app.logger.warning(f"Serving placeholder for missing thumbnail: {filename}")
                    return redirect(url_for('static', filename='img/placeholder.png'))
                abort(404)
        
    except Exception as e:
        current_app.logger.error(f"Error serving file {filename} for user {user_id}: {e}")
        # If it's a thumbnail request and we hit an exception, serve placeholder instead of 404
        if 'is_thumbnail_request' in locals() and is_thumbnail_request:
            current_app.logger.warning(f"Serving placeholder due to exception for thumbnail: {filename}")
            return redirect(url_for('static', filename='img/placeholder.png'))
        abort(404)

@gallery_bp.route('/api/photos/bulk-download', methods=['POST'])
@login_required
def bulk_download_photos():
    """Create ZIP file of selected photos and serve for download"""
    try:
        from photovault.models import Photo
        
        # Get photo IDs from form data
        photo_ids = request.form.getlist('photo_ids')
        
        if not photo_ids:
            flash('No photos selected for download.', 'warning')
            return redirect(url_for('gallery.photos'))
        
        # Server-side limits for resource protection
        MAX_PHOTOS = 50  # Limit bulk downloads to 50 photos
        MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500MB limit
        
        if len(photo_ids) > MAX_PHOTOS:
            flash(f'Too many photos selected. Maximum {MAX_PHOTOS} photos allowed per download.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Validate that all photos belong to current user
        photos = Photo.query.filter(
            Photo.id.in_(photo_ids),
            Photo.user_id == current_user.id
        ).all()
        
        if not photos:
            flash('No valid photos found for download.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Pre-validate file sizes to avoid resource exhaustion
        total_size = 0
        valid_photos = []
        
        for photo in photos:
            filename_to_use = photo.edited_filename if photo.edited_filename else photo.filename
            file_size = 0
            
            # Check App Storage first
            app_storage_path = f"users/{photo.user_id}/{filename_to_use}"
            if file_exists_enhanced(app_storage_path):
                valid_photos.append((photo, app_storage_path, None))
                # Estimate file size (cannot get exact size from App Storage easily)
                file_size = 5 * 1024 * 1024  # Estimate 5MB per photo for safety
            elif photo.file_path:
                # Check local filesystem
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
                file_path = photo.file_path
                
                if os.path.isabs(file_path):
                    full_path = file_path
                elif file_path.startswith(upload_folder + '/'):
                    full_path = file_path
                elif file_path.startswith('uploads/') or file_path.startswith('users/'):
                    path_parts = file_path.split('/', 1)
                    if len(path_parts) > 1:
                        full_path = os.path.join(upload_folder, path_parts[1])
                    else:
                        full_path = os.path.join(upload_folder, str(photo.user_id), filename_to_use)
                else:
                    full_path = os.path.join(upload_folder, str(photo.user_id), file_path)
                
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    valid_photos.append((photo, None, full_path))
            
            total_size += file_size
            if total_size > MAX_TOTAL_SIZE:
                flash(f'Selected photos exceed maximum download size limit ({MAX_TOTAL_SIZE // (1024*1024)}MB).', 'error')
                return redirect(url_for('gallery.photos'))
        
        if not valid_photos:
            flash('No valid photo files found for download.', 'error')
            return redirect(url_for('gallery.photos'))
        
        # Use TemporaryDirectory for guaranteed cleanup
        with tempfile.TemporaryDirectory() as temp_dir:
            timestamp = int(time.time())
            zip_filename = f"photovault_photos_{timestamp}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                added_files = 0
                file_count = {}  # Track duplicate filenames
                
                for photo, app_storage_path, local_path in valid_photos:
                    try:
                        filename_to_use = photo.edited_filename if photo.edited_filename else photo.filename
                        original_name = photo.original_name or filename_to_use
                        
                        # Sanitize filename for ZIP (prevent path traversal)
                        original_name = os.path.basename(original_name).replace('/', '_').replace('\\', '_')
                        
                        # Handle duplicate filenames by adding counter
                        base_name, ext = os.path.splitext(original_name)
                        if original_name in file_count:
                            file_count[original_name] += 1
                            zip_filename_final = f"{base_name}_{file_count[original_name]}{ext}"
                        else:
                            file_count[original_name] = 0
                            zip_filename_final = original_name
                        
                        # Add file to ZIP with memory-efficient approach
                        if app_storage_path:
                            # App Storage: Load file content
                            success, file_content = get_file_content(app_storage_path)
                            if success and file_content:
                                zipf.writestr(zip_filename_final, file_content)
                                added_files += 1
                                current_app.logger.info(f"Added photo {photo.id} from App Storage as {zip_filename_final}")
                            else:
                                current_app.logger.warning(f"Failed to get App Storage content for photo {photo.id}")
                        elif local_path:
                            # Local filesystem: Use ZIP's built-in file reading for better memory usage
                            zipf.write(local_path, zip_filename_final)
                            added_files += 1
                            current_app.logger.info(f"Added photo {photo.id} from local storage as {zip_filename_final}")
                    except Exception as e:
                        current_app.logger.warning(f"Error adding photo {photo.id} to ZIP: {e}")
                        continue
            
            if added_files == 0:
                flash('No photo files could be found for download.', 'error')
                return redirect(url_for('gallery.photos'))
            
            current_app.logger.info(f"Serving ZIP download with {added_files} photos for user {current_user.id}")
            
            # Send the ZIP file (TemporaryDirectory will auto-cleanup)
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f"PhotoVault_Photos_{added_files}_photos.zip",
                mimetype='application/zip'
            )
            # TemporaryDirectory context manager ensures cleanup
            
    except Exception as e:
        current_app.logger.error(f"Error creating bulk download: {e}")
        flash('Failed to create download. Please try again.', 'error')
        return redirect(url_for('gallery.photos'))
