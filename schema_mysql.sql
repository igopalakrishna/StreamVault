-- ============================================================================
-- CS-GY 6083 - Project Part II
-- MySQL Schema DDL
-- 
-- This file contains:
-- 1. All tables from Part I (converted from Oracle to MySQL)
-- 2. GRN_LOGIN table for authentication (Part II extension)
-- 3. Indexes for query optimization (Extra Credit)
-- 4. Check constraints
-- ============================================================================

-- Create database (if running manually)
-- CREATE DATABASE IF NOT EXISTS streaming_platform;
-- USE streaming_platform;

-- ============================================================================
-- DROP EXISTING TABLES (in correct order for FK constraints)
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS GRN_PASSWORD_RESET;
DROP TABLE IF EXISTS GRN_LOGIN;
DROP TABLE IF EXISTS GRN_SCHEDULE;
DROP TABLE IF EXISTS GRN_FEEDBACK;
DROP TABLE IF EXISTS GRN_WS_WS_TYPE;
DROP TABLE IF EXISTS GRN_WS_SUB_LANG;
DROP TABLE IF EXISTS GRN_WS_COUNTRY;
DROP TABLE IF EXISTS GRN_WEB_SERIES_DUBBING;
DROP TABLE IF EXISTS GRN_PROD_PROD_HOUSE;
DROP TABLE IF EXISTS GRN_CONTRACT;
DROP TABLE IF EXISTS GRN_EPISODE;
DROP TABLE IF EXISTS GRN_WEB_SERIES;
DROP TABLE IF EXISTS GRN_PRODUCTION_HOUSE;
DROP TABLE IF EXISTS GRN_PRODUCER;
DROP TABLE IF EXISTS GRN_USER_ACCOUNT;
DROP TABLE IF EXISTS GRN_WEB_SERIES_TYPE;
DROP TABLE IF EXISTS GRN_DUBBING;
DROP TABLE IF EXISTS GRN_SUBTITLE_LANGUAGE;
DROP TABLE IF EXISTS GRN_COUNTRY;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- REFERENCE TABLES (No Foreign Keys)
-- ============================================================================

