"""
CS-GY 6083 - Project Part II
Employee/Admin Routes Module

This module provides admin features for employees:
1. Web Series management (CRUD)
2. Episode management (CRUD)
3. Production entities management (CRUD)
4. Contract management (CRUD)

All routes are protected with @login_required and @role_required('EMPLOYEE').
All database operations use prepared statements to prevent SQL injection.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .db import execute_query, execute_insert, execute_update, transaction, invalidate_cache
from .auth import login_required, role_required
from .security import (
    validate_positive_number, validate_date, validate_date_range,
    validate_tech_interrupt, generate_id
)
from datetime import datetime

employee_bp = Blueprint('employee', __name__)


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@employee_bp.route('/')
@login_required
@role_required('EMPLOYEE')
def dashboard():
    """
    Admin dashboard home page.
    Shows overview statistics and quick links.
    """
    # Get counts for dashboard
    stats = {
        'series_count': execute_query("SELECT COUNT(*) as cnt FROM GRN_WEB_SERIES", fetch_one=True)['cnt'],
        'episode_count': execute_query("SELECT COUNT(*) as cnt FROM GRN_EPISODE", fetch_one=True)['cnt'],
        'user_count': execute_query("SELECT COUNT(*) as cnt FROM GRN_USER_ACCOUNT", fetch_one=True)['cnt'],
        'feedback_count': execute_query("SELECT COUNT(*) as cnt FROM GRN_FEEDBACK", fetch_one=True)['cnt'],
        'contract_count': execute_query("SELECT COUNT(*) as cnt FROM GRN_CONTRACT", fetch_one=True)['cnt'],
        'producer_count': execute_query("SELECT COUNT(*) as cnt FROM GRN_PRODUCER", fetch_one=True)['cnt'],
        'ph_count': execute_query("SELECT COUNT(*) as cnt FROM GRN_PRODUCTION_HOUSE", fetch_one=True)['cnt'],
    }
    
    # Recent series
    recent_series = execute_query("""
        SELECT WS_ID, WS_NAME, RELEASE_DATE 
        FROM GRN_WEB_SERIES 
        ORDER BY RELEASE_DATE DESC 
        LIMIT 5
    """)
    
    return render_template('employee/dashboard.html', stats=stats, recent_series=recent_series)


# ============================================================================
# WEB SERIES MANAGEMENT
# ============================================================================

@employee_bp.route('/series')
@login_required
@role_required('EMPLOYEE')
def list_series():
    """List all web series with edit/delete options."""
    series_list = execute_query("""
        SELECT ws.*, ph.PH_NAME
        FROM GRN_WEB_SERIES ws
        JOIN GRN_PRODUCTION_HOUSE ph ON ws.PH_ID = ph.PH_ID
        ORDER BY ws.WS_NAME
    """)
    return render_template('employee/series_list.html', series_list=series_list)


@employee_bp.route('/series/create', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def create_series():
    """Create a new web series."""
    if request.method == 'GET':
        production_houses = execute_query("SELECT PH_ID, PH_NAME FROM GRN_PRODUCTION_HOUSE ORDER BY PH_NAME")
        types = execute_query("SELECT WS_TYPE_ID, WS_TYPE_NAME FROM GRN_WEB_SERIES_TYPE ORDER BY WS_TYPE_NAME")
        countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
        dubbing_langs = execute_query("SELECT LANG_ID, LANG_NAME FROM GRN_DUBBING ORDER BY LANG_NAME")
        subtitle_langs = execute_query("SELECT LANG_ID, LANG_NAME FROM GRN_SUBTITLE_LANGUAGE ORDER BY LANG_NAME")
        return render_template('employee/series_form.html', 
                             production_houses=production_houses,
                             types=types,
                             countries=countries,
                             dubbing_langs=dubbing_langs,
                             subtitle_langs=subtitle_langs,
                             series=None)
    
    # POST - Create series
    ws_name = request.form.get('ws_name', '').strip()
    num_of_eps = request.form.get('num_of_eps', '1')
    language = request.form.get('language', '').strip()
    release_date = request.form.get('release_date', '')
    country_of_origin = request.form.get('country_of_origin', '').strip()
    ph_id = request.form.get('ph_id', '')
    
    # Get multi-select values
    selected_types = request.form.getlist('types')
    selected_countries = request.form.getlist('release_countries')
    selected_dubbing = request.form.getlist('dubbing_langs')
    selected_subtitles = request.form.getlist('subtitle_langs')
    
    # Validation
    errors = []
    if not all([ws_name, num_of_eps, language, release_date, country_of_origin, ph_id]):
        errors.append("All required fields must be filled.")
    
    if not validate_positive_number(num_of_eps):
        errors.append("Number of episodes must be positive.")
    
    if not validate_date(release_date):
        errors.append("Invalid release date format.")
    
    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('employee.create_series'))
    
    try:
        ws_id = generate_id('WS')
        
        # Use transaction for multi-table insert
        # TRANSACTION: Ensures all related records are created or none
        with transaction() as cursor:
            # Insert main series record
            cursor.execute("""
                INSERT INTO GRN_WEB_SERIES 
                (WS_ID, WS_NAME, NUM_OF_EPS, LANGUAGE, RELEASE_DATE, COUNTRY_OF_ORIGIN, PH_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (ws_id, ws_name, int(num_of_eps), language, release_date, country_of_origin, ph_id))
            
            # Insert series types
            for type_id in selected_types:
                cursor.execute("""
                    INSERT INTO GRN_WS_WS_TYPE (WS_ID, WS_TYPE_ID)
                    VALUES (%s, %s)
                """, (ws_id, type_id))
            
            # Insert country releases
            for country_id in selected_countries:
                cursor.execute("""
                    INSERT INTO GRN_WS_COUNTRY (COUNTRY_RELEASE_DT, WS_ID, COUNTRY_ID)
                    VALUES (%s, %s, %s)
                """, (release_date, ws_id, country_id))
            
            # Insert dubbing languages
            for lang_id in selected_dubbing:
                cursor.execute("""
                    INSERT INTO GRN_WEB_SERIES_DUBBING (WS_ID, LANG_ID)
                    VALUES (%s, %s)
                """, (ws_id, lang_id))
            
            # Insert subtitle languages
            for lang_id in selected_subtitles:
                cursor.execute("""
                    INSERT INTO GRN_WS_SUB_LANG (WS_ID, LANG_ID)
                    VALUES (%s, %s)
                """, (ws_id, lang_id))
        
        # Invalidate related caches
        invalidate_cache()
        
        flash(f'Web series "{ws_name}" created successfully.', 'success')
        return redirect(url_for('employee.list_series'))
        
    except Exception as e:
        flash(f'Failed to create web series: {str(e)}', 'danger')
        return redirect(url_for('employee.create_series'))


