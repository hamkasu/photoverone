#!/usr/bin/env python3
"""
PhotoVault WSGI Production Entry Point
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

This is the production entry point for PhotoVault using Gunicorn
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the application factory
from photovault import create_app
from config import ProductionConfig

# Create the application using the production configuration
app = create_app(ProductionConfig)

if __name__ == "__main__":
    # This will only run in development mode
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)