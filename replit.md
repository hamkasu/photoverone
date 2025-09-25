# Overview

PhotoVault by Calmic Sdn Bhd is a professional photo management platform built with Flask. Its purpose is to provide secure storage, advanced editing, and comprehensive organization of photographs. It aims to deliver an enterprise-grade solution for personal and professional photo archiving, featuring robust security, role-based access control, user management, and administrative tools. The platform seeks to offer an efficient and secure environment for managing photo collections.

## Recent Changes (September 25, 2025)
- **Fresh GitHub Import Completed**: Successfully imported PhotoVault project from GitHub into Replit environment
- **Python Dependencies**: Installed all required Python packages including Flask, SQLAlchemy, OpenCV, and image processing libraries
- **PostgreSQL Database**: Set up Replit PostgreSQL database and marked existing schema migrations as applied
- **Flask Configuration**: Verified Flask backend is properly configured for Replit environment with:
  - Host binding to 0.0.0.0 (required for Replit proxy)
  - Port 5000 configuration
  - Proper database connection settings
- **Development Workflow**: Configured and started "PhotoVault Frontend" workflow on port 5000
- **Application Testing**: Verified application is running and serving requests successfully with proper static file handling
- **Production Deployment**: Configured autoscale deployment with Gunicorn for production use
- **Previous Migration Notes**: 
  - Fixed Railway deployment compatibility with App Storage detection logic
  - Resolved image serving issues for cross-platform compatibility
  - Application works seamlessly in both Replit and external platforms like Railway

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