"""
PhotoVault Main Application File
Development entry point using centralized app factory
"""
import os
from photovault import create_app
from config import get_config

# Create app at module level for WSGI compatibility (Railway backup)
config_class = get_config()
app = create_app(config_class)

if __name__ == '__main__':
    # Development server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting PhotoVault server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )