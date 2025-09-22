# Overview

PhotoVault is a professional photo management platform by Calmic Sdn Bhd, focusing on secure storage, advanced editing, and comprehensive organization of photographs. Leveraging Flask, it provides enterprise-grade security, role-based access control, and robust features for managing photo collections, including user management and administrative tools. The platform's goal is to offer a secure and efficient solution for personal and professional photo archiving with business vision, market potential, and project ambitions.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## UI/UX Decisions
-   **Design**: Mobile-responsive with touch support, professional Calmic branding, updated navigation bar with a darker theme.
-   **Templating**: Jinja2 with Bootstrap 5 for a responsive and modern UI.

## Technical Implementations
-   **Backend Framework**: Flask for core web application, routing, and request handling.
-   **Database ORM**: Flask-SQLAlchemy for database interactions.
-   **Authentication**: Flask-Login for user session management, with Werkzeug for password hashing.
-   **Database Migrations**: Flask-Migrate for schema management using Alembic.
-   **Form Handling & Security**: Flask-WTF for form processing and CSRF protection.
-   **File Management**: Pillow for image manipulation, Werkzeug for secure filename handling, and organized storage for original and edited versions.
-   **API**: `/api` health check endpoint for monitoring.
-   **Photo Editing**: Client-side canvas-based editing with JavaScript, including responsive sizing and coordinate mapping.
-   **Camera Integration**: WebRTC getUserMedia API for direct camera access with dual-mode (Sequential and Quad Split) photo capture.

## Feature Specifications
-   **Security**: Role-Based Access Control (User, Admin, Superuser), server-side input validation, file validation, and decorator-based route protection.
-   **Storage**: Maintains separate original and edited versions of photos.
-   **Metadata**: Tracks file size, upload timestamps, and editing history.
-   **Organization**: Supports album creation (time-based, event-based) and person tagging.
-   **Enhancement**: OpenCV-based advanced image processing for old photograph restoration (CLAHE, bilateral filtering, auto-levels, brightness/contrast adjustments).
-   **Email Service**: Integrated password reset system with secure token generation, validation, and professional HTML/text email templates.

## System Design Choices
-   Production deployment configured using Gunicorn autoscale with optimized worker configuration and timeout settings.
-   Robust `release.py` script for Railway deployments handling database table creation, connectivity testing, and table verification.
-   Centralized environment variable management for database configurations.

# External Dependencies

## Core Framework
-   **Flask**: Web application framework.
-   **Flask-SQLAlchemy**: Database ORM.
-   **Flask-Login**: User authentication.
-   **Flask-Migrate**: Database migrations.
-   **Flask-WTF**: Form handling and CSRF protection.

## Database
-   **PostgreSQL**: Primary database (configured with native Replit PostgreSQL integration).
-   **SQLAlchemy**: Database abstraction layer.

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
-   **Replit Mail service (OpenInt API)**: For email functionality.