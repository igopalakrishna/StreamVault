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

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g
from functools import wraps
from .db import execute_query, transaction, execute_update
from .security import (
    hash_password, check_password, validate_email, validate_username,
    validate_password_strength, generate_id
)
from datetime import datetime

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
