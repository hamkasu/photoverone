# Overview

PhotoVault is a professional photo management platform designed for secure storage, advanced editing, and comprehensive organization of photographs. Developed by Calmic Sdn Bhd, it leverages Flask to provide enterprise-grade security, role-based access control, and robust features for managing photo collections, including user management and administrative tools. The platform aims to offer a secure and efficient solution for personal and professional photo archiving.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend
- **Framework**: Flask for core web application, routing, and request handling.
- **Database ORM**: Flask-SQLAlchemy for database interactions and model definitions.
- **Authentication**: Flask-Login for user session management and authentication, with Werkzeug for password hashing.
- **Database Migrations**: Flask-Migrate for schema management using Alembic.
- **Form Handling & Security**: Flask-WTF for form processing and CSRF protection.
- **Security**: Role-Based Access Control (User, Admin, Superuser), server-side input validation, file validation, and decorator-based route protection.
- **File Management**: Pillow for image manipulation, Werkzeug for secure filename handling, and organized storage for original and edited versions.

## Frontend
- **Templating**: Jinja2 with Bootstrap 5 for a responsive and modern UI.
- **Photo Editing**: Client-side canvas-based editing with JavaScript.
- **Camera Integration**: WebRTC getUserMedia API for direct camera access.
- **Design**: Mobile-responsive with touch support and professional Calmic branding.

## Photo Management Features
- **Storage**: Maintains separate original and edited versions of photos.
- **Metadata**: Tracks file size, upload timestamps, and editing history.
- **Organization**: Supports album creation (time-based, event-based) and person tagging.
- **Enhancement**: OpenCV-based advanced image processing for old photograph restoration, including CLAHE, bilateral filtering, auto-levels, and brightness/contrast adjustments.

# External Dependencies

## Core Framework
- **Flask**: Web application framework.
- **Flask-SQLAlchemy**: Database ORM.
- **Flask-Login**: User authentication.
- **Flask-Migrate**: Database migrations.
- **Flask-WTF**: Form handling and CSRF protection.

## Database
- **SQLite**: Primary database for the Replit environment.
- **PostgreSQL**: Supported for production deployments (via psycopg2-binary).
- **SQLAlchemy**: Database abstraction layer.

## Image Processing
- **Pillow**: Image manipulation and validation.
- **Canvas API**: Client-side image editing.
- **OpenCV.js**: Used for advanced computer vision features and photo enhancement.

## Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design.
- **Bootstrap Icons**: Icon library.
- **WebRTC getUserMedia**: For camera access.

## Production & Development Utilities
- **Gunicorn**: WSGI HTTP server for production.
- **python-dotenv**: Environment variable management.
- **Werkzeug**: WSGI utilities and security.

# Recent Changes

## September 18, 2025 - Fresh GitHub Import Successfully Configured
- **GitHub Import Setup**: Successfully set up fresh clone of PhotoVault repository in Replit environment
- **Python Environment**: Installed Python 3.11 with all project dependencies from requirements.txt using UPM
- **Version Compatibility Fix**: Resolved Flask-Werkzeug version mismatch error by installing exact compatible versions (Flask==3.0.3, Werkzeug==3.0.3)
- **Dependencies Installation**: Successfully installed all required packages including Flask, image processing libraries (Pillow, OpenCV), database libraries (SQLAlchemy, psycopg2), and production tools (Gunicorn)
- **Database Configuration**: Verified existing SQLite databases are intact and accessible (photovault_dev.db, photovault.db)
- **Development Server**: Configured Flask development server on port 5000 with host 0.0.0.0 for Replit compatibility
- **Workflow Configuration**: Set up "PhotoVault Server" workflow for automatic server management on port 5000
- **Application Testing**: Verified application starts successfully and serves web interface without internal server errors
- **Frontend Compatibility**: Confirmed application works properly in Replit's proxied environment, serving requests with proper HTTP status codes
- **Production Deployment**: Configured autoscale deployment with Gunicorn WSGI server for production using port 5000
- **Error Resolution**: Fixed TypeError involving 'partitioned' parameter in Flask sessions by ensuring version compatibility
- **Import Status**: PhotoVault application fully operational in Replit environment - GitHub import setup completed successfully

## September 18, 2025 - Photo Editor Responsive Sizing & Save Functionality Fixed
- **Image Sizing Fixed**: Resolved image sizing problem where editor images were sized for laptop screens regardless of device
- **Responsive Canvas**: Modified `resizeCanvas()` function to calculate available screen space and scale images to fit device screens
- **Aspect Ratio Preservation**: Ensures images maintain proper proportions on all device sizes (mobile, tablet, desktop)
- **Coordinate Mapping**: Updated `getMousePos()` function for accurate drawing and interaction with scaled images
- **Dynamic Adaptation**: Added window resize listener for device orientation changes and responsive behavior
- **Mobile Optimization**: Editor provides optimal viewing and editing experience across all device types
- **Toolbox Layout Improved**: Widened editing toolbox and optimized button layout to prevent word wrapping in markup tool labels
- **Save Functionality Fixed**: Resolved save failure issue by ensuring CSRF token is properly available to JavaScript
- **Security Maintained**: Fixed save functionality while keeping all CSRF protection intact - no security compromises

