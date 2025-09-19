"""
PhotoVault Enhanced Upload Route
Handles file uploads from both traditional file selection and camera capture
"""
import os
import uuid
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from flask import Blueprint, request, jsonify, current_app, session, url_for
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf, CSRFError
from photovault.extensions import csrf
from PIL import Image
import logging

# Import your models
from photovault.models import Photo, Album, User
from photovault.extensions import db

# Create blueprint
photo_bp = Blueprint('photo', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
MAX_IMAGE_DIMENSION = 4096  # Maximum width/height
THUMBNAIL_SIZE = (300, 300)

def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_content(file_stream):
    """Validate that the file is actually a valid image"""
    try:
        with Image.open(file_stream) as img:
            img.verify()  # Verify image integrity
            return True
    except Exception as e:
        logger.warning(f"Image validation failed: {str(e)}")
        return False

def get_image_info(file_path):
    """Extract image metadata"""
    try:
        with Image.open(file_path) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': os.path.getsize(file_path)
            }
    except Exception as e:
        logger.error(f"Failed to get image info: {str(e)}")
        return None

def create_thumbnail(original_path, thumbnail_path):
    """Create thumbnail for uploaded image"""
    try:
        with Image.open(original_path) as img:
            # Convert to RGB if necessary (for PNG with transparency, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
            logger.info(f"Created thumbnail: {thumbnail_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {str(e)}")
        return False

def process_uploaded_file(file, upload_source='file'):
    """Process and save uploaded file"""
    try:
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create secure filename with username
        from flask_login import current_user
        original_name = f"{current_user.username}_{secure_filename(file.filename)}" if file.filename else f"{current_user.username}_capture_{timestamp}"
        safe_filename = f"{current_user.username}_{unique_id}_{timestamp}.{file_extension}"
        thumbnail_filename = f"{current_user.username}_thumb_{safe_filename}"
        
        # Create upload directories if they don't exist
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        thumbnails_dir = os.path.join(upload_dir, 'thumbnails')
        
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # File paths
        file_path = os.path.join(upload_dir, safe_filename)
        thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
        
        # Save original file
        file.save(file_path)
        logger.info(f"Saved file: {file_path}")
        
        # Get image information
        image_info = get_image_info(file_path)
        if not image_info:
            raise ValueError("Invalid image file")
        
        # Check image dimensions
        if image_info['width'] > MAX_IMAGE_DIMENSION or image_info['height'] > MAX_IMAGE_DIMENSION:
            raise ValueError(f"Image dimensions too large. Max: {MAX_IMAGE_DIMENSION}px")
        
        # Create thumbnail
        thumbnail_created = create_thumbnail(file_path, thumbnail_path)
        
        # Prepare file metadata
        file_metadata = {
            'id': unique_id,
            'original_name': original_name,
            'filename': safe_filename,
            'thumbnail_filename': thumbnail_filename if thumbnail_created else None,
            'file_path': file_path,
            'thumbnail_path': thumbnail_path if thumbnail_created else None,
            'upload_source': upload_source,  # 'file' or 'camera'
            'upload_time': datetime.now(),
            'file_size': image_info['size_bytes'],
            'image_width': image_info['width'],
            'image_height': image_info['height'],
            'image_format': image_info['format'],
            'mime_type': mimetypes.guess_type(file_path)[0]
        }
        
        # Save to database  
        from photovault.models import Photo
        photo = Photo()
        photo.user_id = current_user.id if current_user.is_authenticated else None
        photo.filename = safe_filename
        photo.original_name = original_name
        photo.file_path = file_path
        photo.thumbnail_path = thumbnail_path if thumbnail_created else None
        photo.file_size = image_info['size_bytes']
        photo.width = image_info['width']
        photo.height = image_info['height']
        photo.mime_type = mimetypes.guess_type(file_path)[0]
        photo.upload_source = upload_source
        db.session.add(photo)
        db.session.commit()
        
        logger.info(f"Successfully processed {upload_source} upload: {original_name}")
        return file_metadata
        
    except Exception as e:
        logger.error(f"Failed to process uploaded file: {str(e)}")
        # Rollback database session
        db.session.rollback()
        # Clean up partial files
        file_path = locals().get('file_path')
        thumbnail_path = locals().get('thumbnail_path')
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except:
            pass
        raise

