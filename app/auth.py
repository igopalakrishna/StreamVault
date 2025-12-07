"""
CS-GY 6083 - Project Part II
Authentication Module

This module provides:
1. User registration
2. Login/Logout functionality
3. Role-based access control decorators
4. Session management

SECURITY FEATURES:
- bcrypt password hashing
- Session-based authentication
- Role-based access control (CUSTOMER vs EMPLOYEE)
- Transaction support for multi-table operations
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g, current_app
from functools import wraps
from .db import execute_query, transaction, execute_update, execute_insert
from .security import (
    hash_password, check_password, validate_email, validate_username,
    validate_password_strength, generate_id
)
from .email_utils import send_password_reset_email
from datetime import datetime, timedelta
import secrets

auth_bp = Blueprint('auth', __name__)


# ============================================================================
# ACCESS CONTROL DECORATORS
# ============================================================================

def login_required(f):
    """
    Decorator to require user authentication.
    Redirects to login page if user is not authenticated.
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(role):
    """
    Decorator to require specific user role.
    Must be used after @login_required.
    
    Usage:
        @app.route('/admin')
        @login_required
        @role_required('EMPLOYEE')
        def admin_only():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('customer.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """Get the currently logged-in user's information."""
    if 'user_id' not in session:
        return None
    
    query = """
        SELECT l.LOGIN_ID, l.USERNAME, l.ROLE, l.ACCOUNT_ID,
               u.FIRST_NAME, u.LAST_NAME, u.EMAIL_ADDR
        FROM GRN_LOGIN l
        JOIN GRN_USER_ACCOUNT u ON l.ACCOUNT_ID = u.ACCOUNT_ID
        WHERE l.LOGIN_ID = %s
    """
    return execute_query(query, (session['user_id'],), fetch_one=True)


