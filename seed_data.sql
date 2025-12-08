-- ============================================================================
-- CS-GY 6083 - Project Part II
-- Sample Seed Data for Demo
-- 
-- This file contains realistic sample data for all GRN_* tables.
-- Run this after schema_mysql.sql to populate the database.
-- ============================================================================

USE streaming_platform;

-- ============================================================================
-- REFERENCE DATA
-- ============================================================================

-- Countries
INSERT INTO GRN_COUNTRY (COUNTRY_ID, COUNTRY_NAME) VALUES
('CNT001', 'United States'),
('CNT002', 'United Kingdom'),
('CNT003', 'Canada'),
('CNT004', 'Australia'),
('CNT005', 'Germany'),
('CNT006', 'France'),
('CNT007', 'Japan'),
('CNT008', 'South Korea'),
('CNT009', 'India'),
('CNT010', 'Brazil');

-- Subtitle Languages
INSERT INTO GRN_SUBTITLE_LANGUAGE (LANG_ID, LANG_NAME) VALUES
('SUB001', 'English'),
('SUB002', 'Spanish'),
('SUB003', 'French'),
('SUB004', 'German'),
('SUB005', 'Japanese'),
('SUB006', 'Korean'),
('SUB007', 'Portuguese'),
('SUB008', 'Chinese'),
('SUB009', 'Hindi'),
('SUB010', 'Arabic');

-- Web Series Types/Genres
INSERT INTO GRN_WEB_SERIES_TYPE (WS_TYPE_ID, WS_TYPE_NAME) VALUES
('TYPE001', 'Drama'),
('TYPE002', 'Comedy'),
('TYPE003', 'Thriller'),
('TYPE004', 'Sci-Fi'),
('TYPE005', 'Horror'),
('TYPE006', 'Romance'),
('TYPE007', 'Action'),
('TYPE008', 'Documentary'),
('TYPE009', 'Fantasy'),
('TYPE010', 'Crime');

-- Dubbing Languages
INSERT INTO GRN_DUBBING (LANG_ID, LANG_NAME) VALUES
('DUB001', 'English'),
('DUB002', 'Spanish'),
('DUB003', 'French'),
('DUB004', 'German'),
('DUB005', 'Japanese'),
('DUB006', 'Korean'),
('DUB007', 'Portuguese'),
('DUB008', 'Italian');

-- ============================================================================
-- PRODUCTION HOUSES
-- ============================================================================

INSERT INTO GRN_PRODUCTION_HOUSE (PH_ID, PH_NAME, STREET_ADDR, CITY, STATE, POSTAL_CODE, COUNTRY, YEAR_ESTABLISHED) VALUES
('PH001', 'Netflix Studios', '5808 Sunset Blvd', 'Los Angeles', 'California', '90028', 'United States', 2013),
('PH002', 'HBO Productions', '1100 Avenue of Americas', 'New York', 'New York', '10036', 'United States', 1972),
('PH003', 'BBC Studios', 'Television Centre', 'London', 'England', 'W127R', 'United Kingdom', 1946),
('PH004', 'Studio Dragon', '543 Gangnam-daero', 'Seoul', 'Seoul', '06050', 'South Korea', 2016),
('PH005', 'Amazon MGM Studios', '2100 Broadway', 'Santa Monica', 'California', '90404', 'United States', 2010);

-- ============================================================================
-- PRODUCERS
-- ============================================================================

INSERT INTO GRN_PRODUCER (PRODUCER_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, STREET_ADDR, CITY, STATE, POSTAL_CODE, COUNTRY, PHONE_NUMBER, EMAIL_ADDR) VALUES
('PROD001', 'Shonda', 'Lynn', 'Rhimes', '4024 Radford Ave', 'Studio City', 'California', '91604', 'United States', '818-555-0101', 'shonda.rhimes@email.com'),
('PROD002', 'David', NULL, 'Benioff', '500 S Buena Vista St', 'Burbank', 'California', '91521', 'United States', '818-555-0102', 'david.benioff@email.com'),
('PROD003', 'Greg', NULL, 'Berlanti', '3000 W Olive Ave', 'Burbank', 'California', '91505', 'United States', '818-555-0103', 'greg.berlanti@email.com'),
('PROD004', 'Ryan', NULL, 'Murphy', '10201 W Pico Blvd', 'Los Angeles', 'California', '90064', 'United States', '310-555-0104', 'ryan.murphy@email.com'),
('PROD005', 'Joon-ho', NULL, 'Bong', '100 Seocho-dong', 'Seoul', 'Seoul', '06654', 'South Korea', '822-555-0105', 'bong.joonho@email.com');

