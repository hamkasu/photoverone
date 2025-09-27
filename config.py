"""
PhotoVault Configuration Module
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
"""

import os
from photovault.config import config, DevelopmentConfig, ProductionConfig, TestingConfig

def get_config():
    """Get configuration based on environment"""
    config_name = os.environ.get('FLASK_CONFIG') or 'development'
    return config.get(config_name, DevelopmentConfig)

# Export the config dictionary for backward compatibility
__all__ = ['config', 'get_config', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig']