# photovault/routes/photo_detection.py

import os
import uuid
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, render_template, url_for, send_file
from flask_login import login_required, current_user
from werkzeug.exceptions import RequestEntityTooLarge
from photovault.utils.file_handler import validate_image_file, generate_unique_filename
from photovault.utils.enhanced_file_handler import save_uploaded_file_enhanced, delete_file_enhanced
from photovault.utils.photo_detection import detect_photos_in_image, extract_detected_photos
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
photo_detection_bp = Blueprint('photo_detection', __name__)

# Temporary storage for uploaded files with secure tokens
# In production, this should be stored in a database or cache like Redis
_temp_files = {}

@photo_detection_bp.route('/photo-detection')
@login_required
def photo_detection_page():
    """Render the photo detection page"""
    return render_template('photo_detection.html', title='Photo Detection & Cropping')

@photo_detection_bp.route('/api/photo-detection/upload', methods=['POST'])
@login_required
def upload_for_detection():
    """
    Handle image upload for photo detection and cropping
    """
    try:
        logger.info(f"Photo detection upload request from user: {current_user.id}")
        
        # Check if file was provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if not file.filename:
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        logger.info(f"Processing file: {file.filename}")
        
        # Validate file
        is_valid, validation_msg = validate_image_file(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f"Invalid file: {validation_msg}"
            }), 400
        
        # Generate unique filename
        unique_filename = generate_unique_filename(
            file.filename, 
            prefix='detection',
            username=current_user.username
        )
        
        # Save file temporarily for processing
        success, file_path_or_error = save_uploaded_file_enhanced(
            file, unique_filename, current_user.id
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': f"Upload failed: {file_path_or_error}"
            }), 500
        
        file_path = file_path_or_error
        
        # Check image size before processing to prevent memory issues
        try:
            from PIL import Image as PILImage
            with PILImage.open(file_path) as img:
                width, height = img.size
                # Limit image size to prevent memory exhaustion
                max_pixels = 25000000  # ~25MP limit to match detection logic
                if width * height > max_pixels:
                    delete_file_enhanced(file_path)
                    return jsonify({
                        'success': False,
                        'error': f'Image too large ({width}x{height} pixels). Maximum supported size is 25 megapixels.'
                    }), 400
        except Exception as e:
            delete_file_enhanced(file_path)
            return jsonify({
                'success': False,
                'error': f'Could not process image: {str(e)}'
            }), 400
        
        # Detect photos in the uploaded image
        detected_photos = detect_photos_in_image(file_path)
        
        if not detected_photos:
            # Clean up uploaded file if no photos detected
            delete_file_enhanced(file_path)
            return jsonify({
                'success': False,
                'error': 'No photos detected in the uploaded image. Please try with an image containing clear rectangular photos.'
            }), 400
        
        logger.info(f"Detected {len(detected_photos)} photos in {file.filename}")
        
        # Generate secure token for this upload session
        secure_token = str(uuid.uuid4())
        expiry_time = datetime.now() + timedelta(hours=1)  # 1 hour expiry
        
        # Store file info securely with token
        _temp_files[secure_token] = {
            'file_path': file_path,
            'user_id': current_user.id,
            'original_filename': file.filename,
            'detected_photos': detected_photos,
            'expiry': expiry_time
        }
        
        # Clean up expired tokens
        _cleanup_expired_tokens()
        
        # Prepare response data (no file paths exposed)
        response_data = {
            'success': True,
            'token': secure_token,
            'original_filename': file.filename,
            'detected_photos': detected_photos,
            'detection_count': len(detected_photos),
            'message': f'Successfully detected {len(detected_photos)} photo(s) in the uploaded image.'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Photo detection upload failed: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred during photo detection.'
        }), 500

