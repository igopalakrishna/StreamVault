"""
CS-GY 6083 - Project Part II
Analytics Routes Module (EXTRA CREDIT)

This module provides data visualization dashboards:
1. Top-N series by total viewers
2. Top-N series by average rating
3. Distribution of series by country
4. Additional business analytics

Uses Chart.js for client-side visualization.
Implements optional caching for read-heavy queries.
"""

from flask import Blueprint, render_template, jsonify, request
from .db import execute_query, execute_cached_query, get_cache_stats
from .auth import login_required, role_required

analytics_bp = Blueprint('analytics', __name__)


# ============================================================================
# ANALYTICS DASHBOARD
# ============================================================================

@analytics_bp.route('/')
@login_required
@role_required('EMPLOYEE')
def dashboard():
    """
    Main analytics dashboard page.
    Displays multiple visualizations using Chart.js.
    """
    return render_template('analytics/dashboard.html')


# ============================================================================
# API ENDPOINTS FOR CHART DATA
# ============================================================================

@analytics_bp.route('/api/top-series-viewers')
@login_required
@role_required('EMPLOYEE')
def top_series_by_viewers():
    """
    API endpoint: Top N series by total viewers.
    
    EXTRA CREDIT: Uses caching for performance optimization.
    
    Query joins GRN_WEB_SERIES with GRN_EPISODE to aggregate viewer counts.
    """
    n = request.args.get('n', 10, type=int)
    
    # Query with aggregation - SECURITY: Parameterized
    query = """
        SELECT 
            ws.WS_ID,
            ws.WS_NAME,
            COALESCE(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS
        FROM GRN_WEB_SERIES ws
        LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
        GROUP BY ws.WS_ID, ws.WS_NAME
        ORDER BY TOTAL_VIEWERS DESC
        LIMIT %s
    """
    
    # Use cached query for better performance
    results = execute_cached_query(
        query, 
        (n,), 
        cache_key=f'top_viewers_{n}',
        ttl=300  # 5 minutes cache
    )
    
    return jsonify({
        'labels': [r['WS_NAME'] for r in results],
        'data': [int(r['TOTAL_VIEWERS']) for r in results]
    })


@analytics_bp.route('/api/top-series-rating')
@login_required
@role_required('EMPLOYEE')
def top_series_by_rating():
    """
    API endpoint: Top N series by average rating.
    
    Query joins GRN_WEB_SERIES with GRN_FEEDBACK to compute average ratings.
    Only includes series with at least one rating.
    """
    n = request.args.get('n', 10, type=int)
    
    query = """
        SELECT 
            ws.WS_ID,
            ws.WS_NAME,
            AVG(f.RATING) AS AVG_RATING,
            COUNT(f.ACCOUNT_ID) AS RATING_COUNT
        FROM GRN_WEB_SERIES ws
        JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
        GROUP BY ws.WS_ID, ws.WS_NAME
        HAVING COUNT(f.ACCOUNT_ID) >= 1
        ORDER BY AVG_RATING DESC, RATING_COUNT DESC
        LIMIT %s
    """
    
    results = execute_cached_query(
        query,
        (n,),
        cache_key=f'top_rating_{n}',
        ttl=300
    )
    
    return jsonify({
        'labels': [r['WS_NAME'] for r in results],
        'data': [float(r['AVG_RATING']) for r in results],
        'counts': [int(r['RATING_COUNT']) for r in results]
    })


@analytics_bp.route('/api/series-by-country')
@login_required
@role_required('EMPLOYEE')
def series_by_country():
    """
    API endpoint: Distribution of series by country.
    
    Query joins GRN_WS_COUNTRY with GRN_COUNTRY to show how many
    series are available in each country.
    """
    query = """
        SELECT 
            c.COUNTRY_NAME,
            COUNT(DISTINCT wsc.WS_ID) AS SERIES_COUNT
        FROM GRN_COUNTRY c
        LEFT JOIN GRN_WS_COUNTRY wsc ON c.COUNTRY_ID = wsc.COUNTRY_ID
        GROUP BY c.COUNTRY_ID, c.COUNTRY_NAME
        HAVING SERIES_COUNT > 0
        ORDER BY SERIES_COUNT DESC
    """
    
    results = execute_cached_query(
        query,
        cache_key='series_by_country',
        ttl=300
    )
    
    return jsonify({
        'labels': [r['COUNTRY_NAME'] for r in results],
        'data': [int(r['SERIES_COUNT']) for r in results]
    })


