# PhotoVault - Professional Photo Management Platform

## Overview
PhotoVault is a professional photo management platform built with Python Flask backend. It provides advanced camera features, secure storage, and photo organization capabilities. The application includes user authentication, admin controls, and comprehensive photo processing features.

## Recent Changes (September 27, 2025)
- ✅ Successfully imported from GitHub and configured for Replit environment
- ✅ Installed Python 3.11 and all required dependencies 
- ✅ Set up PostgreSQL database using Replit's built-in database service
- ✅ Ran database migrations successfully - all tables created
- ✅ Fixed workflow configuration to use correct Python path
- ✅ Created superuser account (admin/admin@photovault.com)
- ✅ Configured deployment settings for Replit Autoscale
- ✅ Verified all image processing libraries (OpenCV, Pillow, scikit-image) are working

## Project Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.3 with SQLAlchemy ORM
- **Database**: PostgreSQL (Replit managed)
- **Image Processing**: OpenCV, Pillow, scikit-image for advanced photo features
- **Authentication**: Flask-Login with admin/superuser roles
- **Security**: CSRF protection, secure sessions, password hashing

### Key Features
- Professional camera interface with full-screen mode
- Automatic photo upload and organization
- Secure cloud storage integration (Replit Object Storage)
- Face detection and recognition capabilities
- Advanced image enhancement and editing
- Multi-user family vault system
- Admin dashboard and user management
- Voice memo functionality

### Dependencies
- Core: Flask, SQLAlchemy, Flask-Login, Flask-Migrate
- Image: OpenCV, Pillow, numpy, scikit-image
- Database: psycopg2-binary for PostgreSQL
- Storage: replit-object-storage
- Email: SendGrid integration

## Development Setup

### Environment Variables
- `SECRET_KEY`: Application secret key
- `FLASK_ENV`: Set to 'development'
- `FLASK_CONFIG`: Set to 'development'
- `DATABASE_URL`: PostgreSQL connection (auto-configured by Replit)
- `PHOTOVAULT_SUPERUSER_*`: Default admin account credentials

### Running the Application
The application runs automatically through the Replit workflow:
- **Host**: 0.0.0.0 (configured for Replit proxy)
- **Port**: 5000 (required for Replit frontend)
- **Python Path**: `/home/runner/workspace/.pythonlibs/bin/python3`

### Database
- PostgreSQL database managed by Replit
- Migrations handled by Flask-Migrate
- All tables created and superuser account initialized

## Deployment
- **Target**: Replit Autoscale (stateless web application)
- **Production Server**: Gunicorn with 2 workers
- **Static Files**: Served by Flask in development, CDN recommended for production
- **SSL**: Handled by Replit deployment platform

## User Preferences
- Professional photo management application
- Clean, modern UI design
- Security-focused with proper authentication
- Advanced image processing capabilities
- Multi-user support with role-based access

## Current Status
The application is fully operational and ready for use. All core features are working including:
- User registration and authentication
- Photo upload and management
- Camera functionality
- Image processing features
- Admin controls
- Database operations

## Mobile App
The project includes a React Native mobile application in `photovault-ios/` directory, but the main focus is the web application for the Replit environment.