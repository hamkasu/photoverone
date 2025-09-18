"""
PhotoVault Camera Routes
Enhanced camera functionality with full screen + landscape support
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from PIL import Image
import io

# Create camera blueprint with URL prefix to avoid conflicts
camera_bp = Blueprint('camera', __name__, url_prefix='/camera')

@camera_bp.route('/')
@login_required
def camera():
    """Render the enhanced camera page with full screen support"""
    return render_template('camera.html', 
                         title='Camera',
                         user=current_user)

@camera_bp.route('/upload', methods=['POST'])
@login_required  
def upload_image():
    """Handle image uploads from camera capture"""
    try:
        # Check if image was sent
        if 'image' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No image data received'
            }), 400

        file = request.files['image']
        
        # Validate file
        if file.filename == '':
            return jsonify({
                'success': False, 
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': 'Invalid file type'
            }), 400

        # Get capture mode information
        quadrant = request.form.get('quadrant', '')
        sequence_number = request.form.get('sequence_number', '')
        
        # Generate secure filename with username and mode info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        file_extension = get_file_extension(file.filename)
        
        if quadrant:
            filename = f"{current_user.username}_camera_quad_{quadrant}_{timestamp}_{unique_id}{file_extension}"
        elif sequence_number:
            filename = f"{current_user.username}_camera_seq_{sequence_number}_{timestamp}_{unique_id}{file_extension}"
        else:
            filename = f"{current_user.username}_camera_{timestamp}_{unique_id}{file_extension}"
        
        # Ensure upload directory exists
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(upload_path, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(upload_path, filename)
        
        # Process and save image
        success, message = process_and_save_image(file, file_path)
        
        if success:
            # Save to database (adjust based on your models structure)
            try:
                # Import your models - adjust path as needed
                from photovault.models import Photo, db
                
                # Prepare photo metadata
                original_name = f"{current_user.username}_{file.filename}" if file.filename else f'{current_user.username}_camera-capture.jpg'
                if quadrant:
                    original_name = f"{current_user.username}_quad_{quadrant}_capture.jpg"
                elif sequence_number:
                    original_name = f"{current_user.username}_sequential_{sequence_number}_capture.jpg"
                
                photo = Photo(
                    filename=filename,
                    original_name=original_name,
                    user_id=current_user.id,
                    file_path=file_path,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    file_size=os.path.getsize(file_path),
                    upload_source='camera',  # Mark as camera capture
                    # Note: quadrant info is preserved in filename and original_name
                )
                
                db.session.add(photo)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Photo captured and saved successfully!',
                    'filename': filename,
                    'photo_id': photo.id
                })
                
            except Exception as db_error:
                current_app.logger.error(f"Database error: {str(db_error)}")
                # File was saved but DB failed
                return jsonify({
                    'success': True,
                    'message': 'Photo saved but database error occurred',
                    'filename': filename,
                    'warning': 'Database sync issue'
                })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error during upload'
        }), 500

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """Get file extension with dot"""
    if '.' in filename:
        return '.' + filename.rsplit('.', 1)[1].lower()
    return '.jpg'  # Default to jpg

def process_and_save_image(file, file_path):
    """Process and save image with optimization"""
    try:
        # Read image data
        image_data = file.read()
        file.seek(0)  # Reset file pointer
        
        # Open with PIL for processing
        image = Image.open(io.BytesIO(image_data))
        
        # Auto-rotate based on EXIF data
        if hasattr(image, '_getexif'):
            exif = image._getexif()
            if exif is not None:
                orientation = exif.get(274, 1)  # Orientation tag
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Optimize file size while maintaining quality
        max_size = (2048, 2048)  # Max dimensions
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        save_kwargs = {
            'format': 'JPEG',
            'quality': 85,
            'optimize': True
        }
        
        image.save(file_path, **save_kwargs)
        
        current_app.logger.info(f"Image saved: {file_path}")
        return True, "Image processed and saved successfully"
        
    except Exception as e:
        current_app.logger.error(f"Image processing error: {str(e)}")
        return False, f"Image processing failed: {str(e)}"

@camera_bp.route('/camera/settings')
@login_required
def camera_settings():
    """Camera settings and preferences"""
    return render_template('camera_settings.html',
                         title='Camera Settings',
                         user=current_user)

@camera_bp.route('/api/camera/check-support')
def check_camera_support():
    """API endpoint to check camera capabilities"""
    return jsonify({
        'server_support': True,
        'upload_max_size': current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024),
        'allowed_formats': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
        'features': {
            'fullscreen': True,
            'orientation_lock': True,
            'high_resolution': True,
            'auto_upload': True
        }
    })