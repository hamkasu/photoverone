# photovault/utils/enhanced_file_handler.py

import os
import uuid
import mimetypes
import io
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image
import logging
from photovault.services.app_storage_service import app_storage
from photovault.utils.file_handler import validate_image_file, generate_unique_filename

logger = logging.getLogger(__name__)

def save_uploaded_file_enhanced(file, filename, user_id=None):
    """
    Save uploaded file to App Storage with fallback to local directory
    
    Args:
        file: FileStorage object from Flask request
        filename: String filename to save as
        user_id: Optional user ID for organizing files
        
    Returns:
        tuple: (success, file_path_or_error_message)
    """
    try:
        # Try App Storage first
        if app_storage.is_available():
            logger.info(f'Using App Storage for file: {filename}')
            success, storage_path = app_storage.upload_file(file, filename, str(user_id) if user_id else None)
            if success:
                logger.info(f'File saved successfully to App Storage: {filename}')
                return True, storage_path
            else:
                logger.warning(f'App Storage failed, falling back to local storage: {storage_path}')
        
        # Fallback to local storage
        logger.info(f'Using local storage for file: {filename}')
        
        # Get upload directory
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
        if not upload_folder:
            return False, 'UPLOAD_FOLDER not configured'
        
        # Create user-specific subdirectory if user_id provided
        if user_id:
            upload_folder = os.path.join(upload_folder, str(user_id))
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(upload_folder, filename)
        
        # Reset file pointer for local save
        file.seek(0)
        
        # Save the file
        file.save(file_path)
        
        # Verify file was saved
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logger.info(f'File saved successfully to local storage: {filename}')
            return True, file_path
        else:
            logger.error(f'File not found after save or is empty: {filename}')
            return False, 'File save verification failed'
            
    except Exception as e:
        logger.error(f'Error saving file {filename}: {str(e)}')
        return False, f'Save error: {str(e)}'

def create_thumbnail_enhanced(file_path, thumbnail_size=(150, 150)):
    """
    Create thumbnail for uploaded image, supporting both App Storage and local files
    
    Args:
        file_path: Path to original image (App Storage path or local path)
        thumbnail_size: Tuple of (width, height) for thumbnail
        
    Returns:
        tuple: (success, thumbnail_path_or_error)
    """
    try:
        # Check if it's an App Storage path
        if file_path.startswith('users/') or file_path.startswith('uploads/'):
            # Use App Storage
            return app_storage.create_thumbnail(file_path, thumbnail_size)
        else:
            # Use local file system (fallback to original implementation)
            return _create_thumbnail_local(file_path, thumbnail_size)
            
    except Exception as e:
        logger.error(f'Error creating thumbnail: {str(e)}')
        return False, str(e)

def _create_thumbnail_local(file_path, thumbnail_size=(150, 150)):
    """
    Create thumbnail for local image file
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
        logger.error(f'Error creating local thumbnail: {str(e)}')
        return False, str(e)

def delete_file_enhanced(file_path):
    """
    Safely delete a file from App Storage or local filesystem
    
    Args:
        file_path: Path to file to delete (App Storage path or local path)
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # Check if it's an App Storage path
        if file_path.startswith('users/') or file_path.startswith('uploads/'):
            # Use App Storage
            return app_storage.delete_file(file_path)
        else:
            # Use local file system
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f'Deleted local file: {file_path}')
                return True
            return False
            
    except Exception as e:
        logger.error(f'Error deleting file {file_path}: {str(e)}')
        return False

def get_image_info_enhanced(file_path):
    """
    Get comprehensive image information from App Storage or local files
    
    Args:
        file_path: Path to image file (App Storage path or local path)
        
    Returns:
        dict: Image information or None if error
    """
    try:
        # Check if it's an App Storage path and App Storage is available
        if (file_path.startswith('users/') or file_path.startswith('uploads/')) and app_storage.is_available():
            # Use App Storage
            return app_storage.get_image_info(file_path)
        else:
            # Use local file system - treat App Storage paths as local paths when App Storage unavailable
            if file_path.startswith('users/') or file_path.startswith('uploads/'):
                # Convert App Storage path to local path by stripping the storage namespace
                from flask import current_app
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
                # Strip the leading 'users/' or 'uploads/' prefix 
                path_parts = file_path.split('/', 1)
                if len(path_parts) > 1:
                    local_relative_path = path_parts[1]  # e.g., '123/photo.jpg'
                    local_path = os.path.join(upload_folder, local_relative_path)
                    file_path = local_path
                else:
                    file_path = os.path.join(upload_folder, file_path)
            
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

def get_file_content(file_path):
    """
    Get file content from App Storage or local filesystem
    
    Args:
        file_path: Path to file (App Storage path or local path)
        
    Returns:
        tuple: (success, file_bytes_or_error_message)
    """
    try:
        # Check if it's an App Storage path and App Storage is available
        if (file_path.startswith('users/') or file_path.startswith('uploads/')) and app_storage.is_available():
            # Use App Storage
            return app_storage.download_file(file_path)
        else:
            # Use local file system - treat App Storage paths as local paths when App Storage unavailable
            if file_path.startswith('users/') or file_path.startswith('uploads/'):
                # Convert App Storage path to local path by stripping the storage namespace
                from flask import current_app
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
                # Strip the leading 'users/' or 'uploads/' prefix 
                path_parts = file_path.split('/', 1)
                if len(path_parts) > 1:
                    local_relative_path = path_parts[1]  # e.g., '123/photo.jpg'
                    local_path = os.path.join(upload_folder, local_relative_path)
                    file_path = local_path
                else:
                    file_path = os.path.join(upload_folder, file_path)
                
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                return True, content
            else:
                return False, f"File not found: {file_path}".encode()
                
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return False, str(e).encode()

def file_exists_enhanced(file_path):
    """
    Check if file exists in App Storage or local filesystem
    
    Args:
        file_path: Path to file (App Storage path or local path)
        
    Returns:
        bool: True if file exists, False otherwise
    """
    try:
        # Check if it's an App Storage path and App Storage is available
        if (file_path.startswith('users/') or file_path.startswith('uploads/')) and app_storage.is_available():
            # Use App Storage
            return app_storage.file_exists(file_path)
        else:
            # Use local file system - treat App Storage paths as local paths when App Storage unavailable
            if file_path.startswith('users/') or file_path.startswith('uploads/'):
                # Convert App Storage path to local path by stripping the storage namespace
                from flask import current_app
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'photovault/uploads')
                # Strip the leading 'users/' or 'uploads/' prefix 
                path_parts = file_path.split('/', 1)
                if len(path_parts) > 1:
                    local_relative_path = path_parts[1]  # e.g., '123/photo.jpg'
                    local_path = os.path.join(upload_folder, local_relative_path)
                    return os.path.exists(local_path)
                else:
                    return os.path.exists(os.path.join(upload_folder, file_path))
            else:
                return os.path.exists(file_path)
            
    except Exception as e:
        logger.error(f"Error checking file existence {file_path}: {str(e)}")
        return False