@employee_bp.route('/series/<ws_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def edit_series(ws_id):
    """Edit an existing web series."""
    if request.method == 'GET':
        series = execute_query("SELECT * FROM GRN_WEB_SERIES WHERE WS_ID = %s", (ws_id,), fetch_one=True)
        if not series:
            flash('Series not found.', 'danger')
            return redirect(url_for('employee.list_series'))
        
        production_houses = execute_query("SELECT PH_ID, PH_NAME FROM GRN_PRODUCTION_HOUSE ORDER BY PH_NAME")
        types = execute_query("SELECT WS_TYPE_ID, WS_TYPE_NAME FROM GRN_WEB_SERIES_TYPE ORDER BY WS_TYPE_NAME")
        countries = execute_query("SELECT COUNTRY_ID, COUNTRY_NAME FROM GRN_COUNTRY ORDER BY COUNTRY_NAME")
        dubbing_langs = execute_query("SELECT LANG_ID, LANG_NAME FROM GRN_DUBBING ORDER BY LANG_NAME")
        subtitle_langs = execute_query("SELECT LANG_ID, LANG_NAME FROM GRN_SUBTITLE_LANGUAGE ORDER BY LANG_NAME")
        
        # Get current selections
        current_types = [r['WS_TYPE_ID'] for r in execute_query(
            "SELECT WS_TYPE_ID FROM GRN_WS_WS_TYPE WHERE WS_ID = %s", (ws_id,))]
        current_countries = [r['COUNTRY_ID'] for r in execute_query(
            "SELECT COUNTRY_ID FROM GRN_WS_COUNTRY WHERE WS_ID = %s", (ws_id,))]
        current_dubbing = [r['LANG_ID'] for r in execute_query(
            "SELECT LANG_ID FROM GRN_WEB_SERIES_DUBBING WHERE WS_ID = %s", (ws_id,))]
        current_subtitles = [r['LANG_ID'] for r in execute_query(
            "SELECT LANG_ID FROM GRN_WS_SUB_LANG WHERE WS_ID = %s", (ws_id,))]
        
        return render_template('employee/series_form.html',
                             series=series,
                             production_houses=production_houses,
                             types=types,
                             countries=countries,
                             dubbing_langs=dubbing_langs,
                             subtitle_langs=subtitle_langs,
                             current_types=current_types,
                             current_countries=current_countries,
                             current_dubbing=current_dubbing,
                             current_subtitles=current_subtitles)
    
    # POST - Update series
    ws_name = request.form.get('ws_name', '').strip()
    num_of_eps = request.form.get('num_of_eps', '1')
    language = request.form.get('language', '').strip()
    release_date = request.form.get('release_date', '')
    country_of_origin = request.form.get('country_of_origin', '').strip()
    ph_id = request.form.get('ph_id', '')
    
    selected_types = request.form.getlist('types')
    selected_countries = request.form.getlist('release_countries')
    selected_dubbing = request.form.getlist('dubbing_langs')
    selected_subtitles = request.form.getlist('subtitle_langs')
    
    try:
        with transaction() as cursor:
            # Update main series
            cursor.execute("""
                UPDATE GRN_WEB_SERIES 
                SET WS_NAME = %s, NUM_OF_EPS = %s, LANGUAGE = %s, 
                    RELEASE_DATE = %s, COUNTRY_OF_ORIGIN = %s, PH_ID = %s
                WHERE WS_ID = %s
            """, (ws_name, int(num_of_eps), language, release_date, country_of_origin, ph_id, ws_id))
            
            # Update types (delete all, re-insert selected)
            cursor.execute("DELETE FROM GRN_WS_WS_TYPE WHERE WS_ID = %s", (ws_id,))
            for type_id in selected_types:
                cursor.execute("INSERT INTO GRN_WS_WS_TYPE (WS_ID, WS_TYPE_ID) VALUES (%s, %s)", (ws_id, type_id))
            
            # Update countries
            cursor.execute("DELETE FROM GRN_WS_COUNTRY WHERE WS_ID = %s", (ws_id,))
            for country_id in selected_countries:
                cursor.execute("""
                    INSERT INTO GRN_WS_COUNTRY (COUNTRY_RELEASE_DT, WS_ID, COUNTRY_ID) 
                    VALUES (%s, %s, %s)
                """, (release_date, ws_id, country_id))
            
            # Update dubbing
            cursor.execute("DELETE FROM GRN_WEB_SERIES_DUBBING WHERE WS_ID = %s", (ws_id,))
            for lang_id in selected_dubbing:
                cursor.execute("INSERT INTO GRN_WEB_SERIES_DUBBING (WS_ID, LANG_ID) VALUES (%s, %s)", (ws_id, lang_id))
            
            # Update subtitles
            cursor.execute("DELETE FROM GRN_WS_SUB_LANG WHERE WS_ID = %s", (ws_id,))
            for lang_id in selected_subtitles:
                cursor.execute("INSERT INTO GRN_WS_SUB_LANG (WS_ID, LANG_ID) VALUES (%s, %s)", (ws_id, lang_id))
        
        invalidate_cache()
        flash('Web series updated successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to update series: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_series'))


