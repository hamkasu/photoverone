# photovault/services/app_storage_service.py

import os
import io
import logging
from typing import Optional, Tuple, BinaryIO
from flask import current_app
from replit.object_storage import Client
from PIL import Image

logger = logging.getLogger(__name__)

class AppStorageService:
    """Service for handling file storage using Replit App Storage"""
    
    def __init__(self):
        """Initialize the App Storage client"""
        try:
            # Check if we're in Replit environment
            import os
            if not os.environ.get('REPLIT_DB_URL') and not os.environ.get('REPL_ID'):
                logger.info("Not in Replit environment, skipping App Storage initialization")
                self.client = None
                return
                
            self.client = Client()
            logger.info("App Storage client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize App Storage client: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if App Storage is available"""
        return self.client is not None
    
    def upload_file(self, file_obj: BinaryIO, object_name: str, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload a file to App Storage
        
        Args:
            file_obj: File-like object to upload
            object_name: Name of the object in storage
            user_id: Optional user ID for organizing files
            
        Returns:
            tuple: (success, object_path_or_error_message)
        """
        try:
            if not self.is_available():
                return False, "App Storage not available"
            
            # Create user-specific path if user_id provided
            if user_id:
                storage_path = f"users/{user_id}/{object_name}"
            else:
                storage_path = f"uploads/{object_name}"
            
            # Upload file from bytes
            file_obj.seek(0)
            file_bytes = file_obj.read()
            
            result = self.client.upload_from_bytes(storage_path, file_bytes)
            
            if result.error:
                logger.error(f"App Storage upload error: {result.error}")
                return False, f"Upload failed: {result.error}"
            
            logger.info(f"File uploaded successfully to App Storage: {storage_path}")
            return True, storage_path
            
        except Exception as e:
            logger.error(f"Error uploading to App Storage: {str(e)}")
            return False, f"Upload error: {str(e)}"
    
    def download_file(self, object_path: str) -> Tuple[bool, bytes]:
        """
        Download a file from App Storage
        
        Args:
            object_path: Path to the object in storage
            
        Returns:
            tuple: (success, file_bytes_or_error_message)
        """
        try:
            if not self.is_available():
                return False, b"App Storage not available"
            
            result = self.client.download_as_bytes(object_path)
            
            if result.error:
                logger.error(f"App Storage download error: {result.error}")
                return False, str(result.error).encode()
            
            return True, result.value
            
        except Exception as e:
            logger.error(f"Error downloading from App Storage: {str(e)}")
            return False, str(e).encode()
    
    def delete_file(self, object_path: str) -> bool:
        """
        Delete a file from App Storage
        
        Args:
            object_path: Path to the object in storage
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if not self.is_available():
                return False
            
            result = self.client.delete(object_path)
            
            if result.error:
                logger.error(f"App Storage delete error: {result.error}")
                return False
            
            logger.info(f"File deleted successfully from App Storage: {object_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from App Storage: {str(e)}")
            return False
    
    def file_exists(self, object_path: str) -> bool:
        """
        Check if a file exists in App Storage
        
        Args:
            object_path: Path to the object in storage
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            if not self.is_available():
                return False
            
            # Try to download just the metadata/first byte to check existence
            result = self.client.download_as_bytes(object_path)
            return not result.error
            
        except Exception as e:
            logger.error(f"Error checking file existence: {str(e)}")
            return False
    
    def create_thumbnail(self, original_object_path: str, thumbnail_size: Tuple[int, int] = (150, 150)) -> Tuple[bool, str]:
        """
        Create and upload a thumbnail for an image
        
        Args:
            original_object_path: Path to the original image in storage
            thumbnail_size: Tuple of (width, height) for thumbnail
            
        Returns:
            tuple: (success, thumbnail_path_or_error)
        """
        try:
            if not self.is_available():
                return False, "App Storage not available"
            
            # Download original image
            success, image_bytes = self.download_file(original_object_path)
            if not success:
                return False, f"Failed to download original image: {image_bytes}"
            
            # Open image and create thumbnail
            with Image.open(io.BytesIO(image_bytes)) as image:
                # Convert RGBA to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                    image = rgb_image
                
                # Create thumbnail
                image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail to bytes
                thumbnail_bytes = io.BytesIO()
                image.save(thumbnail_bytes, 'JPEG', optimize=True, quality=85)
                thumbnail_bytes.seek(0)
                
                # Generate thumbnail path
                base_path, ext = os.path.splitext(original_object_path)
                thumbnail_path = f"{base_path}_thumb.jpg"
                
                # Determine user_id correctly
                user_id = None
                if original_object_path.startswith('users/') and '/' in original_object_path[6:]:
                    user_id = original_object_path.split('/')[1]
                
                # Upload thumbnail
                success, upload_path = self.upload_file(thumbnail_bytes, os.path.basename(thumbnail_path), user_id)
                
                if success:
                    return True, upload_path
                else:
                    return False, upload_path
                    
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            return False, str(e)
    
    def get_image_info(self, object_path: str) -> Optional[dict]:
        """
        Get image information from App Storage
        
        Args:
            object_path: Path to the image in storage
            
        Returns:
            dict: Image information or None if error
        """
        try:
            if not self.is_available():
                return None
            
            # Download image
            success, image_bytes = self.download_file(object_path)
            if not success:
                return None
            
            with Image.open(io.BytesIO(image_bytes)) as image:
                return {
                    'width': image.width,
                    'height': image.height,
                    'format': image.format,
                    'mode': image.mode,
                    'size_bytes': len(image_bytes),
                    'mime_type': f"image/{image.format.lower()}" if image.format else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get image info for {object_path}: {str(e)}")
            return None

# Global instance
app_storage = AppStorageService()