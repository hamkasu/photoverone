# photovault/services/montage_service.py

import os
import io
import logging
import uuid
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from flask import current_app
from datetime import datetime

from photovault.utils.enhanced_file_handler import save_uploaded_file_enhanced
from photovault.utils.file_handler import get_image_dimensions
from photovault.services.app_storage_service import app_storage

logger = logging.getLogger(__name__)

class MontageService:
    """Service for creating photo montages/collages"""
    
    def __init__(self):
        self.default_settings = {
            'rows': 2,
            'cols': 2,
            'spacing': 10,
            'background_color': (255, 255, 255),  # White background
            'target_width': 1200,
            'target_height': 800,
            'maintain_aspect': True,
            'border_width': 2,
            'border_color': (200, 200, 200),
            'title': '',
            'title_height': 50
        }
    
    def create_montage(self, photo_paths: List[str], settings: Optional[Dict] = None, 
                      user_id: Optional[int] = None) -> Tuple[bool, str, Dict]:
        """
        Create a montage from multiple photo paths
        
        Args:
            photo_paths: List of file paths to photos
            settings: Custom montage settings
            user_id: User ID for organizing files
            
        Returns:
            tuple: (success, file_path_or_error, applied_settings)
        """
        try:
            if len(photo_paths) < 2:
                return False, "At least 2 photos are required for a montage", {}
            
            # Merge settings with defaults
            montage_settings = self.default_settings.copy()
            if settings:
                montage_settings.update(settings)
            
            logger.info(f"Creating montage from {len(photo_paths)} photos")
            
            # Calculate grid dimensions
            total_photos = len(photo_paths)
            rows = montage_settings['rows']
            cols = montage_settings['cols']
            
            # Auto-adjust grid if needed
            if rows * cols < total_photos:
                cols = (total_photos + rows - 1) // rows  # Ceiling division
                montage_settings['cols'] = cols
            
            # Load and prepare images
            images = []
            for photo_path in photo_paths:
                success, image = self._load_and_prepare_image(photo_path, montage_settings)
                if success:
                    images.append(image)
                else:
                    logger.warning(f"Failed to load image: {photo_path}")
            
            if len(images) < 2:
                return False, "Could not load enough valid images for montage", {}
            
            # Create the montage
            success, montage_image = self._create_grid_montage(images, montage_settings)
            if not success:
                return False, montage_image, {}  # montage_image contains error message
            
            # Add title if specified
            if montage_settings.get('title'):
                montage_image = self._add_title(montage_image, montage_settings['title'], montage_settings)
            
            # Save the montage
            success, file_path = self._save_montage(montage_image, user_id)
            if success:
                logger.info(f"Montage created successfully: {file_path}")
                return True, file_path, montage_settings
            else:
                return False, file_path, {}
                
        except Exception as e:
            logger.error(f"Error creating montage: {str(e)}")
            return False, f"Failed to create montage: {str(e)}", {}
    
    def _load_and_prepare_image(self, photo_path: str, settings: Dict) -> Tuple[bool, Optional[Image.Image]]:
        """Load and prepare an image for the montage"""
        try:
            # Check if file exists for local files or handle app storage paths
            if not photo_path.startswith('users/'):
                # Local file path
                if not os.path.exists(photo_path):
                    logger.error(f"Image file not found: {photo_path}")
                    return False, None
                image = Image.open(photo_path)
            else:
                # App Storage path
                success, image_bytes = app_storage.download_file(photo_path)
                if not success:
                    logger.error(f"Failed to download image from app storage: {photo_path}")
                    return False, None
                image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            
            # Calculate target size for each image in grid
            target_width = settings['target_width'] // settings['cols'] - settings['spacing']
            target_height = settings['target_height'] // settings['rows'] - settings['spacing']
            
            # Resize while maintaining aspect ratio
            if settings['maintain_aspect']:
                image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            else:
                image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            return True, image
            
        except Exception as e:
            logger.error(f"Error preparing image {photo_path}: {str(e)}")
            return False, None
    
    def _create_grid_montage(self, images: List[Image.Image], settings: Dict) -> Tuple[bool, Any]:
        """Create a grid-based montage from prepared images"""
        try:
            rows = settings['rows']
            cols = settings['cols']
            spacing = settings['spacing']
            bg_color = settings['background_color']
            border_width = settings['border_width']
            border_color = settings['border_color']
            
            # Calculate cell dimensions
            if not images:
                return False, "No images provided"
            
            # Use the first image to determine cell size
            sample_image = images[0]
            cell_width, cell_height = sample_image.size
            
            # Calculate total montage dimensions
            total_width = cols * cell_width + (cols + 1) * spacing
            total_height = rows * cell_height + (rows + 1) * spacing
            
            # Add title height if needed
            if settings.get('title'):
                total_height += settings['title_height']
            
            # Create the montage canvas
            montage = Image.new('RGB', (total_width, total_height), bg_color)
            
            # Calculate starting Y position (account for title)
            start_y = settings['title_height'] if settings.get('title') else 0
            
            # Place images in grid
            for idx, image in enumerate(images):
                if idx >= rows * cols:
                    break  # Don't exceed grid capacity
                
                row = idx // cols
                col = idx % cols
                
                # Calculate position
                x = spacing + col * (cell_width + spacing)
                y = start_y + spacing + row * (cell_height + spacing)
                
                # Create a bordered version if border is specified
                if border_width > 0:
                    bordered_image = Image.new('RGB', 
                                             (image.width + 2*border_width, image.height + 2*border_width), 
                                             border_color)
                    bordered_image.paste(image, (border_width, border_width))
                    montage.paste(bordered_image, (x - border_width, y - border_width))
                else:
                    montage.paste(image, (x, y))
            
            return True, montage
            
        except Exception as e:
            logger.error(f"Error creating grid montage: {str(e)}")
            return False, f"Failed to create montage grid: {str(e)}"
    
    def _add_title(self, montage: Image.Image, title: str, settings: Dict) -> Image.Image:
        """Add a title to the montage"""
        try:
            draw = ImageDraw.Draw(montage)
            
            # Try to use a nice font, fall back to default
            try:
                # Try to find a good font
                font_size = 24
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except (OSError, IOError):
                    font = ImageFont.load_default()
            
            # Calculate text position (centered)
            text_bbox = draw.textbbox((0, 0), title, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (montage.width - text_width) // 2
            y = (settings['title_height'] - text_height) // 2
            
            # Draw text
            draw.text((x, y), title, fill=(50, 50, 50), font=font)
            
            return montage
            
        except Exception as e:
            logger.error(f"Error adding title to montage: {str(e)}")
            return montage  # Return montage without title on error
    
    def _save_montage(self, montage: Image.Image, user_id: Optional[int]) -> Tuple[bool, str]:
        """Save the montage to storage"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"montage_{timestamp}_{str(uuid.uuid4())[:8]}.jpg"
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            montage.save(img_bytes, format='JPEG', quality=90, optimize=True)
            img_bytes.seek(0)
            
            # Save using enhanced file handler
            success, file_path = save_uploaded_file_enhanced(img_bytes, filename, user_id)
            
            return success, file_path
            
        except Exception as e:
            logger.error(f"Error saving montage: {str(e)}")
            return False, f"Failed to save montage: {str(e)}"


# Create global instance
montage_service = MontageService()

def create_montage(photo_paths: List[str], settings: Optional[Dict] = None, 
                  user_id: Optional[int] = None) -> Tuple[bool, str, Dict]:
    """
    Convenience function to create a montage
    
    Args:
        photo_paths: List of file paths to photos
        settings: Custom montage settings
        user_id: User ID for organizing files
        
    Returns:
        tuple: (success, file_path_or_error, applied_settings)
    """
    return montage_service.create_montage(photo_paths, settings, user_id)