@photo_bp.route('/api/upload', methods=['POST'])
@csrf.exempt
@login_required
def upload_photo():
    """
    Handle photo upload from file selection or camera capture
    Supports both single and multiple file uploads
    """
    # Note: CSRF is exempt for this upload endpoint since user is authenticated
    
    try:
        logger.info(f"Upload request from user: {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
        # Check if files were provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        files = request.files.getlist('file')
        if not files or all(file.filename == '' for file in files):
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        # Determine upload source from request or headers
        upload_source = request.form.get('source', 'file')
        user_agent = request.headers.get('User-Agent', '').lower()
        if 'mobile' in user_agent or upload_source == 'camera':
            upload_source = 'camera'
        
        logger.info(f"Processing {len(files)} file(s) from {upload_source}")
        
        # Process each file
        uploaded_files = []
        errors = []
        
        for file in files:
            if not file or file.filename == '':
                continue
                
            try:
                # Validate file extension
                if not allowed_file(file.filename):
                    errors.append(f"Invalid file type for {file.filename}")
                    continue
                
                # Check file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > MAX_FILE_SIZE:
                    size_mb = file_size / (1024 * 1024)
                    max_mb = MAX_FILE_SIZE / (1024 * 1024)
                    errors.append(f"File {file.filename} too large ({size_mb:.1f}MB, max: {max_mb}MB)")
                    continue
                
                # Validate image content
                if not validate_image_content(file):
                    errors.append(f"Invalid image content in {file.filename}")
                    continue
                
                # Reset file pointer after validation
                file.seek(0)
                
                # Process the file
                file_metadata = process_uploaded_file(file, upload_source)
                uploaded_files.append(file_metadata)
                
            except ValueError as e:
                errors.append(f"Error processing {file.filename}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
                errors.append(f"Failed to process {file.filename}")
                continue
        
        # Prepare response
        if uploaded_files:
            response_data = {
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                'uploaded_files': len(uploaded_files),
                'files': [
                    {
                        'id': f['id'],
                        'filename': f['filename'],
                        'original_name': f['original_name'],
                        'file_size': f['file_size'],
                        'dimensions': f"{f['image_width']}x{f['image_height']}",
                        'upload_source': f['upload_source'],
                        'thumbnail_url': f"/api/thumbnail/{f['id']}" if f.get('thumbnail_filename') else None
                    }
                    for f in uploaded_files
                ]
            }
            
            if errors:
                response_data['warnings'] = errors
                response_data['message'] += f" ({len(errors)} files had errors)"
            
            logger.info(f"Upload successful: {len(uploaded_files)} files processed")
            return jsonify(response_data), 200
        
        else:
            # All files failed
            return jsonify({
                'success': False,
                'error': 'All files failed to upload',
                'details': errors
            }), 400
            
    except RequestEntityTooLarge:
        return jsonify({
            'success': False,
            'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
        }), 413
        
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error occurred'
        }), 500

@photo_bp.route('/api/thumbnail/<file_id>')
def get_thumbnail(file_id):
    """Serve thumbnail images"""
    try:
        # You would typically look up the file in your database here
        # For now, we'll construct the path directly
        thumbnails_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'thumbnails')
        
        # Find thumbnail file by ID
        for filename in os.listdir(thumbnails_dir):
            if filename.startswith(f"thumb_{file_id}"):
                thumbnail_path = os.path.join(thumbnails_dir, filename)
                if os.path.exists(thumbnail_path):
                    from flask import send_file
                    return send_file(thumbnail_path, mimetype='image/jpeg')
        
        return jsonify({'error': 'Thumbnail not found'}), 404
        
    except Exception as e:
        logger.error(f"Error serving thumbnail {file_id}: {str(e)}")
        return jsonify({'error': 'Failed to serve thumbnail'}), 500