-- ============================================================================
-- PRODUCER-PRODUCTION HOUSE ALLIANCES
-- ============================================================================

INSERT INTO GRN_PROD_PROD_HOUSE (ALLIANCE_DATE, END_DATE, PRODUCER_ID, PH_ID) VALUES
('2017-07-01', '2027-07-01', 'PROD001', 'PH001'),
('2019-01-15', '2026-01-15', 'PROD002', 'PH002'),
('2018-06-01', '2025-06-01', 'PROD003', 'PH001'),
('2020-02-01', '2028-02-01', 'PROD004', 'PH001'),
('2021-03-15', '2026-03-15', 'PROD005', 'PH004');

-- ============================================================================
-- WEB SERIES (with poster images and YouTube trailer embeds)
-- ============================================================================

INSERT INTO GRN_WEB_SERIES (WS_ID, WS_NAME, NUM_OF_EPS, LANGUAGE, RELEASE_DATE, COUNTRY_OF_ORIGIN, PH_ID, IMAGE_URL, TRAILER_URL) VALUES
('WS001', 'Stranger Things', 34, 'English', '2016-07-15', 'United States', 'PH001', 
    'https://image.tmdb.org/t/p/w500/x2LSRK2Cm7MZhjluni1msVJ3wDF.jpg', 
    'https://www.youtube.com/embed/b9EkMc79ZSU'),
('WS002', 'Game of Thrones', 73, 'English', '2011-04-17', 'United States', 'PH002',
    'https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg',
    'https://www.youtube.com/embed/KPLWWIOCOOQ'),
('WS003', 'Squid Game', 9, 'Korean', '2021-09-17', 'South Korea', 'PH001',
    'https://image.tmdb.org/t/p/w500/dDlEmu3EZ0Pgg93K2SVNLCjCSvE.jpg',
    'https://www.youtube.com/embed/oqxAJKy0ii4'),
('WS004', 'The Crown', 60, 'English', '2016-11-04', 'United Kingdom', 'PH001',
    'https://image.tmdb.org/t/p/w500/1M876KPjulVwppEpldhdc8V4o68.jpg',
    'https://www.youtube.com/embed/JWtnJjn6ng0'),
('WS005', 'Breaking Bad', 62, 'English', '2008-01-20', 'United States', 'PH005',
    'https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg',
    'https://www.youtube.com/embed/HhesaQXLnzU'),
('WS006', 'Dark', 26, 'German', '2017-12-01', 'Germany', 'PH001',
    'https://image.tmdb.org/t/p/w500/apbrbWs8M9lyOpJYU5WXrpFbk1Z.jpg',
    'https://www.youtube.com/embed/rrwycJ08PSA'),
('WS007', 'Money Heist', 41, 'Spanish', '2017-05-02', 'Spain', 'PH001',
    'https://image.tmdb.org/t/p/w500/reEMJA1uzscCbkpeRJeTT2bjqUp.jpg',
    'https://www.youtube.com/embed/_InqQJRqGW4'),
('WS008', 'Sherlock', 15, 'English', '2010-07-25', 'United Kingdom', 'PH003',
    'https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg',
    'https://www.youtube.com/embed/xK7S9mrFWL4'),
('WS009', 'The Witcher', 24, 'English', '2019-12-20', 'United States', 'PH001',
    'https://image.tmdb.org/t/p/w500/7vjaCdMw15FEbXyLQTVa04URsPm.jpg',
    'https://www.youtube.com/embed/ndl1W4ltcmg'),
('WS010', 'Bridgerton', 16, 'English', '2020-12-25', 'United States', 'PH001',
    'https://image.tmdb.org/t/p/w500/luoKpgVwi1E5nQsi7W0UuKHu2Rq.jpg',
    'https://www.youtube.com/embed/gpv7ayf_tyE');

