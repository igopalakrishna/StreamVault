# CS-GY 6083 - Project Part II Report Outline

---

## TITLE PAGE

**CS-GY 6083 – B, Fall 2025**  
**Principles of Database Systems**  
**NYU Tandon School of Engineering**

### Project Part II: Web-Based Streaming Platform

**Team Members:**
- Gopala Krishna Abba (Net ID: ga2664)
- Riya Patil (Net ID: rsp9219)
- Neha Nainan (Net ID: nan6504)

**Date:** [Insert Submission Date]

---

## TABLE OF CONTENTS

1. Executive Summary
2. System Overview
3. Technology Stack
4. Database Schema
   - 4.1 Entity-Relationship Diagram
   - 4.2 Relational Model
   - 4.3 New Tables for Part II
   - 4.4 Performance Indexes
5. Application Architecture
6. Security Implementation
   - 6.1 SQL Injection Prevention
   - 6.2 XSS Protection
   - 6.3 Password Security
   - 6.4 Role-Based Access Control
   - 6.5 Transaction Management
7. Feature Implementation
   - 7.1 Authentication System
   - 7.2 Customer Features
   - 7.3 Employee/Admin Features
8. Extra Credit Features
   - 8.1 Performance Indexes
   - 8.2 Analytics Dashboard
   - 8.3 Query Caching
9. Business Analysis Queries (Q1-Q6)
10. Testing and Validation
11. Lessons Learned
12. Appendices

---

## 1. EXECUTIVE SUMMARY

[Write 1 page summarizing the project]

StreamVault is a web-based streaming platform management system developed as Project Part II for CS-GY 6083. The application extends the database schema designed in Part I with authentication capabilities and provides a comprehensive web interface for managing web series content.

**Key Accomplishments:**
- Implemented secure user authentication with bcrypt password hashing
- Created role-based access control separating Customer and Employee permissions
- Built full CRUD functionality for all 17+ database tables from Part I
- Developed analytics dashboard with Chart.js visualizations
- Ensured SQL injection and XSS protection throughout the application
- Implemented transaction management for multi-table operations

**Technologies Used:**
- Backend: Python Flask framework
- Database: MySQL with mysql-connector-python (no ORM, raw SQL visible)
- Frontend: HTML/CSS with Bootstrap 5, Chart.js for visualizations
- Security: bcrypt for passwords, parameterized queries, Jinja2 auto-escaping

The application successfully demonstrates database principles including prepared statements, transactions, indexes, and complex SQL queries while providing a functional and user-friendly interface.

---

## 2. SYSTEM OVERVIEW

[Describe the overall system architecture]

The StreamVault application follows a traditional Model-View-Controller (MVC) architecture:

- **Model Layer**: MySQL database with GRN_* tables, accessed via prepared statements
- **View Layer**: Jinja2 templates with Bootstrap 5 styling
- **Controller Layer**: Flask routes organized by user role

**User Roles:**
1. **Customers**: Can browse series, view details, submit feedback, manage profile
2. **Employees**: Full administrative access to manage all content and view analytics

---

## 3. TECHNOLOGY STACK

| Layer | Technology | Purpose |
|-------|------------|---------|
| Web Framework | Flask 3.0 | Route handling, session management |
| Database | MySQL 8.0 | Data persistence |
| DB Connector | mysql-connector-python | Parameterized query execution |
| Template Engine | Jinja2 | HTML rendering with auto-escaping |
| Password Hashing | bcrypt | Secure password storage |
| Frontend Framework | Bootstrap 5 | Responsive UI components |
| Charts | Chart.js 4.x | Data visualization |

---

## 4. DATABASE SCHEMA

### 4.1 Entity-Relationship Diagram
[Insert ERD from Part I]

### 4.2 Relational Model
[Insert Relational diagram from Part I]

### 4.3 New Tables for Part II

**GRN_LOGIN** - Authentication table:
```sql
CREATE TABLE GRN_LOGIN (
    LOGIN_ID VARCHAR(12) NOT NULL,
    ACCOUNT_ID VARCHAR(12) NOT NULL,
    USERNAME VARCHAR(30) NOT NULL UNIQUE,
    PASSWORD_HASH VARCHAR(255) NOT NULL,
    ROLE ENUM('CUSTOMER', 'EMPLOYEE') NOT NULL,
    CREATED_AT DATETIME NOT NULL,
    PRIMARY KEY (LOGIN_ID),
    FOREIGN KEY (ACCOUNT_ID) REFERENCES GRN_USER_ACCOUNT(ACCOUNT_ID)
);
```

