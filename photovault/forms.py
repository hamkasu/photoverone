# photovault/forms.py

import re
import secrets
import string
from datetime import datetime, timedelta

def validate_vault_name(name):
    """Validate family vault name"""
    if not name or len(name.strip()) < 3:
        return False, "Vault name must be at least 3 characters long"
    if len(name.strip()) > 200:
        return False, "Vault name must be less than 200 characters"
    return True, "Valid vault name"

def validate_vault_description(description):
    """Validate family vault description"""
    if description and len(description) > 1000:
        return False, "Description must be less than 1000 characters"
    return True, "Valid description"

def validate_email_for_invitation(email):
    """Validate email format for invitations"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email:
        return False, "Email is required"
    if not re.match(pattern, email):
        return False, "Please enter a valid email address"
    return True, "Valid email"

def validate_invitation_role(role):
    """Validate family member role"""
    valid_roles = ['member', 'contributor', 'admin']
    if role not in valid_roles:
        return False, f"Role must be one of: {', '.join(valid_roles)}"
    return True, "Valid role"

def validate_story_title(title):
    """Validate story title"""
    if not title or len(title.strip()) < 3:
        return False, "Story title must be at least 3 characters long"
    if len(title.strip()) > 200:
        return False, "Story title must be less than 200 characters"
    return True, "Valid title"

def validate_story_content(content):
    """Validate story content"""
    if not content or len(content.strip()) < 10:
        return False, "Story content must be at least 10 characters long"
    if len(content.strip()) > 10000:
        return False, "Story content must be less than 10,000 characters"
    return True, "Valid content"

def validate_story_type(story_type):
    """Validate story type"""
    valid_types = ['memory', 'biography', 'event', 'tradition']
    if story_type not in valid_types:
        return False, f"Story type must be one of: {', '.join(valid_types)}"
    return True, "Valid story type"

def generate_vault_code():
    """Generate a unique vault code for sharing"""
    characters = string.ascii_uppercase + string.digits
    # Generate a code like 'PV-ABC123' (PhotoVault prefix)
    code = 'PV-' + ''.join(secrets.choice(characters) for _ in range(6))
    return code

def generate_invitation_token():
    """Generate a secure invitation token"""
    return secrets.token_urlsafe(32)

def get_invitation_expiry():
    """Get expiry date for invitations (7 days from now)"""
    return datetime.utcnow() + timedelta(days=7)

def validate_vault_code(code):
    """Validate vault code format"""
    if not code:
        return False, "Vault code is required"
    # Check if it matches PV-XXXXXX format
    pattern = r'^PV-[A-Z0-9]{6}$'
    if not re.match(pattern, code):
        return False, "Invalid vault code format. Should be like 'PV-ABC123'"
    return True, "Valid vault code"

def validate_person_role_in_story(role):
    """Validate person's role in a story"""
    if role and len(role) > 100:
        return False, "Role description must be less than 100 characters"
    return True, "Valid role"

def validate_photo_caption(caption):
    """Validate photo caption for stories or vault shares"""
    if caption and len(caption) > 500:
        return False, "Caption must be less than 500 characters"
    return True, "Valid caption"