@employee_bp.route('/series/<ws_id>/delete', methods=['POST'])
@login_required
@role_required('EMPLOYEE')
def delete_series(ws_id):
    """
    Delete a web series.
    
    WARNING: This may fail if there are related records in child tables
    due to foreign key constraints. The UI should warn the user.
    """
    try:
        # Delete in correct order to respect FK constraints
        with transaction() as cursor:
            # Delete from junction/child tables first
            cursor.execute("DELETE FROM GRN_WS_WS_TYPE WHERE WS_ID = %s", (ws_id,))
            cursor.execute("DELETE FROM GRN_WS_COUNTRY WHERE WS_ID = %s", (ws_id,))
            cursor.execute("DELETE FROM GRN_WEB_SERIES_DUBBING WHERE WS_ID = %s", (ws_id,))
            cursor.execute("DELETE FROM GRN_WS_SUB_LANG WHERE WS_ID = %s", (ws_id,))
            cursor.execute("DELETE FROM GRN_FEEDBACK WHERE WS_ID = %s", (ws_id,))
            
            # Delete schedules for episodes
            cursor.execute("""
                DELETE s FROM GRN_SCHEDULE s
                JOIN GRN_EPISODE e ON s.EP_ID = e.EP_ID
                WHERE e.WS_ID = %s
            """, (ws_id,))
            
            cursor.execute("DELETE FROM GRN_EPISODE WHERE WS_ID = %s", (ws_id,))
            cursor.execute("DELETE FROM GRN_CONTRACT WHERE WS_ID = %s", (ws_id,))
            
            # Finally delete the series
            cursor.execute("DELETE FROM GRN_WEB_SERIES WHERE WS_ID = %s", (ws_id,))
        
        invalidate_cache()
        flash('Web series deleted successfully.', 'success')
        
    except Exception as e:
        flash(f'Cannot delete series: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_series'))


