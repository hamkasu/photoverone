# photovault/__init__.py

from flask import Flask
from photovault.extensions import db, login_manager, migrate, csrf
from photovault.config import config, DevelopmentConfig, ProductionConfig, TestingConfig
import os

def get_config():
    """Get configuration based on environment"""
    config_name = os.environ.get('FLASK_CONFIG') or 'development'
    return config.get(config_name, DevelopmentConfig)

def _reset_railway_database(app, db):
    """Reset database on Railway by dropping all tables and recreating them"""
    from sqlalchemy import text
    
    app.logger.warning("Railway: Starting complete database reset...")
    
    try:
        # Get all table names to drop
        result = db.session.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ))
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            app.logger.info(f"Railway: Dropping {len(tables)} existing tables: {tables}")
            # Drop all tables with CASCADE to handle foreign key constraints
            for table in tables:
                db.session.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            db.session.commit()
            app.logger.info("Railway: All existing tables dropped successfully")
        
        # Recreate all tables using SQLAlchemy models
        app.logger.info("Railway: Creating fresh database schema...")
        db.create_all()
        app.logger.info("Railway: Database schema created successfully")
        
        # Verify the photo table has the file_path column
        result = db.session.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'photo' AND column_name = 'file_path'"
        ))
        if result.fetchone():
            app.logger.info("Railway: Verified photo table has file_path column")
        else:
            raise RuntimeError("Railway: Photo table still missing file_path column after reset")
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Railway: Database reset failed: {str(e)}")
        raise

def _create_superuser_if_needed(app):
    """Create superuser account from environment variables if no superuser exists"""
    from photovault.models import User
    
    try:
        # Check if any superuser already exists
        if User.query.filter_by(is_superuser=True).first():
            return
    except Exception as e:
        # Tables don't exist yet - skip superuser creation
        app.logger.info(f"Skipping superuser creation - tables not ready: {str(e)}")
        return
        
    # Get superuser credentials from environment variables
    username = os.environ.get('PHOTOVAULT_SUPERUSER_USERNAME')
    email = os.environ.get('PHOTOVAULT_SUPERUSER_EMAIL')
    password = os.environ.get('PHOTOVAULT_SUPERUSER_PASSWORD')
    
    if username and email and password:
        try:
            # Check if user with same username or email already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                # Make existing user a superuser
                existing_user.is_superuser = True
                existing_user.is_admin = True
                db.session.commit()
                app.logger.info(f"Made existing user {existing_user.username} a superuser")
            else:
                # Create new superuser
                superuser = User(
                    username=username,
                    email=email,
                    is_admin=True,
                    is_superuser=True
                )
                superuser.set_password(password)
                db.session.add(superuser)
                db.session.commit()
                app.logger.info(f"Created superuser account: {username}")
        except Exception as e:
            app.logger.error(f"Failed to create superuser: {str(e)}")
            db.session.rollback()