-- Country reference table
CREATE TABLE GRN_COUNTRY (
    COUNTRY_ID VARCHAR(12) NOT NULL,
    COUNTRY_NAME VARCHAR(30) NOT NULL,
    PRIMARY KEY (COUNTRY_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Country reference table for geographic data';

-- Subtitle language reference table
CREATE TABLE GRN_SUBTITLE_LANGUAGE (
    LANG_ID VARCHAR(12) NOT NULL,
    LANG_NAME VARCHAR(30) NOT NULL,
    PRIMARY KEY (LANG_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Subtitle language options';

-- Web series type/genre reference table
CREATE TABLE GRN_WEB_SERIES_TYPE (
    WS_TYPE_ID VARCHAR(12) NOT NULL,
    WS_TYPE_NAME VARCHAR(30) NOT NULL,
    PRIMARY KEY (WS_TYPE_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Web series type/genre classifications';

-- Dubbing language reference table
CREATE TABLE GRN_DUBBING (
    LANG_ID VARCHAR(12) NOT NULL,
    LANG_NAME VARCHAR(30) NOT NULL,
    PRIMARY KEY (LANG_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Dubbing language options';

-- ============================================================================
-- ENTITY TABLES
-- ============================================================================

-- Producer entity table
CREATE TABLE GRN_PRODUCER (
    PRODUCER_ID VARCHAR(12) NOT NULL,
    FIRST_NAME VARCHAR(30) NOT NULL,
    MIDDLE_NAME VARCHAR(30),
    LAST_NAME VARCHAR(30) NOT NULL,
    STREET_ADDR VARCHAR(50) NOT NULL,
    CITY VARCHAR(30) NOT NULL,
    STATE VARCHAR(30) NOT NULL,
    POSTAL_CODE VARCHAR(5) NOT NULL,
    COUNTRY VARCHAR(30) NOT NULL,
    PHONE_NUMBER VARCHAR(15) NOT NULL,
    EMAIL_ADDR VARCHAR(100) NOT NULL,
    PRIMARY KEY (PRODUCER_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Producer information';

-- Production house entity table
CREATE TABLE GRN_PRODUCTION_HOUSE (
    PH_ID VARCHAR(12) NOT NULL,
    PH_NAME VARCHAR(30) NOT NULL,
    STREET_ADDR VARCHAR(50) NOT NULL,
    CITY VARCHAR(30) NOT NULL,
    STATE VARCHAR(30) NOT NULL,
    POSTAL_CODE VARCHAR(5) NOT NULL,
    COUNTRY VARCHAR(30) NOT NULL,
    YEAR_ESTABLISHED INT NOT NULL,
    PRIMARY KEY (PH_ID),
    -- CHECK CONSTRAINT: Year must be reasonable (1800-2100)
    CONSTRAINT chk_year_established CHECK (YEAR_ESTABLISHED >= 1800 AND YEAR_ESTABLISHED <= 2100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Production house/studio information';

-- User account entity table
CREATE TABLE GRN_USER_ACCOUNT (
    ACCOUNT_ID VARCHAR(12) NOT NULL,
    FIRST_NAME VARCHAR(30) NOT NULL,
    MIDDLE_NAME VARCHAR(30),
    LAST_NAME VARCHAR(30) NOT NULL,
    EMAIL_ADDR VARCHAR(100) NOT NULL,
    STREET_ADDR VARCHAR(50) NOT NULL,
    CITY VARCHAR(30) NOT NULL,
    STATE VARCHAR(30) NOT NULL,
    POSTAL_CODE VARCHAR(5) NOT NULL,
    COUNTRY VARCHAR(30) NOT NULL,
    DATE_CREATED DATETIME NOT NULL,
    MONTHLY_SUBSCRIPTION DECIMAL(10,2) NOT NULL,
    COUNTRY_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (ACCOUNT_ID),
    CONSTRAINT fk_user_country FOREIGN KEY (COUNTRY_ID) 
        REFERENCES GRN_COUNTRY(COUNTRY_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User account information for customers and employees';

-- Web series entity table
CREATE TABLE GRN_WEB_SERIES (
    WS_ID VARCHAR(12) NOT NULL,
    WS_NAME VARCHAR(50) NOT NULL,
    NUM_OF_EPS INT NOT NULL,
    LANGUAGE VARCHAR(30) NOT NULL,
    RELEASE_DATE DATE NOT NULL,
    COUNTRY_OF_ORIGIN VARCHAR(30) NOT NULL,
    PH_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (WS_ID),
    CONSTRAINT fk_ws_prod_house FOREIGN KEY (PH_ID) 
        REFERENCES GRN_PRODUCTION_HOUSE(PH_ID),
    -- CHECK CONSTRAINT: Number of episodes must be positive
    CONSTRAINT chk_num_of_eps CHECK (NUM_OF_EPS > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Web series main information';

-- Episode entity table
CREATE TABLE GRN_EPISODE (
    EP_ID VARCHAR(12) NOT NULL,
    EP_NAME VARCHAR(30) NOT NULL,
    TOTAL_VIEWERS INT NOT NULL DEFAULT 0,
    TECH_INTERRUPT VARCHAR(3) NOT NULL DEFAULT 'No',
    WS_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (EP_ID),
    CONSTRAINT fk_ep_ws FOREIGN KEY (WS_ID) 
        REFERENCES GRN_WEB_SERIES(WS_ID),
    -- CHECK CONSTRAINT: Technical interrupt must be Yes or No
    CONSTRAINT chk_tech_interrupt CHECK (TECH_INTERRUPT IN ('Yes', 'No'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Episode information for web series';

-- Contract entity table
CREATE TABLE GRN_CONTRACT (
    CONTRACT_ID VARCHAR(12) NOT NULL,
    PER_EP_CHARGE DECIMAL(10,2) NOT NULL,
    CONTRACT_ST_DATE DATE NOT NULL,
    CONTRACT_END_DATE DATE NOT NULL,
    WS_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (CONTRACT_ID),
    CONSTRAINT fk_contract_ws FOREIGN KEY (WS_ID) 
        REFERENCES GRN_WEB_SERIES(WS_ID),
    -- CHECK CONSTRAINT: End date must be after start date
    CONSTRAINT chk_contract_dates CHECK (CONTRACT_END_DATE > CONTRACT_ST_DATE),
    -- CHECK CONSTRAINT: Per episode charge must be positive
    CONSTRAINT chk_per_ep_charge CHECK (PER_EP_CHARGE > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Streaming contracts for web series';

-- Schedule entity table
CREATE TABLE GRN_SCHEDULE (
    SCHEDULE_ID VARCHAR(12) NOT NULL,
    START_DT DATE NOT NULL,
    END_DT DATE NOT NULL,
    EP_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (SCHEDULE_ID),
    CONSTRAINT fk_schedule_ep FOREIGN KEY (EP_ID) 
        REFERENCES GRN_EPISODE(EP_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Episode broadcast schedules';

-- ============================================================================
-- JUNCTION/RELATIONSHIP TABLES
-- ============================================================================

-- Producer-Production House many-to-many relationship
CREATE TABLE GRN_PROD_PROD_HOUSE (
    ALLIANCE_DATE DATE NOT NULL,
    END_DATE DATE NOT NULL,
    PRODUCER_ID VARCHAR(12) NOT NULL,
    PH_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (PRODUCER_ID, PH_ID),
    CONSTRAINT fk_pph_producer FOREIGN KEY (PRODUCER_ID) 
        REFERENCES GRN_PRODUCER(PRODUCER_ID),
    CONSTRAINT fk_pph_house FOREIGN KEY (PH_ID) 
        REFERENCES GRN_PRODUCTION_HOUSE(PH_ID),
    -- CHECK CONSTRAINT: End date must be after alliance date
    CONSTRAINT chk_alliance_dates CHECK (END_DATE > ALLIANCE_DATE)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Producer-Production House alliances';

-- Web Series-Dubbing many-to-many relationship
CREATE TABLE GRN_WEB_SERIES_DUBBING (
    WS_ID VARCHAR(12) NOT NULL,
    LANG_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (WS_ID, LANG_ID),
    CONSTRAINT fk_wsd_ws FOREIGN KEY (WS_ID) 
        REFERENCES GRN_WEB_SERIES(WS_ID),
    CONSTRAINT fk_wsd_lang FOREIGN KEY (LANG_ID) 
        REFERENCES GRN_DUBBING(LANG_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Web series available dubbing languages';

-- Web Series-Country many-to-many relationship (release countries)
CREATE TABLE GRN_WS_COUNTRY (
    COUNTRY_RELEASE_DT DATE NOT NULL,
    WS_ID VARCHAR(12) NOT NULL,
    COUNTRY_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (WS_ID, COUNTRY_ID),
    CONSTRAINT fk_wsc_ws FOREIGN KEY (WS_ID) 
        REFERENCES GRN_WEB_SERIES(WS_ID),
    CONSTRAINT fk_wsc_country FOREIGN KEY (COUNTRY_ID) 
        REFERENCES GRN_COUNTRY(COUNTRY_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Web series release dates by country';

-- Web Series-Subtitle Language many-to-many relationship
CREATE TABLE GRN_WS_SUB_LANG (
    WS_ID VARCHAR(12) NOT NULL,
    LANG_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (WS_ID, LANG_ID),
    CONSTRAINT fk_wssl_ws FOREIGN KEY (WS_ID) 
        REFERENCES GRN_WEB_SERIES(WS_ID),
    CONSTRAINT fk_wssl_lang FOREIGN KEY (LANG_ID) 
        REFERENCES GRN_SUBTITLE_LANGUAGE(LANG_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Web series available subtitle languages';

-- Web Series-Type many-to-many relationship (genres)
CREATE TABLE GRN_WS_WS_TYPE (
    WS_ID VARCHAR(12) NOT NULL,
    WS_TYPE_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (WS_ID, WS_TYPE_ID),
    CONSTRAINT fk_wswt_ws FOREIGN KEY (WS_ID) 
        REFERENCES GRN_WEB_SERIES(WS_ID),
    CONSTRAINT fk_wswt_type FOREIGN KEY (WS_TYPE_ID) 
        REFERENCES GRN_WEB_SERIES_TYPE(WS_TYPE_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Web series genre/type classifications';

-- Feedback/Rating table
CREATE TABLE GRN_FEEDBACK (
    RATING TINYINT NOT NULL,
    FEEDBACK_TXT VARCHAR(400) NOT NULL,
    DATE_RECORDED DATETIME NOT NULL,
    WS_ID VARCHAR(12) NOT NULL,
    ACCOUNT_ID VARCHAR(12) NOT NULL,
    PRIMARY KEY (WS_ID, ACCOUNT_ID),
    CONSTRAINT fk_fb_ws FOREIGN KEY (WS_ID) 
        REFERENCES GRN_WEB_SERIES(WS_ID),
    CONSTRAINT fk_fb_user FOREIGN KEY (ACCOUNT_ID) 
        REFERENCES GRN_USER_ACCOUNT(ACCOUNT_ID),
    -- CHECK CONSTRAINT: Rating must be between 1 and 5
    CONSTRAINT chk_rating CHECK (RATING BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User feedback and ratings for web series';

-- ============================================================================
-- PART II EXTENSION: LOGIN/AUTHENTICATION TABLE
-- ============================================================================

-- Login table for authentication (Part II Extension)
-- This table stores authentication credentials and role information
CREATE TABLE GRN_LOGIN (
    LOGIN_ID VARCHAR(12) NOT NULL COMMENT 'Unique login identifier',
    ACCOUNT_ID VARCHAR(12) NOT NULL COMMENT 'FK to GRN_USER_ACCOUNT',
    USERNAME VARCHAR(30) NOT NULL COMMENT 'Unique username for login',
    PASSWORD_HASH VARCHAR(255) NOT NULL COMMENT 'bcrypt hashed password',
    ROLE ENUM('CUSTOMER', 'EMPLOYEE') NOT NULL DEFAULT 'CUSTOMER' COMMENT 'User role for access control',
    CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Account creation timestamp',
    PRIMARY KEY (LOGIN_ID),
    UNIQUE KEY uk_username (USERNAME),
    CONSTRAINT fk_login_account FOREIGN KEY (ACCOUNT_ID) 
        REFERENCES GRN_USER_ACCOUNT(ACCOUNT_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User login credentials and roles for Part II authentication';

-- ============================================================================
-- PART II EXTENSION: PASSWORD RESET TABLE
-- ============================================================================

-- Password reset tokens table for "Forgot Password" feature
-- This table stores secure, single-use tokens with expiration
DROP TABLE IF EXISTS GRN_PASSWORD_RESET;

CREATE TABLE GRN_PASSWORD_RESET (
    RESET_ID INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique reset token identifier',
    LOGIN_ID VARCHAR(12) NOT NULL COMMENT 'FK to GRN_LOGIN',
    TOKEN VARCHAR(255) NOT NULL COMMENT 'Secure random token (URL-safe)',
    EXPIRES_AT DATETIME NOT NULL COMMENT 'Token expiration timestamp',
    USED TINYINT(1) NOT NULL DEFAULT 0 COMMENT '0=unused, 1=used',
    CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Token creation timestamp',
    UNIQUE KEY uk_reset_token (TOKEN),
    CONSTRAINT fk_reset_login FOREIGN KEY (LOGIN_ID) 
        REFERENCES GRN_LOGIN(LOGIN_ID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Password reset tokens for forgot password feature';

-- Index for efficient token lookups during password reset
CREATE INDEX idx_reset_token_expires 
ON GRN_PASSWORD_RESET (TOKEN, EXPIRES_AT, USED)
COMMENT 'Optimizes token validation queries';

-- Index for cleanup of expired tokens
CREATE INDEX idx_reset_expires 
ON GRN_PASSWORD_RESET (EXPIRES_AT)
COMMENT 'Optimizes expired token cleanup queries';

-- ============================================================================
-- DEADLOCK PROTECTION: STORED PROCEDURE
-- ============================================================================

-- Stored procedure demonstrating deadlock-safe subscription update
-- This procedure shows how to structure database operations to minimize deadlocks
-- by accessing tables in a consistent order and keeping transactions short.

DELIMITER //

CREATE PROCEDURE sp_safe_update_subscription(
    IN p_account_id VARCHAR(12),
    IN p_new_subscription DECIMAL(10,2)
)
COMMENT 'Deadlock-safe procedure to update user subscription.
         Demonstrates consistent table access order and minimal transaction scope.
         DEADLOCK PREVENTION STRATEGIES USED:
         1. Single table access - no multi-table locking issues
         2. Uses primary key for row-level lock only
         3. Short transaction - immediate commit after update'
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        -- On any error, rollback and re-raise
        ROLLBACK;
        RESIGNAL;
    END;
    
    -- Start transaction with explicit isolation level
    START TRANSACTION;
    
    -- Update subscription using primary key (minimal locking)
    -- PRIMARY KEY access ensures only one row is locked
    UPDATE GRN_USER_ACCOUNT 
    SET MONTHLY_SUBSCRIPTION = p_new_subscription
    WHERE ACCOUNT_ID = p_account_id;
    
    -- Immediate commit to release locks quickly
    COMMIT;
END //

-- Procedure to clean up expired password reset tokens
-- Called periodically to maintain table hygiene

CREATE PROCEDURE sp_cleanup_expired_tokens()
COMMENT 'Removes expired password reset tokens to prevent table bloat.
         Safe to run concurrently - uses DELETE with WHERE on indexed column.'
BEGIN
    DELETE FROM GRN_PASSWORD_RESET 
    WHERE EXPIRES_AT < NOW() OR USED = 1;
END //

DELIMITER ;

-- ============================================================================
-- EXTRA CREDIT: PERFORMANCE INDEXES
-- ============================================================================

-- Index 1: GRN_EPISODE - Optimize queries for total viewers per series
-- Use case: Analytics dashboard "Top N series by viewers"
-- Query pattern: SELECT SUM(TOTAL_VIEWERS) FROM GRN_EPISODE WHERE WS_ID = ?
-- Before: Full table scan on GRN_EPISODE
-- After: Index seek on WS_ID + covering index for TOTAL_VIEWERS
CREATE INDEX idx_episode_ws_viewers 
ON GRN_EPISODE (WS_ID, TOTAL_VIEWERS)
COMMENT 'Optimizes aggregation queries for total viewers per web series';

-- Index 2: GRN_FEEDBACK - Optimize queries for ratings by series
-- Use case: Calculating average rating for series detail page
-- Query pattern: SELECT AVG(RATING) FROM GRN_FEEDBACK WHERE WS_ID = ?
-- Before: Full table scan on GRN_FEEDBACK
-- After: Index seek on WS_ID + covering index for RATING
CREATE INDEX idx_feedback_ws_rating 
ON GRN_FEEDBACK (WS_ID, RATING)
COMMENT 'Optimizes rating aggregation queries per web series';

-- Index 3: GRN_WEB_SERIES - Optimize name searches
-- Use case: Search functionality on home page
-- Query pattern: SELECT * FROM GRN_WEB_SERIES WHERE WS_NAME LIKE '%term%'
-- Note: This helps with prefix searches; full-text index would be better for LIKE '%term%'
CREATE INDEX idx_ws_name 
ON GRN_WEB_SERIES (WS_NAME)
COMMENT 'Optimizes web series name searches and sorting';

-- Index 4: GRN_WS_COUNTRY - Optimize country-based queries
-- Use case: Filter series by country, analytics by country
-- Query pattern: SELECT * FROM GRN_WS_COUNTRY WHERE COUNTRY_ID = ?
CREATE INDEX idx_ws_country_country 
ON GRN_WS_COUNTRY (COUNTRY_ID)
COMMENT 'Optimizes queries filtering series by release country';

-- Index 5: GRN_LOGIN - Optimize username lookup for authentication
-- Use case: Login authentication
-- Query pattern: SELECT * FROM GRN_LOGIN WHERE USERNAME = ?
-- Note: USERNAME already has unique constraint which creates an index,
-- but this composite index includes ROLE for authorization checks
CREATE INDEX idx_login_user_role 
ON GRN_LOGIN (USERNAME, ROLE)
COMMENT 'Optimizes login authentication with role verification';

-- Index 6: GRN_USER_ACCOUNT - Optimize email lookups for registration
-- Use case: Check if email already exists during registration
-- Query pattern: SELECT * FROM GRN_USER_ACCOUNT WHERE EMAIL_ADDR = ?
CREATE INDEX idx_user_email 
ON GRN_USER_ACCOUNT (EMAIL_ADDR)
COMMENT 'Optimizes email uniqueness checks during registration';

-- Index 7: GRN_WEB_SERIES - Optimize production house queries
-- Use case: List all series by production house
-- Query pattern: SELECT * FROM GRN_WEB_SERIES WHERE PH_ID = ?
CREATE INDEX idx_ws_production_house 
ON GRN_WEB_SERIES (PH_ID)
COMMENT 'Optimizes queries filtering series by production house';

-- Index 8: GRN_FEEDBACK - Optimize user feedback history queries
-- Use case: Display user's feedback history on profile page
-- Query pattern: SELECT * FROM GRN_FEEDBACK WHERE ACCOUNT_ID = ?
CREATE INDEX idx_feedback_account 
ON GRN_FEEDBACK (ACCOUNT_ID, DATE_RECORDED DESC)
COMMENT 'Optimizes user feedback history queries sorted by date';

-- ============================================================================
-- VERIFY TABLES CREATED
-- ============================================================================

SELECT 'Tables created successfully!' AS STATUS;

SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME LIKE 'GRN_%'
ORDER BY TABLE_NAME;