### 4.4 Performance Indexes

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| idx_episode_ws_viewers | GRN_EPISODE | (WS_ID, TOTAL_VIEWERS) | Viewer aggregation queries |
| idx_feedback_ws_rating | GRN_FEEDBACK | (WS_ID, RATING) | Rating calculation queries |
| idx_ws_name | GRN_WEB_SERIES | (WS_NAME) | Series name searches |
| idx_ws_country_country | GRN_WS_COUNTRY | (COUNTRY_ID) | Country filter queries |
| idx_login_user_role | GRN_LOGIN | (USERNAME, ROLE) | Login authentication |
| idx_user_email | GRN_USER_ACCOUNT | (EMAIL_ADDR) | Email uniqueness checks |
| idx_ws_production_house | GRN_WEB_SERIES | (PH_ID) | Production house queries |
| idx_feedback_account | GRN_FEEDBACK | (ACCOUNT_ID, DATE_RECORDED) | User feedback history |

---

## 5. APPLICATION ARCHITECTURE

[Describe the file structure and component responsibilities]

```
app/
├── __init__.py          # Application factory
├── config.py            # Configuration management
├── db.py                # Database layer (prepared statements, transactions)
├── security.py          # Security utilities (hashing, validation)
├── auth.py              # Authentication routes and decorators
├── routes_customer.py   # Customer-facing features
├── routes_employee.py   # Admin CRUD operations
└── routes_analytics.py  # Analytics dashboard
```

---

## 6. SECURITY IMPLEMENTATION

### 6.1 SQL Injection Prevention

All database queries use parameterized prepared statements. User input is NEVER concatenated into SQL strings.

**Example from `db.py`:**
```python
def execute_query(query, params=None):
    cursor.execute(query, params or ())  # Parameterized - SAFE
```

**Usage example:**
```python
# SAFE: User input passed as parameter
user = execute_query(
    "SELECT * FROM GRN_LOGIN WHERE USERNAME = %s",
    (username,)
)
```

### 6.2 XSS Protection

- Jinja2 auto-escaping enabled for all templates
- `sanitize_input()` function for additional protection
- All user content rendered with `{{ variable }}` syntax

### 6.3 Password Security

- bcrypt hashing with cost factor 12
- Random salt per password
- Timing-safe comparison

```python
def hash_password(password):
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt)
```

### 6.4 Role-Based Access Control

```python
@login_required
@role_required('EMPLOYEE')
def admin_route():
    # Only accessible by employees
```

### 6.5 Transaction Management

Multi-table operations use explicit transactions:

```python
with transaction() as cursor:
    cursor.execute("INSERT INTO GRN_USER_ACCOUNT ...", params1)
    cursor.execute("INSERT INTO GRN_LOGIN ...", params2)
    # Both succeed or both rollback
```

**Deadlock Prevention:**
1. Keep transactions short
2. Access tables in consistent order
3. Use appropriate isolation level

---

## 7. FEATURE IMPLEMENTATION

### 7.1 Authentication System

| Feature | Route | Method |
|---------|-------|--------|
| Registration | `/register` | GET/POST |
| Login | `/login` | GET/POST |
| Logout | `/logout` | GET |
| Create Employee | `/admin/create-employee` | GET/POST |

### 7.2 Customer Features

| Feature | Route | CRUD |
|---------|-------|------|
| Browse Series | `/series` | Read |
| Series Detail | `/series/<id>` | Read |
| Submit Feedback | `/series/<id>/feedback` | Create/Update |
| Delete Feedback | `/series/<id>/feedback/delete` | Delete |
| My Account | `/my-account` | Read/Update |

### 7.3 Employee/Admin Features

| Entity | Routes | CRUD Operations |
|--------|--------|-----------------|
| Web Series | `/admin/series/*` | All |
| Episodes | `/admin/series/<id>/episodes/*` | All |
| Schedules | `/admin/episodes/<id>/schedules/*` | Create/Delete |
| Production Houses | `/admin/production-houses/*` | All |
| Producers | `/admin/producers/*` | All |
| Contracts | `/admin/contracts/*` | All |
| Associations | `/admin/associations/*` | Create/Delete |

---

## 8. EXTRA CREDIT FEATURES

### 8.1 Performance Indexes

