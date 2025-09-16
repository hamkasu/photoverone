# photovault/utils/file_handler.py

import os
from flask import current_app
from werkzeug.utils import secure_filename
import uuid
from PIL import Image
import io

def validate_image_file(file):
    """
    Validate uploaded image file
    
    Args:
        file: FileStorage object from Flask request
        
    Returns:
        bool: True if valid image file, False otherwise
    """
    # Check file exists and has filename
    if not file or not file.filename:
        return False
    
    # Check file type by MIME type
    allowed_types = [
        'image/jpeg', 
        'image/jpg', 
        'image/png', 
        'image/gif', 
        'image/webp'
    ]
    
    if file.content_type not in allowed_types:
        return False
    
    # Check file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    
    if file_ext not in allowed_extensions:
        return False
    
    # Check file size (16MB max)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    max_size = 16 * 1024 * 1024  # 16MB
    if file_size > max_size:
        return False
    
    # Optional: Validate actual image content
    try:
        file.seek(0)
        image = Image.open(file)
        image.verify()  # Verify it's a valid image
        file.seek(0)  # Reset file pointer again
        return True
    except Exception:
        file.seek(0)  # Reset file pointer on error
        return False

def save_uploaded_file(file, filename):
    """
    Save uploaded file to the upload directory
    
    Args:
        file: FileStorage object from Flask request
        filename: String filename to save as
        
    Returns:
        str: Full path to saved file, or None if error
    """
    try:
        # Get upload directory
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            current_app.logger.error('UPLOAD_FOLDER not configured')
            return None
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(upload_folder, filename)
        
        # Save the file
        file.save(file_path)
        
        # Verify file was saved
        if os.path.exists(file_path):
            current_app.logger.info(f'File saved successfully: {filename}')
            return file_path
        else:
            current_app.logger.error(f'File not found after save: {filename}')
            return None
            
    except Exception as e:
        current_app.logger.error(f'Error saving file {filename}: {str(e)}')
        return None

def generate_unique_filename(original_filename):
    """
    Generate a unique filename while preserving the original extension
    
    Args:
        original_filename: Original filename from upload
        
    Returns:
        str: Unique filename with original extension
    """
    # Secure the filename
    safe_filename = secure_filename(original_filename)
    
    # Get file extension
    _, file_ext = os.path.splitext(safe_filename)
    
    # Generate unique name with UUID
    unique_name = str(uuid.uuid4().hex)
    
    # Combine with original extension
    return f"{unique_name}{file_ext}"

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
        str: Path to thumbnail file, or None if error
    """
    try:
        # Open image
        with Image.open(file_path) as image:
            # Create thumbnail
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Generate thumbnail filename
            base_path, ext = os.path.splitext(file_path)
            thumbnail_path = f"{base_path}_thumb{ext}"
            
            # Save thumbnail
            image.save(thumbnail_path, optimize=True, quality=85)
            
            return thumbnail_path
            
    except Exception as e:
        current_app.logger.error(f'Error creating thumbnail: {str(e)}')
        return None

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
            return True
        return False
    except Exception as e:
        current_app.logger.error(f'Error deleting file {file_path}: {str(e)}')
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