-- ============================================================================
-- EPISODES
-- ============================================================================

-- Stranger Things Episodes (WS001)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP001', 'Chapter One: The Vanishing', 15400000, 'No', 'WS001'),
('EP002', 'Chapter Two: The Weirdo', 14200000, 'No', 'WS001'),
('EP003', 'Chapter Three: Holly Jolly', 13800000, 'No', 'WS001'),
('EP004', 'Chapter Four: The Body', 14500000, 'Yes', 'WS001');

-- Game of Thrones Episodes (WS002)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP005', 'Winter Is Coming', 2220000, 'No', 'WS002'),
('EP006', 'The Kingsroad', 2400000, 'No', 'WS002'),
('EP007', 'Lord Snow', 2500000, 'No', 'WS002'),
('EP008', 'The Long Night', 17800000, 'Yes', 'WS002');

-- Squid Game Episodes (WS003)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP009', 'Red Light Green Light', 111000000, 'No', 'WS003'),
('EP010', 'Hell', 95000000, 'No', 'WS003'),
('EP011', 'The Man with Umbrella', 87000000, 'No', 'WS003');

-- The Crown Episodes (WS004)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP012', 'Wolferton Splash', 3500000, 'No', 'WS004'),
('EP013', 'Hyde Park Corner', 3200000, 'No', 'WS004'),
('EP014', 'Windsor', 3100000, 'No', 'WS004');

-- Breaking Bad Episodes (WS005)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP015', 'Pilot', 1400000, 'No', 'WS005'),
('EP016', 'Cats in the Bag', 1500000, 'No', 'WS005'),
('EP017', 'Felina', 10280000, 'No', 'WS005');

-- Dark Episodes (WS006)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP018', 'Secrets', 8500000, 'No', 'WS006'),
('EP019', 'Lies', 9200000, 'No', 'WS006'),
('EP020', 'Past and Present', 10100000, 'No', 'WS006');

-- Money Heist Episodes (WS007)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP021', 'The Beginning', 15000000, 'No', 'WS007'),
('EP022', 'The Plan', 16500000, 'No', 'WS007'),
('EP023', 'The Heist', 18000000, 'No', 'WS007');

-- Sherlock Episodes (WS008)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP024', 'A Study in Pink', 12000000, 'No', 'WS008'),
('EP025', 'The Blind Banker', 11500000, 'No', 'WS008'),
('EP026', 'The Great Game', 13200000, 'No', 'WS008');

-- The Witcher Episodes (WS009)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP027', 'The End Begins', 22000000, 'No', 'WS009'),
('EP028', 'Four Marks', 20500000, 'No', 'WS009'),
('EP029', 'Betrayer Moon', 21800000, 'No', 'WS009');

-- Bridgerton Episodes (WS010)
INSERT INTO GRN_EPISODE (EP_ID, EP_NAME, TOTAL_VIEWERS, TECH_INTERRUPT, WS_ID) VALUES
('EP030', 'Diamond of the Season', 25000000, 'No', 'WS010'),
('EP031', 'Shock and Delight', 24500000, 'No', 'WS010'),
('EP032', 'Art of the Swoon', 26000000, 'No', 'WS010');

-- ============================================================================
-- WEB SERIES - TYPE ASSOCIATIONS
-- ============================================================================

INSERT INTO GRN_WS_WS_TYPE (WS_ID, WS_TYPE_ID) VALUES
('WS001', 'TYPE003'), -- Stranger Things - Thriller
('WS001', 'TYPE004'), -- Stranger Things - Sci-Fi
('WS001', 'TYPE005'), -- Stranger Things - Horror
('WS002', 'TYPE001'), -- Game of Thrones - Drama
('WS002', 'TYPE009'), -- Game of Thrones - Fantasy
('WS002', 'TYPE007'), -- Game of Thrones - Action
('WS003', 'TYPE001'), -- Squid Game - Drama
('WS003', 'TYPE003'), -- Squid Game - Thriller
('WS004', 'TYPE001'), -- The Crown - Drama
('WS004', 'TYPE008'), -- The Crown - Documentary
('WS005', 'TYPE001'), -- Breaking Bad - Drama
('WS005', 'TYPE010'), -- Breaking Bad - Crime
('WS005', 'TYPE003'), -- Breaking Bad - Thriller
('WS006', 'TYPE003'), -- Dark - Thriller
('WS006', 'TYPE004'), -- Dark - Sci-Fi
('WS007', 'TYPE007'), -- Money Heist - Action
('WS007', 'TYPE010'), -- Money Heist - Crime
('WS008', 'TYPE003'), -- Sherlock - Thriller
('WS008', 'TYPE010'), -- Sherlock - Crime
('WS009', 'TYPE009'), -- The Witcher - Fantasy
('WS009', 'TYPE007'), -- The Witcher - Action
('WS010', 'TYPE006'), -- Bridgerton - Romance
('WS010', 'TYPE001'); -- Bridgerton - Drama

