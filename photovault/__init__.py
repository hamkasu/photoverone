# photovault/__init__.py

from flask import Flask
from photovault.extensions import db, login_manager, migrate, csrf
from config import config, get_config
import os

def _create_superuser_if_needed(app):
    """Create superuser account from environment variables if no superuser exists"""
    from photovault.models import User
    
    # Check if any superuser already exists
    if User.query.filter_by(is_superuser=True).first():
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
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(upload_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(superuser_bp, url_prefix='/superuser')
    app.register_blueprint(photo_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(family_bp)
    
    # Note: Upload file serving is handled securely via gallery.uploaded_file route with authentication
    
    # Initialize database
    with app.app_context():
        # Create tables if they don't exist
        # For SQLite in production or development/testing environments
        if app.debug or app.testing or 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
            try:
                db.create_all()
            except Exception as e:
                app.logger.warning(f"Table creation warning (may already exist): {str(e)}")
        
        # Bootstrap superuser account if environment variables are set
        _create_superuser_if_needed(app)
    
    return app