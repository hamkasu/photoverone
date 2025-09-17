# photovault/models.py

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from photovault.extensions import db

class User(UserMixin, db.Model):
    """User model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    photos = db.relationship('Photo', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Photo(db.Model):
    """Photo model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    edited_filename = db.Column(db.String(255))  # For edited versions
    edited_path = db.Column(db.String(500))  # For edited versions
    file_size = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    upload_source = db.Column(db.String(50), default='file')  # 'file' or 'camera'

    # EXIF Metadata fields
    date_taken = db.Column('photo_date', db.DateTime)  # Original date photo was taken
    camera_make = db.Column(db.String(100))  # Camera manufacturer
    camera_model = db.Column(db.String(100))  # Camera model
    
    # Camera settings
    iso = db.Column(db.Integer)  # ISO sensitivity
    aperture = db.Column(db.Float)  # f-stop value
    shutter_speed = db.Column(db.String(50))  # Exposure time
    focal_length = db.Column(db.Float)  # Focal length in mm
    flash_used = db.Column(db.Boolean)  # Whether flash was fired
    
    # GPS coordinates
    gps_latitude = db.Column(db.Float)  # GPS latitude in decimal degrees
    gps_longitude = db.Column(db.Float)  # GPS longitude in decimal degrees
    gps_altitude = db.Column(db.Float)  # GPS altitude in meters
    location_name = db.Column(db.String(255))  # Human-readable location
    
    # Image properties
    orientation = db.Column(db.Integer)  # EXIF orientation value
    color_space = db.Column(db.String(50))  # Color space (sRGB, Adobe RGB, etc.)
    
    # Enhancement settings
    auto_enhanced = db.Column(db.Boolean, default=False)  # Whether auto-enhancement was applied
    enhancement_settings = db.Column(db.Text)  # JSON of enhancement parameters applied
    
    # User-added metadata
    description = db.Column(db.Text)  # User description of the photo
    tags = db.Column(db.String(500))  # Comma-separated tags
    event_name = db.Column(db.String(255))  # Event or occasion name
    estimated_year = db.Column(db.Integer)  # Estimated year if date_taken unavailable

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Photo {self.original_name}>'

class Person(db.Model):
    """Person model for photo tagging"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50))
    relationship = db.Column(db.String(50))
    birth_year = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    photo_tags = db.relationship('PhotoTag', backref='person', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def photo_count(self):
        """Count of photos this person is tagged in"""
        return self.photo_tags.count()
    
    def __repr__(self):
        return f'<Person {self.name}>'

class PhotoTag(db.Model):
    """Photo tagging model"""
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    manually_tagged = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    photo = db.relationship('Photo', backref='tags')
    
    def __repr__(self):
        return f'<PhotoTag {self.photo_id}-{self.person_id}>'

class VoiceMemo(db.Model):
    """Voice memo model for audio recordings attached to photos"""
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Audio file information
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))  # audio/webm, audio/wav, etc.
    duration = db.Column(db.Float)  # Duration in seconds
    
    # User metadata
    title = db.Column(db.String(200))  # Optional title for the voice memo
    transcript = db.Column(db.Text)  # Optional transcription of the memo
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    photo = db.relationship('Photo', backref='voice_memos')
    user = db.relationship('User', backref='voice_memos')
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file_size:
            return round(self.file_size / 1024 / 1024, 2)
        return 0
    
    @property
    def duration_formatted(self):
        """Return duration in MM:SS format"""
        if self.duration:
            minutes = int(self.duration // 60)
            seconds = int(self.duration % 60)
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    
    def __repr__(self):
        return f'<VoiceMemo {self.filename} for Photo {self.photo_id}>'