-- ============================================================================
-- WEB SERIES - COUNTRY RELEASES
-- ============================================================================

INSERT INTO GRN_WS_COUNTRY (COUNTRY_RELEASE_DT, WS_ID, COUNTRY_ID) VALUES
('2016-07-15', 'WS001', 'CNT001'), -- Stranger Things - USA
('2016-07-15', 'WS001', 'CNT002'), -- Stranger Things - UK
('2016-07-16', 'WS001', 'CNT003'), -- Stranger Things - Canada
('2011-04-17', 'WS002', 'CNT001'), -- Game of Thrones - USA
('2011-04-18', 'WS002', 'CNT002'), -- Game of Thrones - UK
('2021-09-17', 'WS003', 'CNT001'), -- Squid Game - USA
('2021-09-17', 'WS003', 'CNT008'), -- Squid Game - South Korea
('2021-09-17', 'WS003', 'CNT007'), -- Squid Game - Japan
('2016-11-04', 'WS004', 'CNT001'), -- The Crown - USA
('2016-11-04', 'WS004', 'CNT002'), -- The Crown - UK
('2008-01-20', 'WS005', 'CNT001'), -- Breaking Bad - USA
('2017-12-01', 'WS006', 'CNT005'), -- Dark - Germany
('2017-12-01', 'WS006', 'CNT001'), -- Dark - USA
('2017-05-02', 'WS007', 'CNT001'), -- Money Heist - USA
('2010-07-25', 'WS008', 'CNT002'), -- Sherlock - UK
('2010-07-26', 'WS008', 'CNT001'), -- Sherlock - USA
('2019-12-20', 'WS009', 'CNT001'), -- The Witcher - USA
('2020-12-25', 'WS010', 'CNT001'), -- Bridgerton - USA
('2020-12-25', 'WS010', 'CNT002'); -- Bridgerton - UK

-- ============================================================================
-- WEB SERIES - DUBBING LANGUAGES
-- ============================================================================

INSERT INTO GRN_WEB_SERIES_DUBBING (WS_ID, LANG_ID) VALUES
('WS001', 'DUB001'), -- Stranger Things - English
('WS001', 'DUB002'), -- Stranger Things - Spanish
('WS001', 'DUB003'), -- Stranger Things - French
('WS002', 'DUB001'), -- Game of Thrones - English
('WS002', 'DUB002'), -- Game of Thrones - Spanish
('WS003', 'DUB006'), -- Squid Game - Korean
('WS003', 'DUB001'), -- Squid Game - English
('WS003', 'DUB005'), -- Squid Game - Japanese
('WS004', 'DUB001'), -- The Crown - English
('WS005', 'DUB001'), -- Breaking Bad - English
('WS005', 'DUB002'), -- Breaking Bad - Spanish
('WS006', 'DUB004'), -- Dark - German
('WS006', 'DUB001'), -- Dark - English
('WS007', 'DUB002'), -- Money Heist - Spanish
('WS007', 'DUB001'), -- Money Heist - English
('WS008', 'DUB001'), -- Sherlock - English
('WS009', 'DUB001'), -- The Witcher - English
('WS009', 'DUB007'), -- The Witcher - Portuguese
('WS010', 'DUB001'); -- Bridgerton - English

-- ============================================================================
-- WEB SERIES - SUBTITLE LANGUAGES
-- ============================================================================

