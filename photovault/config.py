import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def get_engine_options(database_uri):
        """Get SQLAlchemy engine options based on database type"""
        base_options = {
            'pool_pre_ping': True,  # Validates connections before use
            'pool_recycle': 300,    # Recycle connections every 5 minutes
            'pool_timeout': 20,     # Timeout for connection checkout
            'pool_size': 5,         # Connection pool size
            'max_overflow': 10,     # Allow some overflow connections
        }
        
        if database_uri and 'postgresql' in database_uri:
            # PostgreSQL-specific settings
            base_options['connect_args'] = {
                'connect_timeout': 10,
                'sslmode': 'require',
                'options': '-c statement_timeout=30s'
            }
        
        return base_options
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photovault_dev.db')
    
    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False
    
    def __init__(self):
        super().__init__()
        self.SQLALCHEMY_ENGINE_OPTIONS = self.get_engine_options(self.SQLALCHEMY_DATABASE_URI)

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    def __init__(self):
        super().__init__()
        self.SQLALCHEMY_ENGINE_OPTIONS = self.get_engine_options(getattr(self, 'SQLALCHEMY_DATABASE_URI', None))
    
    # Production SECRET_KEY - generate random if not provided but log critical warning
    _secret_key = os.environ.get('SECRET_KEY') or os.environ.get('RAILWAY_SECRET_KEY')
    if not _secret_key:
        import secrets
        _secret_key = secrets.token_urlsafe(32)
        # This will be logged as a critical error in init_app
    SECRET_KEY = _secret_key
    
    # Handle Railway's DATABASE_URL format (postgresql:// vs postgres://)
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('RAILWAY_DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Require explicit confirmation for SQLite in production
    if not database_url:
        if os.environ.get('ALLOW_SQLITE_IN_PROD') == '1':
            database_url = 'sqlite:///photovault_production.db'
        else:
            # Set to None to trigger fail-fast in init_app
            database_url = None
    
    SQLALCHEMY_DATABASE_URI = database_url
    
    # Railway-compatible security settings
    SESSION_COOKIE_SECURE = os.environ.get('HTTPS', 'true').lower() == 'true'
    WTF_CSRF_SSL_STRICT = os.environ.get('HTTPS', 'true').lower() == 'true'
    
    # Production logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', '1')
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Critical security checks
        if not (os.environ.get('SECRET_KEY') or os.environ.get('RAILWAY_SECRET_KEY')):
            app.logger.critical('SECURITY RISK: SECRET_KEY not provided! Generated random key for this session only. '
                              'Set SECRET_KEY environment variable immediately! User sessions will not persist across restarts.')
        
        # Fail-fast if no database configured in production
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            app.logger.critical('DATABASE_URL environment variable must be set for production. '
                              'Set DATABASE_URL or ALLOW_SQLITE_IN_PROD=1 to use SQLite (data loss risk).')
            raise RuntimeError('DATABASE_URL environment variable must be set for production')
        
        if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
            app.logger.warning('SQLite enabled in production via ALLOW_SQLITE_IN_PROD=1 - data may be lost on restarts')
        
        # Log configuration for debugging (without exposing credentials)
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
        if db_uri != 'Not set':
            if 'sqlite' in db_uri:
                app.logger.info("Database: SQLite")
            elif 'postgresql' in db_uri:
                app.logger.info("Database: PostgreSQL")
            else:
                app.logger.info("Database: Configured")
        else:
            app.logger.info("Database: Not set")
        
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