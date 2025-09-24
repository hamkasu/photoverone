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

## September 23, 2025 - Family Vault Email Invitations Implementation
- Added comprehensive email functionality to family vault invitation system
- Implemented `send_invitation_email` function using existing Replit Mail service integration
- Created professional invitation email templates with branded PhotoVault styling and clear call-to-action buttons  
- Enhanced `invite_member` route to automatically send emails after creating database invitations
- Added robust error handling with appropriate user feedback for both email success and failure scenarios
- Configured email system to provide manual invitation links as fallback when email delivery fails
- Implemented reliability improvements including proper auth token handling and 2xx status code acceptance
- Email functionality includes 7-day invitation expiry with secure token-based invitation acceptance
- All email security best practices maintained: no credential logging, secure token generation, proper timeout handling

## September 24, 2025 - Sequential Button Removal from Camera Interface
- Removed Sequential capture mode from camera interface per user request
- Updated enhanced camera JavaScript to only support Single and Quad Split modes
- Modified `toggleMultiPhotoMode()` to switch directly between single and quad modes
- Removed sequential capture methods: `captureSequentialPhotos()`, `showSequentialCountdown()`, `captureSinglePhotoSequential()`, and `uploadFileWithSequential()`
- Updated mode selector UI logic to only display quad split mode when in multi-photo mode
- Camera interface now has cleaner, simpler mode switching with only essential capture options
- Application maintains all other camera functionality including full-screen mode, zoom controls, flash, and quad split capture

## September 24, 2025 - Navigation Menu Consistency Fix
- Fixed navigation menu inconsistency across application pages  
- Updated `gallery/dashboard.html` template to extend base.html instead of standalone HTML structure
- Updated `index.html` template to extend base.html instead of standalone HTML structure
- All pages now display complete navigation menu with all items: Dashboard, Upload, Gallery, Enhancement, Montage, People, Family, About
- Verified consistent navigation experience across authenticated user pages
- Application maintains professional UI consistency and user experience standards

## September 24, 2025 - Fresh GitHub Import Replit Setup Complete (FINAL)
- Successfully imported fresh PhotoVault GitHub repository to Replit environment from clean repository state
- Installed Python 3.11 programming language module with complete development toolchain and package managers
- Installed all Python dependencies from requirements.txt: Flask 3.0.3, SQLAlchemy 2.0.25, OpenCV image processing libraries, Pillow 11.0.0, and all required packages for full PhotoVault functionality
- Created fresh PostgreSQL database using Replit's native database service with proper environment variables configured (DATABASE_URL, PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE)
- Removed unnecessary iOS workflow and created clean PhotoVault Server workflow on port 5000 with webview output
- Configured Flask development server properly on port 5000 with 0.0.0.0 host binding for Replit proxy compatibility and iframe access
- Successfully verified PhotoVault Server workflow running with status RUNNING - application startup successful with no errors
- Configured production deployment with autoscale targeting and optimized Gunicorn WSGI server configuration (`gunicorn --bind=0.0.0.0:5000 --reuse-port wsgi:app`)
- Verified application functionality: database connections working, web interface fully accessible, all static assets loading (CSS, images, favicon, Calmic logo)
- Confirmed no database migration issues - existing schema compatible with fresh PostgreSQL instance
- All core PhotoVault features ready for use: photo upload, gallery, enhancement, family vaults, authentication, and admin features
- **PRODUCTION READY**: Complete deployment configuration set for autoscale with persistent PostgreSQL database - all data persists between restarts
- **ENVIRONMENT**: Development server running successfully in Replit with proper host configuration for proxy access
- **STATUS**: Fresh GitHub import setup complete and fully operational - application ready for immediate use and development

## September 24, 2025 - Fresh GitHub Clone Replit Environment Setup
- Successfully imported PhotoVault from fresh GitHub repository clone to Replit environment
- Installed Python 3.11 module with complete development toolchain and all Python dependencies
- Configured PostgreSQL database with native Replit database service (DATABASE_URL, PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE)
- Established PhotoVault Server workflow running Flask development server on 0.0.0.0:5000 for Replit proxy compatibility
- Verified successful application startup with all static assets loading (CSS, JavaScript, images, favicon)
- Configured production deployment targeting autoscale with Gunicorn WSGI server
- Application fully operational with complete feature set: photo management, user authentication, family vaults, image enhancement
- All database connections and web interfaces verified working - ready for immediate use and development

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