INSERT INTO GRN_WS_SUB_LANG (WS_ID, LANG_ID) VALUES
('WS001', 'SUB001'), ('WS001', 'SUB002'), ('WS001', 'SUB003'),
('WS002', 'SUB001'), ('WS002', 'SUB002'), ('WS002', 'SUB004'),
('WS003', 'SUB001'), ('WS003', 'SUB006'), ('WS003', 'SUB005'),
('WS004', 'SUB001'), ('WS004', 'SUB002'),
('WS005', 'SUB001'), ('WS005', 'SUB002'),
('WS006', 'SUB001'), ('WS006', 'SUB004'),
('WS007', 'SUB001'), ('WS007', 'SUB002'),
('WS008', 'SUB001'),
('WS009', 'SUB001'), ('WS009', 'SUB007'),
('WS010', 'SUB001'), ('WS010', 'SUB002');

-- ============================================================================
-- CONTRACTS
-- ============================================================================

INSERT INTO GRN_CONTRACT (CONTRACT_ID, PER_EP_CHARGE, CONTRACT_ST_DATE, CONTRACT_END_DATE, WS_ID) VALUES
('CON001', 1500000.00, '2016-01-01', '2026-12-31', 'WS001'),
('CON002', 2000000.00, '2011-01-01', '2022-05-19', 'WS002'),
('CON003', 2500000.00, '2021-01-01', '2028-12-31', 'WS003'),
('CON004', 1800000.00, '2016-01-01', '2026-12-31', 'WS004'),
('CON005', 900000.00, '2008-01-01', '2018-09-29', 'WS005'),
('CON006', 1200000.00, '2017-01-01', '2024-07-01', 'WS006'),
('CON007', 1100000.00, '2017-01-01', '2025-12-03', 'WS007'),
('CON008', 1000000.00, '2010-01-01', '2024-01-01', 'WS008'),
('CON009', 2200000.00, '2019-01-01', '2029-12-31', 'WS009'),
('CON010', 1900000.00, '2020-01-01', '2030-12-31', 'WS010');

-- ============================================================================
-- SCHEDULES
-- ============================================================================

INSERT INTO GRN_SCHEDULE (SCHEDULE_ID, START_DT, END_DT, EP_ID) VALUES
('SCH001', '2024-01-01', '2024-01-07', 'EP001'),
('SCH002', '2024-01-08', '2024-01-14', 'EP002'),
('SCH003', '2024-01-15', '2024-01-21', 'EP003'),
('SCH004', '2024-01-01', '2024-01-07', 'EP005'),
('SCH005', '2024-01-01', '2024-01-07', 'EP009'),
('SCH006', '2024-01-08', '2024-01-14', 'EP010');

-- ============================================================================
-- USER ACCOUNTS (Customers and Admin for Demo)
-- ============================================================================

INSERT INTO GRN_USER_ACCOUNT (ACCOUNT_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME, EMAIL_ADDR, STREET_ADDR, CITY, STATE, POSTAL_CODE, COUNTRY, DATE_CREATED, MONTHLY_SUBSCRIPTION, COUNTRY_ID) VALUES
-- Admin/Employee Account
('ACC001', 'Admin', NULL, 'User', 'admin@streamingplatform.com', '100 Admin Street', 'New York', 'New York', '10001', 'United States', '2023-01-01 00:00:00', 0.00, 'CNT001'),
-- Customer Accounts
('ACC002', 'John', 'Michael', 'Smith', 'john.smith@email.com', '123 Main St', 'Los Angeles', 'California', '90001', 'United States', '2023-06-15 10:30:00', 15.99, 'CNT001'),
('ACC003', 'Emily', NULL, 'Johnson', 'emily.j@email.com', '456 Oak Ave', 'Chicago', 'Illinois', '60601', 'United States', '2023-07-20 14:45:00', 19.99, 'CNT001'),
('ACC004', 'David', 'James', 'Williams', 'david.w@email.com', '789 Pine Rd', 'London', 'England', 'SW1A1', 'United Kingdom', '2023-08-10 09:15:00', 12.99, 'CNT002'),
('ACC005', 'Sarah', NULL, 'Brown', 'sarah.b@email.com', '321 Elm St', 'Toronto', 'Ontario', 'M5V2T', 'Canada', '2023-09-05 16:20:00', 14.99, 'CNT003'),
('ACC006', 'Michael', 'Robert', 'Davis', 'michael.d@email.com', '654 Maple Dr', 'Sydney', 'NSW', '20001', 'Australia', '2023-10-12 11:00:00', 17.99, 'CNT004'),
('ACC007', 'Jessica', NULL, 'Miller', 'jessica.m@email.com', '987 Cedar Ln', 'Berlin', 'Berlin', '10115', 'Germany', '2023-11-01 08:30:00', 11.99, 'CNT005'),
('ACC008', 'Chris', 'Andrew', 'Wilson', 'chris.w@email.com', '147 Birch St', 'Paris', 'Ile-de-France', '75001', 'France', '2023-11-15 13:45:00', 13.99, 'CNT006'),
('ACC009', 'Ashley', NULL, 'Taylor', 'ashley.t@email.com', '258 Spruce Ave', 'Tokyo', 'Tokyo', '10000', 'Japan', '2023-12-01 10:00:00', 16.99, 'CNT007'),
('ACC010', 'Daniel', 'Lee', 'Anderson', 'daniel.a@email.com', '369 Walnut Rd', 'Seoul', 'Seoul', '03142', 'South Korea', '2024-01-10 15:30:00', 14.99, 'CNT008');

