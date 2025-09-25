"""
PhotoVault Automatic Photo Detection
Uses OpenCV to detect rectangular photos within larger images and extract them automatically
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# Check OpenCV availability
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV available for photo detection")
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available - photo detection disabled")

class PhotoDetector:
    """Automatic detection and extraction of rectangular photos from images"""
    
    def __init__(self):
        self.min_photo_area = 10000  # Minimum area for a valid photo (pixels)
        self.max_photo_area_ratio = 0.8  # Max ratio of detected photo to original image
        self.min_aspect_ratio = 0.3  # Minimum width/height ratio
        self.max_aspect_ratio = 3.0  # Maximum width/height ratio
        self.contour_area_threshold = 0.01  # Min contour area as fraction of image
        
    def detect_photos(self, image_path: str) -> List[Dict]:
        """
        Detect rectangular photos in an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of detected photo regions with coordinates and metadata
        """
        if not OPENCV_AVAILABLE:
            logger.warning("Photo detection not available - OpenCV not installed")
            return []
            
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return []
            
        image = None
        try:
            # Load image with memory management
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
                
            logger.info(f"Starting photo detection on {image_path}")
            
            # Check image size to prevent memory issues - reject instead of resize
            height, width = image.shape[:2]
            if height * width > 25000000:  # ~25MP limit for detection
                logger.error(f"Image too large for processing: {width}x{height} pixels. Maximum supported: 25MP")
                return []
            
            # Get image dimensions
            height, width = image.shape[:2]
            original_area = width * height
            
            # Preprocess image for edge detection
            try:
                processed = self._preprocess_image(image)
                
                # Find contours (potential photo boundaries)
                contours = self._find_contours(processed)
                
                # Filter and validate potential photos
                detected_photos = []
            except Exception as e:
                logger.error(f"Image preprocessing failed: {e}")
                return []
            
            for i, contour in enumerate(contours):
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Apply filters
                if not self._is_valid_photo_region(x, y, w, h, original_area):
                    continue
                    
                # Calculate confidence based on shape analysis
                confidence = self._calculate_confidence(contour, x, y, w, h)
                
                if confidence > 0.3:  # Minimum confidence threshold
                    detected_photos.append({
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h),
                        'area': int(area),
                        'confidence': float(confidence),
                        'aspect_ratio': float(w/h),
                        'contour': contour.tolist()  # For debugging/visualization
                    })
            
            # Sort by confidence
            detected_photos.sort(key=lambda p: p['confidence'], reverse=True)
            
            # Limit number of detected photos to prevent excessive memory usage
            max_detections = 10
            if len(detected_photos) > max_detections:
                detected_photos = detected_photos[:max_detections]
                logger.info(f"Limited detections to {max_detections} highest confidence photos")
            
            logger.info(f"Detected {len(detected_photos)} potential photos in {image_path}")
            return detected_photos
            
        except MemoryError:
            logger.error(f"Out of memory during photo detection for {image_path}")
            return []
        except Exception as e:
            logger.error(f"Photo detection failed for {image_path}: {e}")
            return []
        finally:
            # Ensure memory cleanup
            if 'image' in locals() and image is not None:
                try:
                    del image
                except:
                    pass
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better edge detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold for better edge detection
        adaptive = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply Canny edge detection
        edges = cv2.Canny(adaptive, 50, 150, apertureSize=3)
        
        # Apply morphological operations to close gaps
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        return edges
        
    def _find_contours(self, processed_image: np.ndarray) -> List:
        """Find contours in the processed image"""
        # Find contours
        contours, _ = cv2.findContours(
            processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Filter by minimum area
        min_area = processed_image.shape[0] * processed_image.shape[1] * self.contour_area_threshold
        filtered_contours = [c for c in contours if cv2.contourArea(c) > min_area]
        
        return filtered_contours[:20]  # Limit to top 20 contours for efficiency
    
    def _is_valid_photo_region(self, x: int, y: int, w: int, h: int, original_area: int) -> bool:
        """Validate if a region could be a photo"""
        area = w * h
        aspect_ratio = w / h
        
        # Check minimum area
        if area < self.min_photo_area:
            return False
            
        # Check maximum area (shouldn't be too large relative to original)
        if area > original_area * self.max_photo_area_ratio:
            return False
            
        # Check aspect ratio (photos are usually rectangular)
        if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
            return False
            
        # Check if region is not too close to image borders (photos usually have margins)
        margin = 10
        if x < margin or y < margin:
            return False
            
        return True
        
    def _calculate_confidence(self, contour, x: int, y: int, w: int, h: int) -> float:
        """Calculate confidence score for a detected photo region"""
        # Base confidence from contour area vs bounding box area
        contour_area = cv2.contourArea(contour)
        bbox_area = w * h
        area_ratio = contour_area / bbox_area if bbox_area > 0 else 0
        
        # Rectangular photos should have high area ratio
        confidence = area_ratio * 0.6
        
        # Bonus for good aspect ratios (common photo ratios)
        aspect_ratio = w / h
        common_ratios = [4/3, 3/2, 16/9, 5/4, 1.0]  # Common photo aspect ratios
        
        min_ratio_diff = min([abs(aspect_ratio - ratio) for ratio in common_ratios])
        aspect_bonus = max(0, 1 - min_ratio_diff) * 0.3
        
        confidence += aspect_bonus
        
        # Bonus for reasonable size
        if 20000 < bbox_area < 500000:  # Sweet spot for photo size
            confidence += 0.1
            
        return min(1.0, confidence)
    
    def extract_photos(self, image_path: str, output_dir: str, detected_photos: List[Dict]) -> List[Dict]:
        """
        Extract detected photos and save them as separate images
        
        Args:
            image_path: Path to the original image
            output_dir: Directory to save extracted photos
            detected_photos: List of detected photo regions
            
        Returns:
            List of extracted photo information with file paths
        """
        if not OPENCV_AVAILABLE:
            return []
            
        image = None
        try:
            # Load original image with memory management
            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
            
            # Check image size for extraction
            height, width = image.shape[:2]
            if height * width > 30000000:  # Limit for extraction (slightly higher)
                logger.error(f"Image too large for extraction: {width}x{height} pixels")
                return []
                
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            extracted_photos = []
            base_filename = os.path.splitext(os.path.basename(image_path))[0]
            
            for i, photo in enumerate(detected_photos):
                try:
                    # Extract region
                    x, y, w, h = photo['x'], photo['y'], photo['width'], photo['height']
                    
                    # Add some padding around the detected region
                    padding = 10
                    x_start = max(0, x - padding)
                    y_start = max(0, y - padding)
                    x_end = min(image.shape[1], x + w + padding)
                    y_end = min(image.shape[0], y + h + padding)
                    
                    # Extract the region
                    extracted_region = image[y_start:y_end, x_start:x_end]
                    
                    # Generate filename
                    output_filename = f"{base_filename}_photo_{i+1:02d}_conf{photo['confidence']:.2f}.jpg"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # Save extracted photo with quality control
                    success = cv2.imwrite(output_path, extracted_region, 
                                        [cv2.IMWRITE_JPEG_QUALITY, 95])
                    if not success:
                        logger.error(f"Failed to save extracted photo: {output_path}")
                        continue
                    
                    extracted_info = {
                        'original_region': photo,
                        'filename': output_filename,
                        'file_path': output_path,
                        'extracted_width': x_end - x_start,
                        'extracted_height': y_end - y_start,
                        'confidence': photo['confidence']
                    }
                    
                    extracted_photos.append(extracted_info)
                    logger.info(f"Extracted photo {i+1}: {output_filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to extract photo {i+1}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(extracted_photos)} photos from {image_path}")
            return extracted_photos
            
        except MemoryError:
            logger.error(f"Out of memory during photo extraction for {image_path}")
            return []
        except Exception as e:
            logger.error(f"Photo extraction failed for {image_path}: {e}")
            return []
        finally:
            # Ensure memory cleanup
            if 'image' in locals() and image is not None:
                try:
                    del image
                except:
                    pass

# Global instance
photo_detector = PhotoDetector()

def detect_photos_in_image(image_path: str) -> List[Dict]:
    """Convenience function for detecting photos in an image"""
    return photo_detector.detect_photos(image_path)

def extract_detected_photos(image_path: str, output_dir: str, detected_photos: List[Dict]) -> List[Dict]:
    """Convenience function for extracting detected photos"""
    return photo_detector.extract_photos(image_path, output_dir, detected_photos)