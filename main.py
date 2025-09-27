"""
PhotoVault Main Application File
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Development entry point using centralized app factory
"""
import os
import logging
from photovault import create_app
from config import get_config

# Create app at module level for WSGI compatibility (Railway backup)
config_class = get_config()
app = create_app(config_class)

# Configure logging to suppress health check requests
class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        # Suppress logs for HEAD /api health checks
        return not (hasattr(record, 'getMessage') and 
                   'HEAD /api' in record.getMessage())

if __name__ == '__main__':
    # Development server configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Add filter to suppress health check logs
    logging.getLogger('werkzeug').addFilter(HealthCheckFilter())
    
    print(f"Starting PhotoVault server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )