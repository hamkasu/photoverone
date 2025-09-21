"""
Face Detection Utilities for PhotoVault
Implements automatic face detection using OpenCV with multiple detection methods
"""

import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FaceDetector:
    """Face detection using OpenCV with multiple detection methods"""
    
    def __init__(self):
        self.opencv_available = True
        self.face_cascade = None
        self.dnn_net = None
        self.confidence_threshold = 0.5
        
        try:
            import cv2
            self._initialize_detectors()
            logger.info("Face detection initialized successfully")
        except ImportError:
            self.opencv_available = False
            logger.warning("OpenCV not available - face detection disabled")
        except Exception as e:
            logger.error(f"Failed to initialize face detection: {e}")
            self.opencv_available = False
    
    def _initialize_detectors(self):
        """Initialize face detection models"""
        try:
            # Initialize Haar Cascade detector (fast but less accurate)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                logger.info("Haar cascade face detector loaded")
            else:
                logger.warning("Haar cascade file not found")
            
            # Try to initialize DNN detector (more accurate but slower)
            try:
                # Download DNN model files if they don't exist
                model_dir = Path(__file__).parent / 'models'
                model_dir.mkdir(exist_ok=True)
                
                prototxt_path = model_dir / 'deploy.prototxt'
                model_path = model_dir / 'res10_300x300_ssd_iter_140000.caffemodel'
                
                # Create basic prototxt if it doesn't exist
                if not prototxt_path.exists():
                    self._create_dnn_prototxt(prototxt_path)
                
                # If model file exists, load DNN
                if model_path.exists():
                    self.dnn_net = cv2.dnn.readNetFromCaffe(str(prototxt_path), str(model_path))
                    logger.info("DNN face detector loaded")
                else:
                    logger.info("DNN model file not found - using Haar cascade only")
                    
            except Exception as e:
                logger.warning(f"DNN detector initialization failed: {e}")
                
        except Exception as e:
            logger.error(f"Error initializing detectors: {e}")
            raise
    
    def _create_dnn_prototxt(self, prototxt_path: Path):
        """Create a basic prototxt file for DNN face detection"""
        prototxt_content = '''name: "OpenFace"

input: "data"
input_dim: 1
input_dim: 3
input_dim: 300
input_dim: 300

layer {
  name: "conv1_1"
  type: "Convolution"
  bottom: "data"
  top: "conv1_1"
}
'''
        with open(prototxt_path, 'w') as f:
            f.write(prototxt_content)
    
    def detect_faces_haar(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces using Haar cascade classifier
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of detected faces with bounding boxes and confidence scores
        """
        if not self.opencv_available or self.face_cascade is None:
            return []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            detected_faces = []
            for (x, y, w, h) in faces:
                # Haar cascade doesn't provide confidence scores, so we estimate based on size
                confidence = min(0.95, max(0.6, (w * h) / (image.shape[0] * image.shape[1]) * 10))
                
                detected_faces.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'confidence': float(confidence),
                    'method': 'haar'
                })
            
            logger.info(f"Haar cascade detected {len(detected_faces)} faces")
            return detected_faces
            
        except Exception as e:
            logger.error(f"Haar cascade face detection failed: {e}")
            return []
    
    def detect_faces_dnn(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces using DNN (more accurate but requires model files)
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of detected faces with bounding boxes and confidence scores
        """
        if not self.opencv_available or self.dnn_net is None:
            return []
        
        try:
            # Get image dimensions
            (h, w) = image.shape[:2]
            
            # Create blob from image
            blob = cv2.dnn.blobFromImage(
                cv2.resize(image, (300, 300)), 1.0,
                (300, 300), (104.0, 177.0, 123.0)
            )
            
            # Pass blob through network
            self.dnn_net.setInput(blob)
            detections = self.dnn_net.forward()
            
            detected_faces = []
            
            # Process detections
            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                # Filter weak detections
                if confidence > self.confidence_threshold:
                    # Compute bounding box coordinates
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (x, y, x1, y1) = box.astype("int")
                    
                    # Ensure coordinates are within image bounds
                    x = max(0, x)
                    y = max(0, y)
                    x1 = min(w, x1)
                    y1 = min(h, y1)
                    
                    width = x1 - x
                    height = y1 - y
                    
                    if width > 0 and height > 0:
                        detected_faces.append({
                            'x': int(x),
                            'y': int(y),
                            'width': int(width),
                            'height': int(height),
                            'confidence': float(confidence),
                            'method': 'dnn'
                        })
            
            logger.info(f"DNN detected {len(detected_faces)} faces")
            return detected_faces
            
        except Exception as e:
            logger.error(f"DNN face detection failed: {e}")
            return []
    
    def detect_faces(self, image_path: str) -> List[Dict]:
        """
        Detect faces in an image using the best available method
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of detected faces with metadata
        """
        if not self.opencv_available:
            logger.warning("Face detection not available - OpenCV not installed")
            return []
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []
        
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
            
            # Try DNN first (more accurate), fall back to Haar cascade
            faces = []
            
            if self.dnn_net is not None:
                faces = self.detect_faces_dnn(image)
                if faces:
                    logger.info(f"DNN detection successful: {len(faces)} faces found")
            
            # If DNN didn't work or found no faces, try Haar cascade
            if not faces and self.face_cascade is not None:
                faces = self.detect_faces_haar(image)
                if faces:
                    logger.info(f"Haar cascade detection successful: {len(faces)} faces found")
            
            # Add image metadata to each face
            for face in faces:
                face['image_path'] = image_path
                face['image_width'] = image.shape[1]
                face['image_height'] = image.shape[0]
            
            return faces
            
        except Exception as e:
            logger.error(f"Face detection failed for {image_path}: {e}")
            return []
    
    def validate_face_detection(self, faces: List[Dict]) -> List[Dict]:
        """
        Validate and filter face detections
        
        Args:
            faces: List of detected faces
            
        Returns:
            Filtered list of valid faces
        """
        valid_faces = []
        
        for face in faces:
            # Check minimum size requirements
            if face['width'] < 20 or face['height'] < 20:
                continue
            
            # Check aspect ratio (faces should be roughly rectangular)
            aspect_ratio = face['width'] / face['height']
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                continue
            
            # Check confidence threshold
            if face['confidence'] < 0.3:
                continue
            
            valid_faces.append(face)
        
        logger.info(f"Validated {len(valid_faces)} out of {len(faces)} detected faces")
        return valid_faces
    
    def is_available(self) -> bool:
        """Check if face detection is available"""
        return self.opencv_available and (self.face_cascade is not None or self.dnn_net is not None)

# Global instance
face_detector = FaceDetector()

def detect_faces_in_photo(image_path: str) -> List[Dict]:
    """
    Convenience function to detect faces in a photo
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List of detected faces with bounding boxes and confidence scores
    """
    faces = face_detector.detect_faces(image_path)
    return face_detector.validate_face_detection(faces)