"""
CS-GY 6083 - Project Part II
Security Module

This module provides:
1. Password hashing with bcrypt
2. Input validation and sanitization
3. XSS protection utilities

SECURITY IMPLEMENTATION NOTES:
- Passwords are hashed using bcrypt with automatic salting
- Input validation prevents malformed data from entering the database
- XSS protection is primarily handled by Jinja2 auto-escaping
- Additional sanitization functions provided for defense in depth
"""

import bcrypt
import re
from html import escape
from functools import wraps
from flask import request, abort


# ============================================================================
# PASSWORD HASHING (bcrypt)
# ============================================================================

def hash_password(password):
    """
    Hash a password using bcrypt.
    
    SECURITY: bcrypt automatically handles:
    - Salting (random salt generated per password)
    - Cost factor (makes brute force attacks expensive)
    - Timing-safe comparison built into check function
    
    Args:
        password (str): Plain text password
    
    Returns:
        str: bcrypt hash of the password
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash (cost factor 12 is a good default)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')


def check_password(password, hashed_password):
    """
    Verify a password against its bcrypt hash.
    
    SECURITY: bcrypt.checkpw is timing-safe, preventing timing attacks.
    
    Args:
        password (str): Plain text password to verify
        hashed_password (str): bcrypt hash from database
    
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # Return False on any error (don't leak information)
        return False


# ============================================================================
# INPUT VALIDATION
# ============================================================================

def validate_email(email):
    """
    Validate email format.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if valid email format
    """
    if not email or len(email) > 100:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username):
    """
    Validate username format.
    
    Requirements:
    - 3-30 characters
    - Alphanumeric and underscores only
    
    Args:
        username (str): Username to validate
    
    Returns:
        bool: True if valid username
    """
    if not username or len(username) < 3 or len(username) > 30:
        return False
    
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))


def validate_password_strength(password):
    """
    Validate password meets minimum security requirements.
    
    Requirements:
    - At least 8 characters
    - Contains at least one letter
    - Contains at least one number
    
    Args:
        password (str): Password to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None


def validate_rating(rating):
    """
    Validate feedback rating is between 1 and 5.
    
    This mirrors the CHECK constraint in the database:
    CHECK (RATING BETWEEN 1 AND 5)
    
    Args:
        rating: Rating value to validate
    
    Returns:
        bool: True if valid rating
    """
    try:
        rating_int = int(rating)
        return 1 <= rating_int <= 5
    except (ValueError, TypeError):
        return False


def validate_positive_number(value):
    """
    Validate value is a positive number.
    
    Used for: PER_EP_CHARGE, NUM_OF_EPS, etc.
    
    Args:
        value: Value to validate
    
    Returns:
        bool: True if positive number
    """
    try:
        num = float(value)
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_date(date_str, format='%Y-%m-%d'):
    """
    Validate date string format.
    
    Args:
        date_str (str): Date string to validate
        format (str): Expected date format
    
    Returns:
        bool: True if valid date
    """
    from datetime import datetime
    try:
        datetime.strptime(date_str, format)
        return True
    except (ValueError, TypeError):
        return False


def validate_date_range(start_date, end_date):
    """
    Validate that end_date is after start_date.
    
    Mirrors database constraints:
    - CONTRACT_END_DATE > CONTRACT_ST_DATE
    - END_DATE > ALLIANCE_DATE
    
    Args:
        start_date (str): Start date string
        end_date (str): End date string
    
    Returns:
        bool: True if end_date > start_date
    """
    from datetime import datetime
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return end > start
    except (ValueError, TypeError):
        return False


def validate_varchar_length(value, max_length):
    """
    Validate string doesn't exceed maximum length.
    
    Args:
        value (str): String to validate
        max_length (int): Maximum allowed length
    
    Returns:
        bool: True if within length limit
    """
    if value is None:
        return True
    return len(str(value)) <= max_length


def validate_tech_interrupt(value):
    """
    Validate TECH_INTERRUPT is 'Yes' or 'No'.
    
    Mirrors database CHECK constraint:
    CHECK (TECH_INTERRUPT IN ('Yes', 'No'))
    
    Args:
        value (str): Value to validate
    
    Returns:
        bool: True if valid
    """
    return value in ('Yes', 'No')


# ============================================================================
# XSS PROTECTION
# ============================================================================

def sanitize_input(value):
    """
    Sanitize user input for safe display.
    
    NOTE: Jinja2's auto-escaping handles most XSS prevention automatically.
    This function provides additional defense in depth for:
    - Content stored in the database
    - Content used outside of Jinja2 templates
    
    Args:
        value: Value to sanitize
    
    Returns:
        str: Sanitized string
    """
    if value is None:
        return None
    
    # Convert to string and escape HTML entities
    return escape(str(value))


def sanitize_dict(data_dict, fields_to_sanitize):
    """
    Sanitize specific fields in a dictionary.
    
    Args:
        data_dict (dict): Dictionary with user data
        fields_to_sanitize (list): List of field names to sanitize
    
    Returns:
        dict: Dictionary with sanitized fields
    """
    sanitized = data_dict.copy()
    for field in fields_to_sanitize:
        if field in sanitized and sanitized[field]:
            sanitized[field] = sanitize_input(sanitized[field])
    return sanitized


# ============================================================================
# REQUEST VALIDATION DECORATOR
# ============================================================================

def validate_request_data(required_fields=None, validators=None):
    """
    Decorator to validate request form data before processing.
    
    Args:
        required_fields (list): List of required field names
        validators (dict): Dictionary mapping field names to validation functions
    
    Usage:
        @validate_request_data(
            required_fields=['username', 'email'],
            validators={'email': validate_email, 'rating': validate_rating}
        )
        def my_route():
            # Request data has been validated
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check required fields
            if required_fields:
                for field in required_fields:
                    if not request.form.get(field):
                        abort(400, description=f"Missing required field: {field}")
            
            # Run validators
            if validators:
                for field, validator in validators.items():
                    value = request.form.get(field)
                    if value and not validator(value):
                        abort(400, description=f"Invalid value for field: {field}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# ID GENERATION
# ============================================================================

def generate_id(prefix='', length=8):
    """
    Generate a unique ID for database records.
    
    Args:
        prefix (str): Prefix for the ID (e.g., 'ACC', 'WS')
        length (int): Length of random portion
    
    Returns:
        str: Generated ID
    """
    import uuid
    import string
    import random
    
    # Generate random alphanumeric string
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=length))
    
    if prefix:
        return f"{prefix}{random_part}"[:12]  # Limit to 12 chars (VARCHAR(12))
    return random_part[:12]
