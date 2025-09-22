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
    
    # CRITICAL: Force production config for Railway deployment
    os.environ['FLASK_CONFIG'] = 'production'
    os.environ['PHOTOVAULT_RELEASE_PHASE'] = '1'
    
    if not DEPENDENCIES_AVAILABLE:
        print("PhotoVault Release: Skipping migrations - dependencies not available")
        return True
    
    try:
        from photovault import create_app, get_config
        from photovault.extensions import db
        
        # Create app with production config
        config_class = get_config()
        app = create_app(config_class)
        print(f"PhotoVault Release: App created successfully with config: {config_class.__name__}")
        
        # CRITICAL: Validate we're using PostgreSQL, not SQLite
        database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not database_uri or 'postgresql' not in database_uri:
            print(f"PhotoVault Release: ERROR - Not using PostgreSQL in release phase. URI: {database_uri}")
            print("PhotoVault Release: This would create tables in wrong database - aborting")
            return False
        
        # Log database target (safely, without credentials)
        try:
            db_url = db.engine.url
            print(f"PhotoVault Release: Target database - Driver: {db_url.drivername}, Host: {db_url.host}, Database: {db_url.database}")
        except Exception as log_error:
            print(f"PhotoVault Release: Could not log database details: {log_error}")
            
    except ImportError as e:
        print(f"PhotoVault Release: Cannot import application modules: {e}")
        return True  # Don't fail the deployment
    except Exception as e:
        print(f"PhotoVault Release: Failed to create app: {str(e)}")
        return False
    
    with app.app_context():
        # First, test database connectivity
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("PhotoVault Release: Database connectivity verified")
        except Exception as e:
            print(f"PhotoVault Release: Database connection failed: {str(e)}")
            return False
        
        # Check if tables and required columns exist
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            required_tables = ['user', 'photo', 'album']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"PhotoVault Release: Missing tables: {missing_tables}")
            else:
                # Check if user table has required columns (this is the critical fix)
                if 'user' in existing_tables:
                    user_columns = [col['name'] for col in inspector.get_columns('user')]
                    required_user_columns = ['is_active', 'is_admin', 'is_superuser', 'terms_accepted_at']
                    missing_columns = [col for col in required_user_columns if col not in user_columns]
                    
                    if missing_columns:
                        print(f"PhotoVault Release: User table missing required columns: {missing_columns}")
                        print("PhotoVault Release: Will run migration to add missing columns")
                    else:
                        print("PhotoVault Release: All required tables and columns exist, skipping migration")
                        return True
                else:
                    print("PhotoVault Release: User table missing")
        except Exception as e:
            print(f"PhotoVault Release: Could not check existing tables/columns: {str(e)}")
        
        # Try migrations first
        migration_success = False
        try:
            print("PhotoVault Release: Attempting Flask-Migrate upgrade...")
            upgrade()
            print("PhotoVault Release: Database migrations completed successfully")
            migration_success = True
        except Exception as e:
            print(f"PhotoVault Release: Migration failed: {str(e)}")
            migration_success = False
        
        # Always check for missing columns regardless of migration success
        try:
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'user' in existing_tables:
                user_columns = [col['name'] for col in inspector.get_columns('user')]
                
                # Add missing columns with direct SQL (safer than recreating table)
                missing_fixes = []
                if 'is_active' not in user_columns:
                    missing_fixes.append("ALTER TABLE \"user\" ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
                if 'is_admin' not in user_columns:
                    missing_fixes.append("ALTER TABLE \"user\" ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
                if 'is_superuser' not in user_columns:
                    missing_fixes.append("ALTER TABLE \"user\" ADD COLUMN is_superuser BOOLEAN DEFAULT FALSE")
                if 'terms_accepted_at' not in user_columns:
                    missing_fixes.append("ALTER TABLE \"user\" ADD COLUMN terms_accepted_at TIMESTAMP")
                
                if missing_fixes:
                    print(f"PhotoVault Release: Adding {len(missing_fixes)} missing columns to user table...")
                    for sql in missing_fixes:
                        print(f"PhotoVault Release: Executing: {sql}")
                        db.session.execute(text(sql))
                    db.session.commit()
                    print("PhotoVault Release: Missing columns added successfully!")
                    
                    # Set NOT NULL constraints to match the model (after backfill)
                    constraint_updates = []
                    columns_added = [fix.split()[-4] for fix in missing_fixes]  # Extract column names correctly
                    
                    if 'is_admin' in columns_added:
                        constraint_updates.append({
                            'column': 'is_admin',
                            'backfill': "UPDATE \"user\" SET is_admin = FALSE WHERE is_admin IS NULL",
                            'constraint': "ALTER TABLE \"user\" ALTER COLUMN is_admin SET NOT NULL"
                        })
                    if 'is_superuser' in columns_added:
                        constraint_updates.append({
                            'column': 'is_superuser',
                            'backfill': "UPDATE \"user\" SET is_superuser = FALSE WHERE is_superuser IS NULL",
                            'constraint': "ALTER TABLE \"user\" ALTER COLUMN is_superuser SET NOT NULL"
                        })
                    
                    if constraint_updates:
                        print("PhotoVault Release: Backfilling NULL values and setting NOT NULL constraints...")
                        for update in constraint_updates:
                            print(f"PhotoVault Release: Backfilling {update['column']}: {update['backfill']}")
                            db.session.execute(text(update['backfill']))
                            print(f"PhotoVault Release: Setting constraint: {update['constraint']}")
                            db.session.execute(text(update['constraint']))
                        db.session.commit()
                        print("PhotoVault Release: Constraints updated successfully!")
                else:
                    print("PhotoVault Release: All required user columns already exist")
            
            # Create any missing tables
            print("PhotoVault Release: Ensuring all tables exist with db.create_all()...")
            db.create_all()
            print("PhotoVault Release: Table creation/column addition completed successfully")
            
            if migration_success:
                return True
        except Exception as fallback_error:
            print(f"PhotoVault Release: Column addition failed: {str(fallback_error)}")
            # Rollback any failed transaction to clear session state
            try:
                db.session.rollback()
                print("PhotoVault Release: Database session rolled back")
            except Exception:
                pass
            
            if migration_success:
                print("PhotoVault Release: Migration succeeded but column addition failed - may still work")
                return True
        
        # Final verification that all required tables exist
        try:
            inspector = db.inspect(db.engine)
            created_tables = inspector.get_table_names()
            required_tables = ['user', 'photo', 'album']
            still_missing = [table for table in required_tables if table not in created_tables]
            
            if still_missing:
                print(f"PhotoVault Release: ERROR - Tables still missing after all attempts: {still_missing}")
                return False
            else:
                print(f"PhotoVault Release: Confirmed all required tables exist: {required_tables}")
            
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
        except Exception as final_error:
            print(f"PhotoVault Release: Final verification failed: {str(final_error)}")
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