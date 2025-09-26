# Overview

PhotoVault by Calmic Sdn Bhd is a professional photo management platform built with Flask. Its purpose is to provide secure storage, advanced editing, and comprehensive organization of photographs. It aims to deliver an enterprise-grade solution for personal and professional photo archiving, featuring robust security, role-based access control, user management, and administrative tools. The platform seeks to offer an efficient and secure environment for managing photo collections.

## Recent Changes (September 26, 2025)
- **Fresh GitHub Import Setup Complete**: Successfully set up PhotoVault project from GitHub clone in Replit environment
- **Python Environment**: Installed Python 3.11 and all required dependencies from requirements.txt including Flask, SQLAlchemy, OpenCV, and image processing libraries
- **PostgreSQL Database**: Set up Replit PostgreSQL database with proper DATABASE_URL configuration and resolved database schema synchronization issues
- **Database Schema Fix**: Resolved critical missing `file_path` column error in photo table by manually adding all missing columns from SQLAlchemy model to synchronize database schema with application code
- **Flask Configuration**: Verified Flask backend is properly configured for Replit environment with:
  - Host binding to 0.0.0.0 (required for Replit proxy)
  - Port 5000 configuration  
  - Development mode with proper database connection
- **Development Workflow**: Configured and started "PhotoVault Frontend" workflow on port 5000
- **Application Status**: Verified application is running successfully and serving HTTP requests with proper static file handling
- **Production Deployment**: Configured autoscale deployment with Gunicorn for production use
- **Critical Railway Container Crash Fix**: Fixed photo detection feature causing Railway container crashes by:
  - Implementing memory management with 25MP size limit for detection and 30MP for extraction
  - Removing problematic image resizing that broke coordinate alignment between detection and extraction
  - Adding proper cleanup of OpenCV image objects and database sessions
  - Improving error handling to prevent resource leaks
  - Rejecting oversized images with clear user error messages instead of processing them
- **Previous Bug Fixes**: 
  - Fixed Railway deployment login error by adding missing `is_active` field to User model
  - Resolved database schema alignment between SQLAlchemy models and Alembic migrations
  - Fixed Railway deployment compatibility with App Storage detection logic
  - Resolved image serving issues for cross-platform compatibility

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## UI/UX Decisions
- **Templating**: Jinja2 with Bootstrap 5 for a responsive and modern UI.
- **Design**: Mobile-responsive with touch support, professional Calmic branding, and a dark-themed navigation bar.
- **Camera Interface**: Streamlined camera interface supporting Single and Quad Split modes; sequential capture mode has been removed for simplicity.
- **Navigation Consistency**: All authenticated pages now extend a base template to ensure a consistent navigation menu across the application.

## Technical Implementations
- **Backend Framework**: Flask for core web application, routing, and request handling.
- **Database ORM**: Flask-SQLAlchemy for database interactions, with PostgreSQL as the primary database.
- **Authentication**: Flask-Login for user session management, using Werkzeug for password hashing.
- **Security**: Role-Based Access Control (User, Admin, Superuser), server-side input validation, file validation, CSRF protection via Flask-WTF, and decorator-based route protection. Password reset functionality implemented with secure token generation and email delivery.
- **File Management**: Pillow for image manipulation, Werkzeug for secure filename handling, and organized storage for original and edited versions.
- **API**: `/api` health check endpoint for monitoring.
- **Image Processing**: OpenCV-based advanced image processing for photo enhancement (CLAHE, bilateral filtering, auto-levels, brightness/contrast adjustments).
- **Photo Detection & Cropping**: Dedicated functionality allows users to upload images containing multiple photos, automatically detect them using OpenCV, and extract individual photos. This includes secure token-based file handling and a drag-and-drop interface.
- **Email Services**: Integration with Replit Mail for features like password reset and family vault invitations, utilizing secure token-based systems and branded HTML templates.

## Feature Specifications
- **Photo Storage**: Maintains separate original and edited versions, tracking metadata like file size and timestamps.
- **Organization**: Supports album creation (time-based, event-based) and person tagging.
- **Camera Integration**: WebRTC getUserMedia API for direct camera access.
- **Family Vaults**: Supports invitation systems with email functionality and secure, time-limited tokens.

# External Dependencies

## Core Framework
- **Flask**: Web application framework.
- **Flask-SQLAlchemy**: Database ORM.
- **Flask-Login**: User authentication.
- **Flask-Migrate**: Database migrations.
- **Flask-WTF**: Form handling and CSRF protection.

## Database
- **PostgreSQL**: Primary database (Replit native integration).
- **SQLAlchemy**: Database abstraction layer.

## Image Processing
- **Pillow**: Image manipulation and validation.
- **OpenCV**: Advanced computer vision and photo enhancement.
- **scikit-image**: Image processing library.

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design.
- **Bootstrap Icons**: Icon library.
- **WebRTC getUserMedia**: For camera access.

## Production & Development Utilities
- **Gunicorn**: WSGI HTTP server for production deployment.
- **python-dotenv**: Environment variable management.
- **Werkzeug**: WSGI utilities and security.