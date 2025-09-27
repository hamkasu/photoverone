"""
PhotoVault Extensions
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.

Centralized extension initialization to avoid instance duplication.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize extensions as singletons
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()