@analytics_bp.route('/api/series-by-type')
@login_required
@role_required('EMPLOYEE')
def series_by_type():
    """
    API endpoint: Distribution of series by type/genre.
    
    Query joins GRN_WS_WS_TYPE with GRN_WEB_SERIES_TYPE.
    """
    query = """
        SELECT 
            wst.WS_TYPE_NAME,
            COUNT(DISTINCT wswt.WS_ID) AS SERIES_COUNT
        FROM GRN_WEB_SERIES_TYPE wst
        LEFT JOIN GRN_WS_WS_TYPE wswt ON wst.WS_TYPE_ID = wswt.WS_TYPE_ID
        GROUP BY wst.WS_TYPE_ID, wst.WS_TYPE_NAME
        HAVING SERIES_COUNT > 0
        ORDER BY SERIES_COUNT DESC
    """
    
    results = execute_cached_query(
        query,
        cache_key='series_by_type',
        ttl=300
    )
    
    return jsonify({
        'labels': [r['WS_TYPE_NAME'] for r in results],
        'data': [int(r['SERIES_COUNT']) for r in results]
    })


@analytics_bp.route('/api/monthly-feedback')
@login_required
@role_required('EMPLOYEE')
def monthly_feedback():
    """
    API endpoint: Feedback submissions by month.
    
    Shows trend of user engagement over time.
    """
    query = """
        SELECT 
            DATE_FORMAT(DATE_RECORDED, '%Y-%m') AS MONTH,
            COUNT(*) AS FEEDBACK_COUNT,
            AVG(RATING) AS AVG_RATING
        FROM GRN_FEEDBACK
        GROUP BY DATE_FORMAT(DATE_RECORDED, '%Y-%m')
        ORDER BY MONTH DESC
        LIMIT 12
    """
    
    results = execute_cached_query(
        query,
        cache_key='monthly_feedback',
        ttl=300
    )
    
    # Reverse to show chronological order
    results = list(reversed(results))
    
    return jsonify({
        'labels': [r['MONTH'] for r in results],
        'feedback_counts': [int(r['FEEDBACK_COUNT']) for r in results],
        'avg_ratings': [float(r['AVG_RATING']) if r['AVG_RATING'] else 0 for r in results]
    })


@analytics_bp.route('/api/production-house-stats')
@login_required
@role_required('EMPLOYEE')
def production_house_stats():
    """
    API endpoint: Production house statistics.
    
    Shows number of series and total viewers per production house.
    """
    query = """
        SELECT 
            ph.PH_NAME,
            COUNT(DISTINCT ws.WS_ID) AS SERIES_COUNT,
            COALESCE(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS
        FROM GRN_PRODUCTION_HOUSE ph
        LEFT JOIN GRN_WEB_SERIES ws ON ph.PH_ID = ws.PH_ID
        LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
        GROUP BY ph.PH_ID, ph.PH_NAME
        ORDER BY SERIES_COUNT DESC
        LIMIT 10
    """
    
    results = execute_cached_query(
        query,
        cache_key='ph_stats',
        ttl=300
    )
    
    return jsonify({
        'labels': [r['PH_NAME'] for r in results],
        'series_counts': [int(r['SERIES_COUNT']) for r in results],
        'viewer_counts': [int(r['TOTAL_VIEWERS']) for r in results]
    })


@analytics_bp.route('/api/rating-distribution')
@login_required
@role_required('EMPLOYEE')
def rating_distribution():
    """
    API endpoint: Distribution of ratings (1-5 stars).
    """
    query = """
        SELECT 
            RATING,
            COUNT(*) AS COUNT
        FROM GRN_FEEDBACK
        GROUP BY RATING
        ORDER BY RATING
    """
    
    results = execute_cached_query(
        query,
        cache_key='rating_distribution',
        ttl=300
    )
    
    # Ensure all ratings 1-5 are represented
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in results:
        distribution[r['RATING']] = r['COUNT']
    
    return jsonify({
        'labels': ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
        'data': [distribution[i] for i in range(1, 6)]
    })


