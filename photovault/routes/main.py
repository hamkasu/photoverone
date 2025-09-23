"""
PhotoVault Main Routes Blueprint
This should only contain routes, not a Flask app
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required

# Create the main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    try:
        # Calculate photo statistics for the current user
        from photovault.models import Photo
        
        total_photos = Photo.query.filter_by(user_id=current_user.id).count()
        # Count photos with edited versions
        edited_photos = Photo.query.filter_by(user_id=current_user.id)\
                              .filter(Photo.edited_filename.isnot(None))\
                              .count()
        # Original photos are those without edited versions
        original_photos = total_photos - edited_photos
        
        # Calculate total storage used (in MB)
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        total_size_bytes = sum(photo.file_size or 0 for photo in photos)
        total_size_mb = round(total_size_bytes / 1024 / 1024, 2) if total_size_bytes > 0 else 0
        
        # Calculate storage usage percentage (assuming 1GB = 1024MB limit for demo)
        storage_limit_mb = 1024  # 1GB limit
        storage_usage_percent = (total_size_mb / storage_limit_mb * 100) if storage_limit_mb > 0 else 0
        
        stats = {
            'total_photos': total_photos,
            'edited_photos': edited_photos,
            'original_photos': original_photos,
            'total_size_mb': total_size_mb,
            'storage_usage_percent': storage_usage_percent
        }
        
        # Get recent photos for dashboard display (limit to 12 most recent)
        from photovault.models import VoiceMemo
        from photovault.extensions import db
        from sqlalchemy import func
        
        # Get photos with voice memo counts
        recent_photos = db.session.query(
            Photo,
            func.count(VoiceMemo.id).label('voice_memo_count')
        ).outerjoin(VoiceMemo).filter(
            Photo.user_id == current_user.id
        ).group_by(Photo.id).order_by(Photo.created_at.desc()).limit(12).all()
        
        # Convert to a format the template expects
        photos_with_memos = []
        for photo, memo_count in recent_photos:
            photo.voice_memo_count = memo_count
            photos_with_memos.append(photo)
        
        return render_template('dashboard.html', stats=stats, photos=photos_with_memos)
    except Exception as e:
        # Simple fallback for errors - just log to console
        print(f"Dashboard error: {str(e)}")
        # Return simple stats in case of error
        stats = {'total_photos': 0, 'edited_photos': 0, 'original_photos': 0, 'total_size_mb': 0, 'storage_usage_percent': 0}
        return render_template('dashboard.html', stats=stats, photos=[])

@main_bp.route('/upload')
@login_required
def upload():
    """Upload page"""
    return render_template('upload.html', user=current_user)

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Initialize with defaults
    stats = {
        'total_photos': 0,
        'edited_photos': 0,
        'total_size': 0,
        'member_since': 'Unknown'
    }
    
    try:
        # Calculate user statistics
        from photovault.models import Photo
        from datetime import datetime
        import os
        
        # Get all photos for current user
        user_photos = Photo.query.filter_by(user_id=current_user.id).all()
        
        # Calculate statistics - update file sizes if they're missing
        total_photos = len(user_photos)
        edited_photos = sum(1 for photo in user_photos if photo.edited_filename and photo.edited_filename.strip())
        
        # Calculate total size, and update database if file_size is missing
        total_size = 0
        for photo in user_photos:
            if photo.file_size and photo.file_size > 0:
                total_size += photo.file_size
            else:
                # Try to get file size from disk and update database
                try:
                    if os.path.exists(photo.file_path):
                        file_size = os.path.getsize(photo.file_path)
                        photo.file_size = file_size
                        total_size += file_size
                        # Don't commit yet - batch update
                except:
                    pass
        
        # Commit any file size updates
        try:
            from photovault.extensions import db
            db.session.commit()
        except:
            pass
        
        # Format member since date
        if current_user.created_at:
            member_since = current_user.created_at.strftime('%B %Y')
        else:
            member_since = 'Unknown'
            
        stats = {
            'total_photos': total_photos,
            'edited_photos': edited_photos, 
            'total_size': total_size,
            'member_since': member_since
        }
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        # stats already initialized with defaults above
        
    return render_template('profile.html', user=current_user, stats=stats)

@main_bp.route('/gallery')
@login_required
def gallery():
    """Gallery page"""
    try:
        from photovault.models import Photo
        
        # Get all photos for the current user with voice memo counts
        from photovault.models import VoiceMemo
        from photovault.extensions import db
        from sqlalchemy import func
        
        photos_with_counts = db.session.query(
            Photo,
            func.count(VoiceMemo.id).label('voice_memo_count')
        ).outerjoin(VoiceMemo).filter(
            Photo.user_id == current_user.id
        ).group_by(Photo.id).order_by(Photo.created_at.desc()).all()
        
        # Convert to a format the template expects
        photos_with_memos = []
        for photo, memo_count in photos_with_counts:
            photo.voice_memo_count = memo_count
            photos_with_memos.append(photo)
        
        return render_template('gallery/dashboard.html', photos=photos_with_memos, total_photos=len(photos_with_memos))
    except Exception as e:
        print(f"Gallery error: {str(e)}")
        return render_template('gallery/dashboard.html', photos=[], total_photos=0)

@main_bp.route('/photos/<int:photo_id>/edit')
@login_required
def edit_photo(photo_id):
    """Photo editor page"""
    try:
        from photovault.models import Photo
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return redirect(url_for('main.dashboard'))
            
        return render_template('editor.html', photo=photo)
    except Exception as e:
        print(f"Edit photo error: {str(e)}")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/advanced-enhancement')
@login_required
def advanced_enhancement():
    """Advanced Image Enhancement page"""
    try:
        from photovault.models import Photo
        from photovault.utils.image_enhancement import OPENCV_AVAILABLE
        
        # Get user's photos for selection
        photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.created_at.desc()).limit(20).all()
        
        return render_template('advanced_enhancement.html', 
                             photos=photos,
                             opencv_available=OPENCV_AVAILABLE)
    except Exception as e:
        print(f"Advanced enhancement error: {str(e)}")
        flash('Error accessing advanced enhancement features.', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/photos/<int:photo_id>/enhance')
@login_required
def enhance_photo(photo_id):
    """Advanced Image Enhancement page for specific photo"""
    try:
        from photovault.models import Photo
        from photovault.utils.image_enhancement import OPENCV_AVAILABLE
        
        # Get the photo and verify ownership
        photo = Photo.query.get_or_404(photo_id)
        if photo.user_id != current_user.id:
            return redirect(url_for('main.dashboard'))
            
        return render_template('advanced_enhancement.html', 
                             photo=photo,
                             opencv_available=OPENCV_AVAILABLE)
    except Exception as e:
        print(f"Enhanced photo error: {str(e)}")
        return redirect(url_for('main.dashboard'))

@main_bp.route('/people')
@login_required
def people():
    """People management page"""
    try:
        from photovault.models import Person
        
        # Get all people for the current user with pagination
        page = request.args.get('page', 1, type=int)
        people = Person.query.filter_by(user_id=current_user.id).order_by(Person.name.asc()).paginate(
            page=page, per_page=12, error_out=False
        )
        
        return render_template('people.html', people=people)
    except Exception as e:
        print(f"People page error: {str(e)}")
        return render_template('people.html', people=None)

@main_bp.route('/montage')
@login_required
def montage():
    """Photo montage creation page"""
    try:
        from photovault.models import Photo
        # Get user's photos for montage creation
        photos = Photo.query.filter_by(user_id=current_user.id).all()
        return render_template('montage.html', photos=photos)
    except Exception as e:
        flash('Error loading montage page.', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/people/add', methods=['POST'])
@login_required
def add_person():
    """Add a new person"""
    try:
        from photovault.models import Person, db
        
        name = request.form.get('name', '').strip()
        nickname = request.form.get('nickname', '').strip()
        relationship = request.form.get('relationship', '').strip()
        birth_year = request.form.get('birth_year')
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('Name is required.', 'error')
            return redirect(url_for('main.people'))
        
        # Convert birth_year to int if provided
        birth_year_int = None
        if birth_year:
            try:
                birth_year_int = int(birth_year)
            except ValueError:
                flash('Birth year must be a valid number.', 'error')
                return redirect(url_for('main.people'))
        
        # Create new person
        person = Person(
            user_id=current_user.id,
            name=name,
            nickname=nickname if nickname else None,
            relationship=relationship if relationship else None,
            birth_year=birth_year_int,
            notes=notes if notes else None
        )
        
        db.session.add(person)
        db.session.commit()
        
        flash(f'{name} has been added successfully!', 'success')
        return redirect(url_for('main.people'))
        
    except Exception as e:
        print(f"Add person error: {str(e)}")
        flash('Error adding person. Please try again.', 'error')
        return redirect(url_for('main.people'))

@main_bp.route('/people/<int:person_id>/edit', methods=['POST'])
@login_required
def edit_person(person_id):
    """Edit an existing person"""
    try:
        from photovault.models import Person, db
        
        person = Person.query.get_or_404(person_id)
        
        # Verify ownership
        if person.user_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('main.people'))
        
        name = request.form.get('name', '').strip()
        nickname = request.form.get('nickname', '').strip()
        relationship = request.form.get('relationship', '').strip()
        birth_year = request.form.get('birth_year')
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('Name is required.', 'error')
            return redirect(url_for('main.people'))
        
        # Convert birth_year to int if provided
        birth_year_int = None
        if birth_year:
            try:
                birth_year_int = int(birth_year)
            except ValueError:
                flash('Birth year must be a valid number.', 'error')
                return redirect(url_for('main.people'))
        
        # Update person
        person.name = name
        person.nickname = nickname if nickname else None
        person.relationship = relationship if relationship else None
        person.birth_year = birth_year_int
        person.notes = notes if notes else None
        
        db.session.commit()
        
        flash(f'{name} has been updated successfully!', 'success')
        return redirect(url_for('main.people'))
        
    except Exception as e:
        print(f"Edit person error: {str(e)}")
        flash('Error updating person. Please try again.', 'error')
        return redirect(url_for('main.people'))

@main_bp.route('/api', methods=['GET', 'HEAD'])
def api_health():
    """API health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'PhotoVault'})

@main_bp.route('/api/person/delete/<int:person_id>', methods=['DELETE'])
@login_required
def delete_person(person_id):
    """Delete a person"""
    try:
        from photovault.models import Person, db
        
        person = Person.query.get_or_404(person_id)
        
        # Verify ownership
        if person.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        name = person.name
        db.session.delete(person)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{name} deleted successfully'})
        
    except Exception as e:
        print(f"Delete person error: {str(e)}")
        return jsonify({'success': False, 'error': 'Error deleting person'}), 500