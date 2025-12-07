"""
CS-GY 6083 - Project Part II
Application Configuration

Contains all configuration settings for the Flask application.
In production, these should be loaded from environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Flask secret key for session management
    # SECURITY: In production, use a strong random key from environment
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3307)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'streaming_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'streaming_password'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'streaming_platform'
    MYSQL_SOCKET = os.environ.get('MYSQL_SOCKET') or '/opt/homebrew/var/mysql/mysql.sock'
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
    
    # Pagination settings
    ITEMS_PER_PAGE = 10
    
    # Cache settings for extra credit
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.environ.get('CACHE_TTL') or 300)  # 5 minutes default
    
    # =========================================================================
    # EMAIL CONFIGURATION (for password reset feature)
    # =========================================================================
    # Configure these via environment variables for your SMTP provider
    # Examples: Gmail SMTP, Mailtrap, SendGrid, University SMTP, etc.
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or None
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or None
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@streamvault.com'
    
    # Password reset token expiry (in minutes)
    PASSWORD_RESET_EXPIRY_MINUTES = int(os.environ.get('PASSWORD_RESET_EXPIRY_MINUTES') or 60)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # In production, ensure SECRET_KEY is set from environment
