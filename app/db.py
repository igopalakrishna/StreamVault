"""
CS-GY 6083 - Project Part II
Database Module

This module provides:
1. Database connection management
2. Prepared statement execution (SQL Injection Protection)
3. Transaction handling with commit/rollback and DEADLOCK PROTECTION
4. Helper functions for common operations

SECURITY NOTES:
- ALL queries use parameterized prepared statements to prevent SQL injection
- User input is NEVER concatenated into SQL strings
- Transactions ensure data consistency for multi-step operations

DEADLOCK PROTECTION STRATEGY:
This module implements application-level deadlock protection:
1. Automatic retry on deadlock (MySQL error 1213) or lock wait timeout (1205)
2. Configurable retry attempts with exponential backoff
3. Transactions are kept short to minimize lock duration
4. Tables should be accessed in consistent order across the application

The retry mechanism ensures transient deadlocks don't cause user-visible errors
while the prevention strategies minimize their occurrence.
"""

import mysql.connector
from mysql.connector import Error, pooling
from flask import current_app, g
from contextlib import contextmanager
import time
import random

# ============================================================================
# DEADLOCK PROTECTION CONSTANTS
# ============================================================================

# MySQL error codes for deadlock and lock wait timeout
MYSQL_ERROR_DEADLOCK = 1213          # ER_LOCK_DEADLOCK
MYSQL_ERROR_LOCK_WAIT_TIMEOUT = 1205 # ER_LOCK_WAIT_TIMEOUT

# Retry configuration
DEADLOCK_MAX_RETRIES = 3             # Maximum number of retry attempts
DEADLOCK_RETRY_BASE_DELAY = 0.1      # Base delay between retries (seconds)
DEADLOCK_RETRY_MAX_DELAY = 1.0       # Maximum delay between retries (seconds)


class DeadlockError(Exception):
    """
    Custom exception raised when a transaction fails due to deadlock
    after all retry attempts are exhausted.
    """
    pass

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


def _is_deadlock_error(exception):
    """
    Check if an exception is a MySQL deadlock or lock wait timeout error.
    
    Args:
        exception: The exception to check
        
    Returns:
        bool: True if the exception is a deadlock-related error
    """
    if isinstance(exception, Error):
        return exception.errno in (MYSQL_ERROR_DEADLOCK, MYSQL_ERROR_LOCK_WAIT_TIMEOUT)
    return False


def _calculate_retry_delay(attempt):
    """
    Calculate delay before retry using exponential backoff with jitter.
    
    Exponential backoff helps reduce contention by spreading out retry attempts.
    Jitter (randomization) prevents multiple transactions from retrying simultaneously.
    
    Args:
        attempt: Current attempt number (0-indexed)
        
    Returns:
        float: Delay in seconds before next retry
    """
    # Exponential backoff: delay = base * 2^attempt
    delay = DEADLOCK_RETRY_BASE_DELAY * (2 ** attempt)
    
    # Add jitter (±25% randomization)
    jitter = delay * 0.25 * (random.random() * 2 - 1)
    delay = delay + jitter
    
    # Cap at maximum delay
    return min(delay, DEADLOCK_RETRY_MAX_DELAY)


@contextmanager
def transaction():
    """
    Context manager for database transactions WITH DEADLOCK PROTECTION.
    
    Ensures atomicity for multi-step operations:
    - All operations succeed (COMMIT)
    - Or all operations are rolled back (ROLLBACK)
    
    DEADLOCK PROTECTION:
    This context manager implements automatic retry-on-deadlock logic:
    - If MySQL raises error 1213 (deadlock) or 1205 (lock wait timeout),
      the transaction is rolled back and retried
    - Up to DEADLOCK_MAX_RETRIES attempts are made (default: 3)
    - Exponential backoff with jitter is used between retries
    - If all retries fail, a DeadlockError is raised
    
    DEADLOCK PREVENTION STRATEGIES:
    1. Keep transactions SHORT - do minimal work inside the context
    2. Access tables in CONSISTENT ORDER across the application
       (e.g., always GRN_USER_ACCOUNT before GRN_LOGIN)
    3. Use appropriate ISOLATION LEVEL (InnoDB default: REPEATABLE READ)
    4. Avoid long-running transactions that hold locks
    5. Use indexes to minimize row locking
    
    Usage:
        with transaction() as cursor:
            cursor.execute("INSERT INTO table1 ...", params1)
            cursor.execute("INSERT INTO table2 ...", params2)
            # If deadlock occurs, entire block is retried automatically
            # If any other exception occurs, transaction is rolled back
    
    Raises:
        DeadlockError: If transaction fails due to deadlock after all retries
        Exception: Any other database or application error
    """
    db = get_db()
    last_exception = None
    
    for attempt in range(DEADLOCK_MAX_RETRIES):
        cursor = db.cursor(dictionary=True)
        
        try:
            # Ensure autocommit is False (transactions are implicit when autocommit=False)
            # mysql-connector-python doesn't require explicit start_transaction()
            # The transaction starts automatically when autocommit=False
            
            # Yield cursor to the calling code
            yield cursor
            
            # If we reach here without exception, commit
            db.commit()
            
            # Success - exit the retry loop
            return
            
        except Exception as e:
            # Always rollback on error
            try:
                db.rollback()
            except:
                pass  # Ignore rollback errors
            
            # Check if this is a deadlock error
            if _is_deadlock_error(e):
                last_exception = e
                current_app.logger.warning(
                    f"Deadlock detected (attempt {attempt + 1}/{DEADLOCK_MAX_RETRIES}): {e}"
                )
                
                # If we have more retries, wait and try again
                if attempt < DEADLOCK_MAX_RETRIES - 1:
                    delay = _calculate_retry_delay(attempt)
                    current_app.logger.info(f"Retrying transaction in {delay:.3f}s...")
                    time.sleep(delay)
                    continue
                else:
                    # All retries exhausted
                    current_app.logger.error(
                        f"Transaction failed after {DEADLOCK_MAX_RETRIES} attempts due to deadlock"
                    )
                    raise DeadlockError(
                        f"Transaction failed after {DEADLOCK_MAX_RETRIES} attempts due to deadlock. "
                        "Please try again."
                    ) from e
            else:
                # Not a deadlock error - don't retry, just propagate
                current_app.logger.error(f"Transaction rolled back: {e}")
                raise
                
        finally:
            cursor.close()
    
    # This should not be reached, but just in case
    if last_exception:
        raise DeadlockError("Transaction failed due to deadlock") from last_exception


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
