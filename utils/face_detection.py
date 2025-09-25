"""
Face Detection Utilities for PhotoVault
Face detection functionality has been disabled
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FaceDetector:
    """Face detection - DISABLED (OpenCV removed)"""
    
    def __init__(self):
        self.opencv_available = False
        self.face_cascade = None
        self.dnn_net = None
        self.confidence_threshold = 0.5
        logger.info("Face detection disabled - OpenCV functionality removed")
    
    def detect_faces(self, image_path: str) -> List[Dict]:
        """
        Detect faces in an image - DISABLED
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Empty list (face detection disabled)
        """
        logger.warning("Face detection is disabled - OpenCV functionality removed")
        return []
    
    def is_available(self) -> bool:
        """Check if face detection is available - always returns False"""
        return False

# Global instance
face_detector = FaceDetector()

def detect_faces(image_path: str) -> List[Dict]:
    """Convenience function for detecting faces in an image - DISABLED"""
    return face_detector.detect_faces(image_path)