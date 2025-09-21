"""
Face Detection Service for PhotoVault
Integrates automatic face detection with photo uploads and person assignment
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from flask import current_app
from photovault.utils.face_detection import face_detector
from photovault.utils.face_recognition import face_recognizer
from photovault.models import Photo, Person, PhotoPerson
from photovault.extensions import db

logger = logging.getLogger(__name__)

class FaceDetectionService:
    """Service for intelligent face detection and person assignment"""
    
    def __init__(self):
        self.face_detector = face_detector
        self.face_recognizer = face_recognizer
    
    def process_photo_faces(self, photo: Photo) -> List[Dict]:
        """
        Process a photo to detect faces and attempt recognition
        
        Args:
            photo: Photo model instance
            
        Returns:
            List of detected faces with recognition results
        """
        try:
            logger.info(f"Processing faces for photo {photo.id}: {photo.original_name}")
            
            # Check if face detection is available
            if not self.face_detector.is_available():
                logger.warning("Face detection not available - skipping photo processing")
                return []
            
            # Use the file path directly as it's already a complete path
            photo_path = photo.file_path
            
            if not os.path.exists(photo_path):
                logger.error(f"Photo file not found: {photo_path}")
                return []
            
            # Detect faces in the photo
            detected_faces = self.face_detector.detect_faces(photo_path)
            
            if not detected_faces:
                logger.info(f"No faces detected in photo {photo.id}")
                return []
            
            logger.info(f"Detected {len(detected_faces)} faces in photo {photo.id}")
            
            # Process each detected face
            processed_faces = []
            for face in detected_faces:
                face_result = self._process_single_face(photo, photo_path, face)
                if face_result:
                    processed_faces.append(face_result)
            
            return processed_faces
            
        except Exception as e:
            logger.error(f"Error processing faces for photo {photo.id}: {e}")
            return []
    
    def _process_single_face(self, photo: Photo, photo_path: str, face: Dict) -> Optional[Dict]:
        """
        Process a single detected face for recognition and tagging
        
        Args:
            photo: Photo model instance
            photo_path: Full path to the photo file
            face: Face detection result dictionary
            
        Returns:
            Processed face result with recognition data
        """
        try:
            face_result = {
                'bounding_box': {
                    'x': face['x'],
                    'y': face['y'], 
                    'width': face['width'],
                    'height': face['height']
                },
                'detection_confidence': face['confidence'],
                'detection_method': face.get('method', 'auto'),
                'recognized_person': None,
                'recognition_confidence': 0.0
            }
            
            # Attempt face recognition if available
            if self.face_recognizer.is_available():
                recognition_result = self.face_recognizer.recognize_face(photo_path, face)
                
                if recognition_result:
                    # Found a matching person
                    person = Person.query.filter_by(
                        id=recognition_result['person_id'],
                        user_id=photo.user_id
                    ).first()
                    
                    if person:
                        face_result['recognized_person'] = {
                            'id': person.id,
                            'name': person.name,
                            'nickname': person.nickname
                        }
                        face_result['recognition_confidence'] = recognition_result['confidence']
                        
                        logger.info(f"Recognized person {person.name} in photo {photo.id}")
            
            return face_result
            
        except Exception as e:
            logger.error(f"Error processing single face: {e}")
            return None
    
    def create_automatic_photo_tag(self, photo: Photo, face_result: Dict, person: Person) -> Optional[PhotoPerson]:
        """
        Create an automatic photo tag from face detection results
        
        Args:
            photo: Photo model instance
            face_result: Face detection/recognition result
            person: Person to tag
            
        Returns:
            Created PhotoPerson instance or None
        """
        try:
            # Check if this person is already tagged in this photo
            existing_tag = PhotoPerson.query.filter_by(
                photo_id=photo.id,
                person_id=person.id
            ).first()
            
            if existing_tag:
                logger.info(f"Person {person.name} already tagged in photo {photo.id}")
                return existing_tag
            
            # Create new photo tag
            photo_tag = PhotoPerson(
                photo_id=photo.id,
                person_id=person.id,
                manually_tagged=False,  # This is automatic
                verified=False,
                confidence=face_result['detection_confidence']
            )
            
            # Set face detection bounding box
            bbox = face_result['bounding_box']
            photo_tag.face_box_x = bbox['x']
            photo_tag.face_box_y = bbox['y']
            photo_tag.face_box_width = bbox['width']
            photo_tag.face_box_height = bbox['height']
            
            db.session.add(photo_tag)
            db.session.commit()
            
            logger.info(f"Created automatic tag for {person.name} in photo {photo.id}")
            return photo_tag
            
        except Exception as e:
            logger.error(f"Error creating automatic photo tag: {e}")
            db.session.rollback()
            return None
    
    def process_and_tag_photo(self, photo: Photo, auto_tag: bool = True) -> Dict:
        """
        Complete workflow: detect faces, recognize people, and optionally create tags
        
        Args:
            photo: Photo model instance
            auto_tag: Whether to automatically create tags for recognized faces
            
        Returns:
            Summary of processing results
        """
        try:
            logger.info(f"Starting complete face processing for photo {photo.id}")
            
            # Detect and process faces
            faces = self.process_photo_faces(photo)
            
            results = {
                'photo_id': photo.id,
                'faces_detected': len(faces),
                'faces_recognized': 0,
                'tags_created': 0,
                'faces': faces,
                'tags_created_list': []
            }
            
            if not faces:
                return results
            
            # Process all detected faces for auto-tagging (recognized and unrecognized)
            if auto_tag:
                for face_result in faces:
                    if face_result.get('recognized_person'):
                        # Create tag with recognized person
                        person_id = face_result['recognized_person']['id']
                        person = Person.query.get(person_id)
                        
                        if person:
                            tag = self.create_automatic_photo_tag(photo, face_result, person)
                            if tag:
                                results['tags_created'] += 1
                    else:
                        # Create detection-only tag for unrecognized face
                        try:
                            photo_tag = PhotoPerson(
                                photo_id=photo.id,
                                person_id=None,  # No person assigned yet
                                manually_tagged=False,
                                verified=False,
                                confidence=face_result['detection_confidence']
                            )
                            
                            # Set face detection bounding box
                            bbox = face_result['bounding_box']
                            photo_tag.face_box_x = bbox['x']
                            photo_tag.face_box_y = bbox['y']
                            photo_tag.face_box_width = bbox['width']
                            photo_tag.face_box_height = bbox['height']
                            
                            db.session.add(photo_tag)
                            db.session.commit()
                            results['tags_created'] += 1
                            
                        except Exception as e:
                            logger.error(f"Error creating detection-only tag: {e}")
                            db.session.rollback()
            
            logger.info(f"Face processing complete for photo {photo.id}: {results['faces_detected']} faces, "
                       f"{results['faces_recognized']} recognized, {results['tags_created']} tagged")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in complete face processing for photo {photo.id}: {e}")
            return {
                'photo_id': photo.id,
                'error': str(e),
                'faces_detected': 0,
                'faces_recognized': 0,
                'tags_created': 0
            }
    
    def add_person_training_data(self, person: Person, photo: Photo, face_box: Dict) -> bool:
        """
        Add a known face for a person to improve recognition accuracy
        
        Args:
            person: Person model instance
            photo: Photo containing the person's face
            face_box: Bounding box of the person's face
            
        Returns:
            Success status
        """
        try:
            if not self.face_recognizer.is_available():
                logger.warning("Face recognition not available")
                return False
            
            # Use the file path directly as it's already a complete path
            photo_path = photo.file_path
            
            if not os.path.exists(photo_path):
                logger.error(f"Photo file not found: {photo_path}")
                return False
            
            # Add face encoding for this person
            self.face_recognizer.add_person_encoding(
                person.id, 
                person.name, 
                photo_path, 
                face_box
            )
            
            logger.info(f"Added training data for {person.name} from photo {photo.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding person training data: {e}")
            return False
    
    def get_face_detection_stats(self, user_id: int) -> Dict:
        """
        Get face detection statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics dictionary
        """
        try:
            # Count photos with detected faces (photos that have tags)
            photos_with_faces = db.session.query(Photo.id).join(PhotoPerson).filter(
                Photo.user_id == user_id
            ).distinct().count()
            
            # Count total faces detected
            total_faces = PhotoPerson.query.join(Photo).filter(
                Photo.user_id == user_id
            ).count()
            
            # Count verified faces
            verified_faces = PhotoPerson.query.join(Photo).filter(
                Photo.user_id == user_id,
                PhotoPerson.verified == True
            ).count()
            
            # Count unique people tagged
            unique_people = db.session.query(PhotoPerson.person_id).join(Photo).filter(
                Photo.user_id == user_id
            ).distinct().count()
            
            return {
                'photos_with_faces': photos_with_faces,
                'total_faces_detected': total_faces,
                'verified_faces': verified_faces,
                'unique_people_tagged': unique_people,
                'face_detection_available': self.face_detector.is_available(),
                'face_recognition_available': self.face_recognizer.is_available()
            }
            
        except Exception as e:
            logger.error(f"Error getting face detection stats: {e}")
            return {
                'error': str(e),
                'face_detection_available': False,
                'face_recognition_available': False
            }

# Global service instance
face_detection_service = FaceDetectionService()