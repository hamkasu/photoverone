# PhotoVault - Professional Photo Management Platform

## Overview
PhotoVault is a comprehensive, professional-grade photo management platform developed by Calmic Sdn Bhd. This full-stack application provides advanced photo management capabilities with seamless camera integration, automatic organization, secure storage, and AI-powered features for both web and mobile platforms. The project aims to deliver a production-ready solution for professional photo management and storage, utilizing a modern full-stack web application architecture with a mobile companion.

## User Preferences
- The agent should prioritize the completion of the current task.
- If more information is needed, the agent should ask for it.
- Before making significant changes, the agent should ask for confirmation.
- The agent should use clear and concise language in its responses.
- The agent should propose changes in an iterative manner, focusing on one feature or fix at a time.
- The agent should explain the reasoning behind its code suggestions.
- The agent should not make changes to the `photovault-ios/` folder unless explicitly instructed.
- The agent should not modify the `LICENSE` file.

## System Architecture
PhotoVault utilizes a modern full-stack architecture. The backend is built with Python/Flask, employing SQLAlchemy for ORM with a PostgreSQL database (Replit Neon-backed). Authentication is handled via Flask-Login, and migrations with Flask-Migrate. Image processing leverages OpenCV, Pillow, and scikit-image. The frontend for the web application uses server-side rendered Jinja2 templates with modern CSS and Vanilla JS, featuring a professional camera interface and galleries. The mobile application is developed with Expo React Native, using React Navigation, Axios for HTTP requests, and Expo SecureStore for token management. Core features include a professional camera system with real-time preview and metadata capture, intelligent photo management with AI-powered tagging and face recognition, secure storage with Replit Object Storage integration, advanced photo enhancement tools using OpenCV, multi-user support with role-based access control, and a RESTful API for seamless mobile integration. The system supports a family vault system, montage creation, and voice memo annotations.

### Core Features
- **Professional Camera System**: Full-screen interface, tap-to-capture, real-time preview, metadata capture, multiple format support.
- **Intelligent Photo Management**: Automatic upload/organization, smart categorization via AI, face detection/recognition, people tagging, advanced search.
- **Secure Storage & Organization**: Professional-grade security, Replit Object Storage, custom album management, family vaults, permission-based access.
- **Advanced Photo Enhancement**: Image editing with OpenCV, automatic enhancement, photo comparison, montage creation, voice memo annotations.
- **Multi-User & Administration**: User authentication, admin dashboard, superuser capabilities, family sharing, role-based access control.
- **API & Mobile Integration**: RESTful API, token-based authentication, real-time sync, offline capability for mobile, cross-platform compatibility.

### Technology Stack
- **Backend**: Python 3.11+, Flask 3.0.3, SQLAlchemy 2.0.25, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, WTForms, OpenCV, Pillow, scikit-image, Gunicorn.
- **Frontend (Web)**: Jinja2, modern CSS, Vanilla JS.
- **Mobile (React Native)**: Expo React Native, React Navigation 7.x, Axios, Expo SecureStore, Expo Camera, Expo Image Manipulator.

### Database Architecture
Key entities include Users, Photos, Albums, People, Family Vaults, Stories, and Voice Memos, with various junction tables for many-to-many relationships.

## External Dependencies
- **Database**: PostgreSQL (Replit Neon-backed)
- **Object Storage**: Replit Object Storage
- **Image Processing Libraries**: OpenCV, Pillow, scikit-image
- **Mobile Development Platform**: Expo

## Recent Changes (September 28, 2025)
- Successfully imported GitHub project into Replit environment
- Configured Flask application for Replit deployment with proper host settings (0.0.0.0:5000)
- Set up PostgreSQL database using Replit's built-in Neon database
- Installed all Python dependencies via pip
- Created database tables and verified connectivity
- Configured development workflow with proper environment variables
- Set up deployment configuration for Replit Autoscale using Gunicorn
- Verified application functionality with working homepage, authentication, and static assets

## Replit Configuration
- **Development Server**: Flask dev server on port 5000, binding to 0.0.0.0
- **Production Deployment**: Gunicorn WSGI server configured for Replit Autoscale
- **Database**: Connected to Replit PostgreSQL with proper SSL configuration
- **Environment Variables**: SECRET_KEY, DATABASE_URL, and other database credentials configured
- **Workflow**: PhotoVault Frontend workflow configured and running successfully