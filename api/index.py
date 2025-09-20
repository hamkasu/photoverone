"""
PhotoVault Vercel Serverless Entry Point
This file serves as the entry point for Vercel serverless deployment
"""
import sys
import os
from flask import Flask

# Add the root directory to Python path so we can import photovault
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from photovault import create_app
    from config import get_config
    
    # Create the Flask app for production
    os.environ.setdefault('FLASK_CONFIG', 'production')
    app = create_app(get_config())
    
except Exception as e:
    # Fallback in case of import issues
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return f"Import Error: {str(e)}", 500

# This is the WSGI application object that Vercel will use
application = app

# For development testing
if __name__ == '__main__':
    app.run(debug=False)