@analytics_bp.route('/api/top-countries-viewers')
@login_required
@role_required('EMPLOYEE')
def top_countries_by_viewers():
    """
    API endpoint: Countries with highest total viewers.
    
    This is a more complex query that aggregates viewers by country.
    """
    query = """
        SELECT 
            c.COUNTRY_NAME,
            COALESCE(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS
        FROM GRN_COUNTRY c
        JOIN GRN_WS_COUNTRY wsc ON c.COUNTRY_ID = wsc.COUNTRY_ID
        JOIN GRN_WEB_SERIES ws ON wsc.WS_ID = ws.WS_ID
        JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
        GROUP BY c.COUNTRY_ID, c.COUNTRY_NAME
        ORDER BY TOTAL_VIEWERS DESC
        LIMIT 10
    """
    
    results = execute_cached_query(
        query,
        cache_key='top_countries_viewers',
        ttl=300
    )
    
    return jsonify({
        'labels': [r['COUNTRY_NAME'] for r in results],
        'data': [int(r['TOTAL_VIEWERS']) for r in results]
    })


# ============================================================================
# CACHE MANAGEMENT (EXTRA CREDIT)
# ============================================================================

@analytics_bp.route('/cache-stats')
@login_required
@role_required('EMPLOYEE')
def cache_statistics():
    """
    Display cache statistics.
    
    EXTRA CREDIT: Shows cache utilization for performance monitoring.
    """
    stats = get_cache_stats()
    return jsonify(stats)


# ============================================================================
# DETAILED REPORTS
# ============================================================================

@analytics_bp.route('/report/series-performance')
@login_required
@role_required('EMPLOYEE')
def series_performance_report():
    """
    Detailed series performance report.
    
    Shows comprehensive metrics for all series.
    """
    query = """
        SELECT 
            ws.WS_ID,
            ws.WS_NAME,
            ws.LANGUAGE,
            ws.COUNTRY_OF_ORIGIN,
            ws.RELEASE_DATE,
            ws.NUM_OF_EPS,
            ph.PH_NAME AS PRODUCTION_HOUSE,
            COALESCE(AVG(f.RATING), 0) AS AVG_RATING,
            COUNT(DISTINCT f.ACCOUNT_ID) AS RATING_COUNT,
            COALESCE(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS,
            COUNT(DISTINCT e.EP_ID) AS ACTUAL_EPISODES
        FROM GRN_WEB_SERIES ws
        LEFT JOIN GRN_PRODUCTION_HOUSE ph ON ws.PH_ID = ph.PH_ID
        LEFT JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
        LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
        GROUP BY ws.WS_ID, ws.WS_NAME, ws.LANGUAGE, ws.COUNTRY_OF_ORIGIN,
                 ws.RELEASE_DATE, ws.NUM_OF_EPS, ph.PH_NAME
        ORDER BY TOTAL_VIEWERS DESC
    """
    
    results = execute_query(query)
    
    return render_template('analytics/series_report.html', series_list=results)


@analytics_bp.route('/report/user-engagement')
@login_required
@role_required('EMPLOYEE')
def user_engagement_report():
    """
    User engagement report.
    
    Shows users who have provided feedback and their activity.
    """
    query = """
        SELECT 
            u.ACCOUNT_ID,
            u.FIRST_NAME,
            u.LAST_NAME,
            u.DATE_CREATED,
            c.COUNTRY_NAME,
            COUNT(f.WS_ID) AS FEEDBACK_COUNT,
            AVG(f.RATING) AS AVG_RATING_GIVEN,
            MAX(f.DATE_RECORDED) AS LAST_FEEDBACK_DATE
        FROM GRN_USER_ACCOUNT u
        LEFT JOIN GRN_COUNTRY c ON u.COUNTRY_ID = c.COUNTRY_ID
        LEFT JOIN GRN_FEEDBACK f ON u.ACCOUNT_ID = f.ACCOUNT_ID
        GROUP BY u.ACCOUNT_ID, u.FIRST_NAME, u.LAST_NAME, u.DATE_CREATED, c.COUNTRY_NAME
        HAVING COUNT(f.WS_ID) > 0
        ORDER BY FEEDBACK_COUNT DESC
    """
    
    results = execute_query(query)
    
    return render_template('analytics/user_report.html', users=results)
