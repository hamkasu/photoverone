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