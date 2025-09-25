"""
Face Recognition Utilities for PhotoVault
Face recognition functionality has been disabled
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class FaceRecognizer:
    """Face recognition - DISABLED (OpenCV removed)"""
    
    def __init__(self):
        self.opencv_available = False
        self.face_recognizer = None
        self.face_cascade = None
        self.encodings_cache = {}
        self.encodings_file = Path(__file__).parent / 'face_encodings.pkl'
        logger.info("Face recognition disabled - OpenCV functionality removed")
    
    def is_available(self) -> bool:
        """Check if face recognition is available - always returns False"""
        return False
    
    def add_person_encoding(self, person_id: int, person_name: str, 
                           image_path: str, face_box: Dict) -> bool:
        """
        Add a person's face encoding - DISABLED
        
        Args:
            person_id: Database ID of the person
            person_name: Name of the person
            image_path: Path to the image containing the face
            face_box: Face bounding box dictionary
            
        Returns:
            False (face recognition disabled)
        """
        logger.warning("Face recognition is disabled - cannot add person encoding")
        return False
    
    def recognize_faces(self, image_path: str, face_boxes: List[Dict]) -> List[Dict]:
        """
        Recognize faces in an image - DISABLED
        
        Args:
            image_path: Path to the image
            face_boxes: List of face bounding box dictionaries
            
        Returns:
            Empty list (face recognition disabled)
        """
        logger.warning("Face recognition is disabled - cannot recognize faces")
        return []
    
    def get_person_encodings(self, person_id: int) -> List[Dict]:
        """Get stored encodings for a person - DISABLED"""
        logger.warning("Face recognition is disabled - no encodings available")
        return []

# Global instance
face_recognizer = FaceRecognizer()

def add_person_encoding(person_id: int, person_name: str, image_path: str, face_box: Dict):
    """
    Convenience function for adding person encoding - DISABLED
    
    Args:
        person_id: Database ID of the person
        person_name: Name of the person  
        image_path: Path to the image
        face_box: Face bounding box dictionary
    """
    face_recognizer.add_person_encoding(person_id, person_name, image_path, face_box)