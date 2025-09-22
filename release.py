#!/usr/bin/env python3
"""
PhotoVault Release Script
Runs database migrations and other deployment tasks for Railway/production deployments
"""
import os
import sys
import logging

# Gracefully handle missing dependencies
DEPENDENCIES_AVAILABLE = False
try:
    from flask import Flask
    from flask_migrate import upgrade
    DEPENDENCIES_AVAILABLE = True
    print("PhotoVault Release: Flask dependencies loaded successfully")
except ImportError as e:
    print(f"PhotoVault Release: Dependencies not available: {e}")
    print("PhotoVault Release: This is normal during build phase")
except Exception as e:
    print(f"PhotoVault Release: Unexpected error loading dependencies: {e}")
    print("PhotoVault Release: Will skip migrations")

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migrations():
    """Run database migrations"""
    print("PhotoVault Release: Starting database migrations...")
    
    # Set release phase flag for the app
    os.environ['PHOTOVAULT_RELEASE_PHASE'] = '1'
    
    if not DEPENDENCIES_AVAILABLE:
        print("PhotoVault Release: Skipping migrations - dependencies not available")
        return True
    
    try:
        from photovault import create_app, get_config
        
        # Create app with production config
        config_class = get_config()
        app = create_app(config_class)
    except ImportError as e:
        print(f"PhotoVault Release: Cannot import application modules: {e}")
        return True  # Don't fail the deployment
    
    with app.app_context():
        try:
            # Run migrations
            upgrade()
            print("PhotoVault Release: Database migrations completed successfully")
            return True
        except Exception as e:
            print(f"PhotoVault Release: Migration failed: {str(e)}")
            print("PhotoVault Release: Attempting fallback table creation...")
            
            # Fallback: Create tables directly
            try:
                from photovault.models import db
                db.create_all()
                print("PhotoVault Release: Fallback table creation successful")
                
                # Stamp Alembic migration state to sync with actual schema
                try:
                    from flask import current_app
                    from alembic import command
                    config = current_app.extensions['migrate'].config
                    command.stamp(config, 'head')
                    print("PhotoVault Release: Alembic migration state stamped successfully")
                except Exception as stamp_error:
                    print(f"PhotoVault Release: Warning - Could not stamp migration state: {str(stamp_error)}")
                    print("PhotoVault Release: This may cause issues with future migrations")
                
                return True
            except Exception as fallback_error:
                print(f"PhotoVault Release: Fallback table creation also failed: {str(fallback_error)}")
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
    
    if not DEPENDENCIES_AVAILABLE:
        print("PhotoVault Release: Dependencies not available - this is likely during build phase")
        print("PhotoVault Release: Migrations will run during application startup")
        return
    
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