@photo_detection_bp.route('/api/photo-detection/extract', methods=['POST'])
@login_required
def extract_detected_photos_api():
    """
    Extract and save detected photos as separate images
    """
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required token'
            }), 400
        
        token = data['token']
        selected_indices = data.get('selected_photos', [])
        
        # Validate token and get file info
        if token not in _temp_files:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired session token'
            }), 400
        
        file_info = _temp_files[token]
        
        # Check if token belongs to current user
        if file_info['user_id'] != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized access'
            }), 403
        
        # Check if token is expired
        if datetime.now() > file_info['expiry']:
            del _temp_files[token]
            return jsonify({
                'success': False,
                'error': 'Session expired, please upload again'
            }), 400
        
        file_path = file_info['file_path']
        detected_photos = file_info['detected_photos']
        
        # Filter to only extract selected photos
        photos_to_extract = [detected_photos[i] for i in selected_indices if 0 <= i < len(detected_photos)]
        
        if not photos_to_extract:
            return jsonify({
                'success': False,
                'error': 'No photos selected for extraction'
            }), 400
        
        # Create output directory for extracted photos
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        extraction_dir = os.path.join(user_upload_dir, 'extracted_photos')
        
        # Extract the selected photos
        extracted_photos = extract_detected_photos(file_path, extraction_dir, photos_to_extract)
        
        if not extracted_photos:
            return jsonify({
                'success': False,
                'error': 'Failed to extract photos'
            }), 500
        
        # Save extracted photos to database
        saved_photos = []
        from photovault.models import Photo
        from photovault.extensions import db
        from photovault.utils.file_handler import get_image_dimensions
        from PIL import Image
        
        try:
            
            for extracted_photo in extracted_photos:
                file_path_full = extracted_photo['file_path']
                filename = extracted_photo['filename']
                
                # Get image metadata
                width, height = get_image_dimensions(file_path_full)
                file_size = os.path.getsize(file_path_full)
                
                # Create relative path for database storage
                user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
                relative_path = os.path.relpath(file_path_full, user_upload_dir)
                
                # Create new Photo record
                new_photo = Photo()
                new_photo.filename = filename
                new_photo.original_name = f"Extracted from {file_info['original_filename']}"
                new_photo.file_path = relative_path
                new_photo.file_size = file_size
                new_photo.width = width
                new_photo.height = height
                new_photo.mime_type = 'image/jpeg'
                new_photo.upload_source = 'photo_detection'
                new_photo.user_id = current_user.id
                new_photo.processing_notes = f"Extracted via photo detection with {extracted_photo['confidence']:.2f} confidence"
                
                db.session.add(new_photo)
                saved_photos.append({
                    'filename': filename,
                    'width': width,
                    'height': height,
                    'confidence': extracted_photo['confidence']
                })
            
            db.session.commit()
            logger.info(f"Successfully saved {len(saved_photos)} extracted photos to database for user {current_user.id}")
            
        except Exception as e:
            logger.error(f"Database save failed for extracted photos: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass  # Session might already be closed
            
            # Clean up extracted files since database save failed
            for extracted_photo in extracted_photos:
                try:
                    if os.path.exists(extracted_photo['file_path']):
                        os.remove(extracted_photo['file_path'])
                except Exception:
                    pass
            
            # Clean up the temporary original file and token
            delete_file_enhanced(file_path)
            del _temp_files[token]
            
            return jsonify({
                'success': False,
                'error': f'Failed to save extracted photos to database: {str(e)}'
            }), 500
        
        # Clean up the temporary original file and token
        delete_file_enhanced(file_path)
        del _temp_files[token]
        
        logger.info(f"Successfully extracted {len(extracted_photos)} photos for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'extracted_photos': saved_photos,
            'extraction_count': len(extracted_photos),
            'message': f'Successfully extracted {len(extracted_photos)} photo(s) and saved them to your gallery.'
        })
        
    except Exception as e:
        logger.error(f"Photo extraction failed: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred during photo extraction.'
        }), 500

@photo_detection_bp.route('/api/photo-detection/preview/<token>')
@login_required
def preview_original(token):
    """
    Preview the uploaded image using secure token
    """
    try:
        # Validate token
        if token not in _temp_files:
            return jsonify({'error': 'Invalid or expired session token'}), 404
        
        file_info = _temp_files[token]
        
        # Check if token belongs to current user
        if file_info['user_id'] != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if token is expired
        if datetime.now() > file_info['expiry']:
            del _temp_files[token]
            return jsonify({'error': 'Session expired'}), 404
        
        file_path = file_info['file_path']
        
        # Verify file exists and is within user directory (defense in depth)
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        real_file_path = os.path.realpath(file_path)
        real_user_dir = os.path.realpath(user_upload_dir)
        
        if not real_file_path.startswith(real_user_dir):
            logger.warning(f"Path traversal attempt detected: {file_path}")
            return jsonify({'error': 'Invalid file'}), 403
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path)
        
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        return jsonify({'error': 'Preview failed'}), 500

def _cleanup_expired_tokens():
    """Clean up expired tokens from temporary storage"""
    current_time = datetime.now()
    expired_tokens = [token for token, info in _temp_files.items() 
                     if current_time > info['expiry']]
    
    for token in expired_tokens:
        file_info = _temp_files[token]
        try:
            # Clean up the file if it exists
            if os.path.exists(file_info['file_path']):
                delete_file_enhanced(file_info['file_path'])
        except Exception as e:
            logger.warning(f"Failed to clean up expired file {file_info['file_path']}: {e}")
        
        del _temp_files[token]
    
    if expired_tokens:
        logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")