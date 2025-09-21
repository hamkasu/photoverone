# photovault/routes/upload.py

import os
import uuid
import json
import mimetypes
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from werkzeug.exceptions import RequestEntityTooLarge
from photovault.utils.file_handler import (
    validate_image_file, save_uploaded_file, generate_unique_filename,
    create_thumbnail, get_image_info, delete_file_safely
)
from photovault.utils.metadata_extractor import extract_metadata_for_photo
from photovault.utils.image_enhancement import enhance_for_old_photo
from photovault.utils.face_detection import detect_faces_in_photo
from photovault.utils.face_recognition import face_recognizer
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload')
@login_required
def upload_page():
    """Render the upload page"""
    return render_template('upload.html', title='Upload Photos')

@upload_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_photos():
    """
    Handle photo upload from file selection or camera capture
    Supports both single and multiple file uploads with auto-enhancement and metadata extraction
    """
    try:
        logger.info(f"Upload request from user: {current_user.id}")
        
        # Check if files were provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        files = request.files.getlist('file')
        
        # Filter out empty files
        files = [f for f in files if f.filename]
        
        if not files:
            return jsonify({
                'success': False,
                'error': 'No valid files provided'
            }), 400
        
        logger.info(f"Processing {len(files)} file(s) from {'camera' if request.form.get('upload_source') == 'camera' else 'file'}")
        
        # Get upload source
        upload_source = request.form.get('upload_source', 'file')  # 'file' or 'camera'
        
        uploaded_files = []
        errors = []
        
        for file in files:
            if not file.filename:
                continue
                
            try:
                # Validate file
                is_valid, validation_msg = validate_image_file(file)
                if not is_valid:
                    errors.append(f"{file.filename}: {validation_msg}")
                    continue
                
                # Generate unique filename with username
                unique_filename = generate_unique_filename(
                    file.filename, 
                    prefix='camera' if upload_source == 'camera' else 'upload',
                    username=current_user.username
                )
                
                # Save file
                success, file_path_or_error = save_uploaded_file(
                    file, unique_filename, current_user.id
                )
                
                if not success:
                    errors.append(f"{file.filename}: {file_path_or_error}")
                    continue
                
                file_path = file_path_or_error
                
                # Get image information
                image_info = get_image_info(file_path)
                if not image_info:
                    delete_file_safely(file_path)
                    errors.append(f"{file.filename}: Failed to read image information")
                    continue
                
                # Extract EXIF metadata
                photo_metadata = {}
                try:
                    photo_metadata = extract_metadata_for_photo(file_path)
                    logger.info(f"Extracted metadata for {file.filename}")
                except Exception as e:
                    logger.warning(f"Metadata extraction failed for {file.filename}: {e}")
                
                # Skip auto-enhancement to preserve original image quality
                # Auto-enhancement can be manually applied later if needed
                photo_metadata['auto_enhanced'] = False
                
                # Re-get image info after enhancement (dimensions may have changed)
                final_image_info = get_image_info(file_path)
                if final_image_info:
                    image_info = final_image_info
                
                # Create thumbnail (after enhancement)
                thumb_success, thumb_path_or_error = create_thumbnail(file_path)
                thumbnail_path = thumb_path_or_error if thumb_success else None
                
                # Save to database
                try:
                    from photovault.models import Photo, db
                    
                    # Create photo record with metadata
                    photo = Photo(
                        user_id=current_user.id,
                        filename=unique_filename,
                        original_name=f"{current_user.username}_{file.filename}" if file.filename else f'{current_user.username}_capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg',
                        file_path=file_path,
                        thumbnail_path=thumbnail_path,
                        file_size=image_info['size_bytes'],
                        width=image_info['width'],
                        height=image_info['height'],
                        mime_type=image_info['mime_type'],
                        upload_source=upload_source,
                        
                        # Available metadata fields
                        photo_date=photo_metadata.get('date_taken'),
                        auto_enhanced=photo_metadata.get('auto_enhanced', False)
                    )
                    
                    db.session.add(photo)
                    db.session.commit()
                    
                    # Automatic face detection on newly uploaded photo
                    faces_detected = 0
                    try:
                        faces = detect_faces_in_photo(file_path)
                        if faces:
                            from photovault.models import PhotoPerson
                            for face in faces:
                                try:
                                    # Try to recognize the face
                                    recognition_result = face_recognizer.recognize_face(file_path, face)
                                    
                                    # Create PhotoPerson record
                                    photo_person = PhotoPerson(
                                        photo_id=photo.id,
                                        person_id=recognition_result['person_id'] if recognition_result else None,
                                        confidence=recognition_result['confidence'] if recognition_result else face['confidence'],
                                        face_box_x=face['x'],
                                        face_box_y=face['y'],
                                        face_box_width=face['width'],
                                        face_box_height=face['height'],
                                        manually_tagged=False,
                                        verified=bool(recognition_result)
                                    )
                                    
                                    db.session.add(photo_person)
                                    faces_detected += 1
                                    
                                except Exception as face_error:
                                    logger.warning(f"Error storing face detection for {file.filename}: {face_error}")
                                    continue
                            
                            # Commit face detections
                            if faces_detected > 0:
                                db.session.commit()
                                logger.info(f"Detected and stored {faces_detected} faces in {file.filename}")
                    
                    except Exception as face_detection_error:
                        logger.warning(f"Face detection failed for {file.filename}: {face_detection_error}")
                        # Don't fail the upload if face detection fails
                    
                    uploaded_files.append({
                        'id': photo.id,
                        'filename': unique_filename,
                        'original_name': f"{current_user.username}_{file.filename}" if file.filename else f'{current_user.username}_capture',
                        'file_size': image_info['size_bytes'],
                        'dimensions': f"{image_info['width']}x{image_info['height']}",
                        'upload_source': upload_source,
                        'thumbnail_url': f"/api/thumbnail/{photo.id}" if thumbnail_path else None,
                        'auto_enhanced': photo_metadata.get('auto_enhanced', False),
                        'has_metadata': bool(photo_metadata.get('date_taken')),
                        'faces_detected': faces_detected
                    })
                    
                except Exception as db_error:
                    logger.error(f"Database error for {file.filename}: {str(db_error)}")
                    # Clean up file if database save failed
                    delete_file_safely(file_path)
                    if thumbnail_path:
                        delete_file_safely(thumbnail_path)
                    errors.append(f"{file.filename}: Database save failed")
                    continue
                
            except Exception as e:
                logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
                errors.append(f"{file.filename}: Processing failed")
                continue
        
        # Prepare response
        if uploaded_files:
            response_data = {
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                'uploaded_count': len(uploaded_files),
                'files': uploaded_files
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
            'error': 'File too large. Maximum size allowed is 16MB.'
        }), 413
        
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Upload processing failed',
            'details': str(e)
        }), 500

@upload_bp.route('/api/thumbnail/<int:photo_id>')
def get_thumbnail(photo_id):
    """Serve thumbnail images"""
    try:
        from photovault.models import Photo
        from flask import send_file
        
        photo = Photo.query.filter_by(id=photo_id, user_id=current_user.id).first()
        if not photo or not photo.thumbnail_path:
            return jsonify({'error': 'Thumbnail not found'}), 404
        
        if os.path.exists(photo.thumbnail_path):
            return send_file(photo.thumbnail_path, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Thumbnail file not found'}), 404
        
    except Exception as e:
        logger.error(f"Error serving thumbnail {photo_id}: {str(e)}")
        return jsonify({'error': 'Failed to serve thumbnail'}), 500