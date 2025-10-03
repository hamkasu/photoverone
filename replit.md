# PhotoVault - Professional Photo Management Platform

## Overview
PhotoVault is a professional photo management web application built with Flask and PostgreSQL. It provides advanced features for photo organization, editing, face detection, family vaults for shared collections, and camera integration.

**Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.**

## Project Architecture

### Technology Stack
- **Backend Framework**: Flask 3.0.3 with Python 3.11
- **Database**: PostgreSQL (Neon-backed via Replit)
- **ORM**: SQLAlchemy 2.0.25 with Flask-SQLAlchemy
- **Migrations**: Alembic via Flask-Migrate
- **Authentication**: Flask-Login with session management
- **Image Processing**: Pillow, OpenCV (headless), scikit-image
- **Forms & CSRF**: Flask-WTF, WTForms
- **Production Server**: Gunicorn 21.2.0
- **Storage**: Replit Object Storage
- **Email**: SendGrid integration
- **Mobile App**: React Native (photovault-ios directory)

### Project Structure
```
photovault/                 # Main application package
├── __init__.py            # App factory and configuration
├── config.py              # Configuration classes
├── models.py              # Database models
├── extensions.py          # Flask extensions initialization
├── forms.py               # WTForms forms
├── routes/                # Route blueprints
│   ├── main.py           # Main/index routes
│   ├── auth.py           # Authentication routes
│   ├── upload.py         # Photo upload handling
│   ├── photo.py          # Photo management
│   ├── gallery.py        # Gallery views
│   ├── family.py         # Family vault features
│   ├── camera_routes.py  # Camera integration
│   ├── photo_detection.py # Face detection
│   ├── smart_tagging.py  # Auto-tagging
│   ├── admin.py          # Admin dashboard
│   └── superuser.py      # Superuser management
├── services/             # Business logic services
│   ├── face_detection_service.py
│   ├── montage_service.py
│   ├── sendgrid_service.py
│   └── app_storage_service.py
├── utils/                # Utility modules
│   ├── file_handler.py
│   ├── image_enhancement.py
│   ├── metadata_extractor.py
│   └── security.py
├── static/               # CSS, JS, images
└── templates/            # Jinja2 templates

migrations/                # Alembic database migrations
main.py                   # Development entry point
wsgi.py                   # Production WSGI entry point
config.py                 # Configuration loader
```

## Recent Changes
- **2025-10-03**: Fresh GitHub import setup completed
  - Installed Python 3.11 module and all required dependencies from requirements.txt
  - Created PostgreSQL database and configured connection via DATABASE_URL
  - Created all database tables using SQLAlchemy models (db.create_all)
  - Stamped migrations to latest version (ad11b5287a15) to sync with schema
  - Verified Flask development server running successfully on port 5000
  - Configured Replit Autoscale deployment with Gunicorn
  - Application tested and confirmed working with all features operational

## Key Features
1. **Photo Management**: Upload, organize, edit, and manage photos
2. **Face Detection**: Automatic face detection using OpenCV
3. **Family Vaults**: Shared photo collections for families
4. **Camera Integration**: Direct camera capture with tap-to-focus
5. **Photo Editing**: Basic and advanced image enhancement
6. **Smart Tagging**: Auto-tagging and metadata extraction
7. **Gallery Views**: Multiple view modes (originals, edited, comparison)
8. **User Management**: Admin and superuser roles
9. **Story Creation**: Create stories from photo collections
10. **Voice Memos**: Attach voice notes to photos

## Environment Configuration

### Required Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (automatically set by Replit)
- `SECRET_KEY`: Flask secret key for sessions (optional, auto-generated if missing)

### Optional Environment Variables
- `FLASK_CONFIG`: Configuration mode (development/production/testing)
- `FLASK_ENV`: Flask environment
- `FLASK_DEBUG`: Debug mode (true/false)
- `MAIL_SERVER`: SMTP server for email
- `MAIL_PORT`: SMTP port
- `MAIL_USE_TLS`: Enable TLS for email
- `MAIL_USERNAME`: Email username
- `MAIL_PASSWORD`: Email password
- `PHOTOVAULT_SUPERUSER_USERNAME`: Initial superuser username
- `PHOTOVAULT_SUPERUSER_EMAIL`: Initial superuser email
- `PHOTOVAULT_SUPERUSER_PASSWORD`: Initial superuser password

## Database

### Schema
The database includes tables for:
- `user`: User accounts with authentication
- `photo`: Photo metadata and storage references
- `album`: Photo albums/collections
- `family_vault`: Shared family photo collections
- `family_member`: Vault membership
- `vault_invitation`: Vault join invitations
- `vault_photo`: Photos in vaults
- `person`: Detected people in photos
- `photo_people`: Photo-person associations
- `story`: Photo stories/narratives
- `story_photo`: Photos in stories
- `story_person`: People featured in stories
- `password_reset_token`: Password reset tokens
- `voice_memo`: Voice notes attached to photos

### Migrations
Database migrations are managed via Flask-Migrate (Alembic).

**Commands:**
- `flask db upgrade`: Apply pending migrations
- `flask db downgrade`: Revert last migration
- `flask db history`: View migration history
- `flask db stamp <revision>`: Mark database as being at a specific revision

**Current Migration**: `ad11b5287a15` - Add last_sent_at to VaultInvitation

## Development

### Running Locally
The application runs automatically via the configured workflow:
```bash
python main.py
```
The server starts on `http://0.0.0.0:5000`

### Configuration
- Development mode uses `DevelopmentConfig` class
- Database: PostgreSQL (Replit-provided)
- Debug mode: Disabled by default for performance
- Session management: Configured for Replit proxy environment

## Deployment

### Replit Autoscale (Production)
The application is configured for Replit Autoscale deployment:
- **Server**: Gunicorn with 2 workers and 4 threads
- **Port**: 5000
- **Configuration**: Uses `ProductionConfig` class
- **WSGI Entry Point**: `wsgi.py`

**Deployment Command:**
```bash
gunicorn --bind=0.0.0.0:5000 --workers=2 --threads=4 --timeout=120 --access-logfile=- --error-logfile=- wsgi:app
```

### Production Considerations
1. Set `SECRET_KEY` environment variable for consistent sessions
2. Database migrations are automatically tracked
3. Logs output to stdout for Replit monitoring
4. SSL/TLS handled by Replit's proxy
5. Object storage via Replit Object Storage

## Security Features
- CSRF protection via Flask-WTF
- Password hashing for user authentication
- Session management with secure cookies
- File upload validation and security
- Rate limiting for sensitive operations
- SQL injection protection via SQLAlchemy ORM

## Mobile Application
The `photovault-ios/` directory contains a React Native mobile app for iOS/Android that interfaces with the PhotoVault backend API.

## Integrations
- **Replit Object Storage**: For photo storage
- **SendGrid**: Email delivery service
- **PostgreSQL (Neon)**: Database hosting

## Future Enhancements
- Enhanced face recognition features
- AI-powered photo tagging
- Cloud backup integration
- Advanced photo editing tools
- Social sharing features

## Notes
- The application is production-ready and tested
- All dependencies are installed and configured
- Database schema is current and migrated
- Workflow is configured for automatic startup
- Deployment settings are optimized for Replit Autoscale
