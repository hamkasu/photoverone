"""
Face Detection Service for PhotoVault
Face detection functionality has been disabled
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)

class FaceDetectionService:
    """Service for face detection - DISABLED (OpenCV removed)"""
    
    def __init__(self):
        self.face_detector = None
        self.face_recognizer = None
        logger.info("Face detection service disabled - OpenCV functionality removed")
    
    def process_photo_faces(self, photo) -> List[Dict]:
        """
        Process a photo to detect faces - DISABLED
        
        Args:
            photo: Photo model instance
            
        Returns:
            Empty list (face detection disabled)
        """
        logger.warning("Face detection is disabled - cannot process photo faces")
        return []
    
    def is_available(self) -> bool:
        """Check if face detection service is available - always returns False"""
        return False

# Global instance
face_detection_service = FaceDetectionService()