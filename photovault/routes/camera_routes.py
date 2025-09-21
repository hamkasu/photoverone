"""
PhotoVault Camera Routes
Enhanced camera functionality with full screen + landscape support
Includes comprehensive security validation and rate limiting
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect
from photovault.extensions import csrf
import os
from datetime import datetime
import logging
from PIL import Image
import io

# Import enhanced security utilities
from photovault.utils.upload_security import (
    validate_image_file, 
    validate_upload_request,
    generate_secure_filename,
    create_secure_upload_path,
    sanitize_form_data,
    get_safe_error_message,
    log_security_event,
    UploadSecurityError,
    RateLimitExceeded
)

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
@csrf.exempt  # CSRF handled manually with enhanced validation
@login_required
def upload_image():
    """
    Handle secure image uploads from camera capture
    Includes comprehensive validation, rate limiting, and error handling
    """
    start_time = datetime.now()
    logger = logging.getLogger(__name__)
    
    try:
        # Validate request security and rate limits
        request_valid, request_error = validate_upload_request(required_csrf=True)
        if not request_valid:
            log_security_event(
                "camera_upload_blocked", 
                {"reason": request_error, "user_id": current_user.id},
                "WARNING"
            )
            return jsonify({
                'success': False,
                'error': request_error
            }), 400
        
        # Check if image was sent
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']
        
        # Validate image file with comprehensive security checks
        is_valid, validation_error, file_metadata = validate_image_file(file, check_dimensions=True)
        if not is_valid:
            log_security_event(
                "camera_upload_validation_failed",
                {"reason": validation_error, "filename": file.filename},
                "WARNING"
            )
            return jsonify({
                'success': False,
                'error': validation_error
            }), 400
        
        # Sanitize form data
        sanitized_form = sanitize_form_data(request.form.to_dict())
        quadrant = sanitized_form.get('quadrant', '')
        sequence_number = sanitized_form.get('sequence_number', '')
        
        # Generate secure filename with proper sanitization
        prefix_parts = []
        if quadrant:
            prefix_parts.extend(['camera', 'quad', quadrant])
        elif sequence_number:
            prefix_parts.extend(['camera', 'seq', sequence_number])
        else:
            prefix_parts.append('camera')
        
        prefix = "_".join(prefix_parts)
        # Force JPEG format for camera uploads to ensure format/extension alignment
        filename = generate_secure_filename(
            file.filename, 
            username=current_user.username, 
            prefix=prefix,
            force_format='jpg'  # Camera always saves as JPEG
        )
        
        # Create secure file path
        file_path = create_secure_upload_path(current_user.id, filename)
        
        # Process and save image with enhanced error handling
        try:
            success, process_message = process_and_save_image(file, file_path)
            if not success:
                return jsonify({
                    'success': False,
                    'error': get_safe_error_message(Exception(process_message), "Image processing failed")
                }), 500
                
        except Exception as process_error:
            safe_error = get_safe_error_message(process_error, "Image processing failed")
            logger.error(f"Image processing error for user {current_user.id}: {str(process_error)}")
            return jsonify({
                'success': False,
                'error': safe_error
            }), 500
        
        # Save to database with proper error handling
        try:
            from photovault.models import Photo, db
            
            # Prepare secure original name
            original_name_parts = [current_user.username]
            if quadrant:
                original_name_parts.extend(['quad', quadrant, 'capture'])
            elif sequence_number:
                original_name_parts.extend(['seq', sequence_number, 'capture'])
            else:
                original_name_parts.append('camera-capture')
            
            original_name = "_".join(original_name_parts) + ".jpg"
            
            # Get additional metadata from file
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            photo = Photo(
                filename=filename,
                original_name=original_name,
                user_id=current_user.id,
                file_path=file_path,
                file_size=file_size,
                width=file_metadata.get('width'),
                height=file_metadata.get('height'),
                mime_type='image/jpeg',  # Camera always saves as JPEG
                upload_source='camera',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(photo)
            db.session.commit()
            
            # Log successful upload
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            log_security_event(
                "camera_upload_success",
                {
                    "photo_id": photo.id,
                    "filename": filename,
                    "file_size": file_size,
                    "dimensions": f"{file_metadata.get('width', 0)}x{file_metadata.get('height', 0)}",
                    "processing_time_ms": round(duration_ms, 2),
                    "capture_mode": "quad" if quadrant else ("sequential" if sequence_number else "single")
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Photo captured and saved successfully',
                'photo_id': photo.id,
                'filename': filename,
                'file_size': file_size,
                'dimensions': {
                    'width': file_metadata.get('width'),
                    'height': file_metadata.get('height')
                }
            })
            
        except Exception as db_error:
            # Log database error but don't expose details
            logger.error(f"Database error for user {current_user.id}: {str(db_error)}")
            safe_error = get_safe_error_message(db_error, "Failed to save photo information")
            
            # Clean up file if database save failed
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass  # Don't fail if cleanup fails
            
            return jsonify({
                'success': False,
                'error': safe_error
            }), 500
            
    except RateLimitExceeded as rate_error:
        log_security_event(
            "camera_upload_rate_limit",
            {"user_id": current_user.id, "error": str(rate_error)},
            "WARNING"
        )
        return jsonify({
            'success': False,
            'error': str(rate_error)
        }), 429
        
    except UploadSecurityError as security_error:
        log_security_event(
            "camera_upload_security_error",
            {"user_id": current_user.id, "error": str(security_error)},
            "ERROR"
        )
        return jsonify({
            'success': False,
            'error': get_safe_error_message(security_error, "Security validation failed")
        }), 400
        
    except Exception as e:
        # Log unexpected errors but don't expose details
        logger.error(f"Unexpected camera upload error for user {current_user.id}: {str(e)}")
        safe_error = get_safe_error_message(e, "Upload failed due to server error")
        
        return jsonify({
            'success': False,
            'error': safe_error
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
    """
    Process and save image with enhanced optimization and dimension limits
    Includes memory-safe processing for large images
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Read and validate image data
        file.seek(0)
        image_data = file.read()
        file.seek(0)  # Reset for subsequent use
        
        if len(image_data) == 0:
            return False, "Empty image file"
        
        # Create PIL image with memory safety
        try:
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            return False, f"Invalid image format: {str(e)[:50]}"
        
        # Check image dimensions BEFORE processing to prevent memory issues
        original_width, original_height = image.size
        max_dimension = current_app.config.get('MAX_IMAGE_DIMENSION', 4096)
        
        if original_width > max_dimension or original_height > max_dimension:
            return False, f"Image too large: {original_width}x{original_height} (max: {max_dimension}px)"
        
        # Memory safety check - prevent decompression bombs
        max_pixels = max_dimension * max_dimension
        if original_width * original_height > max_pixels:
            return False, f"Image has too many pixels (potential security risk)"
        
        # Auto-rotate based on EXIF data (with error handling)
        try:
            # Use newer method if available
            if hasattr(image, 'getexif'):
                exif = image.getexif()
                if exif:
                    orientation = exif.get(274, 1)  # Orientation tag
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
            elif hasattr(image, '_getexif'):
                # Fallback to older method
                exif = image._getexif()
                if exif is not None:
                    orientation = exif.get(274, 1)
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
        except Exception as exif_error:
            logger.warning(f"EXIF processing failed, continuing without rotation: {exif_error}")
        
        # Convert to RGB with proper handling of transparency
        # CRITICAL: Strip EXIF metadata to prevent privacy leaks (GPS, device info)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparency
            background = Image.new('RGB', image.size, (255, 255, 255))
            
            if image.mode == 'P':
                # Convert palette to RGBA first
                image = image.convert('RGBA')
            
            # Paste image onto background, preserving alpha channel
            if image.mode in ('RGBA', 'LA'):
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)
            
            image = background
        else:
            # For RGB/L images, create new image without EXIF data
            image_without_exif = Image.new(image.mode, image.size)
            image_without_exif.putdata(list(image.getdata()))
            image = image_without_exif
        
        # Smart resizing based on camera quality settings
        camera_max_size = current_app.config.get('CAMERA_MAX_DIMENSION', 2048)
        
        if image.size[0] > camera_max_size or image.size[1] > camera_max_size:
            # Calculate new size maintaining aspect ratio
            original_ratio = image.size[0] / image.size[1]
            
            if image.size[0] > image.size[1]:  # Landscape
                new_width = camera_max_size
                new_height = int(camera_max_size / original_ratio)
            else:  # Portrait or square
                new_height = camera_max_size  
                new_width = int(camera_max_size * original_ratio)
            
            # Use high-quality resampling
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
        
        # Save with optimized settings
        camera_quality = current_app.config.get('CAMERA_QUALITY', 0.85)
        save_kwargs = {
            'format': 'JPEG',
            'quality': int(camera_quality * 100),
            'optimize': True,
            'progressive': True,  # Better for web viewing
            'subsampling': 0,     # Keep high color quality
        }
        
        # Save to file
        image.save(file_path, **save_kwargs)
        
        # Verify file was created successfully
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False, "File save verification failed"
        
        final_size = os.path.getsize(file_path)
        logger.info(f"Image processed and saved: {file_path} ({final_size/1024:.1f}KB)")
        
        return True, "Image processed and saved successfully"
        
    except MemoryError:
        logger.error("Memory error during image processing - image too large")
        return False, "Image too large to process"
        
    except OSError as os_error:
        logger.error(f"File system error during image processing: {str(os_error)}")
        return False, "File system error during processing"
        
    except Exception as e:
        logger.error(f"Image processing error: {str(e)}")
        return False, get_safe_error_message(e, "Image processing failed")

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