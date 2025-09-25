"""
PhotoVault Photo Detection
Photo detection functionality has been disabled
"""
import os
import logging
from typing import List, Dict, Tuple
from PIL import Image

logger = logging.getLogger(__name__)

# OpenCV functionality disabled
OPENCV_AVAILABLE = False
logger.info("Photo detection disabled - OpenCV functionality removed")

class PhotoDetector:
    """Photo detection - DISABLED (OpenCV removed)"""
    
    def __init__(self):
        self.min_photo_area = 10000
        self.max_photo_area_ratio = 0.8
        self.min_aspect_ratio = 0.3
        self.max_aspect_ratio = 3.0
        self.contour_area_threshold = 0.01
        
    def detect_photos(self, image_path: str) -> List[Dict]:
        """
        Detect rectangular photos in an image - DISABLED
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Empty list (photo detection disabled)
        """
        logger.warning("Photo detection is disabled - OpenCV functionality removed")
        return []
    
    def extract_detected_photos(self, image_path: str, detected_photos: List[Dict] = None) -> List[Dict]:
        """
        Extract detected photos from an image - DISABLED
        
        Args:
            image_path: Path to the source image
            detected_photos: List of detected photo regions (ignored)
            
        Returns:
            Empty list (photo extraction disabled)
        """
        logger.warning("Photo extraction is disabled - OpenCV functionality removed")
        return []

# Global instance
photo_detector = PhotoDetector()

def detect_photos_in_image(image_path: str) -> List[Dict]:
    """Convenience function for detecting photos in an image - DISABLED"""
    return photo_detector.detect_photos(image_path)

def extract_detected_photos(image_path: str, detected_photos: List[Dict] = None) -> List[Dict]:
    """Convenience function for extracting detected photos - DISABLED"""
    return photo_detector.extract_detected_photos(image_path, detected_photos)