def create_app(config_class=None):
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    if config_class is None:
        config_class = get_config()
    
    if isinstance(config_class, str):
        config_class = config.get(config_class, config['default'])
    
    app.config.from_object(config_class)
    
    # Initialize configuration
    config_class.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from photovault.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from photovault.routes.main import main_bp
    from photovault.routes.auth import auth_bp
    from photovault.routes.upload import upload_bp
    from photovault.routes.admin import admin_bp
    from photovault.routes.superuser import superuser_bp
    from photovault.routes.photo import photo_bp
    from photovault.routes.camera_routes import camera_bp
    from photovault.routes.gallery import gallery_bp
    from photovault.routes.family import family_bp
    from photovault.routes.smart_tagging import smart_tagging_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(upload_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(superuser_bp, url_prefix='/superuser')
    app.register_blueprint(photo_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(smart_tagging_bp)
    
    # Note: Upload file serving is handled securely via gallery.uploaded_file route with authentication
    
    # Initialize database
    with app.app_context():
        # Only create tables in development/testing or SQLite environments
        # NEVER run db.create_all() in production with PostgreSQL to prevent data loss
        if app.debug or app.testing or 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
            try:
                db.create_all()
                app.logger.info("Created database tables (development/testing mode)")
            except Exception as e:
                app.logger.warning(f"Table creation warning (may already exist): {str(e)}")
        else:
            # Production mode - use migrations instead of db.create_all() to preserve data
            app.logger.info("Production mode: Using migrations to manage schema, preserving existing data")
            
            # Check if running on Railway
            is_railway = os.environ.get('RAILWAY_ENVIRONMENT_NAME') is not None or os.environ.get('RAILWAY_PROJECT_ID') is not None
            railway_auto_reset = os.environ.get('PHOTOVAULT_RAILWAY_AUTO_RESET', '1') == '1'
            
            if is_railway and railway_auto_reset:
                app.logger.info("Railway environment detected - enabling automatic database reset on schema mismatch")
            
            # Verify database connectivity and fail-fast if issues
            try:
                from sqlalchemy import text
                result = db.session.execute(text('SELECT 1'))
                db.session.commit()  # Ensure write access works
                app.logger.info("Database connection verified - read/write access confirmed")
                
                # Verify critical tables exist - use dialect-aware approach
                required_tables = ['user', 'photo', 'album']
                missing_tables = []
                allow_schema_mismatch = os.environ.get('PHOTOVAULT_ALLOW_SCHEMA_MISMATCH', '0') == '1'
                
                try:
                    # Use dialect-aware table detection
                    if db.engine.dialect.name == 'postgresql':
                        # PostgreSQL-specific query using current schema and search path
                        for table in required_tables:
                            result = db.session.execute(text(
                                "SELECT 1 FROM pg_catalog.pg_tables WHERE tablename = :table_name AND schemaname = ANY(current_schemas(false))"
                            ), {"table_name": table})
                            if not result.fetchone():
                                missing_tables.append(table)
                    else:
                        # Fall back to SQLAlchemy inspector for other databases
                        inspector = db.inspect(db.engine)
                        existing_tables = inspector.get_table_names()
                        missing_tables = [table for table in required_tables if table not in existing_tables]
                    
                    # Also verify migration state if using Alembic
                    try:
                        migration_result = db.session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                        current_version = migration_result.scalar()
                        if current_version:
                            app.logger.info(f"Database migration version: {current_version}")
                        else:
                            app.logger.warning("No migration version found in alembic_version table")
                    except Exception as migration_check_error:
                        app.logger.warning(f"Could not verify migration state: {str(migration_check_error)}")
                    
                except Exception as validation_error:
                    app.logger.error(f"Database validation error: {str(validation_error)}")
                    # Railway auto-reset on schema validation errors
                    if is_railway and railway_auto_reset:
                        app.logger.warning("Railway: Schema validation failed, attempting automatic database reset...")
                        try:
                            _reset_railway_database(app, db)
                            app.logger.info("Railway: Database reset completed successfully")
                            return app  # Return early after successful reset
                        except Exception as reset_error:
                            app.logger.error(f"Railway: Database reset failed: {str(reset_error)}")
                            raise RuntimeError(f"Railway database reset failed: {str(reset_error)}")
                    elif not allow_schema_mismatch:
                        raise RuntimeError(f"Database validation failed: {str(validation_error)}")
                
                # Check for schema mismatch (missing file_path column in photo table)
                schema_mismatch_detected = False
                try:
                    # Test for the specific file_path column issue
                    result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'photo' AND column_name = 'file_path'"))
                    if not result.fetchone():
                        schema_mismatch_detected = True
                        app.logger.error("Schema mismatch detected: photo table missing file_path column")
                except Exception as column_check_error:
                    app.logger.warning(f"Could not verify photo table schema: {str(column_check_error)}")
                
                if missing_tables or schema_mismatch_detected:
                    # Check if we're specifically in release phase (not runtime)
                    import sys
                    is_release_phase = 'release.py' in ' '.join(sys.argv) or os.environ.get('PHOTOVAULT_RELEASE_PHASE') == '1'
                    
                    # Railway auto-reset for missing tables or schema mismatch
                    if is_railway and railway_auto_reset and (missing_tables or schema_mismatch_detected):
                        issue_description = f"missing tables: {missing_tables}" if missing_tables else "schema mismatch (file_path column)"
                        app.logger.warning(f"Railway: Database issues detected ({issue_description}), attempting automatic reset...")
                        try:
                            _reset_railway_database(app, db)
                            app.logger.info("Railway: Database reset completed successfully")
                            return app  # Return early after successful reset
                        except Exception as reset_error:
                            app.logger.error(f"Railway: Database reset failed: {str(reset_error)}")
                            raise RuntimeError(f"Railway database reset failed: {str(reset_error)}")
                    elif is_release_phase:
                        app.logger.warning(f"Missing database tables during release phase: {missing_tables}. Release script should create them.")
                    elif allow_schema_mismatch:
                        app.logger.warning(f"Missing tables detected but PHOTOVAULT_ALLOW_SCHEMA_MISMATCH=1: {missing_tables}")
                    else:
                        app.logger.critical(f"Missing required database tables: {missing_tables}. Run 'flask db upgrade' to apply migrations.")
                        raise RuntimeError(f"Database schema incomplete - missing tables: {missing_tables}. Run migrations to fix.")
                
                app.logger.info("Database schema validation completed successfully")
                
            except Exception as e:
                app.logger.critical(f"Database connection/schema validation failed: {str(e)}")
                app.logger.critical("Ensure DATABASE_URL is set and database is accessible")
                raise RuntimeError(f"Database connection failed: {str(e)}")
        
        # Bootstrap superuser account if environment variables are set
        _create_superuser_if_needed(app)
    
    return app