# ============================================================================
# EPISODE MANAGEMENT
# ============================================================================

@employee_bp.route('/series/<ws_id>/episodes')
@login_required
@role_required('EMPLOYEE')
def list_episodes(ws_id):
    """List all episodes for a series."""
    series = execute_query("SELECT * FROM GRN_WEB_SERIES WHERE WS_ID = %s", (ws_id,), fetch_one=True)
    if not series:
        flash('Series not found.', 'danger')
        return redirect(url_for('employee.list_series'))
    
    episodes = execute_query("""
        SELECT e.*, 
               (SELECT COUNT(*) FROM GRN_SCHEDULE WHERE EP_ID = e.EP_ID) as schedule_count
        FROM GRN_EPISODE e
        WHERE e.WS_ID = %s
        ORDER BY e.EP_ID
    """, (ws_id,))
    
    return render_template('employee/episode_list.html', series=series, episodes=episodes)


@employee_bp.route('/series/<ws_id>/episodes/create', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def create_episode(ws_id):
    """Create a new episode."""
    series = execute_query("SELECT * FROM GRN_WEB_SERIES WHERE WS_ID = %s", (ws_id,), fetch_one=True)
    if not series:
        flash('Series not found.', 'danger')
        return redirect(url_for('employee.list_series'))
    
    if request.method == 'GET':
        return render_template('employee/episode_form.html', series=series, episode=None)
    
    # POST
    ep_name = request.form.get('ep_name', '').strip()
    total_viewers = request.form.get('total_viewers', '0')
    tech_interrupt = request.form.get('tech_interrupt', 'No')
    
    # Validation
    if not ep_name:
        flash('Episode name is required.', 'danger')
        return redirect(url_for('employee.create_episode', ws_id=ws_id))
    
    if not validate_tech_interrupt(tech_interrupt):
        flash('Technical interrupt must be Yes or No.', 'danger')
        return redirect(url_for('employee.create_episode', ws_id=ws_id))
    
    try:
        ep_id = generate_id('EP')
        execute_insert("""
            INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID)
            VALUES (%s, %s, %s, %s, %s)
        """, (ep_id, ep_name, int(total_viewers), tech_interrupt, ws_id))
        
        invalidate_cache()
        flash(f'Episode "{ep_name}" created successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to create episode: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_episodes', ws_id=ws_id))


@employee_bp.route('/episodes/<ep_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def edit_episode(ep_id):
    """Edit an episode."""
    episode = execute_query("SELECT * FROM GRN_EPISODE WHERE EP_ID = %s", (ep_id,), fetch_one=True)
    if not episode:
        flash('Episode not found.', 'danger')
        return redirect(url_for('employee.list_series'))
    
    series = execute_query("SELECT * FROM GRN_WEB_SERIES WHERE WS_ID = %s", (episode['WS_ID'],), fetch_one=True)
    
    if request.method == 'GET':
        return render_template('employee/episode_form.html', series=series, episode=episode)
    
    # POST
    ep_name = request.form.get('ep_name', '').strip()
    total_viewers = request.form.get('total_viewers', '0')
    tech_interrupt = request.form.get('tech_interrupt', 'No')
    
    try:
        execute_update("""
            UPDATE GRN_EPISODE 
            SET EP_NAME = %s, TOTAL_VIEWERS = %s, TECH_INTERRUPT = %s
            WHERE EP_ID = %s
        """, (ep_name, int(total_viewers), tech_interrupt, ep_id))
        
        invalidate_cache()
        flash('Episode updated successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to update episode: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_episodes', ws_id=episode['WS_ID']))


@employee_bp.route('/episodes/<ep_id>/delete', methods=['POST'])
@login_required
@role_required('EMPLOYEE')
def delete_episode(ep_id):
    """Delete an episode."""
    episode = execute_query("SELECT WS_ID FROM GRN_EPISODE WHERE EP_ID = %s", (ep_id,), fetch_one=True)
    if not episode:
        flash('Episode not found.', 'danger')
        return redirect(url_for('employee.list_series'))
    
    ws_id = episode['WS_ID']
    
    try:
        with transaction() as cursor:
            # Delete schedules first (child records)
            cursor.execute("DELETE FROM GRN_SCHEDULE WHERE EP_ID = %s", (ep_id,))
            # Delete episode
            cursor.execute("DELETE FROM GRN_EPISODE WHERE EP_ID = %s", (ep_id,))
        
        invalidate_cache()
        flash('Episode deleted successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to delete episode: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_episodes', ws_id=ws_id))


# ============================================================================
# SCHEDULE MANAGEMENT
# ============================================================================

