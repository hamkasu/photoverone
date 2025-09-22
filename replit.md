# Overview

PhotoVault is a professional photo management platform by Calmic Sdn Bhd, focusing on secure storage, advanced editing, and comprehensive organization of photographs. Leveraging Flask, it provides enterprise-grade security, role-based access control, and robust features for managing photo collections, including user management and administrative tools. The platform's goal is to offer a secure and efficient solution for personal and professional photo archiving with business vision, market potential, and project ambitions.

# Recent Changes

## September 21, 2025 - Fresh GitHub Import Setup Complete
- Successfully imported fresh GitHub repository to Replit environment  
- Installed Python 3.11 with all required dependencies from requirements.txt including Flask, SQLAlchemy, OpenCV, and image processing libraries
- Created and configured PostgreSQL database with proper environment variables (DATABASE_URL, PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE)
- Verified existing database schema with all required tables (user, photo, album, person, photo_people, family_vault, etc.)
- Configured Flask development server on port 5000 with 0.0.0.0 host binding for Replit proxy compatibility
- Set up production deployment configuration with Gunicorn and autoscale targeting for seamless production deployment
- Database connection verified and application startup confirmed successful
- All core components verified working: database connections, web server, static files, routing, frontend interface, user registration, and authentication flows
- Application successfully running with professional dark-themed UI and all PhotoVault features accessible
- OpenCV image enhancement and face detection services properly initialized
- Production-ready WSGI configuration with proper security settings configured

## September 22, 2025 - Fresh GitHub Import Setup Complete (Latest)
- Successfully imported fresh PhotoVault GitHub repository to Replit environment
- Installed Python 3.11 module with complete dependency management
- Cleaned up and fixed requirements.txt file, removing duplicate entries and installing all Flask ecosystem packages
- Installed comprehensive dependency stack: Flask 3.0.3, SQLAlchemy 2.0.25, OpenCV with headless support, Pillow 11.0.0, scikit-image, and all production dependencies
- Created and configured new PostgreSQL database instance with full environment variable setup (DATABASE_URL, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGHOST)
- Verified database connectivity and validated complete PhotoVault schema with all tables (User, Photo, Album, Person, PhotoPerson, PasswordResetToken, VoiceMemo, FamilyVault, Story, etc.)
- Configured Flask development server with 0.0.0.0 host binding on port 5000 for Replit proxy compatibility
- Successfully started PhotoVault server workflow with database table creation in development mode
- Verified application responsiveness with HTTP 200 responses and proper frontend rendering
- Configured production deployment using Gunicorn autoscale with proper WSGI configuration
- Fixed deployment build configuration in nixpacks.toml and made release.py script robust for deployment phases
- All core PhotoVault components verified operational: Flask routing, database ORM, authentication systems, static file serving, and professional UI
- Complete setup verified through testing showing functional PhotoVault interface
- Fresh import setup completed successfully with all original features preserved and ready for development/production use

## September 22, 2025 - Fresh GitHub Repository Import Setup Complete (Previous) (Previous)
- Successfully re-imported PhotoVault project from GitHub to fresh Replit environment
- Installed Python 3.11 runtime with full dependency management using packager tool
- Installed all required Python packages including Flask, SQLAlchemy, OpenCV, image processing libraries, and production dependencies
- Created new PostgreSQL database instance with proper environment variable configuration (DATABASE_URL, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGHOST)
- Verified PhotoVault application structure and all core models (User, Photo, Album, Person, PhotoPerson, PasswordResetToken, VoiceMemo, FamilyVault, etc.)
- Confirmed Flask server startup on port 5000 with 0.0.0.0 host binding for Replit proxy compatibility
- Verified frontend accessibility through Replit proxy with proper host configuration allowing all origins
- Set up production deployment configuration using Gunicorn with autoscale targeting for seamless production deployment
- Application tested and verified running successfully with professional PhotoVault interface accessible
- All core components operational: database connections, web server, static file serving, authentication flows, and professional UI
- Import process completed successfully with all features preserved from original codebase and ready for use

