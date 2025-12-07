"""
CS-GY 6083 - Project Part II
Email Utilities Module

This module provides email sending functionality for:
1. Password reset emails
2. (Future) Account verification, notifications, etc.

CONFIGURATION:
Configure SMTP settings via environment variables:
- MAIL_SERVER: SMTP server hostname (default: localhost)
- MAIL_PORT: SMTP port (default: 587 for TLS)
- MAIL_USERNAME: SMTP authentication username
- MAIL_PASSWORD: SMTP authentication password
- MAIL_USE_TLS: Enable TLS (default: true)
- MAIL_USE_SSL: Enable SSL (default: false)
- MAIL_DEFAULT_SENDER: Default 'From' address

USAGE:
    from app.email_utils import send_password_reset_email
    send_password_reset_email('user@example.com', 'https://app.com/reset/TOKEN')
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def get_smtp_connection():
    """
    Create and return an SMTP connection using app configuration.
    
    Returns:
        smtplib.SMTP or smtplib.SMTP_SSL: Connected SMTP object
        
    Raises:
        Exception: If connection fails
    """
    server = current_app.config.get('MAIL_SERVER', 'localhost')
    port = current_app.config.get('MAIL_PORT', 587)
    use_tls = current_app.config.get('MAIL_USE_TLS', True)
    use_ssl = current_app.config.get('MAIL_USE_SSL', False)
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')
    
    try:
        # Use SSL connection if configured
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port)
        else:
            smtp = smtplib.SMTP(server, port)
            
            # Start TLS if configured (and not using SSL)
            if use_tls:
                smtp.starttls()
        
        # Authenticate if credentials provided
        if username and password:
            smtp.login(username, password)
            
        return smtp
        
    except Exception as e:
        current_app.logger.error(f"SMTP connection error: {e}")
        raise


def send_email(to_email, subject, text_body, html_body=None):
    """
    Send an email using configured SMTP settings.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject line
        text_body (str): Plain text email body
        html_body (str, optional): HTML email body
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@streamvault.com')
    
    try:
        # Create message
        if html_body:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
        else:
            msg = MIMEText(text_body, 'plain')
        
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to_email
        
        # Send email
        with get_smtp_connection() as smtp:
            smtp.sendmail(sender, [to_email], msg.as_string())
        
        current_app.logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_password_reset_email(to_email, reset_link):
    """
    Send a password reset email to the user.
    
    Args:
        to_email (str): User's email address
        reset_link (str): Full URL to the password reset page with token
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "StreamVault - Password Reset Instructions"
    
    # Plain text version
    text_body = f"""
Hello,

We received a request to reset your password for your StreamVault account.

To reset your password, please click the link below (or copy and paste it into your browser):

{reset_link}

This link will expire in 1 hour for security reasons.

If you did not request a password reset, please ignore this email. Your password will remain unchanged.

For security, do not share this link with anyone.

Best regards,
The StreamVault Team

---
This is an automated message. Please do not reply to this email.
"""
    
    # HTML version (optional, for nicer formatting)
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a1a1a; color: #fff; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; color: #e63946; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; }}
        .button {{ display: inline-block; background: #e63946; color: #fff; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .button:hover {{ background: #dc2626; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 StreamVault</h1>
        </div>
        <div class="content">
            <h2>Password Reset Request</h2>
            <p>Hello,</p>
            <p>We received a request to reset your password for your StreamVault account.</p>
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Reset My Password</a>
            </p>
            <p style="font-size: 12px; color: #666;">
                Or copy and paste this link into your browser:<br>
                <code style="word-break: break-all;">{reset_link}</code>
            </p>
            <div class="warning">
                <strong>⚠️ Security Notice:</strong><br>
                This link will expire in 1 hour. If you did not request this reset, please ignore this email.
            </div>
        </div>
        <div class="footer">
            <p>This is an automated message from StreamVault. Please do not reply.</p>
            <p>&copy; 2025 StreamVault - CS-GY 6083 Project</p>
        </div>
    </div>
</body>
</html>
"""
    
    return send_email(to_email, subject, text_body, html_body)

