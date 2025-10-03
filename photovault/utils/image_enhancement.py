"""
Image Enhancement Utilities for PhotoVault
Provides auto-enhancement functions for digitizing old photographs
"""

import numpy as np
from PIL import Image, ImageEnhance, ExifTags
import json
import logging
from typing import Dict, Tuple, Optional, Union
import os

logger = logging.getLogger(__name__)

# Optional OpenCV import for enhanced features
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV available - full image enhancement features enabled")
except ImportError as e:
    cv2 = None
    OPENCV_AVAILABLE = False
    logger.warning(f"OpenCV not available - limited image enhancement features: {e}")

class ImageEnhancer:
    """Advanced image enhancement for old photograph restoration"""
    
    def __init__(self):
        self.default_settings = {
            'brightness': 1.0,
            'contrast': 1.0,
            'sharpness': 1.0,
            'color': 1.0,
            'denoise': True,
            'clahe_enabled': True,
            'auto_levels': True,
            'colorize': False
        }
    
    def auto_enhance_photo(self, image_path: str, output_path: str = None, 
                          settings: Dict = None) -> Tuple[str, Dict]:
        """
        Automatically enhance a photo for optimal viewing
        
        Args:
            image_path: Path to input image
            output_path: Path for enhanced output (if None, overwrites original)
            settings: Custom enhancement settings
            
        Returns:
            Tuple of (output_path, applied_settings)
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Starting auto-enhancement for: {image_path}")
        
        # Merge default with custom settings
        enhancement_settings = self.default_settings.copy()
        if settings:
            enhancement_settings.update(settings)
        
        if OPENCV_AVAILABLE:
            # Full OpenCV enhancement pipeline
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Step 0: Colorize if enabled
            if enhancement_settings.get('colorize', False):
                img = self._apply_colorization(img)
            
            # Step 1: Denoise if enabled
            if enhancement_settings.get('denoise', True):
                img = self._apply_denoising(img)
            
            # Step 2: Apply CLAHE for contrast enhancement
            if enhancement_settings.get('clahe_enabled', True):
                img = self._apply_clahe(img)
            
            # Step 3: Auto-levels adjustment
            if enhancement_settings.get('auto_levels', True):
                img = self._apply_auto_levels(img)
            
            # Step 4: Convert to PIL for fine adjustments
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        else:
            # Fallback to PIL-only enhancement
            logger.info("Using PIL-only enhancement (OpenCV not available)")
            pil_img = Image.open(image_path)
            
            # Apply colorization using PIL if requested
            if enhancement_settings.get('colorize', False):
                pil_img = self._apply_colorization_pil(pil_img)
        
        # Step 5: Apply PIL enhancements
        pil_img = self._apply_pil_enhancements(pil_img, enhancement_settings)
        
        # Step 6: Save enhanced image
        if output_path is None:
            output_path = image_path
        
        if OPENCV_AVAILABLE:
            # Convert back to BGR for OpenCV saving
            final_cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            # Save with original quality
            success = cv2.imwrite(output_path, final_cv_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            if not success:
                raise IOError(f"Failed to save enhanced image: {output_path}")
        else:
            # Use PIL for saving
            pil_img.save(output_path, 'JPEG', quality=95)
        
        logger.info(f"Auto-enhancement completed: {output_path}")
        return output_path, enhancement_settings
    
    def _apply_denoising(self, img: np.ndarray) -> np.ndarray:
        """Apply bilateral filtering to reduce noise while preserving edges"""
        if not OPENCV_AVAILABLE:
            return img
        try:
            # Bilateral filter - reduces noise while keeping edges sharp
            return cv2.bilateralFilter(img, 9, 75, 75)
        except Exception as e:
            logger.warning(f"Denoising failed: {e}")
            return img
    
    def _apply_clahe(self, img: np.ndarray) -> np.ndarray:
        """Apply Contrast Limited Adaptive Histogram Equalization"""
        if not OPENCV_AVAILABLE:
            return img
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to the L channel only
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_l = clahe.apply(l)
            
            # Merge channels back
            enhanced_lab = cv2.merge([enhanced_l, a, b])
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        except Exception as e:
            logger.warning(f"CLAHE enhancement failed: {e}")
            return img
    
    def _apply_auto_levels(self, img: np.ndarray) -> np.ndarray:
        """Automatically adjust levels to improve dynamic range"""
        try:
            # Convert to float for calculations
            img_float = img.astype(np.float64) / 255.0
            
            # Calculate percentile-based levels (ignore extreme 1% on each end)
            low_perc = np.percentile(img_float, 1)
            high_perc = np.percentile(img_float, 99)
            
            # Avoid division by zero
            if high_perc - low_perc < 0.01:
                return img
            
            # Stretch levels
            img_stretched = (img_float - low_perc) / (high_perc - low_perc)
            img_stretched = np.clip(img_stretched, 0, 1)
            
            return (img_stretched * 255).astype(np.uint8)
        except Exception as e:
            logger.warning(f"Auto-levels adjustment failed: {e}")
            return img
    
    def _apply_colorization(self, img: np.ndarray) -> np.ndarray:
        """
        Apply automatic colorization to grayscale images using LAB color space
        This uses a simple but effective technique to add warm tones to B&W photos
        """
        if not OPENCV_AVAILABLE:
            return img
        try:
            # Check if image is grayscale or already color
            if len(img.shape) == 2:
                # Image is grayscale, convert to BGR first
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            
            # Check if image is already colorful (not grayscale)
            b, g, r = cv2.split(img)
            if not (np.allclose(b, g, atol=5) and np.allclose(g, r, atol=5)):
                # Image already has color, skip colorization
                logger.info("Image already has color, skipping colorization")
                return img
            
            # Convert to LAB color space for colorization
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply warm sepia-like tones to create a colorized effect
            # Add warm tones (yellow-orange) to the A channel
            a_colored = np.clip(a.astype(np.float32) + 10, 0, 255).astype(np.uint8)
            # Add slight warm tones to the B channel
            b_colored = np.clip(b.astype(np.float32) + 15, 0, 255).astype(np.uint8)
            
            # Merge back and convert to BGR
            colorized_lab = cv2.merge([l, a_colored, b_colored])
            colorized = cv2.cvtColor(colorized_lab, cv2.COLOR_LAB2BGR)
            
            logger.info("Applied automatic colorization with warm tones")
            return colorized
            
        except Exception as e:
            logger.warning(f"Colorization failed: {e}")
            return img
    
    def _apply_colorization_pil(self, pil_img: Image.Image) -> Image.Image:
        """
        Apply colorization using PIL (fallback method)
        Converts grayscale to sepia tone
        """
        try:
            # Convert to grayscale first if not already
            if pil_img.mode != 'L':
                # Check if image is effectively grayscale
                r, g, b = pil_img.split()
                if not (np.array_equal(np.array(r), np.array(g)) and np.array_equal(np.array(g), np.array(b))):
                    logger.info("Image already has color, skipping PIL colorization")
                    return pil_img
                pil_img = pil_img.convert('L')
            
            # Convert to RGB
            pil_img = pil_img.convert('RGB')
            
            # Apply sepia tone effect
            width, height = pil_img.size
            pixels = pil_img.load()
            
            for py in range(height):
                for px in range(width):
                    r, g, b = pil_img.getpixel((px, py))
                    
                    # Sepia tone formula
                    tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                    tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                    tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                    
                    # Clamp values
                    pixels[px, py] = (min(255, tr), min(255, tg), min(255, tb))
            
            logger.info("Applied PIL sepia tone colorization")
            return pil_img
            
        except Exception as e:
            logger.warning(f"PIL colorization failed: {e}")
            return pil_img
    
    def _apply_pil_enhancements(self, pil_img: Image.Image, settings: Dict) -> Image.Image:
        """Apply PIL-based enhancements for fine-tuning"""
        try:
            # Brightness adjustment
            if settings.get('brightness', 1.0) != 1.0:
                brightness_enhancer = ImageEnhance.Brightness(pil_img)
                pil_img = brightness_enhancer.enhance(settings['brightness'])
            
            # Contrast adjustment
            if settings.get('contrast', 1.0) != 1.0:
                contrast_enhancer = ImageEnhance.Contrast(pil_img)
                pil_img = contrast_enhancer.enhance(settings['contrast'])
            
            # Color/Saturation adjustment
            if settings.get('color', 1.0) != 1.0:
                color_enhancer = ImageEnhance.Color(pil_img)
                pil_img = color_enhancer.enhance(settings['color'])
            
            # Sharpness adjustment
            if settings.get('sharpness', 1.0) != 1.0:
                sharpness_enhancer = ImageEnhance.Sharpness(pil_img)
                pil_img = sharpness_enhancer.enhance(settings['sharpness'])
            
            return pil_img
        except Exception as e:
            logger.warning(f"PIL enhancements failed: {e}")
            return pil_img
    
    def detect_and_enhance_old_photo(self, image_path: str) -> Dict:
        """
        Analyze photo characteristics and suggest optimal enhancement settings
        Particularly useful for old, faded, or damaged photographs
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return self.default_settings.copy()
            
            # Analyze image characteristics
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calculate metrics
            brightness = np.mean(gray) / 255.0
            contrast = np.std(gray) / 255.0
            
            # Suggest enhancements based on analysis
            suggested_settings = self.default_settings.copy()
            
            # Adjust brightness if image is too dark or too bright
            if brightness < 0.3:  # Dark image
                suggested_settings['brightness'] = 1.3
                suggested_settings['contrast'] = 1.2
            elif brightness > 0.8:  # Bright/overexposed image
                suggested_settings['brightness'] = 0.8
                suggested_settings['contrast'] = 1.1
            
            # Increase contrast if image appears flat
            if contrast < 0.1:  # Low contrast
                suggested_settings['contrast'] = 1.5
                suggested_settings['clahe_enabled'] = True
            
            # Enhance sharpness for older photos
            suggested_settings['sharpness'] = 1.2
            
            # Slightly enhance color for faded photos
            suggested_settings['color'] = 1.1
            
            logger.info(f"Suggested enhancement settings for old photo: {suggested_settings}")
            return suggested_settings
            
        except Exception as e:
            logger.error(f"Error analyzing photo for enhancement: {e}")
            return self.default_settings.copy()
    
    def create_enhanced_copy(self, original_path: str, user_id: int) -> str:
        """Create an enhanced copy of the original image"""
        try:
            # Generate enhanced filename
            base, ext = os.path.splitext(original_path)
            enhanced_path = f"{base}_enhanced{ext}"
            
            # Detect optimal settings for old photos
            optimal_settings = self.detect_and_enhance_old_photo(original_path)
            
            # Apply enhancements
            output_path, applied_settings = self.auto_enhance_photo(
                original_path, enhanced_path, optimal_settings
            )
            
            return enhanced_path
            
        except Exception as e:
            logger.error(f"Error creating enhanced copy: {e}")
            return original_path

# Create global enhancer instance
enhancer = ImageEnhancer()

def auto_enhance_photo(image_path: str, output_path: str = None, 
                      settings: Dict = None) -> Tuple[str, Dict]:
    """Convenience function for auto-enhancing photos"""
    return enhancer.auto_enhance_photo(image_path, output_path, settings)

def enhance_for_old_photo(image_path: str, output_path: str = None) -> Tuple[str, Dict]:
    """Enhanced specifically for digitized old photographs"""
    optimal_settings = enhancer.detect_and_enhance_old_photo(image_path)
    return enhancer.auto_enhance_photo(image_path, output_path, optimal_settings)