@photo_bp.route('/api/photos', methods=['GET'])
@login_required
def list_photos():
    """List uploaded photos for the current user"""
    try:
        # This would typically query your database
        # For now, return a basic response
        return jsonify({
            'success': True,
            'photos': [],
            'total': 0,
            'message': 'Photo listing endpoint - implement with your database model'
        })
        
    except Exception as e:
        logger.error(f"Error listing photos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to list photos'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/annotate', methods=['POST'])
@login_required
def annotate_photo(photo_id):
    """Save annotated version of a photo"""
    try:
        import base64
        import io
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get the annotated image data from request
        data = request.get_json()
        if not data or 'imageData' not in data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        # Decode base64 image data
        image_data = data['imageData']
        if image_data.startswith('data:image'):
            # Remove data:image/png;base64, prefix
            image_data = image_data.split(',')[1]
        
        # Decode and process the image
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        
        # Generate filename for edited version
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        base_name = os.path.splitext(photo.filename)[0]
        edited_filename = f"{base_name}_edited_{timestamp}_{unique_id}.jpg"
        
        # Create user upload directory
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Save the edited image
        edited_filepath = os.path.join(user_upload_dir, edited_filename)
        img.convert('RGB').save(edited_filepath, 'JPEG', quality=90)
        
        # Create thumbnail for edited version
        thumbnail_filename = f"{base_name}_edited_{timestamp}_{unique_id}_thumb.jpg"
        thumbnail_path = os.path.join(user_upload_dir, thumbnail_filename)
        create_thumbnail(edited_filepath, thumbnail_path)
        
        # Update photo record with edited version info
        photo.edited_filename = edited_filename
        photo.edited_path = edited_filepath
        photo.thumbnail_path = thumbnail_path
        photo.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Successfully saved annotated photo for user {current_user.id}, photo {photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Annotated photo saved successfully',
            'edited_filename': edited_filename,
            'thumbnail_url': url_for('uploaded_file', filename=f'{current_user.id}/{thumbnail_filename}'),
            'edited_url': url_for('uploaded_file', filename=f'{current_user.id}/{edited_filename}')
        })
        
    except Exception as e:
        logger.error(f"Error saving annotated photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to save annotated photo'
        }), 500

@photo_bp.route('/api/photos/<int:photo_id>/delete', methods=['DELETE'])
@login_required
def delete_photo(photo_id):
    """Delete a photo and its files with selective deletion options"""
    try:
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get deletion type from request body or default to 'both'
        data = request.get_json() or {}
        deletion_type = data.get('deletion_type', 'both')  # 'original', 'edited', 'both'
        
        # Validate deletion type
        if deletion_type not in ['original', 'edited', 'both']:
            return jsonify({'success': False, 'error': 'Invalid deletion type'}), 400
        
        # Check if photo has edited version for validation
        has_edited = bool(photo.edited_filename)
        
        if deletion_type == 'edited' and not has_edited:
            return jsonify({'success': False, 'error': 'No edited version to delete'}), 400
        
        if deletion_type == 'original' and not has_edited:
            return jsonify({'success': False, 'error': 'Cannot delete original when no edited version exists'}), 400
        
        files_deleted = []
        
        # Handle selective file deletion
        if deletion_type in ['original', 'both']:
            # Delete original file
            if photo.file_path and os.path.exists(photo.file_path):
                os.remove(photo.file_path)
                files_deleted.append('original')
            
            # Delete thumbnail (always tied to original)
            if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
                os.remove(photo.thumbnail_path)
        
        if deletion_type in ['edited', 'both']:
            # Delete edited version if it exists
            if photo.edited_filename:
                edited_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(photo.user_id), photo.edited_filename)
                if os.path.exists(edited_path):
                    os.remove(edited_path)
                    files_deleted.append('edited')
        
        # Handle database updates and associations based on deletion type
        from photovault.models import VoiceMemo, VaultPhoto, PhotoPerson, StoryPhoto
        
        if deletion_type == 'both':
            # Delete entire photo record and all associations
            
            # Delete associated voice memos
            voice_memos = VoiceMemo.query.filter_by(photo_id=photo.id).all()
            for memo in voice_memos:
                if memo.file_path and os.path.exists(memo.file_path):
                    os.remove(memo.file_path)
                db.session.delete(memo)
            
            # Delete associated vault photo shares
            vault_photos = VaultPhoto.query.filter_by(photo_id=photo.id).all()
            for vault_photo in vault_photos:
                db.session.delete(vault_photo)
            
            # Delete associated photo-person tags
            photo_people = PhotoPerson.query.filter_by(photo_id=photo.id).all()
            for photo_person in photo_people:
                db.session.delete(photo_person)
            
            # Delete associated story photo attachments
            story_photos = StoryPhoto.query.filter_by(photo_id=photo.id).all()
            for story_photo in story_photos:
                db.session.delete(story_photo)
            
            # Delete the photo record
            db.session.delete(photo)
            
        elif deletion_type == 'edited':
            # Keep original, remove edited version info from database
            photo.edited_filename = None
            photo.edited_path = None
            # Reset thumbnail_path to ensure it points to original thumbnail
            if photo.thumbnail_path:
                # Check if thumbnail exists, if not regenerate from original
                if not os.path.exists(photo.thumbnail_path):
                    try:
                        # Regenerate thumbnail from original
                        from PIL import Image
                        original_image = Image.open(photo.file_path)
                        original_image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                        
                        # Save thumbnail
                        thumbnail_filename = f"{os.path.splitext(photo.filename)[0]}_thumb.jpg"
                        thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(photo.user_id), thumbnail_filename)
                        original_image.save(thumbnail_path, 'JPEG', quality=85)
                        photo.thumbnail_path = thumbnail_path
                    except Exception as e:
                        logger.warning(f"Failed to regenerate thumbnail for photo {photo.id}: {str(e)}")
                        photo.thumbnail_path = None
            photo.updated_at = datetime.utcnow()
            
        elif deletion_type == 'original':
            # Promote edited version to be the new original
            if photo.edited_filename and photo.edited_path:
                # Update database to use edited version as the main photo
                photo.filename = photo.edited_filename
                photo.file_path = photo.edited_path
                
                # Generate new thumbnail from the edited version
                try:
                    from PIL import Image
                    edited_image = Image.open(photo.edited_path)
                    edited_image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                    
                    # Save new thumbnail
                    thumbnail_filename = f"{os.path.splitext(photo.edited_filename)[0]}_thumb.jpg"
                    new_thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(photo.user_id), thumbnail_filename)
                    edited_image.save(new_thumbnail_path, 'JPEG', quality=85)
                    photo.thumbnail_path = new_thumbnail_path
                except Exception as e:
                    logger.warning(f"Failed to generate thumbnail from edited version for photo {photo.id}: {str(e)}")
                    photo.thumbnail_path = None
                
                # Clear edited fields since it's now the original
                photo.edited_filename = None
                photo.edited_path = None
                photo.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Successfully deleted {deletion_type} version(s) of photo {photo_id} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deletion_type} version(s)',
            'files_deleted': files_deleted,
            'deletion_type': deletion_type
        })
        
    except Exception as e:
        logger.error(f"Error deleting photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete photo'
        }), 500

