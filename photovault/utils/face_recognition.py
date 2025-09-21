"""
Face Recognition Utilities for PhotoVault
Implements face encoding, matching, and identification of known people
"""

import os
import cv2
import numpy as np
import pickle
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class FaceRecognizer:
    """Face recognition and encoding system"""
    
    def __init__(self):
        self.opencv_available = True
        self.face_recognizer = None
        self.face_cascade = None
        self.encodings_cache = {}
        self.encodings_file = Path(__file__).parent / 'face_encodings.pkl'
        
        try:
            import cv2
            self._initialize_recognizer()
            self._load_encodings_cache()
            logger.info("Face recognition initialized successfully")
        except ImportError:
            self.opencv_available = False
            logger.warning("OpenCV not available - face recognition disabled")
        except Exception as e:
            logger.error(f"Failed to initialize face recognition: {e}")
            self.opencv_available = False
    
    def _initialize_recognizer(self):
        """Initialize face recognition models"""
        try:
            # Try to initialize OpenCV face recognizer if available
            try:
                if hasattr(cv2, 'face'):
                    self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
                    logger.info("OpenCV face recognizer initialized")
                else:
                    logger.info("OpenCV contrib face module not available - using basic encoding")
                    self.face_recognizer = None
            except Exception as e:
                logger.warning(f"OpenCV face recognizer not available: {e}")
                self.face_recognizer = None
            
            # Initialize face cascade for preprocessing
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                logger.info("Face recognition models loaded")
            else:
                logger.warning("Face cascade not found - using basic recognition")
                
        except Exception as e:
            logger.error(f"Error initializing face recognizer: {e}")
            # Fall back to basic encoding without OpenCV face module
            self.face_recognizer = None
    
    def _load_encodings_cache(self):
        """Load cached face encodings from disk"""
        try:
            if self.encodings_file.exists():
                with open(self.encodings_file, 'rb') as f:
                    self.encodings_cache = pickle.load(f)
                logger.info(f"Loaded {len(self.encodings_cache)} cached face encodings")
            else:
                self.encodings_cache = {}
                logger.info("No cached encodings found - starting fresh")
        except Exception as e:
            logger.error(f"Error loading encodings cache: {e}")
            self.encodings_cache = {}
    
    def _save_encodings_cache(self):
        """Save face encodings cache to disk"""
        try:
            self.encodings_file.parent.mkdir(exist_ok=True)
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.encodings_cache, f)
            logger.info(f"Saved {len(self.encodings_cache)} face encodings to cache")
        except Exception as e:
            logger.error(f"Error saving encodings cache: {e}")
    
    def extract_face_encoding(self, image_path: str, face_box: Dict) -> Optional[np.ndarray]:
        """
        Extract face encoding from a detected face region
        
        Args:
            image_path: Path to the image file
            face_box: Dictionary with face bounding box coordinates
            
        Returns:
            Face encoding as numpy array or None if extraction fails
        """
        if not self.opencv_available:
            return None
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return None
            
            # Extract face region
            x = face_box['x']
            y = face_box['y']
            w = face_box['width']
            h = face_box['height']
            
            # Add padding around face
            padding = int(min(w, h) * 0.1)
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(image.shape[1] - x, w + 2 * padding)
            h = min(image.shape[0] - y, h + 2 * padding)
            
            face_roi = image[y:y+h, x:x+w]
            
            if face_roi.size == 0:
                logger.warning("Empty face region extracted")
                return None
            
            # Resize to standard size for consistent encoding
            face_resized = cv2.resize(face_roi, (100, 100))
            
            # Convert to grayscale for encoding
            if len(face_resized.shape) == 3:
                face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
            else:
                face_gray = face_resized
            
            # Use histogram as a simple face encoding
            # This is a basic approach - more sophisticated methods would use deep learning
            hist = cv2.calcHist([face_gray], [0], None, [256], [0, 256])
            
            # Normalize the histogram
            hist = hist.flatten()
            hist = hist / np.sum(hist)
            
            # Add texture features using LBP (Local Binary Patterns)
            lbp_features = self._extract_lbp_features(face_gray)
            
            # Combine histogram and LBP features
            encoding = np.concatenate([hist, lbp_features])
            
            logger.debug(f"Extracted face encoding with {len(encoding)} features")
            return encoding
            
        except Exception as e:
            logger.error(f"Error extracting face encoding: {e}")
            return None
    
    def _extract_lbp_features(self, gray_image: np.ndarray) -> np.ndarray:
        """Extract Local Binary Pattern features from a grayscale face image"""
        try:
            # Simple LBP implementation
            rows, cols = gray_image.shape
            lbp = np.zeros((rows-2, cols-2), dtype=np.uint8)
            
            for i in range(1, rows-1):
                for j in range(1, cols-1):
                    center = gray_image[i, j]
                    code = 0
                    
                    # Check 8 neighboring pixels
                    if gray_image[i-1, j-1] >= center: code |= 1
                    if gray_image[i-1, j] >= center: code |= 2
                    if gray_image[i-1, j+1] >= center: code |= 4
                    if gray_image[i, j+1] >= center: code |= 8
                    if gray_image[i+1, j+1] >= center: code |= 16
                    if gray_image[i+1, j] >= center: code |= 32
                    if gray_image[i+1, j-1] >= center: code |= 64
                    if gray_image[i, j-1] >= center: code |= 128
                    
                    lbp[i-1, j-1] = code
            
            # Calculate histogram of LBP values
            hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
            hist = hist.astype(np.float32)
            hist = hist / np.sum(hist)
            
            return hist
            
        except Exception as e:
            logger.error(f"Error extracting LBP features: {e}")
            return np.zeros(256, dtype=np.float32)
    
    def add_person_encoding(self, person_id: int, person_name: str, image_path: str, face_box: Dict):
        """
        Add a face encoding for a known person
        
        Args:
            person_id: Database ID of the person
            person_name: Name of the person
            image_path: Path to the image containing the person's face
            face_box: Bounding box of the face in the image
        """
        try:
            encoding = self.extract_face_encoding(image_path, face_box)
            if encoding is not None:
                # Store encoding with person information
                if person_id not in self.encodings_cache:
                    self.encodings_cache[person_id] = {
                        'name': person_name,
                        'encodings': []
                    }
                
                self.encodings_cache[person_id]['encodings'].append({
                    'encoding': encoding,
                    'image_path': image_path,
                    'face_box': face_box
                })
                
                self._save_encodings_cache()
                logger.info(f"Added face encoding for {person_name} (ID: {person_id})")
            else:
                logger.warning(f"Could not extract encoding for {person_name}")
                
        except Exception as e:
            logger.error(f"Error adding person encoding: {e}")
    
    def recognize_face(self, image_path: str, face_box: Dict, confidence_threshold: float = 0.6) -> Optional[Dict]:
        """
        Try to recognize a face by matching against known encodings
        
        Args:
            image_path: Path to the image
            face_box: Bounding box of the face to recognize
            confidence_threshold: Minimum confidence for recognition
            
        Returns:
            Dictionary with person info and confidence, or None if no match
        """
        if not self.encodings_cache:
            logger.debug("No face encodings available for recognition")
            return None
        
        try:
            # Extract encoding for the unknown face
            unknown_encoding = self.extract_face_encoding(image_path, face_box)
            if unknown_encoding is None:
                return None
            
            best_match = None
            best_distance = float('inf')
            
            # Compare against all known encodings
            for person_id, person_data in self.encodings_cache.items():
                person_name = person_data['name']
                
                for known_face in person_data['encodings']:
                    known_encoding = known_face['encoding']
                    
                    # Calculate distance between encodings
                    distance = self._calculate_encoding_distance(unknown_encoding, known_encoding)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_match = {
                            'person_id': person_id,
                            'person_name': person_name,
                            'distance': distance,
                            'confidence': max(0.0, 1.0 - distance)
                        }
            
            # Check if best match meets confidence threshold
            if best_match and best_match['confidence'] >= confidence_threshold:
                logger.info(f"Recognized face as {best_match['person_name']} with confidence {best_match['confidence']:.2f}")
                return best_match
            else:
                logger.debug(f"No confident face match found (best confidence: {best_match['confidence'] if best_match else 0:.2f})")
                return None
                
        except Exception as e:
            logger.error(f"Error during face recognition: {e}")
            return None
    
    def _calculate_encoding_distance(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """
        Calculate distance between two face encodings
        
        Args:
            encoding1: First face encoding
            encoding2: Second face encoding
            
        Returns:
            Distance between encodings (0 = identical, 1+ = different)
        """
        try:
            # Ensure encodings have the same length
            min_len = min(len(encoding1), len(encoding2))
            enc1 = encoding1[:min_len]
            enc2 = encoding2[:min_len]
            
            # Calculate cosine distance
            dot_product = np.dot(enc1, enc2)
            norm1 = np.linalg.norm(enc1)
            norm2 = np.linalg.norm(enc2)
            
            if norm1 == 0 or norm2 == 0:
                return 1.0
            
            cosine_similarity = dot_product / (norm1 * norm2)
            cosine_distance = 1.0 - cosine_similarity
            
            return float(cosine_distance)
            
        except Exception as e:
            logger.error(f"Error calculating encoding distance: {e}")
            return 1.0
    
    def get_known_people_count(self) -> int:
        """Get the number of people with stored face encodings"""
        return len(self.encodings_cache)
    
    def remove_person_encodings(self, person_id: int):
        """Remove all encodings for a specific person"""
        try:
            if person_id in self.encodings_cache:
                person_name = self.encodings_cache[person_id]['name']
                del self.encodings_cache[person_id]
                self._save_encodings_cache()
                logger.info(f"Removed face encodings for {person_name} (ID: {person_id})")
            else:
                logger.warning(f"No encodings found for person ID: {person_id}")
        except Exception as e:
            logger.error(f"Error removing person encodings: {e}")
    
    def is_available(self) -> bool:
        """Check if face recognition is available"""
        return self.opencv_available

# Global instance
face_recognizer = FaceRecognizer()

def recognize_face_in_photo(image_path: str, face_box: Dict) -> Optional[Dict]:
    """
    Convenience function to recognize a face in a photo
    
    Args:
        image_path: Path to the image file
        face_box: Face bounding box dictionary
        
    Returns:
        Recognition result or None if no match
    """
    return face_recognizer.recognize_face(image_path, face_box)

def add_known_face(person_id: int, person_name: str, image_path: str, face_box: Dict):
    """
    Convenience function to add a known face encoding
    
    Args:
        person_id: Database ID of the person
        person_name: Name of the person
        image_path: Path to the image
        face_box: Face bounding box dictionary
    """
    face_recognizer.add_person_encoding(person_id, person_name, image_path, face_box)