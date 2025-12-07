# StreamVault - Web Series Streaming Platform

**CS-GY 6083 - Principles of Database Systems**  
**NYU Tandon School of Engineering - Fall 2025**  
**Project Part II**

## Team Members
- Gopala Krishna Abba (ga2664)
- Riya Patil (rsp9219)
- Neha Nainan (nan6504)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Setup Instructions](#setup-instructions)
5. [Features & Requirements Mapping](#features--requirements-mapping)
6. [Security Implementation](#security-implementation)
7. [Extra Credit Features](#extra-credit-features)
8. [Demo Accounts](#demo-accounts)
9. [Business Queries (Q1-Q6)](#business-queries)

---

## Project Overview

StreamVault is a web-based streaming platform management system built for the CS-GY 6083 Project Part II. It extends the database schema from Part I (GRN_* tables) with authentication capabilities and provides a full CRUD interface for managing web series, episodes, production houses, contracts, and user feedback.

### Key Features
- **User Authentication**: Registration, login, logout with bcrypt password hashing
- **Role-Based Access Control**: Customer and Employee roles with different permissions
- **Customer Features**: Browse series, view details, submit/edit feedback, manage profile
- **Employee Features**: Full CRUD on all entities (series, episodes, producers, contracts)
- **Analytics Dashboard**: Chart.js visualizations with query caching
- **Dark Theme UI**: Cinematic dark theme with optimized text visibility

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.13, Flask 3.0 |
| Database | MySQL 9.5 (Homebrew) |
| DB Connector | mysql-connector-python 8.2.0 |
| Template Engine | Jinja2 |
| Password Hashing | bcrypt 4.1.2 |
| Frontend | HTML5, CSS3, Bootstrap 5.3 |
| Charts | Chart.js 4.x (via CDN) |
| Icons | Bootstrap Icons |

---

## Project Structure

```
project_part2/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── config.py            # Configuration settings
│   ├── db.py                # Database connection & helpers (SQL injection prevention)
│   ├── security.py          # Password hashing, input validation, XSS protection
│   ├── auth.py              # Authentication routes & decorators
│   ├── routes_customer.py   # Customer-facing routes
│   ├── routes_employee.py   # Admin/employee routes (CRUD)
│   ├── routes_analytics.py  # Analytics dashboard (extra credit)
│   ├── email_utils.py       # Email sending for password reset
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── customer/
│   │   ├── employee/
│   │   ├── analytics/
│   │   └── errors/
│   └── static/
│       └── css/style.css    # Dark theme with full text visibility
├── run.py                   # Application entry point (port 5001)
├── schema_mysql.sql         # MySQL DDL (all tables + indexes)
├── seed_data.sql            # Sample data for demo
├── business_queries.sql     # Q1-Q6 advanced SQL queries
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── report_outline.md        # Report template
```

---

## Setup Instructions

### Prerequisites
- Python 3.8+ (tested with Python 3.13)
- MySQL 8.0+ or Homebrew MySQL on macOS
- macOS, Linux, or Windows

---

### Option A: Setup on macOS with Homebrew (Recommended)

#### 1. Install MySQL via Homebrew

```bash
brew install mysql
```

#### 2. Configure MySQL for Port 3307 (to avoid conflicts)

Create/edit `/opt/homebrew/etc/my.cnf`:

```ini
[mysqld]
port=3307
socket=/opt/homebrew/var/mysql/mysql.sock

[client]
port=3307
socket=/opt/homebrew/var/mysql/mysql.sock
```

#### 3. Start MySQL Service

```bash
brew services start mysql
```

#### 4. Create Database and User

```bash
# Connect to MySQL (no password for fresh install)
/opt/homebrew/bin/mysql -u root --socket=/opt/homebrew/var/mysql/mysql.sock

# In MySQL shell, run:
CREATE DATABASE IF NOT EXISTS streaming_platform;
CREATE USER IF NOT EXISTS 'streaming_user'@'localhost' IDENTIFIED BY 'streaming_password';
GRANT ALL PRIVILEGES ON streaming_platform.* TO 'streaming_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 5. Load Schema and Seed Data

```bash
cd ~/project_part2

# Load schema
/opt/homebrew/bin/mysql -u streaming_user -pstreaming_password \
  --socket=/opt/homebrew/var/mysql/mysql.sock \
  streaming_platform < schema_mysql.sql

# Load sample data
/opt/homebrew/bin/mysql -u streaming_user -pstreaming_password \
  --socket=/opt/homebrew/var/mysql/mysql.sock \
  streaming_platform < seed_data.sql
```

#### 6. Install Python Dependencies

```bash
cd ~/project_part2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 7. Run the Application

```bash
python run.py
```

**Access the app at:** http://localhost:5001

---

### Option B: Setup on Standard MySQL (Port 3306)

#### 1. Create MySQL Database and User

```sql
-- Log into MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE streaming_platform;

-- Create user
CREATE USER 'streaming_user'@'localhost' IDENTIFIED BY 'streaming_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON streaming_platform.* TO 'streaming_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 2. Run Schema and Seed Data

```bash
mysql -u streaming_user -p streaming_platform < schema_mysql.sql
mysql -u streaming_user -p streaming_platform < seed_data.sql
```

#### 3. Update Configuration

Edit `app/config.py` to use port 3306:

```python
MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
MYSQL_SOCKET = os.environ.get('MYSQL_SOCKET') or None  # Remove socket
```

#### 4. Install Dependencies and Run

```bash
cd project_part2
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

---

### Environment Variables (Optional)

Create a `.env` file to override defaults:

```bash
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_USER=streaming_user
MYSQL_PASSWORD=streaming_password
MYSQL_DATABASE=streaming_platform
MYSQL_SOCKET=/opt/homebrew/var/mysql/mysql.sock
CACHE_ENABLED=true
CACHE_TTL=300
```

---

## Current Configuration

| Setting | Value |
|---------|-------|
| **Flask Port** | 5001 (changed from 5000 to avoid macOS AirPlay conflict) |
| **MySQL Port** | 3307 (Homebrew default to avoid conflict with system MySQL) |
| **MySQL Socket** | `/opt/homebrew/var/mysql/mysql.sock` |
| **Database** | `streaming_platform` |
| **DB User** | `streaming_user` |
| **DB Password** | `streaming_password` |

---

## Features & Requirements Mapping

### Authentication (Requirement 4.1)
| Feature | Route | File |
|---------|-------|------|
| Registration | `/register` | `auth.py` |
| Login | `/login` | `auth.py` |
| Logout | `/logout` | `auth.py` |
| Create Employee | `/admin/create-employee` | `auth.py` |

### Customer Features (Requirement 4.2)
| Feature | Route | File |
|---------|-------|------|
| Browse Series | `/`, `/series` | `routes_customer.py` |
| Series Detail | `/series/<ws_id>` | `routes_customer.py` |
| Submit Feedback | `/series/<ws_id>/feedback` | `routes_customer.py` |
| Delete Feedback | `/series/<ws_id>/feedback/delete` | `routes_customer.py` |
| My Account | `/my-account` | `routes_customer.py` |

### Employee Features (Requirement 4.3)
| Feature | Route | File |
|---------|-------|------|
| Dashboard | `/admin/` | `routes_employee.py` |
| Manage Series | `/admin/series/*` | `routes_employee.py` |
| Manage Episodes | `/admin/series/<ws_id>/episodes/*` | `routes_employee.py` |
| Manage Schedules | `/admin/episodes/<ep_id>/schedules/*` | `routes_employee.py` |
| Manage Production Houses | `/admin/production-houses/*` | `routes_employee.py` |
| Manage Producers | `/admin/producers/*` | `routes_employee.py` |
| Manage Contracts | `/admin/contracts/*` | `routes_employee.py` |
| Manage Associations | `/admin/associations/*` | `routes_employee.py` |

---

## Security Implementation

### SQL Injection Prevention (Requirement 5.1)
**File: `app/db.py`**

All database queries use parameterized prepared statements:

```python
def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """
    SECURITY: This function uses parameterized queries to prevent SQL injection.
    The 'params' tuple is passed separately to cursor.execute(), ensuring
    user input is never concatenated into the SQL string.
    """
    cursor.execute(query, params or ())  # Safe parameterized execution
```

### XSS Protection (Requirement 5.2)
**Files: `app/security.py`, `app/templates/base.html`**

- Jinja2 auto-escaping enabled globally
- Additional `sanitize_input()` function for defense in depth
- User content rendered with `{{ variable }}` (auto-escaped)

### Password Security (Requirement 5.3)
**File: `app/security.py`**

```python
def hash_password(password):
    """bcrypt with cost factor 12"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password, hashed_password):
    """Timing-safe comparison"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
```

### Role-Based Access Control (Requirement 5.4)
**File: `app/auth.py`**

```python
@login_required
@role_required('EMPLOYEE')
def admin_only_route():
    pass
```

### Transactions (Requirement 5.5)
**File: `app/db.py`**

```python
@contextmanager
def transaction():
    """
    DEADLOCK PREVENTION STRATEGY:
    1. Keep transactions short
    2. Access tables in consistent order
    3. Use appropriate isolation level
    """
    db.start_transaction()
    yield cursor
    db.commit()  # or rollback on exception
```

---

## Part II Additional Features

### 1. Forgot Password Flow
**Files: `app/auth.py`, `app/email_utils.py`, `schema_mysql.sql`**

| Route | Description |
|-------|-------------|
| `/forgot-password` | Enter email/username to receive reset link |
| `/reset-password/<token>` | Enter new password with valid token |

**Security Features:**
- **Secure Token**: Generated using `secrets.token_urlsafe(32)` 
- **Single-Use**: Token marked as USED after password reset
- **Expiration**: Token expires after 60 minutes (configurable)
- **No Account Enumeration**: Generic success message regardless of account existence

**Database Table:**
```sql
CREATE TABLE GRN_PASSWORD_RESET (
    RESET_ID INT AUTO_INCREMENT PRIMARY KEY,
    LOGIN_ID VARCHAR(12) NOT NULL,
    TOKEN VARCHAR(255) NOT NULL UNIQUE,
    EXPIRES_AT DATETIME NOT NULL,
    USED TINYINT(1) NOT NULL DEFAULT 0,
    CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (LOGIN_ID) REFERENCES GRN_LOGIN(LOGIN_ID) ON DELETE CASCADE
);
```

**Email Configuration (`.env`):**
```bash
MAIL_SERVER=smtp.gmail.com    # or your SMTP server
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@streamvault.com
```

### 2. Deadlock Protection
**File: `app/db.py`**

Application-level retry mechanism for MySQL deadlocks:

```python
MYSQL_ERROR_DEADLOCK = 1213          # ER_LOCK_DEADLOCK
MYSQL_ERROR_LOCK_WAIT_TIMEOUT = 1205 # ER_LOCK_WAIT_TIMEOUT
DEADLOCK_MAX_RETRIES = 3

@contextmanager
def transaction():
    """
    Transaction with automatic retry on deadlock.
    - Detects MySQL error codes 1213 and 1205
    - Retries up to 3 times with exponential backoff
    - Raises DeadlockError if all retries fail
    """
```

**Deadlock Prevention Strategies:**
1. Keep transactions SHORT - minimal work inside transaction
2. Access tables in CONSISTENT ORDER across application
3. Use appropriate ISOLATION LEVEL (InnoDB default: REPEATABLE READ)
4. Use PRIMARY KEY for row-level locks only

**Stored Procedure Example:**
```sql
CREATE PROCEDURE sp_safe_update_subscription(
    IN p_account_id VARCHAR(12),
    IN p_new_subscription DECIMAL(10,2)
)
-- Uses primary key access for minimal locking
-- Immediate commit to release locks quickly
```

---

## Extra Credit Features

### 1. Performance Indexes (schema_mysql.sql)

```sql
-- Index for viewer aggregation queries
CREATE INDEX idx_episode_ws_viewers ON GRN_EPISODE (WS_ID, TOTAL_VIEWERS);

-- Index for rating queries
CREATE INDEX idx_feedback_ws_rating ON GRN_FEEDBACK (WS_ID, RATING);

-- Index for series search
CREATE INDEX idx_ws_name ON GRN_WEB_SERIES (WS_NAME);

-- Additional indexes for common query patterns...
```

**Performance Analysis**: See `EXPLAIN` output in project report.

### 2. Analytics Dashboard (routes_analytics.py)

- **Route**: `/analytics/dashboard`
- **Features**:
  - Top 10 series by viewers (bar chart)
  - Top 10 series by rating (bar chart)
  - Series distribution by country (pie chart)
  - Series distribution by genre (doughnut chart)
  - Rating distribution (bar chart)
  - Production house performance (bar chart)

### 3. Query Caching (db.py)

```python
def execute_cached_query(query, params=None, cache_key=None, ttl=300):
    """In-memory cache for read-heavy analytics queries"""
    # Check cache first
    if cache_key in _query_cache and not expired:
        return _query_cache[cache_key]
    # Execute and cache
    result = execute_query(query, params)
    _query_cache[cache_key] = result
    return result
```

### 4. Dark Theme UI (style.css)

- Cinematic dark theme with proper contrast
- All text colors optimized for visibility on dark backgrounds
- Comprehensive Bootstrap class overrides
- Custom CSS variables for consistent theming

---

## Demo Accounts

| Role | Username | Password |
|------|----------|----------|
| **Employee (Admin)** | `admin` | `Password123` |
| **Customer** | `johnsmith` | `Password123` |
| **Customer** | `emilyj` | `Password123` |
| **Customer** | `davidw` | `Password123` |
| **Customer** | `sarahb` | `Password123` |

**Note**: All demo accounts use the same password: `Password123`

---

## Quick Commands Reference

```bash
# Activate virtual environment
cd ~/project_part2 && source venv/bin/activate

# Start the Flask app
python run.py

# Check MySQL status (Homebrew)
brew services list | grep mysql

# Start MySQL (Homebrew)
brew services start mysql

# Stop MySQL (Homebrew)
brew services stop mysql

# Connect to database directly
/opt/homebrew/bin/mysql -u streaming_user -pstreaming_password \
  --socket=/opt/homebrew/var/mysql/mysql.sock streaming_platform

# Reload schema (warning: drops all data)
/opt/homebrew/bin/mysql -u streaming_user -pstreaming_password \
  --socket=/opt/homebrew/var/mysql/mysql.sock \
  streaming_platform < schema_mysql.sql

# Reload seed data
/opt/homebrew/bin/mysql -u streaming_user -pstreaming_password \
  --socket=/opt/homebrew/var/mysql/mysql.sock \
  streaming_platform < seed_data.sql
```

---

## Business Queries

See `business_queries.sql` for full implementations:

| Query | Type | Description |
|-------|------|-------------|
| Q1 | 3+ Table Join | Series with production house, countries, and average rating |
| Q2 | Multi-row Subquery | Series above average rating |
| Q3 | Correlated Subquery | Top series per country by viewers |
| Q4 | SET Operator (UNION) | Series availability comparison between regions |
| Q5 | CTE/Inline View | Performance tier classification |
| Q6 | TOP-N/BOTTOM-N | Top 5 by viewers, Bottom 5 by rating |

---

## Troubleshooting

### Port 5000 in Use (macOS)
On macOS, AirPlay Receiver uses port 5000. The app is configured to use **port 5001** instead.

### MySQL Connection Failed
1. Check if MySQL is running: `brew services list`
2. Verify socket exists: `ls -la /opt/homebrew/var/mysql/mysql.sock`
3. Test connection: `/opt/homebrew/bin/mysql -u root --socket=/opt/homebrew/var/mysql/mysql.sock`

### Login Not Working
Ensure the seed data was loaded correctly. The password hash in the database must match `Password123`.

### Dark Text Not Visible
Hard refresh your browser (Cmd+Shift+R on Mac) to clear CSS cache.

---

## License

This project is submitted as coursework for CS-GY 6083 at NYU Tandon.

---

## Acknowledgments

- Course: CS-GY 6083 - Principles of Database Systems
- Instructor: NYU Tandon School of Engineering
- Semester: Fall 2025

