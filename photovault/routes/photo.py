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
from flask import Blueprint, request, jsonify, current_app, session
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
        
        # Create secure filename
        original_name = secure_filename(file.filename) if file.filename else f"capture_{timestamp}"
        safe_filename = f"{unique_id}_{timestamp}.{file_extension}"
        thumbnail_filename = f"thumb_{safe_filename}"
        
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
        photo = Photo(
            user_id=current_user.id if current_user.is_authenticated else None,
            filename=safe_filename,
            original_name=original_name,
            file_path=file_path,
            thumbnail_path=thumbnail_path if thumbnail_created else None,
            file_size=image_info['size_bytes'],
            width=image_info['width'],
            height=image_info['height'],
            mime_type=mimetypes.guess_type(file_path)[0],
            upload_source=upload_source
        )
        db.session.add(photo)
        db.session.commit()
        
        logger.info(f"Successfully processed {upload_source} upload: {original_name}")
        return file_metadata
        
    except Exception as e:
        logger.error(f"Failed to process uploaded file: {str(e)}")
        # Clean up partial files
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            if 'thumbnail_path' in locals() and os.path.exists(thumbnail_path):
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
            'thumbnail_url': f'/static/uploads/{current_user.id}/{thumbnail_filename}',
            'edited_url': f'/static/uploads/{current_user.id}/{edited_filename}'
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
    """Delete a photo and its files"""
    try:
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Delete physical files
        if photo.file_path and os.path.exists(photo.file_path):
            os.remove(photo.file_path)
        
        if photo.thumbnail_path and os.path.exists(photo.thumbnail_path):
            os.remove(photo.thumbnail_path)
            
        if photo.edited_path and os.path.exists(photo.edited_path):
            os.remove(photo.edited_path)
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        
        logger.info(f"Successfully deleted photo {photo_id} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Photo deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting photo {photo_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete photo'
        }), 500

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