-- ============================================================================
-- LOGIN ACCOUNTS (Authentication Data)
-- Password for all accounts is: Password123
-- bcrypt hash of "Password123" with cost factor 12
-- ============================================================================

INSERT INTO GRN_LOGIN (LOGIN_ID, ACCOUNT_ID, USERNAME, PASSWORD_HASH, ROLE, CREATED_AT) VALUES
('LOG001', 'ACC001', 'admin', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'EMPLOYEE', '2023-01-01 00:00:00'),
('LOG002', 'ACC002', 'johnsmith', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2023-06-15 10:30:00'),
('LOG003', 'ACC003', 'emilyj', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2023-07-20 14:45:00'),
('LOG004', 'ACC004', 'davidw', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2023-08-10 09:15:00'),
('LOG005', 'ACC005', 'sarahb', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2023-09-05 16:20:00'),
('LOG006', 'ACC006', 'michaeld', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2023-10-12 11:00:00'),
('LOG007', 'ACC007', 'jessicam', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2023-11-01 08:30:00'),
('LOG008', 'ACC008', 'chrisw', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2023-11-15 13:45:00'),
('LOG009', 'ACC009', 'ashleyt', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2023-12-01 10:00:00'),
('LOG010', 'ACC010', 'daniela', '$2b$12$q2cOBg5O38mk7Uf2Qwr/fu18id.1zD3gBQWmSish2QxtQN1ot/cp2', 'CUSTOMER', '2024-01-10 15:30:00');

-- ============================================================================
-- FEEDBACK/RATINGS
-- ============================================================================

INSERT INTO GRN_FEEDBACK (RATING, FEEDBACK_TXT, DATE_RECORDED, WS_ID, ACCOUNT_ID) VALUES
(5, 'Absolutely loved this series! The storyline is captivating and the acting is superb. Cannot wait for the next season.', '2024-01-15 10:30:00', 'WS001', 'ACC002'),
(4, 'Great show with interesting plot twists. Some episodes were a bit slow but overall very enjoyable.', '2024-01-20 14:15:00', 'WS001', 'ACC003'),
(5, 'Best fantasy series ever made. The production quality is outstanding.', '2024-01-10 09:00:00', 'WS002', 'ACC002'),
(4, 'Excellent series but the ending could have been better. Still highly recommended.', '2024-01-25 16:45:00', 'WS002', 'ACC004'),
(5, 'Mind-blowing! This Korean drama exceeded all my expectations. A masterpiece.', '2024-02-01 11:30:00', 'WS003', 'ACC002'),
(5, 'Intense and thrilling from start to finish. One of the best shows I have seen.', '2024-02-05 13:00:00', 'WS003', 'ACC003'),
(4, 'Very unique concept. The tension keeps you hooked throughout.', '2024-02-10 08:45:00', 'WS003', 'ACC005'),
(5, 'Beautiful portrayal of the royal family. The costumes and sets are magnificent.', '2024-01-18 15:20:00', 'WS004', 'ACC004'),
(4, 'Informative and entertaining. Great historical drama.', '2024-01-22 10:00:00', 'WS004', 'ACC006'),
(5, 'A television masterpiece. Walter White is one of the greatest characters ever written.', '2024-01-12 14:30:00', 'WS005', 'ACC002'),
(5, 'Perfect from beginning to end. The character development is unmatched.', '2024-01-28 09:15:00', 'WS005', 'ACC003'),
(4, 'Complex and mind-bending. Requires your full attention but worth it.', '2024-02-08 16:00:00', 'WS006', 'ACC007'),
(5, 'Genius storytelling! The way everything connects is incredible.', '2024-02-12 11:45:00', 'WS006', 'ACC008'),
(4, 'Action-packed heist series. Very entertaining with great characters.', '2024-01-30 13:30:00', 'WS007', 'ACC005'),
(5, 'Benedict Cumberbatch is brilliant as Sherlock. Modern take on classic stories.', '2024-02-03 10:15:00', 'WS008', 'ACC004'),
(4, 'Good fantasy adaptation. Henry Cavill was perfect for the role.', '2024-02-06 15:00:00', 'WS009', 'ACC009'),
(3, 'Decent show but expected more from the source material.', '2024-02-09 08:30:00', 'WS009', 'ACC010'),
(5, 'Regency romance done right! Beautiful costumes and swoon-worthy moments.', '2024-02-11 12:00:00', 'WS010', 'ACC003'),
(4, 'Guilty pleasure viewing. Addictive drama with lovely aesthetics.', '2024-02-14 14:45:00', 'WS010', 'ACC006');

-- ============================================================================
-- VERIFY DATA LOADED
-- ============================================================================

SELECT 'Seed data loaded successfully!' AS STATUS;

SELECT 'GRN_COUNTRY' AS TABLE_NAME, COUNT(*) AS RECORD_COUNT FROM GRN_COUNTRY
UNION ALL SELECT 'GRN_SUBTITLE_LANGUAGE', COUNT(*) FROM GRN_SUBTITLE_LANGUAGE
UNION ALL SELECT 'GRN_WEB_SERIES_TYPE', COUNT(*) FROM GRN_WEB_SERIES_TYPE
UNION ALL SELECT 'GRN_DUBBING', COUNT(*) FROM GRN_DUBBING
UNION ALL SELECT 'GRN_PRODUCER', COUNT(*) FROM GRN_PRODUCER
UNION ALL SELECT 'GRN_PRODUCTION_HOUSE', COUNT(*) FROM GRN_PRODUCTION_HOUSE
UNION ALL SELECT 'GRN_USER_ACCOUNT', COUNT(*) FROM GRN_USER_ACCOUNT
UNION ALL SELECT 'GRN_LOGIN', COUNT(*) FROM GRN_LOGIN
UNION ALL SELECT 'GRN_WEB_SERIES', COUNT(*) FROM GRN_WEB_SERIES
UNION ALL SELECT 'GRN_EPISODE', COUNT(*) FROM GRN_EPISODE
UNION ALL SELECT 'GRN_CONTRACT', COUNT(*) FROM GRN_CONTRACT
UNION ALL SELECT 'GRN_SCHEDULE', COUNT(*) FROM GRN_SCHEDULE
UNION ALL SELECT 'GRN_FEEDBACK', COUNT(*) FROM GRN_FEEDBACK
UNION ALL SELECT 'GRN_PROD_PROD_HOUSE', COUNT(*) FROM GRN_PROD_PROD_HOUSE
UNION ALL SELECT 'GRN_WEB_SERIES_DUBBING', COUNT(*) FROM GRN_WEB_SERIES_DUBBING
UNION ALL SELECT 'GRN_WS_COUNTRY', COUNT(*) FROM GRN_WS_COUNTRY
UNION ALL SELECT 'GRN_WS_SUB_LANG', COUNT(*) FROM GRN_WS_SUB_LANG
UNION ALL SELECT 'GRN_WS_WS_TYPE', COUNT(*) FROM GRN_WS_WS_TYPE;
