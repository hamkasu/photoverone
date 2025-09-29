# PhotoVault - Professional Photo Management Platform

## Overview
PhotoVault is a comprehensive photo management platform developed by Calmic Sdn Bhd featuring advanced camera capabilities, automated photo organization, and secure cloud storage. The application includes both a Flask web backend and a React Native mobile companion app.

## Project Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.3 with Python 3.11
- **Database**: PostgreSQL (via Replit integration)
- **Key Features**:
  - User authentication and authorization
  - Photo upload and management
  - Advanced image processing with OpenCV
  - Face detection and recognition
  - Family vault sharing
  - Smart photo tagging
  - Email integration via SendGrid

### Frontend Mobile App
- **Framework**: React Native with Expo
- **Location**: `photovault-ios/` directory
- **Features**: Camera integration, photo gallery, user authentication

## Current Configuration

### Development Setup
- **Server**: Running on host 0.0.0.0:5000
- **Environment**: Development mode with PostgreSQL database
- **Workflow**: Configured as "PhotoVault Frontend" workflow
- **Dependencies**: All Python packages installed via requirements.txt

### Database
- **Type**: PostgreSQL (Replit managed)
- **Status**: Initialized with all required tables
- **Migrations**: Managed via Flask-Migrate (Alembic)

### Deployment
- **Target**: Replit Autoscale
- **Build Command**: `python release.py` (runs migrations)
- **Run Command**: `gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 --timeout=120 wsgi:app`

## Key Files
- `main.py`: Development entry point
- `wsgi.py`: Production WSGI entry point
- `release.py`: Database migration and deployment script
- `photovault/`: Main application package
- `migrations/`: Database migration files
- `requirements.txt`: Python dependencies

## Environment Variables
- `DATABASE_URL`: Automatically configured by Replit PostgreSQL
- `SECRET_KEY`: Set via workflow environment
- `FLASK_CONFIG`: Set to 'development' for dev, 'production' for deployment

## Recent Changes (2025-09-29)
- Successfully imported from GitHub
- Installed Python 3.11 and all dependencies
- Cleaned up requirements.txt (removed duplicates)
- Configured PostgreSQL database with migrations  
- Created all required database tables
- Set up development workflow on port 5000 with host 0.0.0.0
- Configured deployment for Replit Autoscale (using gunicorn)
- Application is fully functional and ready for use
- Frontend verified working with professional landing page
- All static assets (CSS, images, favicon) loading correctly

## User Preferences
- Development environment properly configured for Replit
- Frontend serves on 0.0.0.0:5000 (required for Replit proxy)
- Database uses managed PostgreSQL service
- Deployment configured for autoscale hosting