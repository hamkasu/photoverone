#!/usr/bin/env python3
"""
PhotoVault Release Script
Runs database migrations and other deployment tasks for Railway/production deployments
"""
import os
import sys
import logging
from flask import Flask
from flask_migrate import upgrade

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from photovault import create_app
from config import get_config

def run_migrations():
    """Run database migrations"""
    print("PhotoVault Release: Starting database migrations...")
    
    # Create app with production config
    config_class = get_config()
    app = create_app(config_class)
    
    with app.app_context():
        try:
            # Run migrations
            upgrade()
            print("PhotoVault Release: Database migrations completed successfully")
            return True
        except Exception as e:
            print(f"PhotoVault Release: Migration failed: {str(e)}")
            return False

def verify_environment():
    """Verify critical environment variables are set"""
    print("PhotoVault Release: Verifying environment configuration...")
    
    # Check for database URL (Railway may use either variable)
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('RAILWAY_DATABASE_URL')
    
    optional_vars = ['SECRET_KEY', 'UPLOAD_FOLDER']
    
    missing_required = []
    missing_optional = []
    
    if not database_url:
        missing_required.append('DATABASE_URL or RAILWAY_DATABASE_URL')
    
    for var in optional_vars:
        if not os.environ.get(var):
            missing_optional.append(var)
    
    if missing_required:
        print(f"PhotoVault Release: CRITICAL - Missing required environment variables: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"PhotoVault Release: WARNING - Missing optional environment variables: {', '.join(missing_optional)}")
        print("PhotoVault Release: These will use default values but may cause issues in production")
    
    print("PhotoVault Release: Environment verification completed")
    return True

def main():
    """Main release script"""
    print("PhotoVault Release: Starting deployment tasks...")
    
    # Verify environment
    if not verify_environment():
        print("PhotoVault Release: Environment verification failed - aborting release")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("PhotoVault Release: Migration failed - aborting release")
        sys.exit(1)
    
    print("PhotoVault Release: All deployment tasks completed successfully")

if __name__ == '__main__':
    main()