**Implementation:** See `schema_mysql.sql` for index definitions.

**Performance Analysis:**

Before index (example query):
```
EXPLAIN SELECT * FROM GRN_EPISODE WHERE WS_ID = 'WS001';
-- type: ALL, rows: 15 (full table scan)
```

After index:
```
EXPLAIN SELECT * FROM GRN_EPISODE WHERE WS_ID = 'WS001';
-- type: ref, rows: 4 (index seek)
```

### 8.2 Analytics Dashboard

**Route:** `/analytics`

**Visualizations:**
1. Top 10 Series by Viewers (horizontal bar chart)
2. Top 10 Series by Rating (horizontal bar chart)
3. Series Distribution by Country (pie chart)
4. Series Distribution by Genre (doughnut chart)
5. Rating Distribution (bar chart)
6. Production House Performance (bar chart)

**Technology:** Chart.js 4.x loaded via CDN

### 8.3 Query Caching

**Implementation:** In-memory cache with TTL in `db.py`

```python
def execute_cached_query(query, params, cache_key, ttl=300):
    if cache_key in cache and not expired:
        return cache[cache_key]
    result = execute_query(query, params)
    cache[cache_key] = result
    return result
```

---

## 9. BUSINESS ANALYSIS QUERIES (Q1-Q6)

### Q1: Join with 3+ Tables
**Business Question:** For each web series, show production house, countries, and average rating.

```sql
SELECT ws.WS_NAME, ph.PH_NAME, 
       GROUP_CONCAT(c.COUNTRY_NAME) AS COUNTRIES,
       AVG(f.RATING) AS AVG_RATING
FROM GRN_WEB_SERIES ws
JOIN GRN_PRODUCTION_HOUSE ph ON ws.PH_ID = ph.PH_ID
LEFT JOIN GRN_WS_COUNTRY wsc ON ws.WS_ID = wsc.WS_ID
LEFT JOIN GRN_COUNTRY c ON wsc.COUNTRY_ID = c.COUNTRY_ID
LEFT JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
GROUP BY ws.WS_ID;
```

### Q2: Multi-row Subquery
**Business Question:** Find series with above-average ratings.

```sql
SELECT WS_NAME, AVG(RATING) AS AVG_RATING
FROM GRN_WEB_SERIES ws
JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
GROUP BY ws.WS_ID
HAVING AVG(RATING) > (SELECT AVG(RATING) FROM GRN_FEEDBACK);
```

### Q3: Correlated Subquery
**Business Question:** For each country, find the series with maximum viewers.

[See business_queries.sql for full implementation]

### Q4: SET Operator (UNION)
**Business Question:** Compare series availability between regions.

[See business_queries.sql for full implementation]

### Q5: CTE/Inline View
**Business Question:** Classify series into performance tiers.

[See business_queries.sql for full implementation]

### Q6: TOP-N/BOTTOM-N
**Business Question:** Top 5 by viewers, Bottom 5 by rating.

[See business_queries.sql for full implementation]

---

## 10. TESTING AND VALIDATION

[Describe testing approach]

- Manual testing of all CRUD operations
- Verification of security measures (SQL injection, XSS)
- Check constraint validation
- Transaction rollback testing
- Cross-browser compatibility

---

## 11. LESSONS LEARNED

### Technical Lessons
- Importance of parameterized queries for security
- Transaction management for data integrity
- Index design for query optimization
- Password hashing best practices

### Project Management Lessons
- Value of clear schema design in Part I
- Iterative development approach
- Importance of documentation

### Challenges Faced
- Converting Oracle DDL to MySQL syntax
- Managing foreign key relationships during deletes
- Implementing proper error handling

### Future Improvements
- Add email verification for registration
- Implement password reset functionality
- Add more detailed analytics
- Implement API endpoints for mobile apps

---

## 12. APPENDICES

### A. Table Record Counts
```sql
SELECT 'GRN_COUNTRY' AS TABLE_NAME, COUNT(*) FROM GRN_COUNTRY
UNION ALL SELECT 'GRN_WEB_SERIES', COUNT(*) FROM GRN_WEB_SERIES
-- ... (see seed_data.sql for full query)
```

### B. Data Dictionary
[Reference to INFORMATION_SCHEMA queries from Part I]

### C. Screenshots
[Insert application screenshots]

### D. Full DDL
[Reference to schema_mysql.sql]

---

*End of Report Outline*