## September 22, 2025 - Fresh GitHub Import Setup Complete (Final)
- Successfully imported fresh PhotoVault GitHub repository to Replit environment from clean slate
- Installed Python 3.11 module with full dependency management and cleaned requirements.txt
- Installed complete dependency stack: Flask 3.0.3, SQLAlchemy 2.0.25, OpenCV with headless support, Pillow 11.0.0, scikit-image, and all production dependencies via packager tool  
- Created and configured new PostgreSQL database with full environment variables (DATABASE_URL, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGHOST)
- Database tables auto-created successfully using SQLAlchemy ORM with all PhotoVault models (User, Photo, Album, Person, PhotoPerson, FamilyVault, Story, etc.)
- Configured Flask development server on port 5000 with 0.0.0.0 host binding for proper Replit proxy compatibility
- Successfully started and verified PhotoVault Server workflow - application running and responding with HTTP 200 status codes
- Verified complete functionality through screenshot testing: professional dark-themed UI, responsive design, navigation working properly  
- Configured production deployment using Gunicorn autoscale targeting with proper WSGI configuration and build commands
- All core PhotoVault components fully operational: Flask routing, database connectivity, authentication systems, static file serving, and professional UI
- Application successfully tested and verified working through Replit proxy with full feature access and proper host configuration
- Fresh GitHub import setup completed successfully with all original features preserved and ready for development and production use

## September 21, 2025 - Email-Based Password Reset Implementation
- Integrated Replit Mail service for email functionality using official OpenInt API
- Implemented comprehensive password reset system with secure token generation and validation
- Created professional HTML and text email templates with branded PhotoVault styling
- Added requests library for HTTP communication with Replit mail service
- Enhanced forgot password routes with actual email sending capability (replaced console logging)
- Configured secure token expiration (1 hour) and single-use validation
- Email system includes fallback to console logging for development environments
- Password reset emails feature styled HTML with clickable buttons and fallback text versions
- All email security best practices implemented: token cleanup, user privacy protection, proper error handling

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend
-   **Framework**: Flask for core web application, routing, and request handling.
-   **Database ORM**: Flask-SQLAlchemy for database interactions.
-   **Authentication**: Flask-Login for user session management, with Werkzeug for password hashing.
-   **Database Migrations**: Flask-Migrate for schema management using Alembic.
-   **Form Handling & Security**: Flask-WTF for form processing and CSRF protection.
-   **Security**: Role-Based Access Control (User, Admin, Superuser), server-side input validation, file validation, and decorator-based route protection.
-   **File Management**: Pillow for image manipulation, Werkzeug for secure filename handling, and organized storage for original and edited versions.
-   **API**: `/api` health check endpoint for monitoring.

## Frontend
-   **Templating**: Jinja2 with Bootstrap 5 for a responsive and modern UI.
-   **Photo Editing**: Client-side canvas-based editing with JavaScript, including responsive sizing and coordinate mapping for various devices.
-   **Camera Integration**: WebRTC getUserMedia API for direct camera access with dual-mode (Sequential and Quad Split) photo capture.
-   **Design**: Mobile-responsive with touch support, professional Calmic branding, and updated navigation bar with a darker theme.

## Photo Management Features
-   **Storage**: Maintains separate original and edited versions of photos.
-   **Metadata**: Tracks file size, upload timestamps, and editing history.
-   **Organization**: Supports album creation (time-based, event-based) and person tagging.
-   **Enhancement**: OpenCV-based advanced image processing for old photograph restoration (CLAHE, bilateral filtering, auto-levels, brightness/contrast adjustments).

# External Dependencies

## Core Framework
-   **Flask**: Web application framework.
-   **Flask-SQLAlchemy**: Database ORM.
-   **Flask-Login**: User authentication.
-   **Flask-Migrate**: Database migrations.
-   **Flask-WTF**: Form handling and CSRF protection.

## Database
-   **PostgreSQL**: Primary database for the Replit environment (configured with native Replit PostgreSQL integration).
-   **SQLAlchemy**: Database abstraction layer.
-   **Flask-Migrate**: Database migration management with Alembic.

## Image Processing
-   **Pillow**: Image manipulation and validation.
-   **Canvas API**: Client-side image editing.
-   **OpenCV.js**: Advanced computer vision and photo enhancement.
-   **scikit-image**: Image processing library.

## Frontend Libraries
-   **Bootstrap 5**: CSS framework for responsive design.
-   **Bootstrap Icons**: Icon library.
-   **WebRTC getUserMedia**: For camera access.

## Production & Development Utilities
-   **Gunicorn**: WSGI HTTP server for production.
-   **python-dotenv**: Environment variable management.
-   **Werkzeug**: WSGI utilities and security.