@employee_bp.route('/episodes/<ep_id>/schedules')
@login_required
@role_required('EMPLOYEE')
def list_schedules(ep_id):
    """List schedules for an episode."""
    episode = execute_query("""
        SELECT e.*, ws.WS_NAME
        FROM GRN_EPISODE e
        JOIN GRN_WEB_SERIES ws ON e.WS_ID = ws.WS_ID
        WHERE e.EP_ID = %s
    """, (ep_id,), fetch_one=True)
    
    if not episode:
        flash('Episode not found.', 'danger')
        return redirect(url_for('employee.list_series'))
    
    schedules = execute_query("""
        SELECT * FROM GRN_SCHEDULE WHERE EP_ID = %s ORDER BY START_DT
    """, (ep_id,))
    
    return render_template('employee/schedule_list.html', episode=episode, schedules=schedules)


@employee_bp.route('/episodes/<ep_id>/schedules/create', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def create_schedule(ep_id):
    """Create a new schedule for an episode."""
    episode = execute_query("SELECT * FROM GRN_EPISODE WHERE EP_ID = %s", (ep_id,), fetch_one=True)
    if not episode:
        flash('Episode not found.', 'danger')
        return redirect(url_for('employee.list_series'))
    
    if request.method == 'GET':
        return render_template('employee/schedule_form.html', episode=episode, schedule=None)
    
    # POST
    start_dt = request.form.get('start_dt', '')
    end_dt = request.form.get('end_dt', '')
    
    if not validate_date(start_dt) or not validate_date(end_dt):
        flash('Invalid date format.', 'danger')
        return redirect(url_for('employee.create_schedule', ep_id=ep_id))
    
    try:
        schedule_id = generate_id('SCH')
        execute_insert("""
            INSERT INTO GRN_SCHEDULE (SCHEDULE_ID, START_DT, END_DT, EP_ID)
            VALUES (%s, %s, %s, %s)
        """, (schedule_id, start_dt, end_dt, ep_id))
        
        flash('Schedule created successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to create schedule: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_schedules', ep_id=ep_id))


@employee_bp.route('/schedules/<schedule_id>/delete', methods=['POST'])
@login_required
@role_required('EMPLOYEE')
def delete_schedule(schedule_id):
    """Delete a schedule."""
    schedule = execute_query("SELECT EP_ID FROM GRN_SCHEDULE WHERE SCHEDULE_ID = %s", (schedule_id,), fetch_one=True)
    if not schedule:
        flash('Schedule not found.', 'danger')
        return redirect(url_for('employee.list_series'))
    
    ep_id = schedule['EP_ID']
    
    try:
        execute_update("DELETE FROM GRN_SCHEDULE WHERE SCHEDULE_ID = %s", (schedule_id,))
        flash('Schedule deleted successfully.', 'success')
    except Exception as e:
        flash(f'Failed to delete schedule: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_schedules', ep_id=ep_id))


# ============================================================================
# PRODUCTION HOUSE MANAGEMENT
# ============================================================================

@employee_bp.route('/production-houses')
@login_required
@role_required('EMPLOYEE')
def list_production_houses():
    """List all production houses."""
    houses = execute_query("""
        SELECT ph.*,
               (SELECT COUNT(*) FROM GRN_WEB_SERIES WHERE PH_ID = ph.PH_ID) as series_count,
               (SELECT COUNT(*) FROM GRN_PROD_PROD_HOUSE WHERE PH_ID = ph.PH_ID) as producer_count
        FROM GRN_PRODUCTION_HOUSE ph
        ORDER BY ph.PH_NAME
    """)
    return render_template('employee/production_house_list.html', houses=houses)


