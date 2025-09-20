# photovault/utils/file_handler.py

import os
import uuid
import mimetypes
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
MAX_IMAGE_DIMENSION = 4096

def validate_image_file(file):
    """
    Validate uploaded image file
    
    Args:
        file: FileStorage object from Flask request
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    try:
        # Check file exists and has filename
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check file type by MIME type
        allowed_types = [
            'image/jpeg', 'image/jpg', 'image/png', 
            'image/gif', 'image/webp', 'image/bmp', 'image/tiff'
        ]
        
        if hasattr(file, 'content_type') and file.content_type not in allowed_types:
            return False, f"Invalid file type: {file.content_type}"
        
        # Check file extension
        file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
        if file_ext not in [f'.{ext}' for ext in ALLOWED_EXTENSIONS]:
            return False, f"Invalid file extension: {file_ext}"
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {MAX_FILE_SIZE / (1024*1024)}MB)"
        
        if file_size == 0:
            return False, "Empty file"
        
        # Validate actual image content
        try:
            file.seek(0)
            with Image.open(file) as image:
                image.verify()  # Verify it's a valid image
                width, height = image.size
                if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                    return False, f"Image dimensions too large: {width}x{height} (max: {MAX_IMAGE_DIMENSION}px)"
            file.seek(0)  # Reset file pointer again
            return True, "Valid image file"
        except Exception as e:
            file.seek(0)  # Reset file pointer on error
            return False, f"Invalid image content: {str(e)}"
            
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return False, f"Validation error: {str(e)}"

def save_uploaded_file(file, filename, user_id=None):
    """
    Save uploaded file to the upload directory
    
    Args:
        file: FileStorage object from Flask request
        filename: String filename to save as
        user_id: Optional user ID for organizing files
        
    Returns:
        tuple: (success, file_path_or_error_message)
    """
    try:
        # Get upload directory
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not upload_folder:
            return False, 'UPLOAD_FOLDER not configured'
        
        # Create user-specific subdirectory if user_id provided
        if user_id:
            upload_folder = os.path.join(upload_folder, str(user_id))
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(upload_folder, filename)
        
        # Save the file
        file.save(file_path)
        
        # Verify file was saved
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logger.info(f'File saved successfully: {filename}')
            return True, file_path
        else:
            logger.error(f'File not found after save or is empty: {filename}')
            return False, 'File save verification failed'
            
    except Exception as e:
        logger.error(f'Error saving file {filename}: {str(e)}')
        return False, f'Save error: {str(e)}'

def generate_unique_filename(original_filename, prefix="", username=None):
    """
    Generate a unique filename while preserving the original extension
    
    Args:
        original_filename: Original filename from upload
        prefix: Optional prefix for the filename
        username: Optional username to include at the start of filename
        
    Returns:
        str: Unique filename with original extension
    """
    # Secure the filename
    safe_filename = secure_filename(original_filename) if original_filename else "upload"
    
    # Get file extension
    _, file_ext = os.path.splitext(safe_filename)
    if not file_ext:
        file_ext = '.jpg'  # Default extension
    
    # Generate unique name with UUID and timestamp
    # Calculate available characters for filename (12 total - extension length)
    available_chars = 12 - len(file_ext)
    if available_chars > 8:
        available_chars = 8
    unique_id = str(uuid.uuid4().hex)[:available_chars]

    
    # Return short filename
    if prefix:
        parts = []
        if username:
            parts.append(secure_filename(username))
        parts.append(prefix)
        # parts.append(timestamp)
        parts.append(unique_id)
        unique_name = "_".join(parts)
    else:
        parts = []
        if username:
            parts.append(secure_filename(username))
        parts.append("upload")
        # parts.append(timestamp)
        parts.append(unique_id)
        unique_name = "_".join(parts)
    
    return f"{unique_id}{file_ext}"

def get_file_size_mb(file_path):
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to file
        
    Returns:
        float: File size in MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except Exception:
        return 0.0

def create_thumbnail(file_path, thumbnail_size=(150, 150)):
    """
    Create thumbnail for uploaded image
    
    Args:
        file_path: Path to original image
        thumbnail_size: Tuple of (width, height) for thumbnail
        
    Returns:
        tuple: (success, thumbnail_path_or_error)
    """
    try:
        # Open image
        with Image.open(file_path) as image:
            # Convert RGBA to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = rgb_image
            
            # Create thumbnail
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Generate thumbnail filename
            base_path, ext = os.path.splitext(file_path)
            thumbnail_path = f"{base_path}_thumb{ext}"
            
            # Save thumbnail
            image.save(thumbnail_path, 'JPEG', optimize=True, quality=85)
            
            return True, thumbnail_path
            
    except Exception as e:
        logger.error(f'Error creating thumbnail: {str(e)}')
        return False, str(e)

def delete_file_safely(file_path):
    """
    Safely delete a file
    
    Args:
        file_path: Path to file to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f'Deleted file: {file_path}')
            return True
        return False
    except Exception as e:
        logger.error(f'Error deleting file {file_path}: {str(e)}')
        return False

def get_image_dimensions(file_path):
    """
    Get image dimensions
    
    Args:
        file_path: Path to image file
        
    Returns:
        tuple: (width, height) or (0, 0) if error
    """
    try:
        with Image.open(file_path) as image:
            return image.size
    except Exception:
        return (0, 0)

def get_image_info(file_path):
    """
    Get comprehensive image information
    
    Args:
        file_path: Path to image file
        
    Returns:
        dict: Image information or None if error
    """
    try:
        with Image.open(file_path) as image:
            return {
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'mode': image.mode,
                'size_bytes': os.path.getsize(file_path),
                'mime_type': mimetypes.guess_type(file_path)[0]
            }
    except Exception as e:
        logger.error(f"Failed to get image info for {file_path}: {str(e)}")
        return None
