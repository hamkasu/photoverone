# PhotoVault - Professional Photo Management Platform

## Overview
PhotoVault is a comprehensive photo management platform built with Flask, featuring advanced camera capabilities, auto-upload functionality, and secure storage. This is a professional photo management solution developed by Calmic Sdn Bhd.

## Current State
- ✅ **Fully functional** Flask web application
- ✅ **Database configured** with PostgreSQL (Neon-backed)
- ✅ **Production ready** with Gunicorn deployment configuration
- ✅ **Replit optimized** with proper host configuration for proxy

## Project Architecture

### Backend (Python Flask)
- **Framework**: Flask 3.0.3 with standard extensions (Login, Migrate, SQLAlchemy, WTF)
- **Database**: PostgreSQL with Alembic migrations
- **Image Processing**: OpenCV, Pillow, scikit-image for advanced photo features
- **Storage**: Replit Object Storage integration
- **Security**: CSRF protection, secure sessions, password hashing

### Features
- **Photo Management**: Upload, organize, and enhance photos
- **Face Detection**: OpenCV-powered face recognition and detection
- **Family Vaults**: Shared photo collections with invitation system
- **Camera Integration**: Full-screen camera with advanced capture modes
- **Auto Enhancement**: Automated photo improvement and metadata extraction
- **Admin Panel**: User management and system statistics

### Database Schema
Complete schema with 14+ tables including:
- Users, Photos, Albums, Family Vaults
- Face detection and people tagging
- Stories and voice memos
- Invitation and permission system

## Development Setup

### Environment Configuration
- **FLASK_CONFIG**: development
- **FLASK_ENV**: development  
- **SECRET_KEY**: Auto-generated for development
- **DATABASE_URL**: Replit PostgreSQL (configured)

### Running the Application
The application runs automatically via the "PhotoVault Frontend" workflow on port 5000.

**Manual start command:**
```bash
export SECRET_KEY="replit-photovault-dev-key-$(date +%s)" && export FLASK_CONFIG=development && export FLASK_ENV=development && export FLASK_DEBUG=false && python main.py
```

## Deployment Configuration
- **Target**: Autoscale deployment (perfect for web applications)
- **Server**: Gunicorn with 3 workers, optimized for Replit environment
- **Port**: 5000 (required for Replit)
- **Host**: 0.0.0.0 (allows all hosts for Replit proxy)

## Recent Changes (September 29, 2025)
- ✅ Installed Python 3.11 and all dependencies
- ✅ Configured PostgreSQL database with existing schema
- ✅ Set up Flask development workflow on port 5000
- ✅ Verified application functionality and UI
- ✅ Configured production deployment settings
- ✅ Completed GitHub import setup for Replit environment

## User Preferences
- **Development approach**: Follow existing project structure and conventions
- **Database**: Use Replit's built-in PostgreSQL (preferred over external services)
- **Deployment**: Use Replit's autoscale deployment for web applications

## Next Steps for Users
1. **Customize configuration**: Set permanent SECRET_KEY in environment variables
2. **Add content**: Upload photos and create family vaults
3. **Configure mail**: Set up SendGrid integration for email features
4. **Deploy**: Use Replit's publish feature to make the app publicly accessible

## File Structure Notes
- **Main application**: `photovault/` package
- **Entry points**: `main.py` (dev), `wsgi.py` (prod), `api/index.py` (serverless)
- **Mobile app**: `photovault-ios/` (React Native - separate deployment)
- **Database migrations**: `migrations/` directory with Alembic
- **Static assets**: `static/` and `photovault/static/`