## September 18, 2025 - Simultaneous Quad-Photo Capture Feature Added
- **New Feature**: Enhanced camera interface with simultaneous quad-photo capture capability
- **Dual Mode System**: Users can choose between Sequential (4 photos with countdown) or Quad Split (4 photos simultaneously)
- **Split-Screen UI**: Visual overlay divides camera into 4 labeled quadrants (Top Left, Top Right, Bottom Left, Bottom Right)
- **Simultaneous Capture**: Single camera frame is split into 4 separate photos captured at exactly the same time
- **Unique Naming**: Each quadrant photo gets distinct filename (quad-top-left, quad-top-right, etc.)
- **Backend Support**: Upload system preserves quadrant information in filenames for proper organization
- **User Experience**: Toggle between Sequential and Quad modes with visual feedback and professional interface
- **Security**: Maintained CSRF protection and login requirements for all camera functionality

## September 18, 2025 - Fresh GitHub Import Setup Complete
- **GitHub Import**: Successfully imported fresh clone of PhotoVault repository
- **Python Environment**: Installed Python 3.11 with all project dependencies from requirements.txt
- **Dependencies Installation**: Successfully installed all Flask, image processing, and utility dependencies including Flask 3.0.3, SQLAlchemy 2.0.25, Pillow 11.0.0, OpenCV, and all required packages
- **Database**: Verified existing SQLite databases are intact and accessible (photovault_dev.db, photovault.db)
- **Development Server**: Configured Flask development server on port 5000 with host 0.0.0.0 for Replit compatibility
- **Workflow**: Set up "PhotoVault Server" workflow for automatic server management on port 5000
- **Application Testing**: Verified application starts successfully and serves web interface with proper Bootstrap styling
- **Frontend Compatibility**: Confirmed application works properly in Replit's proxied environment, serving requests with 200 status codes
- **Deployment**: Configured autoscale deployment with Gunicorn WSGI server for production using port 5000
- **Import Completion**: PhotoVault application fully operational in Replit environment - fresh import successfully completed
- **Bug Fix**: Fixed dashboard statistics to properly count edited photos instead of hardcoded 0, and corrected original photos calculation

## September 19, 2025 - Login System Fixed & Log Cleanup Completed
- **Critical Login Fix**: Resolved Flask-Werkzeug version compatibility issue that was causing "TypeError: Response.set_cookie() got an unexpected keyword argument 'partitioned'" during user authentication
- **Version Control**: Permanently installed exact compatible versions (Flask==3.0.3, Werkzeug==3.0.3) to prevent future compatibility issues
- **Authentication System**: Login, registration, and session management now working properly without internal server errors
- **Health Check Endpoint**: Added `/api` health check endpoint to handle Replit infrastructure monitoring requests
- **Log Cleanup**: Eliminated continuous 404 error spam from missing /api endpoint - now returns proper HTTP 200 responses
- **Server Stability**: PhotoVault server running smoothly with clean logs and proper request handling
- **User Experience**: All authentication features fully operational - users can now log in, register, and access dashboard successfully

## September 19, 2025 - GitHub Import Setup & Navigation Design Update Completed
- **GitHub Fresh Clone**: Successfully imported and configured fresh clone of PhotoVault repository in clean Replit environment
- **Python 3.11 Environment**: Installed Python 3.11 with comprehensive package management support and all required dependencies
- **Complete Dependencies Installation**: Successfully installed all Flask, image processing, and utility dependencies including:
  - Core Framework: Flask 3.0.3, Werkzeug 3.0.3, SQLAlchemy 2.0.25
  - Flask Extensions: Flask-Login 0.6.3, Flask-Migrate 4.1.0, Flask-SQLAlchemy 3.1.1, Flask-WTF 1.2.1  
  - Image Processing: Pillow 11.0.0, OpenCV 4.8.0.76, scikit-image 0.21.0, numpy 1.24.4
  - Database: psycopg2-binary 2.9.9 for PostgreSQL support
  - Production Server: Gunicorn 21.2.0 with security and utility packages
- **Development Server**: Successfully configured Flask development server on port 5000 with host 0.0.0.0 for Replit proxy compatibility  
- **Workflow Configuration**: Set up and verified "PhotoVault Server" workflow running successfully with automatic monitoring
- **Navigation Design Update**: Updated navigation bar across all pages to match clean professional design:
  - Removed icons from main navigation links for cleaner appearance  
  - Applied darker background theme (#2c2c2c) for professional look
  - Improved responsive design for mobile devices
  - Fixed all navigation links to use url_for for consistency
- **Upload Route Optimization**: Changed upload serving from '/static/uploads/' to '/uploads/' to prevent route conflicts
- **Application Testing**: Verified application starts without errors, serves web interface with proper HTTP 200 responses, and all features working
- **Production Deployment Setup**: Configured autoscale deployment with Gunicorn WSGI server using 2 workers for production readiness
- **Fresh Import Status**: PhotoVault application fully operational with updated navigation design - GitHub import and customization completed successfully

## September 19, 2025 - Latest Fresh GitHub Import Setup Completed Successfully
- **Latest Import**: Successfully completed fresh GitHub repository import and full Replit environment setup
- **Python Environment**: Installed Python 3.11 with comprehensive dependency support and package management
- **Dependencies Resolution**: Successfully installed all required packages from requirements.txt including Flask 3.0.3, Werkzeug 3.0.3, SQLAlchemy 2.0.25, image processing libraries (Pillow, OpenCV), and production tools
- **Database Setup**: SQLite development database automatically configured and ready for use
- **Development Server**: Flask development server configured on port 5000 with host 0.0.0.0 for Replit proxy compatibility
- **Workflow Management**: "PhotoVault Server" workflow successfully running and serving HTTP 200 responses
- **Production Configuration**: Autoscale deployment configured with optimized Gunicorn WSGI server settings for production deployment
- **Application Verification**: Verified complete application functionality, proper server startup, and response handling
- **Import Completion**: Fresh GitHub import successfully configured and operational in Replit environment