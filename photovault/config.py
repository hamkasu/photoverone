import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Camera-specific settings
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    CAMERA_QUALITY = 0.85  # JPEG quality for camera captures
    MAX_IMAGE_DIMENSION = 2048  # Maximum width/height for saved images
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security settings
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False  # Set to True in production with HTTPS
    
    # Mail settings (for user registration/password reset)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration"""
        # Create upload directory
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photovault_dev.db')
    
    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Production requires these environment variables - will be validated in init_app
    SECRET_KEY = os.environ.get('SECRET_KEY') or None
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or None
    
    # Strict security for production
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    
    # Production logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Validate required production environment variables
        if not app.config.get('SECRET_KEY'):
            raise RuntimeError('SECRET_KEY environment variable must be set for production')
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            raise RuntimeError('DATABASE_URL environment variable must be set for production')
        
        # Configure logging for production
        import logging
        import sys
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            # Use stdout/stderr logging for containerized environments (Replit Autoscale)
            if os.environ.get('LOG_TO_STDOUT', '').lower() in ['true', '1', 'yes']:
                stream_handler = logging.StreamHandler(sys.stdout)
                stream_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                ))
                stream_handler.setLevel(logging.INFO)
                app.logger.addHandler(stream_handler)
            else:
                # Default to stdout for production deployments like Replit Autoscale
                stream_handler = logging.StreamHandler(sys.stdout)
                stream_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                ))
                stream_handler.setLevel(logging.INFO)
                app.logger.addHandler(stream_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('PhotoVault startup')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}