# ============================================================================
# REGISTRATION
# ============================================================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Customer registration page.
    
    Creates entries in both GRN_USER_ACCOUNT and GRN_LOGIN tables
    using a transaction to ensure atomicity.
    """
    if request.method == 'GET':
        # Get countries for dropdown
        countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
        return render_template('auth/register.html', countries=countries)
    
    # POST - process registration
    # Collect form data
    first_name = request.form.get('first_name', '').strip()
    middle_name = request.form.get('middle_name', '').strip() or None
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    street_addr = request.form.get('street_addr', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    country = request.form.get('country', '').strip()
    country_id = request.form.get('country_id', '').strip()
    monthly_subscription = request.form.get('monthly_subscription', '10')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validation
    errors = []
    
    if not all([first_name, last_name, email, street_addr, city, state, 
                postal_code, country, country_id, username, password]):
        errors.append("All required fields must be filled.")
    
    if not validate_email(email):
        errors.append("Invalid email format.")
    
    if not validate_username(username):
        errors.append("Username must be 3-30 characters, alphanumeric and underscores only.")
    
    is_valid_pwd, pwd_error = validate_password_strength(password)
    if not is_valid_pwd:
        errors.append(pwd_error)
    
    if password != confirm_password:
        errors.append("Passwords do not match.")
    
    # Check if username already exists
    existing_user = execute_query(
        "SELECT LOGIN_ID FROM GRN_LOGIN WHERE USERNAME = %s",
        (username,),
        fetch_one=True
    )
    if existing_user:
        errors.append("Username already exists.")
    
    # Check if email already exists
    existing_email = execute_query(
        "SELECT ACCOUNT_ID FROM GRN_USER_ACCOUNT WHERE EMAIL_ADDR = %s",
        (email,),
        fetch_one=True
    )
    if existing_email:
        errors.append("Email address already registered.")
    
    if errors:
        countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
        for error in errors:
            flash(error, 'danger')
        return render_template('auth/register.html', countries=countries)
    
    # Create user account and login using transaction
    try:
        account_id = generate_id('ACC')
        login_id = generate_id('LOG')
        password_hash = hash_password(password)
        
        # Use transaction for atomicity
        # TRANSACTION: If either insert fails, both are rolled back
        with transaction() as cursor:
            # Insert into GRN_USER_ACCOUNT first (parent table)
            cursor.execute("""
                INSERT INTO GRN_USER_ACCOUNT 
                (ACCOUNT_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, EMAIL_ADDR,
                 STREET_ADDR, CITY, STATE, POSTAL_CODE, COUNTRY, 
                 DATE_CREATED, MONTHLY_SUBSCRIPTION, COUNTRY_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (account_id, first_name, middle_name, last_name, email,
                  street_addr, city, state, postal_code, country,
                  datetime.now(), float(monthly_subscription), country_id))
            
            # Insert into GRN_LOGIN (references GRN_USER_ACCOUNT)
            cursor.execute("""
                INSERT INTO GRN_LOGIN 
                (LOGIN_ID, ACCOUNT_ID, USERNAME, PASSWORD_HASH, ROLE, CREATED_AT)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (login_id, account_id, username, password_hash, 'CUSTOMER', datetime.now()))
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        flash(f'Registration failed. Please try again.', 'danger')
        countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
        return render_template('auth/register.html', countries=countries)


# ============================================================================
# LOGIN / LOGOUT
# ============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page.
    Verifies credentials against GRN_LOGIN table using bcrypt.
    """
    if 'user_id' in session:
        return redirect(url_for('customer.home'))
    
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # POST - process login
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        flash('Please enter both username and password.', 'danger')
        return render_template('auth/login.html')
    
    # Query user from database
    # SECURITY: Using parameterized query to prevent SQL injection
    user = execute_query("""
        SELECT l.LOGIN_ID, l.ACCOUNT_ID, l.USERNAME, l.PASSWORD_HASH, l.ROLE,
               u.FIRST_NAME, u.LAST_NAME
        FROM GRN_LOGIN l
        JOIN GRN_USER_ACCOUNT u ON l.ACCOUNT_ID = u.ACCOUNT_ID
        WHERE l.USERNAME = %s
    """, (username,), fetch_one=True)
    
    if not user:
        flash('Invalid username or password.', 'danger')
        return render_template('auth/login.html')
    
    # Verify password using bcrypt
    if not check_password(password, user['PASSWORD_HASH']):
        flash('Invalid username or password.', 'danger')
        return render_template('auth/login.html')
    
    # Set session data
    session.clear()
    session['user_id'] = user['LOGIN_ID']
    session['account_id'] = user['ACCOUNT_ID']
    session['username'] = user['USERNAME']
    session['role'] = user['ROLE']
    session['name'] = f"{user['FIRST_NAME']} {user['LAST_NAME']}"
    session.permanent = True
    
    flash(f'Welcome back, {user["FIRST_NAME"]}!', 'success')
    
    # Redirect based on role
    next_page = request.args.get('next')
    if next_page:
        return redirect(next_page)
    
    if user['ROLE'] == 'EMPLOYEE':
        return redirect(url_for('employee.dashboard'))
    return redirect(url_for('customer.home'))


@auth_bp.route('/logout')
def logout():
    """Log out the current user."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ============================================================================
# FORGOT PASSWORD / RESET PASSWORD
# ============================================================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Forgot password page.
    
    GET: Display form to enter email or username
    POST: Generate reset token, store in database, and send email
    
    SECURITY:
    - Always shows generic success message to prevent account enumeration
    - Token is cryptographically secure (secrets.token_urlsafe)
    - Token expires after configured time (default: 1 hour)
    """
    if 'user_id' in session:
        return redirect(url_for('customer.home'))
    
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')
    
    # POST - process forgot password request
    email_or_username = request.form.get('email_or_username', '').strip()
    
    if not email_or_username:
        flash('Please enter your email address or username.', 'danger')
        return render_template('auth/forgot_password.html')
    
    # Look up user by email or username
    # SECURITY: Using parameterized query to prevent SQL injection
    user = execute_query("""
        SELECT l.LOGIN_ID, l.USERNAME, u.EMAIL_ADDR, u.FIRST_NAME
        FROM GRN_LOGIN l
        JOIN GRN_USER_ACCOUNT u ON l.ACCOUNT_ID = u.ACCOUNT_ID
        WHERE l.USERNAME = %s OR u.EMAIL_ADDR = %s
    """, (email_or_username, email_or_username), fetch_one=True)
    
    if user:
        try:
            # Generate secure random token
            token = secrets.token_urlsafe(32)
            
            # Calculate expiry time
            expiry_minutes = current_app.config.get('PASSWORD_RESET_EXPIRY_MINUTES', 60)
            expires_at = datetime.now() + timedelta(minutes=expiry_minutes)
            
            # Invalidate any existing unused tokens for this user
            execute_update("""
                UPDATE GRN_PASSWORD_RESET 
                SET USED = 1 
                WHERE LOGIN_ID = %s AND USED = 0
            """, (user['LOGIN_ID'],))
            
            # Insert new reset token
            execute_insert("""
                INSERT INTO GRN_PASSWORD_RESET (LOGIN_ID, TOKEN, EXPIRES_AT, USED)
                VALUES (%s, %s, %s, 0)
            """, (user['LOGIN_ID'], token, expires_at))
            
            # Build reset URL
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Send email
            email_sent = send_password_reset_email(user['EMAIL_ADDR'], reset_url)
            
            if not email_sent:
                current_app.logger.warning(f"Failed to send reset email to {user['EMAIL_ADDR']}")
                
        except Exception as e:
            current_app.logger.error(f"Error processing password reset: {e}")
    
    # SECURITY: Always show generic success message to prevent account enumeration
    flash('If an account with that email or username exists, we have sent password reset instructions.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Reset password page.
    
    GET: Validate token and display password reset form
    POST: Validate token, update password, mark token as used
    
    SECURITY:
    - Token must exist, not be used, and not be expired
    - Password is hashed with bcrypt before storage
    - Token is marked as used immediately after successful reset
    """
    if 'user_id' in session:
        return redirect(url_for('customer.home'))
    
    # Validate token
    reset_record = execute_query("""
        SELECT pr.RESET_ID, pr.LOGIN_ID, pr.EXPIRES_AT, pr.USED,
               l.USERNAME, u.EMAIL_ADDR
        FROM GRN_PASSWORD_RESET pr
        JOIN GRN_LOGIN l ON pr.LOGIN_ID = l.LOGIN_ID
        JOIN GRN_USER_ACCOUNT u ON l.ACCOUNT_ID = u.ACCOUNT_ID
        WHERE pr.TOKEN = %s
    """, (token,), fetch_one=True)
    
    # Check if token is valid
    if not reset_record:
        flash('This password reset link is invalid.', 'danger')
        return render_template('auth/reset_password_invalid.html')
    
    if reset_record['USED'] == 1:
        flash('This password reset link has already been used.', 'danger')
        return render_template('auth/reset_password_invalid.html')
    
    if reset_record['EXPIRES_AT'] < datetime.now():
        flash('This password reset link has expired. Please request a new one.', 'danger')
        return render_template('auth/reset_password_invalid.html')
    
    if request.method == 'GET':
        return render_template('auth/reset_password.html', token=token)
    
    # POST - process password reset
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate passwords
    errors = []
    
    is_valid_pwd, pwd_error = validate_password_strength(new_password)
    if not is_valid_pwd:
        errors.append(pwd_error)
    
    if new_password != confirm_password:
        errors.append("Passwords do not match.")
    
    if errors:
        for error in errors:
            flash(error, 'danger')
        return render_template('auth/reset_password.html', token=token)
    
    try:
        # Hash new password using bcrypt
        password_hash = hash_password(new_password)
        
        # Update password and mark token as used in a transaction
        with transaction() as cursor:
            # Update password in GRN_LOGIN
            cursor.execute("""
                UPDATE GRN_LOGIN 
                SET PASSWORD_HASH = %s 
                WHERE LOGIN_ID = %s
            """, (password_hash, reset_record['LOGIN_ID']))
            
            # Mark token as used
            cursor.execute("""
                UPDATE GRN_PASSWORD_RESET 
                SET USED = 1 
                WHERE RESET_ID = %s
            """, (reset_record['RESET_ID'],))
        
        flash('Your password has been reset successfully. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        current_app.logger.error(f"Password reset error: {e}")
        flash('An error occurred while resetting your password. Please try again.', 'danger')
        return render_template('auth/reset_password.html', token=token)


# ============================================================================
# EMPLOYEE CREATION (Admin only)
# ============================================================================

@auth_bp.route('/admin/create-employee', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def create_employee():
    """
    Create a new employee account.
    Only accessible by existing employees.
    """
    if request.method == 'GET':
        countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
        return render_template('auth/create_employee.html', countries=countries)
    
    # POST - create employee
    first_name = request.form.get('first_name', '').strip()
    middle_name = request.form.get('middle_name', '').strip() or None
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    street_addr = request.form.get('street_addr', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    country = request.form.get('country', '').strip()
    country_id = request.form.get('country_id', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # Validation
    errors = []
    
    if not all([first_name, last_name, email, street_addr, city, state,
                postal_code, country, country_id, username, password]):
        errors.append("All required fields must be filled.")
    
    if not validate_email(email):
        errors.append("Invalid email format.")
    
    if not validate_username(username):
        errors.append("Username must be 3-30 characters, alphanumeric and underscores only.")
    
    is_valid_pwd, pwd_error = validate_password_strength(password)
    if not is_valid_pwd:
        errors.append(pwd_error)
    
    # Check if username exists
    existing = execute_query(
        "SELECT LOGIN_ID FROM GRN_LOGIN WHERE USERNAME = %s",
        (username,),
        fetch_one=True
    )
    if existing:
        errors.append("Username already exists.")
    
    if errors:
        countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
        for error in errors:
            flash(error, 'danger')
        return render_template('auth/create_employee.html', countries=countries)
    
    # Create employee
    try:
        account_id = generate_id('EMP')
        login_id = generate_id('LOG')
        password_hash = hash_password(password)
        
        with transaction() as cursor:
            cursor.execute("""
                INSERT INTO GRN_USER_ACCOUNT 
                (ACCOUNT_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, EMAIL_ADDR,
                 STREET_ADDR, CITY, STATE, POSTAL_CODE, COUNTRY,
                 DATE_CREATED, MONTHLY_SUBSCRIPTION, COUNTRY_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (account_id, first_name, middle_name, last_name, email,
                  street_addr, city, state, postal_code, country,
                  datetime.now(), 0, country_id))
            
            cursor.execute("""
                INSERT INTO GRN_LOGIN 
                (LOGIN_ID, ACCOUNT_ID, USERNAME, PASSWORD_HASH, ROLE, CREATED_AT)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (login_id, account_id, username, password_hash, 'EMPLOYEE', datetime.now()))
        
        flash(f'Employee account created for {username}.', 'success')
        return redirect(url_for('employee.dashboard'))
        
    except Exception as e:
        flash('Failed to create employee account.', 'danger')
        countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
        return render_template('auth/create_employee.html', countries=countries)


# ============================================================================
# CONTEXT PROCESSOR
# ============================================================================

@auth_bp.app_context_processor
def inject_user():
    """Make current user available in all templates."""
    return {
        'current_user': get_current_user() if 'user_id' in session else None,
        'is_authenticated': 'user_id' in session,
        'is_employee': session.get('role') == 'EMPLOYEE'
    }
