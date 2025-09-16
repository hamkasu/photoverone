"""
PhotoVault - Professional Photo Management Platform
Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
"""

# photovault/version.py
"""Version information for PhotoVault by Calmic Sdn Bhd"""

__version__ = "1.0.0"
__build__ = "2025.09.15"
__author__ = "Calmic Sdn Bhd"
__company__ = "Calmic Sdn Bhd"
__description__ = "Professional Photo Storage and Management Platform"
__website__ = "https://calmic.com.my"
__support_email__ = "support@calmic.com.my"

# Company Information
COMPANY_INFO = {
    "name": "Calmic Sdn Bhd",
    "description": "Leading provider of digital solutions and enterprise software",
    "website": "https://calmic.com.my",
    "support_email": "support@calmic.com.my",
    "address": "Malaysia",
    "established": "2022"
}

# Version history
VERSION_HISTORY = {
    "1.0.0": {
        "date": "2025-09-15",
        "changes": [
            "Initial release by Calmic Sdn Bhd",
            "Professional photo upload and storage system",
            "Advanced photo editing tools with canvas support",
            "Enterprise-grade user authentication and authorization",
            "Comprehensive admin panel with user management",
            "Real-time statistics and analytics dashboard",
            "Role-based access control (Admin/Superuser)",
            "Secure file handling with MIME type validation",
            "Mobile-responsive design for all devices",
            "Company branding and customization features"
        ]
    }
}

def get_version():
    """Get the current version string"""
    return __version__

def get_version_info():
    """Get detailed version information"""
    return {
        "version": __version__,
        "build": __build__,
        "author": __author__,
        "company": __company__,
        "description": __description__,
        "website": __website__,
        "support_email": __support_email__
    }

def get_company_info():
    """Get company information"""
    return COMPANY_INFO

def get_full_version():
    """Get full version string with build info"""
    return f"PhotoVault v{__version__} (Build {__build__}) - {__company__}"

def get_app_title():
    """Get application title with company name"""
    return f"PhotoVault by {__company__}"

def get_copyright():
    """Get copyright string"""
    return f"© 2025 {__company__}. All rights reserved."
