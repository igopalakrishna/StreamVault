"""
CS-GY 6083 - Project Part II
Customer Routes Module

This module provides customer-facing features:
1. Browse web series with filters
2. View series details
3. Submit and manage feedback
4. User profile management

All routes use prepared statements to prevent SQL injection.
XSS protection is handled by Jinja2 auto-escaping.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .db import execute_query, execute_insert, execute_update, transaction
from .auth import login_required
from .security import validate_rating, generate_id, sanitize_input
from datetime import datetime

customer_bp = Blueprint('customer', __name__)


# ============================================================================
# HOME / BROWSE SERIES
# ============================================================================

@customer_bp.route('/')
@customer_bp.route('/series')
def home():
    """
    Home page - Browse all web series with filters.
    
    Displays:
    - Series name, type(s), language, country of origin
    - Average rating (from GRN_FEEDBACK)
    - Total viewers (sum from GRN_EPISODE)
    
    Filters:
    - By type (GRN_WS_WS_TYPE -> GRN_WEB_SERIES_TYPE)
    - By language
    - By country of origin
    """
    # Get filter parameters
    type_filter = request.args.get('type', '')
    language_filter = request.args.get('language', '')
    country_filter = request.args.get('country', '')
    search_query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Base query with aggregations
    # This query joins multiple tables to get comprehensive series info
    base_query = """
        SELECT 
            ws.WS_ID,
            ws.WS_NAME,
            ws.LANGUAGE,
            ws.COUNTRY_OF_ORIGIN,
            ws.RELEASE_DATE,
            ws.NUM_OF_EPS,
            ws.IMAGE_URL,
            ph.PH_NAME AS PRODUCTION_HOUSE,
            COALESCE(AVG(f.RATING), 0) AS AVG_RATING,
            COUNT(DISTINCT f.ACCOUNT_ID) AS RATING_COUNT,
            COALESCE(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS,
            GROUP_CONCAT(DISTINCT wst.WS_TYPE_NAME SEPARATOR ', ') AS TYPES
        FROM GRN_WEB_SERIES ws
        LEFT JOIN GRN_PRODUCTION_HOUSE ph ON ws.PH_ID = ph.PH_ID
        LEFT JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
        LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
        LEFT JOIN GRN_WS_WS_TYPE wswt ON ws.WS_ID = wswt.WS_ID
        LEFT JOIN GRN_WEB_SERIES_TYPE wst ON wswt.WS_TYPE_ID = wst.WS_TYPE_ID
    """
    
    # Build WHERE clause with parameterized conditions
    conditions = []
    params = []
    
    if type_filter:
        conditions.append("""
            ws.WS_ID IN (
                SELECT wswt2.WS_ID FROM GRN_WS_WS_TYPE wswt2 
                WHERE wswt2.WS_TYPE_ID = %s
            )
        """)
        params.append(type_filter)
    
    if language_filter:
        conditions.append("ws.LANGUAGE = %s")
        params.append(language_filter)
    
    if country_filter:
        conditions.append("ws.COUNTRY_OF_ORIGIN = %s")
        params.append(country_filter)
    
    if search_query:
        conditions.append("ws.WS_NAME LIKE %s")
        params.append(f"%{search_query}%")
    
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    base_query += """
        GROUP BY ws.WS_ID, ws.WS_NAME, ws.LANGUAGE, ws.COUNTRY_OF_ORIGIN,
                 ws.RELEASE_DATE, ws.NUM_OF_EPS, ws.IMAGE_URL, ph.PH_NAME
        ORDER BY AVG_RATING DESC, TOTAL_VIEWERS DESC
    """
    
    # Add pagination
    offset = (page - 1) * per_page
    paginated_query = base_query + f" LIMIT {per_page} OFFSET {offset}"
    
    # Execute query - SECURITY: Using parameterized query
    series_list = execute_query(paginated_query, tuple(params) if params else None)
    
    # Get filter options for dropdowns
    types = execute_query("SELECT WS_TYPE_ID, WS_TYPE_NAME FROM GRN_WEB_SERIES_TYPE ORDER BY WS_TYPE_NAME")
    languages = execute_query("SELECT DISTINCT LANGUAGE FROM GRN_WEB_SERIES ORDER BY LANGUAGE")
    countries = execute_query("SELECT DISTINCT COUNTRY_OF_ORIGIN FROM GRN_WEB_SERIES ORDER BY COUNTRY_OF_ORIGIN")
    
    # Count total for pagination
    count_query = """
        SELECT COUNT(DISTINCT ws.WS_ID) as total
        FROM GRN_WEB_SERIES ws
        LEFT JOIN GRN_WS_WS_TYPE wswt ON ws.WS_ID = wswt.WS_ID
    """
    if conditions:
        count_query += " WHERE " + " AND ".join(conditions)
    
    total_result = execute_query(count_query, tuple(params) if params else None, fetch_one=True)
    total = total_result['total'] if total_result else 0
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('customer/home.html',
                         series_list=series_list,
                         types=types,
                         languages=languages,
                         countries=countries,
                         current_type=type_filter,
                         current_language=language_filter,
                         current_country=country_filter,
                         search_query=search_query,
                         page=page,
                         total_pages=total_pages)


# ============================================================================
# SERIES DETAIL
# ============================================================================

@customer_bp.route('/series/<ws_id>')
def series_detail(ws_id):
    """
    Series detail page.
    
    Displays:
    - Series info (GRN_WEB_SERIES, GRN_PRODUCTION_HOUSE)
    - Episodes list (GRN_EPISODE)
    - Dubbing languages (GRN_WEB_SERIES_DUBBING -> GRN_DUBBING)
    - Subtitle languages (GRN_WS_SUB_LANG -> GRN_SUBTITLE_LANGUAGE)
    - Release per country (GRN_WS_COUNTRY -> GRN_COUNTRY)
    - Average rating, number of ratings, top reviews
    """
    # Get series info - SECURITY: Parameterized query
    series = execute_query("""
        SELECT 
            ws.*,
            ph.PH_NAME,
            ph.CITY AS PH_CITY,
            ph.COUNTRY AS PH_COUNTRY,
            ph.YEAR_ESTABLISHED
        FROM GRN_WEB_SERIES ws
        JOIN GRN_PRODUCTION_HOUSE ph ON ws.PH_ID = ph.PH_ID
        WHERE ws.WS_ID = %s
    """, (ws_id,), fetch_one=True)
    
    if not series:
        flash('Series not found.', 'danger')
        return redirect(url_for('customer.home'))
    
    # Get episodes
    episodes = execute_query("""
        SELECT EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT
        FROM GRN_EPISODE
        WHERE WS_ID = %s
        ORDER BY EP_ID
    """, (ws_id,))
    
    # Get types
    types = execute_query("""
        SELECT wst.WS_TYPE_NAME
        FROM GRN_WS_WS_TYPE wswt
        JOIN GRN_WEB_SERIES_TYPE wst ON wswt.WS_TYPE_ID = wst.WS_TYPE_ID
        WHERE wswt.WS_ID = %s
    """, (ws_id,))
    
    # Get dubbing languages
    dubbing_langs = execute_query("""
        SELECT d.LANG_NAME
        FROM GRN_WEB_SERIES_DUBBING wsd
        JOIN GRN_DUBBING d ON wsd.LANG_ID = d.LANG_ID
        WHERE wsd.WS_ID = %s
    """, (ws_id,))
    
    # Get subtitle languages
    subtitle_langs = execute_query("""
        SELECT sl.LANG_NAME
        FROM GRN_WS_SUB_LANG wssl
        JOIN GRN_SUBTITLE_LANGUAGE sl ON wssl.LANG_ID = sl.LANG_ID
        WHERE wssl.WS_ID = %s
    """, (ws_id,))
    
    # Get countries where released
    release_countries = execute_query("""
        SELECT c.COUNTRY_NAME, wsc.COUNTRY_RELEASE_DT
        FROM GRN_WS_COUNTRY wsc
        JOIN GRN_COUNTRY c ON wsc.COUNTRY_ID = c.COUNTRY_ID
        WHERE wsc.WS_ID = %s
        ORDER BY wsc.COUNTRY_RELEASE_DT
    """, (ws_id,))
    
    # Get rating stats
    rating_stats = execute_query("""
        SELECT 
            COALESCE(AVG(RATING), 0) AS AVG_RATING,
            COUNT(*) AS TOTAL_RATINGS,
            COALESCE(SUM(TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS
        FROM (
            SELECT f.RATING, NULL AS TOTAL_VIEWERS
            FROM GRN_FEEDBACK f WHERE f.WS_ID = %s
            UNION ALL
            SELECT NULL AS RATING, e.TOTAL_VIEWERS
            FROM GRN_EPISODE e WHERE e.WS_ID = %s
        ) combined
    """, (ws_id, ws_id), fetch_one=True)
    
    # Better rating stats query
    rating_info = execute_query("""
        SELECT 
            COALESCE(AVG(RATING), 0) AS AVG_RATING,
            COUNT(*) AS TOTAL_RATINGS
        FROM GRN_FEEDBACK 
        WHERE WS_ID = %s
    """, (ws_id,), fetch_one=True)
    
    viewer_info = execute_query("""
        SELECT COALESCE(SUM(TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS
        FROM GRN_EPISODE 
        WHERE WS_ID = %s
    """, (ws_id,), fetch_one=True)
    
    # Get recent feedback/reviews
    reviews = execute_query("""
        SELECT 
            f.RATING,
            f.FEEDBACK_TXT,
            f.DATE_RECORDED,
            u.FIRST_NAME,
            u.LAST_NAME
        FROM GRN_FEEDBACK f
        JOIN GRN_USER_ACCOUNT u ON f.ACCOUNT_ID = u.ACCOUNT_ID
        WHERE f.WS_ID = %s
        ORDER BY f.DATE_RECORDED DESC
        LIMIT 10
    """, (ws_id,))
    
    # Check if current user has already reviewed
    user_feedback = None
    if 'account_id' in session:
        user_feedback = execute_query("""
            SELECT RATING, FEEDBACK_TXT, DATE_RECORDED
            FROM GRN_FEEDBACK
            WHERE WS_ID = %s AND ACCOUNT_ID = %s
        """, (ws_id, session['account_id']), fetch_one=True)
    
    return render_template('customer/series_detail.html',
                         series=series,
                         episodes=episodes,
                         types=types,
                         dubbing_langs=dubbing_langs,
                         subtitle_langs=subtitle_langs,
                         release_countries=release_countries,
                         rating_info=rating_info,
                         viewer_info=viewer_info,
                         reviews=reviews,
                         user_feedback=user_feedback)


# ============================================================================
# FEEDBACK / REVIEWS
# ============================================================================

@customer_bp.route('/series/<ws_id>/feedback', methods=['POST'])
@login_required
def submit_feedback(ws_id):
    """
    Submit or update feedback for a series.
    
    Uses composite primary key (WS_ID, ACCOUNT_ID) in GRN_FEEDBACK.
    If feedback exists, updates it; otherwise creates new.
    
    SECURITY: Uses parameterized queries to prevent SQL injection.
    Rating validation enforces CHECK constraint (1-5).
    """
    rating = request.form.get('rating')
    feedback_txt = request.form.get('feedback_txt', '').strip()
    account_id = session['account_id']
    
    # Validate rating (mirrors CHECK constraint)
    if not validate_rating(rating):
        flash('Rating must be between 1 and 5.', 'danger')
        return redirect(url_for('customer.series_detail', ws_id=ws_id))
    
    rating = int(rating)
    
    # Check if feedback already exists
    existing = execute_query("""
        SELECT WS_ID FROM GRN_FEEDBACK
        WHERE WS_ID = %s AND ACCOUNT_ID = %s
    """, (ws_id, account_id), fetch_one=True)
    
    try:
        if existing:
            # Update existing feedback
            execute_update("""
                UPDATE GRN_FEEDBACK
                SET RATING = %s, FEEDBACK_TXT = %s, DATE_RECORDED = %s
                WHERE WS_ID = %s AND ACCOUNT_ID = %s
            """, (rating, feedback_txt, datetime.now(), ws_id, account_id))
            flash('Your feedback has been updated.', 'success')
        else:
            # Insert new feedback
            execute_insert("""
                INSERT INTO GRN_FEEDBACK (RATING, FEEDBACK_TXT, DATE_RECORDED, WS_ID, ACCOUNT_ID)
                VALUES (%s, %s, %s, %s, %s)
            """, (rating, feedback_txt, datetime.now(), ws_id, account_id))
            flash('Thank you for your feedback!', 'success')
    except Exception as e:
        flash('Failed to save feedback. Please try again.', 'danger')
    
    return redirect(url_for('customer.series_detail', ws_id=ws_id))


@customer_bp.route('/series/<ws_id>/feedback/delete', methods=['POST'])
@login_required
def delete_feedback(ws_id):
    """
    Delete user's own feedback for a series.
    
    Users can only delete their own feedback (enforced by WHERE clause).
    """
    account_id = session['account_id']
    
    try:
        rows_affected = execute_update("""
            DELETE FROM GRN_FEEDBACK
            WHERE WS_ID = %s AND ACCOUNT_ID = %s
        """, (ws_id, account_id))
        
        if rows_affected > 0:
            flash('Your feedback has been deleted.', 'success')
        else:
            flash('No feedback found to delete.', 'warning')
    except Exception as e:
        flash('Failed to delete feedback.', 'danger')
    
    return redirect(url_for('customer.series_detail', ws_id=ws_id))


# ============================================================================
# USER PROFILE
# ============================================================================

@customer_bp.route('/my-account')
@login_required
def my_account():
    """
    User profile page.
    Displays user information from GRN_USER_ACCOUNT.
    """
    account_id = session['account_id']
    
    # Get user details
    user = execute_query("""
        SELECT u.*, c.COUNTRY_NAME
        FROM GRN_USER_ACCOUNT u
        LEFT JOIN GRN_COUNTRY c ON u.COUNTRY_ID = c.COUNTRY_ID
        WHERE u.ACCOUNT_ID = %s
    """, (account_id,), fetch_one=True)
    
    # Get user's feedback history
    feedback_history = execute_query("""
        SELECT f.*, ws.WS_NAME
        FROM GRN_FEEDBACK f
        JOIN GRN_WEB_SERIES ws ON f.WS_ID = ws.WS_ID
        WHERE f.ACCOUNT_ID = %s
        ORDER BY f.DATE_RECORDED DESC
    """, (account_id,))
    
    # Get countries for dropdown
    countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
    
    return render_template('customer/my_account.html',
                         user=user,
                         feedback_history=feedback_history,
                         countries=countries)


@customer_bp.route('/my-account/update', methods=['POST'])
@login_required
def update_account():
    """
    Update user account information.
    
    Allows updating:
    - Address fields
    - Monthly subscription
    
    SECURITY: Uses parameterized queries.
    Only updates the logged-in user's own account.
    """
    account_id = session['account_id']
    
    street_addr = request.form.get('street_addr', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    country = request.form.get('country', '').strip()
    country_id = request.form.get('country_id', '').strip()
    monthly_subscription = request.form.get('monthly_subscription', '10')
    
    if not all([street_addr, city, state, postal_code, country, country_id]):
        flash('All address fields are required.', 'danger')
        return redirect(url_for('customer.my_account'))
    
    try:
        execute_update("""
            UPDATE GRN_USER_ACCOUNT
            SET STREET_ADDR = %s, CITY = %s, STATE = %s, POSTAL_CODE = %s,
                COUNTRY = %s, COUNTRY_ID = %s, MONTHLY_SUBSCRIPTION = %s
            WHERE ACCOUNT_ID = %s
        """, (street_addr, city, state, postal_code, country, country_id,
              float(monthly_subscription), account_id))
        
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        flash('Failed to update profile.', 'danger')
    
    return redirect(url_for('customer.my_account'))
