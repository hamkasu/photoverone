"""
Smart Face Tagging Routes for PhotoVault
Combines automatic face detection with manual tagging capabilities
"""

import logging
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from photovault.models import Photo, Person, PhotoPerson, db
from photovault.services.face_detection_service import face_detection_service
from photovault.extensions import csrf

logger = logging.getLogger(__name__)

# Create blueprint
smart_tagging_bp = Blueprint('smart_tagging', __name__)

@smart_tagging_bp.route('/smart-tagging')
@login_required
def smart_tagging_page():
    """Render the smart tagging interface"""
    # Get statistics for the user
    stats = face_detection_service.get_face_detection_stats(current_user.id)
    
    # Get photos with detected faces (unverified tags)
    photos_with_faces = db.session.query(Photo).join(PhotoPerson).filter(
        Photo.user_id == current_user.id,
        PhotoPerson.verified.is_(False)
    ).distinct().limit(50).all()
    
    return render_template('smart_tagging.html',
                         title='Smart Face Tagging',
                         stats=stats,
                         photos_with_faces=photos_with_faces)

@smart_tagging_bp.route('/api/photos-with-faces')
@login_required
def get_photos_with_faces():
    """Get photos that have detected faces for tagging"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Query photos with face tags
        query = db.session.query(Photo).join(PhotoPerson).filter(
            Photo.user_id == current_user.id
        ).distinct()
        
        # Apply filters
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        unverified_only = request.args.get('unverified_only', 'false').lower() == 'true'
        
        if verified_only:
            query = query.filter(PhotoPerson.verified == True)
        elif unverified_only:
            query = query.filter(PhotoPerson.verified == False)
        
        # Paginate
        photos = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        result = []
        for photo in photos.items:
            # Get face tags for this photo
            face_tags = PhotoPerson.query.filter_by(photo_id=photo.id).all()
            
            faces_info = []
            for tag in face_tags:
                face_info = {
                    'tag_id': tag.id,
                    'person_id': tag.person_id,
                    'person_name': tag.person.name if tag.person else 'Unknown',
                    'manually_tagged': tag.manually_tagged,
                    'verified': tag.verified,
                    'detection_confidence': tag.confidence or 0.0,
                    'recognition_confidence': 0.0,  # Not available in PhotoPerson model
                    'detection_method': 'auto' if not tag.manually_tagged else 'manual'
                }
                
                # Add bounding box if available
                if all(getattr(tag, attr) is not None for attr in ['face_box_x', 'face_box_y', 'face_box_width', 'face_box_height']):
                    face_info['bounding_box'] = {
                        'x': tag.face_box_x,
                        'y': tag.face_box_y,
                        'width': tag.face_box_width,
                        'height': tag.face_box_height
                    }
                
                faces_info.append(face_info)
            
            result.append({
                'id': photo.id,
                'filename': photo.filename,
                'original_name': photo.original_name,
                'thumbnail_url': f"/api/thumbnail/{photo.id}",
                'width': photo.width,
                'height': photo.height,
                'faces': faces_info,
                'faces_count': len(faces_info)
            })
        
        return jsonify({
            'success': True,
            'photos': result,
            'page': page,
            'per_page': per_page,
            'total': photos.total,
            'pages': photos.pages,
            'has_next': photos.has_next,
            'has_prev': photos.has_prev
        })
        
    except Exception as e:
        logger.error(f"Error getting photos with faces: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tagging_bp.route('/api/people')
@login_required
def get_people():
    """Get list of people for tagging"""
    try:
        # Get all people for the current user
        people = Person.query.filter_by(user_id=current_user.id).order_by(Person.name).all()
        
        result = []
        for person in people:
            result.append({
                'id': person.id,
                'name': person.name,
                'nickname': person.nickname,
                'relationship': person.relationship,
                'photo_count': person.photo_count
            })
        
        return jsonify({
            'success': True,
            'people': result
        })
        
    except Exception as e:
        logger.error(f"Error getting people list: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tagging_bp.route('/api/create-person', methods=['POST'])
@csrf.exempt
@login_required
def create_person():
    """Create a new person for tagging"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        # Check if person already exists
        existing_person = Person.query.filter_by(
            user_id=current_user.id,
            name=data['name']
        ).first()
        
        if existing_person:
            return jsonify({'success': False, 'error': 'Person with this name already exists'}), 400
        
        # Create new person
        person = Person(
            user_id=current_user.id,
            name=data['name'],
            nickname=data.get('nickname'),
            relationship=data.get('relationship'),
            birth_year=data.get('birth_year'),
            notes=data.get('notes')
        )
        
        db.session.add(person)
        db.session.commit()
        
        logger.info(f"Created new person: {person.name} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'person': {
                'id': person.id,
                'name': person.name,
                'nickname': person.nickname,
                'relationship': person.relationship
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating person: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tagging_bp.route('/api/tag-face', methods=['POST'])
@csrf.exempt
@login_required
def tag_face():
    """Tag or update a face with a person"""
    try:
        data = request.get_json()
        
        required_fields = ['photo_id', 'person_id']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Verify photo belongs to user
        photo = Photo.query.filter_by(id=data['photo_id'], user_id=current_user.id).first()
        if not photo:
            return jsonify({'success': False, 'error': 'Photo not found'}), 404
        
        # Verify person belongs to user
        person = Person.query.filter_by(id=data['person_id'], user_id=current_user.id).first()
        if not person:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
        # Check if we're updating an existing tag or creating a new one
        tag_id = data.get('tag_id')
        if tag_id:
            # Update existing tag
            tag = PhotoPerson.query.filter_by(id=tag_id).first()
            if not tag or tag.photo.user_id != current_user.id:
                return jsonify({'success': False, 'error': 'Tag not found'}), 404
            
            tag.person_id = data['person_id']
            tag.manually_tagged = True
            if hasattr(tag, 'verified'):
                tag.verified = True
            
            logger.info(f"Updated face tag {tag_id} for photo {photo.id}")
            
        else:
            # Create new tag (manual tagging)
            tag = PhotoPerson(
                photo_id=data['photo_id'],
                person_id=data['person_id'],
                manually_tagged=True
            )
            
            if hasattr(tag, 'verified'):
                tag.verified = True
            
            # Set bounding box if provided
            bounding_box = data.get('bounding_box')
            if bounding_box:
                tag.face_box_x = bounding_box.get('x')
                tag.face_box_y = bounding_box.get('y')
                tag.face_box_width = bounding_box.get('width')
                tag.face_box_height = bounding_box.get('height')
            
            db.session.add(tag)
            logger.info(f"Created new face tag for photo {photo.id} and person {person.name}")
        
        db.session.commit()
        
        # Add training data for face recognition if this is a verified tag
        if hasattr(tag, 'bounding_box') and tag.bounding_box:
            try:
                face_detection_service.add_person_training_data(person, photo, tag.bounding_box)
            except Exception as e:
                logger.warning(f"Could not add training data: {e}")
        
        return jsonify({
            'success': True,
            'tag': {
                'id': tag.id,
                'person_name': person.name,
                'manually_tagged': tag.manually_tagged,
                'verified': getattr(tag, 'verified', False)
            }
        })
        
    except Exception as e:
        logger.error(f"Error tagging face: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tagging_bp.route('/api/verify-tag/<int:tag_id>', methods=['POST'])
@csrf.exempt
@login_required
def verify_tag(tag_id):
    """Verify an automatically detected face tag"""
    try:
        tag = PhotoPerson.query.filter_by(id=tag_id).first()
        if not tag or tag.photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Tag not found'}), 404
        
        if hasattr(tag, 'verified'):
            tag.verified = True
            db.session.commit()
            
            # Add training data for face recognition
            if hasattr(tag, 'bounding_box') and tag.bounding_box and tag.person:
                try:
                    face_detection_service.add_person_training_data(tag.person, tag.photo, tag.bounding_box)
                except Exception as e:
                    logger.warning(f"Could not add training data: {e}")
            
            logger.info(f"Verified face tag {tag_id}")
        
        return jsonify({
            'success': True,
            'verified': getattr(tag, 'verified', False)
        })
        
    except Exception as e:
        logger.error(f"Error verifying tag: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tagging_bp.route('/api/delete-tag/<int:tag_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def delete_tag(tag_id):
    """Delete a face tag"""
    try:
        tag = PhotoPerson.query.filter_by(id=tag_id).first()
        if not tag or tag.photo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Tag not found'}), 404
        
        db.session.delete(tag)
        db.session.commit()
        
        logger.info(f"Deleted face tag {tag_id}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting tag: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@smart_tagging_bp.route('/api/stats')
@login_required
def get_tagging_stats():
    """Get face detection and tagging statistics"""
    try:
        stats = face_detection_service.get_face_detection_stats(current_user.id)
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500