@employee_bp.route('/production-houses/create', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def create_production_house():
    """Create a new production house."""
    if request.method == 'GET':
        return render_template('employee/production_house_form.html', house=None)
    
    # POST
    ph_name = request.form.get('ph_name', '').strip()
    street_addr = request.form.get('street_addr', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    country = request.form.get('country', '').strip()
    year_established = request.form.get('year_established', '')
    
    if not all([ph_name, street_addr, city, state, postal_code, country, year_established]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('employee.create_production_house'))
    
    try:
        year = int(year_established)
        if year < 1800 or year > 2100:
            flash('Year established must be between 1800 and 2100.', 'danger')
            return redirect(url_for('employee.create_production_house'))
        
        ph_id = generate_id('PH')
        execute_insert("""
            INSERT INTO GRN_PRODUCTION_HOUSE 
            (PH_ID, PH_NAME, STREET_ADDR, CITY, STATE, POSTAL_CODE, COUNTRY, YEAR_ESTABLISHED)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (ph_id, ph_name, street_addr, city, state, postal_code, country, year))
        
        flash(f'Production house "{ph_name}" created successfully.', 'success')
        
    except ValueError:
        flash('Invalid year format.', 'danger')
        return redirect(url_for('employee.create_production_house'))
    except Exception as e:
        flash(f'Failed to create production house: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_production_houses'))


@employee_bp.route('/production-houses/<ph_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def edit_production_house(ph_id):
    """Edit a production house."""
    house = execute_query("SELECT * FROM GRN_PRODUCTION_HOUSE WHERE PH_ID = %s", (ph_id,), fetch_one=True)
    if not house:
        flash('Production house not found.', 'danger')
        return redirect(url_for('employee.list_production_houses'))
    
    if request.method == 'GET':
        return render_template('employee/production_house_form.html', house=house)
    
    # POST
    ph_name = request.form.get('ph_name', '').strip()
    street_addr = request.form.get('street_addr', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    country = request.form.get('country', '').strip()
    year_established = request.form.get('year_established', '')
    
    try:
        execute_update("""
            UPDATE GRN_PRODUCTION_HOUSE 
            SET PH_NAME = %s, STREET_ADDR = %s, CITY = %s, STATE = %s, 
                POSTAL_CODE = %s, COUNTRY = %s, YEAR_ESTABLISHED = %s
            WHERE PH_ID = %s
        """, (ph_name, street_addr, city, state, postal_code, country, int(year_established), ph_id))
        
        flash('Production house updated successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to update production house: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_production_houses'))


@employee_bp.route('/production-houses/<ph_id>/delete', methods=['POST'])
@login_required
@role_required('EMPLOYEE')
def delete_production_house(ph_id):
    """Delete a production house."""
    # Check if there are related series
    series_count = execute_query(
        "SELECT COUNT(*) as cnt FROM GRN_WEB_SERIES WHERE PH_ID = %s",
        (ph_id,), fetch_one=True
    )['cnt']
    
    if series_count > 0:
        flash(f'Cannot delete: {series_count} web series are associated with this production house.', 'danger')
        return redirect(url_for('employee.list_production_houses'))
    
    try:
        with transaction() as cursor:
            cursor.execute("DELETE FROM GRN_PROD_PROD_HOUSE WHERE PH_ID = %s", (ph_id,))
            cursor.execute("DELETE FROM GRN_PRODUCTION_HOUSE WHERE PH_ID = %s", (ph_id,))
        
        flash('Production house deleted successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to delete production house: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_production_houses'))


# ============================================================================
# PRODUCER MANAGEMENT
# ============================================================================

@employee_bp.route('/producers')
@login_required
@role_required('EMPLOYEE')
def list_producers():
    """List all producers."""
    producers = execute_query("""
        SELECT p.*,
               (SELECT COUNT(*) FROM GRN_PROD_PROD_HOUSE WHERE PRODUCER_ID = p.PRODUCER_ID) as house_count
        FROM GRN_PRODUCER p
        ORDER BY p.LAST_NAME, p.FIRST_NAME
    """)
    return render_template('employee/producer_list.html', producers=producers)


@employee_bp.route('/producers/create', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def create_producer():
    """Create a new producer."""
    if request.method == 'GET':
        return render_template('employee/producer_form.html', producer=None)
    
    # POST
    first_name = request.form.get('first_name', '').strip()
    middle_name = request.form.get('middle_name', '').strip() or None
    last_name = request.form.get('last_name', '').strip()
    street_addr = request.form.get('street_addr', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    country = request.form.get('country', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    email_addr = request.form.get('email_addr', '').strip()
    
    if not all([first_name, last_name, street_addr, city, state, postal_code, country, phone_number, email_addr]):
        flash('All required fields must be filled.', 'danger')
        return redirect(url_for('employee.create_producer'))
    
    try:
        producer_id = generate_id('PROD')
        execute_insert("""
            INSERT INTO GRN_PRODUCER 
            (PRODUCER_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, STREET_ADDR, 
             CITY, STATE, POSTAL_CODE, COUNTRY, PHONE_NUMBER, EMAIL_ADDR)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (producer_id, first_name, middle_name, last_name, street_addr,
              city, state, postal_code, country, phone_number, email_addr))
        
        flash(f'Producer "{first_name} {last_name}" created successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to create producer: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_producers'))


@employee_bp.route('/producers/<producer_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def edit_producer(producer_id):
    """Edit a producer."""
    producer = execute_query("SELECT * FROM GRN_PRODUCER WHERE PRODUCER_ID = %s", (producer_id,), fetch_one=True)
    if not producer:
        flash('Producer not found.', 'danger')
        return redirect(url_for('employee.list_producers'))
    
    if request.method == 'GET':
        return render_template('employee/producer_form.html', producer=producer)
    
    # POST
    first_name = request.form.get('first_name', '').strip()
    middle_name = request.form.get('middle_name', '').strip() or None
    last_name = request.form.get('last_name', '').strip()
    street_addr = request.form.get('street_addr', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    country = request.form.get('country', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    email_addr = request.form.get('email_addr', '').strip()
    
    try:
        execute_update("""
            UPDATE GRN_PRODUCER 
            SET FIRST_NAME = %s, MIDDLE_NAME = %s, LAST_NAME = %s, STREET_ADDR = %s,
                CITY = %s, STATE = %s, POSTAL_CODE = %s, COUNTRY = %s,
                PHONE_NUMBER = %s, EMAIL_ADDR = %s
            WHERE PRODUCER_ID = %s
        """, (first_name, middle_name, last_name, street_addr, city, state,
              postal_code, country, phone_number, email_addr, producer_id))
        
        flash('Producer updated successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to update producer: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_producers'))


@employee_bp.route('/producers/<producer_id>/delete', methods=['POST'])
@login_required
@role_required('EMPLOYEE')
def delete_producer(producer_id):
    """Delete a producer."""
    try:
        with transaction() as cursor:
            cursor.execute("DELETE FROM GRN_PROD_PROD_HOUSE WHERE PRODUCER_ID = %s", (producer_id,))
            cursor.execute("DELETE FROM GRN_PRODUCER WHERE PRODUCER_ID = %s", (producer_id,))
        
        flash('Producer deleted successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to delete producer: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_producers'))


# ============================================================================
# CONTRACT MANAGEMENT
# ============================================================================

@employee_bp.route('/contracts')
@login_required
@role_required('EMPLOYEE')
def list_contracts():
    """List all contracts."""
    contracts = execute_query("""
        SELECT c.*, ws.WS_NAME
        FROM GRN_CONTRACT c
        JOIN GRN_WEB_SERIES ws ON c.WS_ID = ws.WS_ID
        ORDER BY c.CONTRACT_END_DATE DESC
    """)
    return render_template('employee/contract_list.html', contracts=contracts)


@employee_bp.route('/contracts/create', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def create_contract():
    """Create a new contract."""
    if request.method == 'GET':
        series = execute_query("SELECT WS_ID, WS_NAME FROM GRN_WEB_SERIES ORDER BY WS_NAME")
        return render_template('employee/contract_form.html', contract=None, series=series)
    
    # POST
    ws_id = request.form.get('ws_id', '')
    per_ep_charge = request.form.get('per_ep_charge', '')
    contract_st_date = request.form.get('contract_st_date', '')
    contract_end_date = request.form.get('contract_end_date', '')
    
    # Validation - enforce CHECK constraints at app level too
    errors = []
    
    if not all([ws_id, per_ep_charge, contract_st_date, contract_end_date]):
        errors.append("All fields are required.")
    
    if not validate_positive_number(per_ep_charge):
        errors.append("Per episode charge must be positive (CHECK constraint: PER_EP_CHARGE > 0).")
    
    if not validate_date_range(contract_st_date, contract_end_date):
        errors.append("End date must be after start date (CHECK constraint: CONTRACT_END_DATE > CONTRACT_ST_DATE).")
    
    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('employee.create_contract'))
    
    try:
        contract_id = generate_id('CON')
        execute_insert("""
            INSERT INTO GRN_CONTRACT 
            (CONTRACT_ID, PER_EP_CHARGE, CONTRACT_ST_DATE, CONTRACT_END_DATE, WS_ID)
            VALUES (%s, %s, %s, %s, %s)
        """, (contract_id, float(per_ep_charge), contract_st_date, contract_end_date, ws_id))
        
        flash('Contract created successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to create contract: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_contracts'))


@employee_bp.route('/contracts/<contract_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def edit_contract(contract_id):
    """Edit a contract."""
    contract = execute_query("SELECT * FROM GRN_CONTRACT WHERE CONTRACT_ID = %s", (contract_id,), fetch_one=True)
    if not contract:
        flash('Contract not found.', 'danger')
        return redirect(url_for('employee.list_contracts'))
    
    if request.method == 'GET':
        series = execute_query("SELECT WS_ID, WS_NAME FROM GRN_WEB_SERIES ORDER BY WS_NAME")
        return render_template('employee/contract_form.html', contract=contract, series=series)
    
    # POST
    ws_id = request.form.get('ws_id', '')
    per_ep_charge = request.form.get('per_ep_charge', '')
    contract_st_date = request.form.get('contract_st_date', '')
    contract_end_date = request.form.get('contract_end_date', '')
    
    # Validation
    if not validate_positive_number(per_ep_charge):
        flash("Per episode charge must be positive.", 'danger')
        return redirect(url_for('employee.edit_contract', contract_id=contract_id))
    
    if not validate_date_range(contract_st_date, contract_end_date):
        flash("End date must be after start date.", 'danger')
        return redirect(url_for('employee.edit_contract', contract_id=contract_id))
    
    try:
        execute_update("""
            UPDATE GRN_CONTRACT 
            SET WS_ID = %s, PER_EP_CHARGE = %s, CONTRACT_ST_DATE = %s, CONTRACT_END_DATE = %s
            WHERE CONTRACT_ID = %s
        """, (ws_id, float(per_ep_charge), contract_st_date, contract_end_date, contract_id))
        
        flash('Contract updated successfully.', 'success')
        
    except Exception as e:
        flash(f'Failed to update contract: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_contracts'))


@employee_bp.route('/contracts/<contract_id>/delete', methods=['POST'])
@login_required
@role_required('EMPLOYEE')
def delete_contract(contract_id):
    """Delete a contract."""
    try:
        execute_update("DELETE FROM GRN_CONTRACT WHERE CONTRACT_ID = %s", (contract_id,))
        flash('Contract deleted successfully.', 'success')
    except Exception as e:
        flash(f'Failed to delete contract: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_contracts'))


