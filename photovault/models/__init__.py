"""
PhotoVault Database Models
Complete models for User, Photo, Album, Person, and PhotoPerson management
"""
from datetime import datetime, timedelta
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from photovault.extensions import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Admin and superuser fields
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    photos = db.relationship('Photo', backref='user', lazy=True, cascade='all, delete-orphan')
    albums = db.relationship('Album', backref='user', lazy=True, cascade='all, delete-orphan')
    people = db.relationship('Person', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Album(db.Model):
    """Album model for organizing photos"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Time period fields for organizing old photos
    date_start = db.Column(db.Date)  # Start date for photos in this album
    date_end = db.Column(db.Date)    # End date for photos in this album
    time_period = db.Column(db.String(100))  # e.g., "Summer 1987", "Early 1960s"
    location = db.Column(db.String(200))     # e.g., "Grandma's house", "Family farm"
    event_type = db.Column(db.String(100))   # e.g., "Wedding", "Christmas", "Vacation"
    
    # Relationships
    photos = db.relationship('Photo', backref='album', lazy=True)
    
    def __repr__(self):
        return f'<Album {self.name}>'
    
    @property
    def photo_count(self):
        """Return number of photos in album"""
        return len(self.photos)

class Person(db.Model):
    """Person model for tagging people in photos"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    nickname = db.Column(db.String(100))
    birth_year = db.Column(db.Integer)
    relationship = db.Column(db.String(100))  # e.g., "Mother", "Brother", "Friend"
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Person {self.name}>'

class Photo(db.Model):
    """Photo model for storing photo information"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    upload_source = db.Column(db.String(50), default='file')  # 'file' or 'camera'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=True)
    
    # Enhanced fields for old photograph digitization
    photo_date = db.Column(db.Date)           # Best guess at actual photo date
    date_text = db.Column(db.String(100))     # Text like "Summer 1987", "Christmas 1985"
    date_circa = db.Column(db.Boolean, nullable=False, default=False)  # True if date is approximate
    
    # Location and context
    location_text = db.Column(db.String(200))  # "Grandma's house", "School playground"
    occasion = db.Column(db.String(200))       # "Wedding day", "Birthday party"
    
    # Physical photo condition and source
    condition = db.Column(db.String(50))       # "Excellent", "Faded", "Torn", "Stained"
    photo_source = db.Column(db.String(100))   # "Family album", "Shoebox", "Frame"
    back_text = db.Column(db.Text)             # Text written on back of photo
    
    # Processing metadata
    needs_restoration = db.Column(db.Boolean, nullable=False, default=False)
    auto_enhanced = db.Column(db.Boolean, nullable=False, default=False)
    processing_notes = db.Column(db.Text)
    edited_filename = db.Column(db.String(255))  # Stores the filename of the edited image
    
    # Front/back pairing for photos with writing on back
    paired_photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))
    is_back_side = db.Column(db.Boolean, nullable=False, default=False)
    
    # Many-to-many relationship with people through PhotoPerson association
    people = db.relationship('Person', secondary='photo_people', lazy='subquery',
                           backref=db.backref('photos', lazy=True))
    
    def __repr__(self):
        return f'<Photo {self.filename}>'
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file_size:
            return round(self.file_size / 1024 / 1024, 2)
        return 0
    
    @property
    def dimensions(self):
        """Return image dimensions as string"""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unknown"

class PhotoPerson(db.Model):
    """Association model for tagging people in photos with face detection metadata"""
    __tablename__ = 'photo_people'
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Face detection metadata
    confidence = db.Column(db.Float)  # Detection confidence (0.0-1.0)
    face_box_x = db.Column(db.Integer)  # Bounding box coordinates
    face_box_y = db.Column(db.Integer)
    face_box_width = db.Column(db.Integer)
    face_box_height = db.Column(db.Integer)
    manually_tagged = db.Column(db.Boolean, nullable=False, default=False)  # True if manually tagged vs auto-detected
    verified = db.Column(db.Boolean, nullable=False, default=False)  # True if user verified the detection
    notes = db.Column(db.String(255))  # Optional notes about the identification
    
    # Relationships
    photo = db.relationship('Photo', backref='photo_people_records')
    person = db.relationship('Person', backref='photo_people_records')
    
    # Ensure unique photo-person combinations
    __table_args__ = (db.UniqueConstraint('photo_id', 'person_id', name='unique_photo_person'),)
    
    def __repr__(self):
        return f'<PhotoPerson {self.photo_id}-{self.person_id}>'

class PasswordResetToken(db.Model):
    """Password reset token model for secure password resets"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='reset_tokens')
    
    def __init__(self, user_id):
        """Initialize password reset token"""
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    
    def is_valid(self):
        """Check if token is still valid and not used"""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
    
    @staticmethod
    def clean_expired_tokens():
        """Remove expired tokens from database"""
        expired_tokens = PasswordResetToken.query.filter(
            PasswordResetToken.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired_tokens:
            db.session.delete(token)
        db.session.commit()
        
        return len(expired_tokens)
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}...>'

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