@photo_bp.route('/api/photos/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_photos():
    """Delete multiple photos in bulk"""
    try:
        data = request.get_json()
        if not data or 'photo_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'No photo IDs provided'
            }), 400
        
        photo_ids = data['photo_ids']
        if not photo_ids or not isinstance(photo_ids, list):
            return jsonify({
                'success': False,
                'error': 'Invalid photo IDs format'
            }), 400
        
        # Convert to integers and filter out invalid values
        try:
            photo_ids = [int(pid) for pid in photo_ids if str(pid).isdigit()]
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid photo ID format'
            }), 400
        
        if not photo_ids:
            return jsonify({
                'success': False,
                'error': 'No valid photo IDs provided'
            }), 400
        
        # Get photos that belong to current user
        photos_to_delete = Photo.query.filter(
            Photo.id.in_(photo_ids),
            Photo.user_id == current_user.id
        ).all()
        
        if not photos_to_delete:
            return jsonify({
                'success': False,
                'error': 'No photos found or access denied'
            }), 404
        
        deleted_count = 0
        errors = []
        
        # Get upload folder for security validation
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        user_upload_dir = os.path.realpath(os.path.join(upload_folder, str(current_user.id)))
        
        def is_safe_path(filepath, base_dir):
            """Validate that filepath is within base_dir to prevent path traversal"""
            try:
                real_path = os.path.realpath(filepath)
                return real_path.startswith(base_dir + os.sep) or real_path == base_dir
            except (OSError, ValueError):
                return False
        
        for photo in photos_to_delete:
            try:
                # Validate and delete physical files with path security
                if photo.file_path and os.path.exists(photo.file_path):
                    if is_safe_path(photo.file_path, user_upload_dir):
                        os.remove(photo.file_path)
                
                if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
                    if is_safe_path(photo.thumbnail_path, user_upload_dir):
                        os.remove(photo.thumbnail_path)
                    
                # Delete edited version if it exists
                if photo.edited_filename:
                    edited_path = os.path.join(user_upload_dir, photo.edited_filename)
                    if os.path.exists(edited_path):
                        os.remove(edited_path)
                
                # Delete all associated records that reference this photo
                from photovault.models import VoiceMemo, VaultPhoto, PhotoPerson, StoryPhoto
                
                # Delete associated voice memos
                voice_memos = VoiceMemo.query.filter_by(photo_id=photo.id).all()
                for memo in voice_memos:
                    if memo.file_path and os.path.exists(memo.file_path):
                        if is_safe_path(memo.file_path, user_upload_dir):
                            os.remove(memo.file_path)
                    db.session.delete(memo)
                
                # Delete associated vault photo shares
                vault_photos = VaultPhoto.query.filter_by(photo_id=photo.id).all()
                for vault_photo in vault_photos:
                    db.session.delete(vault_photo)
                
                # Delete associated photo-person tags
                photo_people = PhotoPerson.query.filter_by(photo_id=photo.id).all()
                for photo_person in photo_people:
                    db.session.delete(photo_person)
                
                # Delete associated story photo attachments
                story_photos = StoryPhoto.query.filter_by(photo_id=photo.id).all()
                for story_photo in story_photos:
                    db.session.delete(story_photo)
                
                # Delete the photo record
                db.session.delete(photo)
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error deleting photo {photo.id}: {str(e)}")
                errors.append(f"Photo {photo.id}: {str(e)}")
                continue
        
        # Commit all deletions
        db.session.commit()
        
        logger.info(f"Successfully bulk deleted {deleted_count} photos for user {current_user.id}")
        
        response_data = {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} photo{"s" if deleted_count != 1 else ""}'
        }
        
        if errors:
            response_data['warnings'] = errors
            response_data['message'] += f' ({len(errors)} photos had errors)'
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in bulk delete photos: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete photos'
        }), 500