# ============================================================================
# PRODUCER-PRODUCTION HOUSE ASSOCIATIONS
# ============================================================================

@employee_bp.route('/associations')
@login_required
@role_required('EMPLOYEE')
def list_associations():
    """List producer-production house associations."""
    associations = execute_query("""
        SELECT pph.*, 
               p.FIRST_NAME, p.LAST_NAME,
               ph.PH_NAME
        FROM GRN_PROD_PROD_HOUSE pph
        JOIN GRN_PRODUCER p ON pph.PRODUCER_ID = p.PRODUCER_ID
        JOIN GRN_PRODUCTION_HOUSE ph ON pph.PH_ID = ph.PH_ID
        ORDER BY pph.ALLIANCE_DATE DESC
    """)
    return render_template('employee/association_list.html', associations=associations)


@employee_bp.route('/associations/create', methods=['GET', 'POST'])
@login_required
@role_required('EMPLOYEE')
def create_association():
    """Create a new producer-production house association."""
    if request.method == 'GET':
        producers = execute_query("SELECT PRODUCER_ID, FIRST_NAME, LAST_NAME FROM GRN_PRODUCER ORDER BY LAST_NAME")
        houses = execute_query("SELECT PH_ID, PH_NAME FROM GRN_PRODUCTION_HOUSE ORDER BY PH_NAME")
        return render_template('employee/association_form.html', 
                             association=None, producers=producers, houses=houses)
    
    # POST
    producer_id = request.form.get('producer_id', '')
    ph_id = request.form.get('ph_id', '')
    alliance_date = request.form.get('alliance_date', '')
    end_date = request.form.get('end_date', '')
    
    # Validation - CHECK constraint: END_DATE > ALLIANCE_DATE
    if not validate_date_range(alliance_date, end_date):
        flash("End date must be after alliance date (CHECK constraint: END_DATE > ALLIANCE_DATE).", 'danger')
        return redirect(url_for('employee.create_association'))
    
    try:
        execute_insert("""
            INSERT INTO GRN_PROD_PROD_HOUSE 
            (ALLIANCE_DATE, END_DATE, PRODUCER_ID, PH_ID)
            VALUES (%s, %s, %s, %s)
        """, (alliance_date, end_date, producer_id, ph_id))
        
        flash('Association created successfully.', 'success')
        
    except Exception as e:
        if 'Duplicate entry' in str(e):
            flash('This association already exists.', 'danger')
        else:
            flash(f'Failed to create association: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_associations'))


@employee_bp.route('/associations/<producer_id>/<ph_id>/delete', methods=['POST'])
@login_required
@role_required('EMPLOYEE')
def delete_association(producer_id, ph_id):
    """Delete a producer-production house association."""
    try:
        execute_update("""
            DELETE FROM GRN_PROD_PROD_HOUSE 
            WHERE PRODUCER_ID = %s AND PH_ID = %s
        """, (producer_id, ph_id))
        flash('Association deleted successfully.', 'success')
    except Exception as e:
        flash(f'Failed to delete association: {str(e)}', 'danger')
    
    return redirect(url_for('employee.list_associations'))
