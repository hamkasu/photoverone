# photovault/__init__.py

from flask import Flask
from photovault.extensions import db, login_manager, migrate, csrf
from photovault.config import config, DevelopmentConfig, ProductionConfig, TestingConfig
import os

def get_config():
    """Get configuration based on environment"""
    config_name = os.environ.get('FLASK_CONFIG') or 'development'
    return config.get(config_name, DevelopmentConfig)

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
            
            # Verify database connectivity and fail-fast if issues
            try:
                from sqlalchemy import text
                result = db.session.execute(text('SELECT 1'))
                db.session.commit()  # Ensure write access works
                app.logger.info("Database connection verified - read/write access confirmed")
                
                # Verify critical tables exist
                inspector = db.inspect(db.engine)
                required_tables = ['user', 'photo', 'album']
                existing_tables = inspector.get_table_names()
                missing_tables = [table for table in required_tables if table not in existing_tables]
                
                if missing_tables:
                    # Check if we're specifically in release phase (not runtime)
                    import sys
                    is_release_phase = 'release.py' in ' '.join(sys.argv) or os.environ.get('PHOTOVAULT_RELEASE_PHASE') == '1'
                    if is_release_phase:
                        app.logger.warning(f"Missing database tables during release phase: {missing_tables}. Release script should create them.")
                    else:
                        app.logger.critical(f"Missing required database tables: {missing_tables}. Run migrations: flask db upgrade")
                        raise RuntimeError(f"Database schema incomplete - missing tables: {missing_tables}")
                    
                app.logger.info("Database schema validation completed")
                
            except Exception as e:
                app.logger.critical(f"Database connection/schema validation failed: {str(e)}")
                app.logger.critical("Ensure DATABASE_URL is set and database is accessible")
                raise RuntimeError(f"Database connection failed: {str(e)}")
        
        # Bootstrap superuser account if environment variables are set
        _create_superuser_if_needed(app)
    
    return app