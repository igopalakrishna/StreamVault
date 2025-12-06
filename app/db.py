"""
CS-GY 6083 - Project Part II
Database Module

This module provides:
1. Database connection management
2. Prepared statement execution (SQL Injection Protection)
3. Transaction handling with commit/rollback
4. Helper functions for common operations

SECURITY NOTES:
- ALL queries use parameterized prepared statements to prevent SQL injection
- User input is NEVER concatenated into SQL strings
- Transactions ensure data consistency for multi-step operations
"""

import mysql.connector
from mysql.connector import Error, pooling
from flask import current_app, g
from contextlib import contextmanager
import time

# Simple in-memory cache for extra credit
_query_cache = {}
_cache_timestamps = {}


def get_db_config():
    """Get database configuration from Flask app config."""
    config = {
        'host': current_app.config['MYSQL_HOST'],
        'port': current_app.config['MYSQL_PORT'],
        'user': current_app.config['MYSQL_USER'],
        'password': current_app.config['MYSQL_PASSWORD'],
        'database': current_app.config['MYSQL_DATABASE'],
        'autocommit': False,  # We want explicit transaction control
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    # Use Unix socket for Homebrew MySQL on macOS
    socket_path = current_app.config.get('MYSQL_SOCKET')
    if socket_path:
        config['unix_socket'] = socket_path
    return config


def get_db():
    """
    Get database connection for current request.
    Uses Flask's g object to store connection per request.
    """
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(**get_db_config())
        except Error as e:
            current_app.logger.error(f"Database connection error: {e}")
            raise
    return g.db


def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Useful for operations outside of Flask request context.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
    """
    conn = None
    try:
        from flask import current_app
        conn = mysql.connector.connect(**get_db_config())
        yield conn
    finally:
        if conn is not None:
            conn.close()


def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """
    Execute a SELECT query using prepared statements.
    
    SECURITY: This function uses parameterized queries to prevent SQL injection.
    The 'params' tuple is passed separately to cursor.execute(), ensuring
    user input is never concatenated into the SQL string.
    
    Args:
        query (str): SQL query with %s placeholders for parameters
        params (tuple): Parameters to substitute into query (prevents SQL injection)
        fetch_one (bool): If True, return single row
        fetch_all (bool): If True, return all rows (default)
    
    Returns:
        dict or list: Query results
    
    Example:
        # SAFE - uses parameterized query
        results = execute_query(
            "SELECT * FROM GRN_USER_ACCOUNT WHERE ACCOUNT_ID = %s",
            (user_id,)
        )
        
        # UNSAFE - NEVER do this (SQL injection vulnerability)
        # results = execute_query(f"SELECT * FROM users WHERE id = {user_id}")
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Execute with parameters (SQL injection safe)
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
            
        return result
        
    except Error as e:
        current_app.logger.error(f"Query execution error: {e}")
        current_app.logger.error(f"Query: {query}")
        current_app.logger.error(f"Params: {params}")
        raise
    finally:
        cursor.close()


def execute_insert(query, params=None):
    """
    Execute an INSERT query and return the last inserted ID.
    
    SECURITY: Uses parameterized queries to prevent SQL injection.
    
    Args:
        query (str): INSERT query with %s placeholders
        params (tuple): Parameters for the query
    
    Returns:
        int: Last inserted row ID
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(query, params or ())
        db.commit()
        return cursor.lastrowid
        
    except Error as e:
        db.rollback()
        current_app.logger.error(f"Insert error: {e}")
        raise
    finally:
        cursor.close()


def execute_update(query, params=None):
    """
    Execute an UPDATE or DELETE query.
    
    SECURITY: Uses parameterized queries to prevent SQL injection.
    
    Args:
        query (str): UPDATE/DELETE query with %s placeholders
        params (tuple): Parameters for the query
    
    Returns:
        int: Number of affected rows
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute(query, params or ())
        db.commit()
        return cursor.rowcount
        
    except Error as e:
        db.rollback()
        current_app.logger.error(f"Update/Delete error: {e}")
        raise
    finally:
        cursor.close()


@contextmanager
def transaction():
    """
    Context manager for database transactions.
    
    Ensures atomicity for multi-step operations:
    - All operations succeed (COMMIT)
    - Or all operations are rolled back (ROLLBACK)
    
    DEADLOCK PREVENTION STRATEGY:
    1. Keep transactions short - do minimal work inside transaction
    2. Access tables in consistent order across the application
    3. Use appropriate isolation level
    
    Usage:
        with transaction() as cursor:
            cursor.execute("INSERT INTO table1 ...", params1)
            cursor.execute("INSERT INTO table2 ...", params2)
            # If any exception occurs, both inserts are rolled back
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Start transaction explicitly
        db.start_transaction()
        yield cursor
        # If we reach here without exception, commit
        db.commit()
        
    except Exception as e:
        # On any error, rollback the transaction
        db.rollback()
        current_app.logger.error(f"Transaction rolled back: {e}")
        raise
        
    finally:
        cursor.close()


def execute_many(query, params_list):
    """
    Execute a query multiple times with different parameters.
    Useful for bulk inserts.
    
    Args:
        query (str): SQL query with %s placeholders
        params_list (list): List of parameter tuples
    
    Returns:
        int: Total number of affected rows
    """
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.executemany(query, params_list)
        db.commit()
        return cursor.rowcount
        
    except Error as e:
        db.rollback()
        current_app.logger.error(f"Bulk operation error: {e}")
        raise
    finally:
        cursor.close()


# ============================================================================
# EXTRA CREDIT: Simple Query Caching
# ============================================================================

def execute_cached_query(query, params=None, cache_key=None, ttl=None):
    """
    Execute a query with optional caching for read-heavy analytics queries.
    
    EXTRA CREDIT: Implements simple in-memory caching to reduce database load
    for frequently accessed read-only data like analytics dashboards.
    
    Args:
        query (str): SQL query
        params (tuple): Query parameters
        cache_key (str): Unique key for caching (required for caching)
        ttl (int): Time-to-live in seconds (uses config default if not specified)
    
    Returns:
        Query results (from cache if available and fresh)
    """
    if not current_app.config.get('CACHE_ENABLED', False) or not cache_key:
        return execute_query(query, params)
    
    ttl = ttl or current_app.config.get('CACHE_TTL', 300)
    current_time = time.time()
    
    # Check if cached result exists and is fresh
    if cache_key in _query_cache:
        cache_time = _cache_timestamps.get(cache_key, 0)
        if current_time - cache_time < ttl:
            current_app.logger.debug(f"Cache hit for: {cache_key}")
            return _query_cache[cache_key]
    
    # Execute query and cache result
    result = execute_query(query, params)
    _query_cache[cache_key] = result
    _cache_timestamps[cache_key] = current_time
    current_app.logger.debug(f"Cache miss - stored: {cache_key}")
    
    return result


def invalidate_cache(cache_key=None):
    """
    Invalidate cached query results.
    
    Args:
        cache_key (str): Specific key to invalidate, or None to clear all cache
    """
    global _query_cache, _cache_timestamps
    
    if cache_key:
        _query_cache.pop(cache_key, None)
        _cache_timestamps.pop(cache_key, None)
    else:
        _query_cache = {}
        _cache_timestamps = {}


def get_cache_stats():
    """Get cache statistics for monitoring."""
    return {
        'entries': len(_query_cache),
        'keys': list(_query_cache.keys())
    }
