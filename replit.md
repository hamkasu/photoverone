# PhotoVault - Professional Photo Management Platform

## Overview
PhotoVault is a comprehensive photo management platform developed by Calmic Sdn Bhd. The application provides professional photo management with advanced camera features, automatic organization, and secure storage capabilities.

## Current Project Status
- **Status**: Fully operational in Replit environment
- **Last Updated**: September 28, 2025
- **Environment**: Development with PostgreSQL database
- **Port**: 5000 (configured for Replit proxy)

## Architecture
- **Backend**: Flask 3.0.3 application with SQLAlchemy ORM
- **Database**: PostgreSQL (Replit-provided Neon database)
- **Frontend**: Server-side rendered HTML with modern CSS and JavaScript
- **Image Processing**: OpenCV and Pillow for photo enhancement and manipulation
- **Authentication**: Flask-Login with secure password hashing
- **File Handling**: Multi-format support (PNG, JPG, JPEG, GIF, BMP, WEBP)

## Key Features
1. **Professional Camera Interface**: Full-screen camera with landscape mode and tap-to-capture
2. **Automatic Upload & Organization**: Photos automatically uploaded and organized after capture
3. **Secure Storage**: Professional-grade security for photo storage
4. **Face Detection**: Advanced face recognition and people tagging
5. **Photo Enhancement**: Image editing and enhancement tools
6. **Family Vaults**: Shared photo collections with invitation system
7. **Smart Tagging**: AI-powered photo categorization
8. **Admin Dashboard**: Comprehensive user and system management

## Technical Configuration

### Database Schema
Core tables: user, album, person, photo, family_vault, story, voice_memo, and related junction tables for many-to-many relationships.

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (configured)
- `FLASK_CONFIG`: Set to 'development'
- `FLASK_ENV`: Set to 'development'
- `SECRET_KEY`: Auto-generated secure key

### Deployment Configuration
- **Target**: Autoscale deployment (stateless web application)
- **Server**: Gunicorn WSGI server
- **Port Binding**: 0.0.0.0:5000 for Replit compatibility

## File Structure
```
/
├── photovault/           # Main application package
│   ├── routes/          # Route handlers (auth, upload, photo, etc.)
│   ├── models/          # Database models
│   ├── services/        # Business logic services
│   ├── utils/           # Utility functions
│   ├── static/          # CSS, JS, images
│   └── templates/       # Jinja2 HTML templates
├── migrations/          # Database migration files
├── api/                 # API endpoints
├── photovault-ios/      # React Native mobile app
├── main.py              # Development server entry point
├── wsgi.py              # Production WSGI entry point
├── config.py            # Configuration management
└── requirements.txt     # Python dependencies
```

## Development Workflow
1. The application runs on port 5000 with development server
2. Database migrations are handled via Flask-Migrate
3. Static files served from photovault/static/
4. Templates rendered from photovault/templates/

## Mobile Application
Includes a React Native iOS application in `photovault-ios/` directory with:
- Camera functionality
- Gallery viewing
- Authentication screens
- API integration with the Flask backend

## Security Features
- CSRF protection
- Secure session management
- Password hashing with industry standards
- SSL/HTTPS ready configuration
- File upload security validation

## User Preferences
- No specific user preferences recorded yet

## Recent Changes
- **2025-09-28**: Successfully imported from GitHub and configured for Replit environment
- Set up PostgreSQL database with complete schema
- Configured workflows for development server on port 5000
- Tested application functionality - all features working properly
- Configured deployment settings for production readiness