# Voice Memo API Endpoints

@photo_bp.route('/api/photos/<int:photo_id>/voice-memos', methods=['POST'])
@login_required
def upload_voice_memo(photo_id):
    """Upload a voice memo for a photo"""
    try:
        from photovault.models import VoiceMemo
        import uuid
        import os
        from werkzeug.utils import secure_filename
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if audio file was provided
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if not audio_file.filename:
            return jsonify({'success': False, 'error': 'No audio file selected'}), 400
        
        # Validate audio file type (handle codec variations)
        content_type = audio_file.content_type.lower()
        base_type = content_type.split(';')[0].strip()  # Remove codec specifications
        
        allowed_audio_types = {'audio/webm', 'audio/wav', 'audio/mp3', 'audio/ogg', 'audio/mp4', 'audio/mpeg'}
        if base_type not in allowed_audio_types:
            return jsonify({'success': False, 'error': f'Invalid audio file type: {content_type}'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        file_extension = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else 'webm'
        filename = f"voice_memo_{photo_id}_{timestamp}_{unique_id}.{file_extension}"
        
        # Create voice memos directory
        voice_memo_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id), 'voice_memos')
        os.makedirs(voice_memo_dir, exist_ok=True)
        
        # Save audio file
        file_path = os.path.join(voice_memo_dir, filename)
        audio_file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Get optional metadata from request
        title = request.form.get('title', '').strip()
        transcript = request.form.get('transcript', '').strip()
        duration = request.form.get('duration')  # Duration in seconds from frontend
        
        # Convert duration to float if provided
        try:
            duration = float(duration) if duration else None
        except (ValueError, TypeError):
            duration = None
        
        # Auto-generate descriptive title if not provided
        if not title:
            if transcript and len(transcript.strip()) > 0:
                # Use first few words of transcript
                words = transcript.strip().split()[:4]
                title = f"Memo: {' '.join(words)}..."
            else:
                # Use photo name and timestamp
                photo_name = photo.original_name.split('.')[0] if photo.original_name else 'Photo'
                time_str = datetime.now().strftime('%H:%M')
                title = f"Voice memo for {photo_name[:20]} at {time_str}"
        
        # Create voice memo record
        voice_memo = VoiceMemo()
        voice_memo.photo_id = photo_id
        voice_memo.user_id = current_user.id
        voice_memo.filename = filename
        voice_memo.original_name = secure_filename(audio_file.filename)
        voice_memo.file_path = file_path
        voice_memo.file_size = file_size
        voice_memo.mime_type = audio_file.content_type
        voice_memo.duration = duration
        voice_memo.title = title if title else None
        voice_memo.transcript = transcript if transcript else None
        
        db.session.add(voice_memo)
        db.session.commit()
        
        logger.info(f"Voice memo uploaded for photo {photo_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Voice memo uploaded successfully',
            'voice_memo': {
                'id': voice_memo.id,
                'filename': voice_memo.filename,
                'duration': voice_memo.duration,
                'duration_formatted': voice_memo.duration_formatted,
                'file_size_mb': voice_memo.file_size_mb,
                'title': voice_memo.title,
                'transcript': voice_memo.transcript,
                'created_at': voice_memo.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error uploading voice memo for photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to upload voice memo'}), 500

@photo_bp.route('/api/photos/<int:photo_id>/voice-memos', methods=['GET'])
@login_required
def get_voice_memos(photo_id):
    """Get all voice memos for a photo"""
    try:
        from photovault.models import VoiceMemo
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get voice memos for this photo
        voice_memos = VoiceMemo.query.filter_by(photo_id=photo_id).order_by(VoiceMemo.created_at.desc()).all()
        
        memos_data = []
        for memo in voice_memos:
            memos_data.append({
                'id': memo.id,
                'filename': memo.filename,
                'original_name': memo.original_name,
                'duration': memo.duration,
                'duration_formatted': memo.duration_formatted,
                'file_size_mb': memo.file_size_mb,
                'title': memo.title,
                'transcript': memo.transcript,
                'created_at': memo.created_at.isoformat(),
                'updated_at': memo.updated_at.isoformat() if memo.updated_at != memo.created_at else None
            })
        
        return jsonify({
            'success': True,
            'voice_memos': memos_data,
            'total': len(memos_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting voice memos for photo {photo_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get voice memos'}), 500

@photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['GET'])
@login_required
def serve_voice_memo(memo_id):
    """Serve/download a voice memo file"""
    try:
        from photovault.models import VoiceMemo
        from flask import send_file
        
        # Get the voice memo and verify ownership
        voice_memo = VoiceMemo.query.get_or_404(memo_id)
        if voice_memo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if file exists
        if not os.path.exists(voice_memo.file_path):
            return jsonify({'success': False, 'error': 'Voice memo file not found'}), 404
        
        # Serve the file
        return send_file(
            voice_memo.file_path,
            mimetype=voice_memo.mime_type,
            as_attachment=False,
            download_name=voice_memo.original_name
        )
        
    except Exception as e:
        logger.error(f"Error serving voice memo {memo_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to serve voice memo'}), 500

@photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['PUT'])
@login_required
def update_voice_memo(memo_id):
    """Update voice memo metadata (title, transcript)"""
    try:
        from photovault.models import VoiceMemo
        
        # Get the voice memo and verify ownership
        voice_memo = VoiceMemo.query.get_or_404(memo_id)
        if voice_memo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update title if provided
        if 'title' in data:
            voice_memo.title = data['title'].strip() if data['title'] else None
        
        # Update transcript if provided
        if 'transcript' in data:
            voice_memo.transcript = data['transcript'].strip() if data['transcript'] else None
        
        voice_memo.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Voice memo {memo_id} updated by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Voice memo updated successfully',
            'voice_memo': {
                'id': voice_memo.id,
                'title': voice_memo.title,
                'transcript': voice_memo.transcript,
                'updated_at': voice_memo.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating voice memo {memo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update voice memo'}), 500

@photo_bp.route('/api/voice-memos/<int:memo_id>', methods=['DELETE'])
@login_required
def delete_voice_memo(memo_id):
    """Delete a voice memo"""
    try:
        from photovault.models import VoiceMemo
        
        # Get the voice memo and verify ownership
        voice_memo = VoiceMemo.query.get_or_404(memo_id)
        if voice_memo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Delete physical file
        if voice_memo.file_path and os.path.exists(voice_memo.file_path):
            os.remove(voice_memo.file_path)
        
        # Delete from database
        db.session.delete(voice_memo)
        db.session.commit()
        
        logger.info(f"Voice memo {memo_id} deleted by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Voice memo deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting voice memo {memo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete voice memo'}), 500

# Error handlers for the blueprint
@photo_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413

@photo_bp.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400

@photo_bp.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500