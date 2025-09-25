"""
PhotoVault Upload Security & Validation Utility
Centralized, comprehensive validation and security for all file uploads
"""
import os
import re
import time
import uuid
import logging
import mimetypes
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional, List
from collections import defaultdict
from flask import request, current_app, session
from flask_login import current_user
from werkzeug.utils import secure_filename
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Security Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
    'image/webp', 'image/bmp', 'image/tiff'
}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
MAX_IMAGE_DIMENSION = 4096
MIN_IMAGE_DIMENSION = 10
THUMBNAIL_SIZE = (300, 300)

# Rate limiting configuration
RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds
MAX_UPLOADS_PER_WINDOW = 20
MAX_UPLOADS_PER_HOUR = 100

# PRODUCTION WARNING: In-memory rate limiting storage
# This will NOT work correctly in production with multiple processes/instances
# TODO: Replace with Redis or database-backed rate limiting for production deployment
# Recommended: Use Flask-Limiter with Redis backend for production
_rate_limit_storage = defaultdict(list)
_rate_limit_cleanup_last = time.time()

class UploadSecurityError(Exception):
    """Custom exception for upload security violations"""
    pass

class RateLimitExceeded(UploadSecurityError):
    """Rate limit exceeded exception"""
    pass

def sanitize_input(value: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks and path traversal
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Remove any non-printable characters
    sanitized = re.sub(r'[^\x20-\x7E]', '', str(value))
    
    # Remove path traversal attempts
    sanitized = sanitized.replace('..', '').replace('/', '').replace('\\', '')
    
    # Remove script injection attempts
    sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    
    # Truncate to max length
    return sanitized[:max_length].strip()

def generate_secure_filename(original_filename: str, username: str = None, prefix: str = "", force_format: str = None) -> str:
    """
    Generate a secure, unique filename with proper sanitization
    
    Args:
        original_filename: Original filename from upload
        username: Username for file organization (will be sanitized)
        prefix: Optional prefix (e.g., 'camera', 'quad')
        force_format: Force specific extension (e.g., 'jpg' for camera uploads)
        
    Returns:
        Secure filename
    """
    # Sanitize all inputs
    if username:
        username = sanitize_input(username, 50)
    if prefix:
        prefix = sanitize_input(prefix, 20)
    
    # Get secure file extension - force specific format if specified
    if force_format:
        ext = force_format.lower()
        if ext not in ALLOWED_EXTENSIONS:
            ext = 'jpg'  # Fallback to safe extension
    elif original_filename and '.' in original_filename:
        ext = secure_filename(original_filename).rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            ext = 'jpg'  # Default safe extension
    else:
        ext = 'jpg'
    
    # Generate timestamp and unique ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    # Build filename parts
    parts = []
    if username:
        parts.append(username)
    if prefix:
        parts.append(prefix)
    parts.extend([timestamp, unique_id])
    
    filename = "_".join(parts) + f".{ext}"
    
    # Ensure filename isn't too long (filesystem limits)
    if len(filename) > 200:
        filename = f"{unique_id}_{timestamp}.{ext}"
    
    return filename

def check_rate_limit(user_id: str, endpoint: str = "upload") -> bool:
    """
    Check if user has exceeded rate limits for uploads
    
    Args:
        user_id: User identifier
        endpoint: Endpoint identifier for separate rate limits
        
    Returns:
        True if within limits, raises RateLimitExceeded if exceeded
    """
    global _rate_limit_cleanup_last
    
    # Clean up old entries periodically
    current_time = time.time()
    if current_time - _rate_limit_cleanup_last > 60:  # Clean every minute
        _cleanup_rate_limit_storage()
        _rate_limit_cleanup_last = current_time
    
    key = f"{user_id}:{endpoint}"
    now = time.time()
    
    # Get user's upload timestamps
    user_uploads = _rate_limit_storage[key]
    
    # Count uploads in current window (5 minutes)
    recent_uploads = [ts for ts in user_uploads if now - ts < RATE_LIMIT_WINDOW]
    
    # Count uploads in current hour
    hourly_uploads = [ts for ts in user_uploads if now - ts < 3600]
    
    if len(recent_uploads) >= MAX_UPLOADS_PER_WINDOW:
        raise RateLimitExceeded(f"Too many uploads in the last {RATE_LIMIT_WINDOW//60} minutes. Limit: {MAX_UPLOADS_PER_WINDOW}")
    
    if len(hourly_uploads) >= MAX_UPLOADS_PER_HOUR:
        raise RateLimitExceeded(f"Too many uploads in the last hour. Limit: {MAX_UPLOADS_PER_HOUR}")
    
    # Record this upload attempt
    user_uploads.append(now)
    _rate_limit_storage[key] = user_uploads
    
    return True

def _cleanup_rate_limit_storage():
    """Clean up old rate limit entries"""
    cutoff_time = time.time() - 3600  # Keep last hour
    
    for key in list(_rate_limit_storage.keys()):
        _rate_limit_storage[key] = [
            ts for ts in _rate_limit_storage[key] 
            if ts > cutoff_time
        ]
        if not _rate_limit_storage[key]:
            del _rate_limit_storage[key]

def validate_image_file(file, check_dimensions: bool = True) -> Tuple[bool, str, Optional[Dict]]:
    """
    Comprehensive image file validation
    
    Args:
        file: FileStorage object from Flask request
        check_dimensions: Whether to validate image dimensions
        
    Returns:
        Tuple of (is_valid, error_message, metadata)
    """
    try:
        # Basic file checks
        if not file or not file.filename:
            return False, "No file provided", None
        
        # Sanitize filename
        original_filename = sanitize_input(file.filename, 255)
        if not original_filename:
            return False, "Invalid filename", None
        
        # Check file extension
        if '.' not in original_filename:
            return False, "File must have an extension", None
            
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}", None
        
        # Check MIME type if available
        if hasattr(file, 'content_type') and file.content_type:
            if file.content_type not in ALLOWED_MIME_TYPES:
                return False, f"Invalid file type: {file.content_type}", None
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size == 0:
            return False, "File is empty", None
        
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File too large: {size_mb:.1f}MB (maximum: {max_mb}MB)", None
        
        # Validate image content and get metadata
        try:
            file.seek(0)
            with Image.open(file) as img:
                # Verify it's a valid image
                img.verify()
                
                # Re-open for metadata (verify() closes the image)
                file.seek(0)
                with Image.open(file) as img2:
                    width, height = img2.size
                    format_name = img2.format
                    mode = img2.mode
                    
                    # Check dimensions if requested
                    if check_dimensions:
                        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
                            return False, f"Image too small: {width}x{height} (minimum: {MIN_IMAGE_DIMENSION}px)", None
                        
                        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                            return False, f"Image too large: {width}x{height} (maximum: {MAX_IMAGE_DIMENSION}px)", None
                    
                    metadata = {
                        'width': width,
                        'height': height,
                        'format': format_name,
                        'mode': mode,
                        'size_bytes': file_size
                    }
                    
                    file.seek(0)  # Reset for subsequent use
                    return True, "Valid image file", metadata
                    
        except Exception as e:
            file.seek(0)  # Reset on error
            return False, f"Invalid or corrupted image: {str(e)[:100]}", None
            
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return False, "Validation failed due to server error", None

