"""
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
modification, or use of this software is strictly prohibited.

Website: https://www.calmic.com.my
Email: support@calmic.com.my

CALMIC SDN BHD - "Committed to Excellence"
"""

# photovault/models/__init__.py
from photovault import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # --- Add is_admin field ---
    is_admin = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    # --- Add is_superuser field ---
    is_superuser = db.Column(db.Boolean, default=False, nullable=False, server_default='0')
    # --- End Add admin/superuser fields ---
    photos = db.relationship('Photo', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Time period fields for organizing old photos
    date_start = db.Column(db.Date)  # Start date for photos in this album
    date_end = db.Column(db.Date)    # End date for photos in this album
    time_period = db.Column(db.String(100))  # e.g., "Summer 1987", "Early 1960s"
    location = db.Column(db.String(200))     # e.g., "Grandma's house", "Family farm"
    event_type = db.Column(db.String(100))   # e.g., "Wedding", "Christmas", "Vacation"
    # Removed cover_photo_id to break FK cycle - can be implemented later with a separate solution
    
    # Relationship
    photos = db.relationship('Photo', backref='album', lazy=True)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    nickname = db.Column(db.String(100))
    birth_year = db.Column(db.Integer)
    relationship = db.Column(db.String(100))  # e.g., "Mother", "Brother", "Friend"
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# PhotoPerson association model with face detection metadata
class PhotoPerson(db.Model):
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

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False) # This will now point to the original
    original_name = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text)
    tags = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    # --- Add field to track edited version ---
    edited_filename = db.Column(db.String(255), nullable=True) # Stores the filename of the edited image
    # --- End Add field ---
    
    # Enhanced fields for old photograph digitization
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    
    # Date fields for old photos (often imprecise)
    photo_date = db.Column(db.Date)           # Best guess at actual photo date
    date_text = db.Column(db.String(100))     # Text like "Summer 1987", "Christmas 1985"
    date_circa = db.Column(db.Boolean, nullable=False, default=False)  # True if date is approximate
    
    # Location and context
    location_text = db.Column(db.String(200)) # "Grandma's house", "School playground"
    occasion = db.Column(db.String(200))      # "Wedding day", "Birthday party"
    
    # Physical photo condition and source
    condition = db.Column(db.String(50))      # "Excellent", "Faded", "Torn", "Stained"
    photo_source = db.Column(db.String(100))  # "Family album", "Shoebox", "Frame"
    back_text = db.Column(db.Text)            # Text written on back of photo
    
    # Processing metadata
    needs_restoration = db.Column(db.Boolean, nullable=False, default=False)
    auto_enhanced = db.Column(db.Boolean, nullable=False, default=False)
    processing_notes = db.Column(db.Text)
    
    # Front/back pairing for photos with writing on back
    paired_photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))
    is_back_side = db.Column(db.Boolean, nullable=False, default=False)
    
    # Many-to-many relationship with people through PhotoPerson association
    people = db.relationship('Person', secondary='photo_people', lazy='subquery',
                           backref=db.backref('photos', lazy=True))