def validate_upload_request(required_csrf: bool = True) -> Tuple[bool, str]:
    """
    Validate the upload request for security
    
    Args:
        required_csrf: Whether CSRF token is required
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return False, "Authentication required"
        
        # Check rate limits
        try:
            check_rate_limit(str(current_user.id), "upload")
        except RateLimitExceeded as e:
            return False, str(e)
        
        # Validate request method
        if request.method not in ['POST', 'PUT']:
            return False, "Invalid request method"
        
        # Check content type for file uploads
        if not request.content_type or not request.content_type.startswith('multipart/form-data'):
            return False, "Invalid content type for file upload"
        
        # CSRF validation (if required)
        if required_csrf:
            try:
                from flask_wtf.csrf import validate_csrf
                validate_csrf(request.form.get('csrf_token'))
            except Exception as e:
                logger.warning(f"CSRF validation failed: {e}")
                return False, "CSRF token validation failed"
        
        return True, "Request validated"
        
    except Exception as e:
        logger.error(f"Request validation error: {str(e)}")
        return False, "Request validation failed"

def sanitize_form_data(form_data: Dict) -> Dict:
    """
    Sanitize form data from upload request
    
    Args:
        form_data: Dictionary of form data
        
    Returns:
        Sanitized form data dictionary
    """
    sanitized = {}
    
    for key, value in form_data.items():
        if isinstance(value, str):
            # Sanitize string values
            sanitized_key = sanitize_input(key, 50)
            sanitized_value = sanitize_input(value, 255)
            if sanitized_key:  # Only include non-empty keys
                sanitized[sanitized_key] = sanitized_value
        else:
            # Keep non-string values as-is (like file objects)
            sanitized[key] = value
    
    return sanitized

def create_secure_upload_path(user_id: str, filename: str) -> str:
    """
    Create a secure upload path for user files
    
    Args:
        user_id: User identifier
        filename: Secure filename
        
    Returns:
        Full secure path for file storage
    """
    # Sanitize user_id
    safe_user_id = sanitize_input(str(user_id), 50)
    if not safe_user_id:
        raise UploadSecurityError("Invalid user ID")
    
    # Get base upload folder
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    if not upload_folder:
        raise UploadSecurityError("Upload folder not configured")
    
    # Create user-specific directory
    user_upload_dir = os.path.join(upload_folder, safe_user_id)
    
    # Ensure directory exists
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Create full file path
    file_path = os.path.join(user_upload_dir, filename)
    
    # Verify the path is within the upload directory (security check)
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        raise UploadSecurityError("Path traversal attempt detected")
    
    return file_path

def get_safe_error_message(error: Exception, default_message: str = "Upload failed") -> str:
    """
    Get a safe error message that doesn't expose internal information
    
    Args:
        error: Exception object
        default_message: Default message to use
        
    Returns:
        Safe error message for user
    """
    # Map of internal errors to user-friendly messages
    error_mappings = {
        'FileNotFoundError': 'File not found',
        'PermissionError': 'Permission denied',
        'OSError': 'System error occurred',
        'IOError': 'File operation failed',
        'MemoryError': 'File too large to process',
        'PIL.UnidentifiedImageError': 'Invalid image format',
        'PIL.Image.DecompressionBombError': 'Image file is too large'
    }
    
    error_type = type(error).__name__
    
    # Return mapped message or default
    return error_mappings.get(error_type, default_message)

def log_security_event(event_type: str, details: Dict, severity: str = "INFO"):
    """
    Log security-related events for monitoring
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Log severity level
    """
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'user_id': getattr(current_user, 'id', None) if current_user.is_authenticated else None,
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None,
        'details': details
    }
    
    if severity == "ERROR":
        logger.error(f"Security Event: {event_type}", extra=log_data)
    elif severity == "WARNING":
        logger.warning(f"Security Event: {event_type}", extra=log_data)
    else:
        logger.info(f"Security Event: {event_type}", extra=log_data)