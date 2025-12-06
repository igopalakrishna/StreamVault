-- ============================================================================
-- CS-GY 6083 - Project Part II
-- Business Analysis SQL Queries (Q1-Q6)
-- 
-- This file contains 6 advanced SQL queries demonstrating:
-- - Multi-table joins
-- - Subqueries (multi-row and correlated)
-- - SET operators
-- - CTEs/inline views
-- - TOP-N/BOTTOM-N queries
-- ============================================================================

-- ============================================================================
-- Q1: JOIN WITH AT LEAST 3 TABLES
-- Business Question: For each web series, show the production house, 
-- countries where it's available, and average rating.
-- ============================================================================

-- A1) SELECT Statement:
SELECT 
    ws.WS_ID,
    ws.WS_NAME,
    ws.LANGUAGE,
    ws.COUNTRY_OF_ORIGIN,
    ph.PH_NAME AS PRODUCTION_HOUSE,
    ph.YEAR_ESTABLISHED,
    GROUP_CONCAT(DISTINCT c.COUNTRY_NAME ORDER BY c.COUNTRY_NAME SEPARATOR ', ') AS AVAILABLE_COUNTRIES,
    COUNT(DISTINCT wsc.COUNTRY_ID) AS NUM_COUNTRIES,
    COALESCE(ROUND(AVG(f.RATING), 2), 0) AS AVG_RATING,
    COUNT(DISTINCT f.ACCOUNT_ID) AS NUM_RATINGS
FROM GRN_WEB_SERIES ws
JOIN GRN_PRODUCTION_HOUSE ph ON ws.PH_ID = ph.PH_ID
LEFT JOIN GRN_WS_COUNTRY wsc ON ws.WS_ID = wsc.WS_ID
LEFT JOIN GRN_COUNTRY c ON wsc.COUNTRY_ID = c.COUNTRY_ID
LEFT JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
GROUP BY ws.WS_ID, ws.WS_NAME, ws.LANGUAGE, ws.COUNTRY_OF_ORIGIN, 
         ph.PH_NAME, ph.YEAR_ESTABLISHED
ORDER BY AVG_RATING DESC, NUM_COUNTRIES DESC;

-- A2) Sample Result:
-- +--------+----------------+----------+------------------+------------------+------------------+----------------------------------+--------------+------------+-------------+
-- | WS_ID  | WS_NAME        | LANGUAGE | COUNTRY_OF_ORIGIN| PRODUCTION_HOUSE | YEAR_ESTABLISHED | AVAILABLE_COUNTRIES              | NUM_COUNTRIES| AVG_RATING | NUM_RATINGS |
-- +--------+----------------+----------+------------------+------------------+------------------+----------------------------------+--------------+------------+-------------+
-- | WS003  | Squid Game     | Korean   | South Korea      | Netflix Studios  | 2013             | Japan, South Korea, United States| 3            | 4.67       | 3           |
-- | WS005  | Breaking Bad   | English  | United States    | Amazon MGM       | 2010             | United States                    | 1            | 5.00       | 2           |
-- | WS001  | Stranger Things| English  | United States    | Netflix Studios  | 2013             | Canada, United Kingdom, USA      | 3            | 4.50       | 2           |
-- +--------+----------------+----------+------------------+------------------+------------------+----------------------------------+--------------+------------+-------------+

-- A3) Business Explanation:
-- This query helps content strategists understand the relationship between 
-- production houses and content performance. It shows which productions are 
-- reaching the most countries and maintaining high ratings, enabling decisions
-- about partnership renewals and regional expansion.


-- ============================================================================
-- Q2: MULTI-ROW SUBQUERY
-- Business Question: Find series that have higher average rating than 
-- the overall average rating across all series.
-- ============================================================================

-- A1) SELECT Statement:
SELECT 
    ws.WS_ID,
    ws.WS_NAME,
    ws.LANGUAGE,
    ROUND(AVG(f.RATING), 2) AS SERIES_AVG_RATING,
    COUNT(f.ACCOUNT_ID) AS NUM_RATINGS,
    (SELECT ROUND(AVG(RATING), 2) FROM GRN_FEEDBACK) AS OVERALL_AVG_RATING
FROM GRN_WEB_SERIES ws
JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
GROUP BY ws.WS_ID, ws.WS_NAME, ws.LANGUAGE
HAVING AVG(f.RATING) > (
    SELECT AVG(RATING) 
    FROM GRN_FEEDBACK
)
ORDER BY SERIES_AVG_RATING DESC;

-- A2) Sample Result:
-- +--------+----------------+----------+-------------------+-------------+--------------------+
-- | WS_ID  | WS_NAME        | LANGUAGE | SERIES_AVG_RATING | NUM_RATINGS | OVERALL_AVG_RATING |
-- +--------+----------------+----------+-------------------+-------------+--------------------+
-- | WS005  | Breaking Bad   | English  | 5.00              | 2           | 4.42               |
-- | WS006  | Dark           | German   | 4.50              | 2           | 4.42               |
-- | WS003  | Squid Game     | Korean   | 4.67              | 3           | 4.42               |
-- | WS010  | Bridgerton     | English  | 4.50              | 2           | 4.42               |
-- +--------+----------------+----------+-------------------+-------------+--------------------+

-- A3) Business Explanation:
-- This query identifies top-performing content that exceeds platform average.
-- Marketing teams can use this to highlight "Above Average" series in promotions,
-- while content teams can analyze what makes these series successful.


-- ============================================================================
-- Q3: CORRELATED SUBQUERY
-- Business Question: For each country, find the web series with the 
-- maximum total viewers available in that country.
-- ============================================================================

-- A1) SELECT Statement:
SELECT 
    c.COUNTRY_ID,
    c.COUNTRY_NAME,
    ws.WS_ID,
    ws.WS_NAME,
    series_viewers.TOTAL_VIEWERS
FROM GRN_COUNTRY c
JOIN GRN_WS_COUNTRY wsc ON c.COUNTRY_ID = wsc.COUNTRY_ID
JOIN GRN_WEB_SERIES ws ON wsc.WS_ID = ws.WS_ID
JOIN (
    SELECT e.WS_ID, SUM(e.TOTAL_VIEWERS) AS TOTAL_VIEWERS
    FROM GRN_EPISODE e
    GROUP BY e.WS_ID
) series_viewers ON ws.WS_ID = series_viewers.WS_ID
WHERE series_viewers.TOTAL_VIEWERS = (
    -- Correlated subquery: find max viewers for series in THIS country
    SELECT MAX(sv2.TOTAL_VIEWERS)
    FROM GRN_WS_COUNTRY wsc2
    JOIN (
        SELECT e2.WS_ID, SUM(e2.TOTAL_VIEWERS) AS TOTAL_VIEWERS
        FROM GRN_EPISODE e2
        GROUP BY e2.WS_ID
    ) sv2 ON wsc2.WS_ID = sv2.WS_ID
    WHERE wsc2.COUNTRY_ID = c.COUNTRY_ID
)
ORDER BY series_viewers.TOTAL_VIEWERS DESC;

-- A2) Sample Result:
-- +------------+--------------+--------+-----------------+---------------+
-- | COUNTRY_ID | COUNTRY_NAME | WS_ID  | WS_NAME         | TOTAL_VIEWERS |
-- +------------+--------------+--------+-----------------+---------------+
-- | CNT008     | South Korea  | WS003  | Squid Game      | 293000000     |
-- | CNT007     | Japan        | WS003  | Squid Game      | 293000000     |
-- | CNT001     | United States| WS003  | Squid Game      | 293000000     |
-- | CNT002     | United Kingdom| WS001 | Stranger Things | 57900000      |
-- | CNT005     | Germany      | WS006  | Dark            | (viewers)     |
-- +------------+--------------+--------+-----------------+---------------+

-- A3) Business Explanation:
-- This query identifies the most popular content in each geographic market.
-- Regional managers can use this to understand what drives viewership in their
-- territory and optimize content recommendations and marketing spend accordingly.


-- ============================================================================
-- Q4: SET OPERATOR (UNION)
-- Business Question: Compare series available in North America (USA/Canada) 
-- versus series available in Europe (UK/Germany/France).
-- ============================================================================

-- A1) SELECT Statement:
-- Series available ONLY in North America
SELECT 
    'North America Only' AS REGION_AVAILABILITY,
    ws.WS_ID,
    ws.WS_NAME,
    ws.LANGUAGE
FROM GRN_WEB_SERIES ws
WHERE ws.WS_ID IN (
    SELECT WS_ID FROM GRN_WS_COUNTRY WHERE COUNTRY_ID IN ('CNT001', 'CNT003')
)
AND ws.WS_ID NOT IN (
    SELECT WS_ID FROM GRN_WS_COUNTRY WHERE COUNTRY_ID IN ('CNT002', 'CNT005', 'CNT006')
)

UNION

-- Series available ONLY in Europe
SELECT 
    'Europe Only' AS REGION_AVAILABILITY,
    ws.WS_ID,
    ws.WS_NAME,
    ws.LANGUAGE
FROM GRN_WEB_SERIES ws
WHERE ws.WS_ID IN (
    SELECT WS_ID FROM GRN_WS_COUNTRY WHERE COUNTRY_ID IN ('CNT002', 'CNT005', 'CNT006')
)
AND ws.WS_ID NOT IN (
    SELECT WS_ID FROM GRN_WS_COUNTRY WHERE COUNTRY_ID IN ('CNT001', 'CNT003')
)

UNION

-- Series available in BOTH regions
SELECT 
    'Both Regions' AS REGION_AVAILABILITY,
    ws.WS_ID,
    ws.WS_NAME,
    ws.LANGUAGE
FROM GRN_WEB_SERIES ws
WHERE ws.WS_ID IN (
    SELECT WS_ID FROM GRN_WS_COUNTRY WHERE COUNTRY_ID IN ('CNT001', 'CNT003')
)
AND ws.WS_ID IN (
    SELECT WS_ID FROM GRN_WS_COUNTRY WHERE COUNTRY_ID IN ('CNT002', 'CNT005', 'CNT006')
)
ORDER BY REGION_AVAILABILITY, WS_NAME;

-- A2) Sample Result:
-- +---------------------+--------+-----------------+----------+
-- | REGION_AVAILABILITY | WS_ID  | WS_NAME         | LANGUAGE |
-- +---------------------+--------+-----------------+----------+
-- | Both Regions        | WS001  | Stranger Things | English  |
-- | Both Regions        | WS006  | Dark            | German   |
-- | Europe Only         | WS008  | Sherlock        | English  |
-- | North America Only  | WS005  | Breaking Bad    | English  |
-- | North America Only  | WS003  | Squid Game      | Korean   |
-- +---------------------+--------+-----------------+----------+

-- A3) Business Explanation:
-- This query supports content licensing decisions by showing regional content
-- distribution gaps. Business development teams can identify expansion 
-- opportunities where popular content isn't yet available in certain regions.


-- ============================================================================
-- Q5: IN-LINE VIEW / WITH CLAUSE (CTE)
-- Business Question: Compute per-series performance metrics and identify 
-- series that are both highly rated AND have high viewership.
-- ============================================================================

-- A1) SELECT Statement:
WITH SeriesMetrics AS (
    -- CTE 1: Calculate comprehensive metrics for each series
    SELECT 
        ws.WS_ID,
        ws.WS_NAME,
        ws.LANGUAGE,
        ws.NUM_OF_EPS AS PLANNED_EPISODES,
        COUNT(DISTINCT e.EP_ID) AS ACTUAL_EPISODES,
        COALESCE(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS,
        COALESCE(AVG(e.TOTAL_VIEWERS), 0) AS AVG_VIEWERS_PER_EP
    FROM GRN_WEB_SERIES ws
    LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
    GROUP BY ws.WS_ID, ws.WS_NAME, ws.LANGUAGE, ws.NUM_OF_EPS
),
RatingMetrics AS (
    -- CTE 2: Calculate rating metrics
    SELECT 
        WS_ID,
        AVG(RATING) AS AVG_RATING,
        COUNT(*) AS RATING_COUNT,
        MAX(RATING) AS MAX_RATING,
        MIN(RATING) AS MIN_RATING
    FROM GRN_FEEDBACK
    GROUP BY WS_ID
),
PercentileCalc AS (
    -- CTE 3: Calculate percentile ranks
    SELECT 
        sm.WS_ID,
        sm.TOTAL_VIEWERS,
        rm.AVG_RATING,
        PERCENT_RANK() OVER (ORDER BY sm.TOTAL_VIEWERS) AS VIEWER_PERCENTILE,
        PERCENT_RANK() OVER (ORDER BY rm.AVG_RATING) AS RATING_PERCENTILE
    FROM SeriesMetrics sm
    LEFT JOIN RatingMetrics rm ON sm.WS_ID = rm.WS_ID
    WHERE rm.AVG_RATING IS NOT NULL
)
-- Final query: Identify high performers (top 50% in both metrics)
SELECT 
    sm.WS_ID,
    sm.WS_NAME,
    sm.LANGUAGE,
    sm.ACTUAL_EPISODES,
    FORMAT(sm.TOTAL_VIEWERS, 0) AS TOTAL_VIEWERS,
    ROUND(sm.AVG_VIEWERS_PER_EP, 0) AS AVG_VIEWERS_PER_EP,
    ROUND(rm.AVG_RATING, 2) AS AVG_RATING,
    rm.RATING_COUNT,
    ROUND(pc.VIEWER_PERCENTILE * 100, 1) AS VIEWER_PERCENTILE,
    ROUND(pc.RATING_PERCENTILE * 100, 1) AS RATING_PERCENTILE,
    CASE 
        WHEN pc.VIEWER_PERCENTILE >= 0.5 AND pc.RATING_PERCENTILE >= 0.5 
        THEN 'TOP PERFORMER'
        WHEN pc.VIEWER_PERCENTILE >= 0.5 
        THEN 'HIGH VIEWERSHIP'
        WHEN pc.RATING_PERCENTILE >= 0.5 
        THEN 'HIGH RATING'
        ELSE 'DEVELOPING'
    END AS PERFORMANCE_TIER
FROM SeriesMetrics sm
JOIN RatingMetrics rm ON sm.WS_ID = rm.WS_ID
JOIN PercentileCalc pc ON sm.WS_ID = pc.WS_ID
ORDER BY (pc.VIEWER_PERCENTILE + pc.RATING_PERCENTILE) DESC;

-- A2) Sample Result:
-- +--------+-----------------+----------+---------+---------------+--------------------+------------+--------------+-------------------+-------------------+-----------------+
-- | WS_ID  | WS_NAME         | LANGUAGE | ACTUAL_EP| TOTAL_VIEWERS | AVG_VIEWERS_PER_EP | AVG_RATING | RATING_COUNT | VIEWER_PERCENTILE | RATING_PERCENTILE | PERFORMANCE_TIER|
-- +--------+-----------------+----------+---------+---------------+--------------------+------------+--------------+-------------------+-------------------+-----------------+
-- | WS003  | Squid Game      | Korean   | 3       | 293,000,000   | 97666667           | 4.67       | 3            | 100.0             | 87.5              | TOP PERFORMER   |
-- | WS005  | Breaking Bad    | English  | 3       | 13,180,000    | 4393333            | 5.00       | 2            | 50.0              | 100.0             | TOP PERFORMER   |
-- | WS001  | Stranger Things | English  | 4       | 57,900,000    | 14475000           | 4.50       | 2            | 75.0              | 50.0              | TOP PERFORMER   |
-- | WS002  | Game of Thrones | English  | 4       | 24,920,000    | 6230000            | 4.50       | 2            | 62.5              | 50.0              | TOP PERFORMER   |
-- +--------+-----------------+----------+---------+---------------+--------------------+------------+--------------+-------------------+-------------------+-----------------+

-- A3) Business Explanation:
-- This advanced analytics query combines multiple metrics using CTEs to create
-- a comprehensive performance scorecard. Product managers can use this to
-- identify content for flagship promotions, renewal priority, and benchmarking.


-- ============================================================================
-- Q6: TOP-N / BOTTOM-N QUERY
-- Business Question: Find the top 5 series by total viewers and 
-- bottom 5 series by average rating.
-- ============================================================================

-- A1) SELECT Statement - TOP 5 by viewers:
SELECT 
    'TOP 5 BY VIEWERS' AS CATEGORY,
    ws.WS_ID,
    ws.WS_NAME,
    ws.LANGUAGE,
    FORMAT(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS,
    COALESCE(ROUND(AVG(f.RATING), 2), 0) AS AVG_RATING
FROM GRN_WEB_SERIES ws
LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
LEFT JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
GROUP BY ws.WS_ID, ws.WS_NAME, ws.LANGUAGE
ORDER BY SUM(e.TOTAL_VIEWERS) DESC
LIMIT 5;

-- A1) SELECT Statement - BOTTOM 5 by rating:
SELECT 
    'BOTTOM 5 BY RATING' AS CATEGORY,
    ws.WS_ID,
    ws.WS_NAME,
    ws.LANGUAGE,
    FORMAT(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS,
    ROUND(AVG(f.RATING), 2) AS AVG_RATING
FROM GRN_WEB_SERIES ws
JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
GROUP BY ws.WS_ID, ws.WS_NAME, ws.LANGUAGE
HAVING COUNT(f.ACCOUNT_ID) >= 1
ORDER BY AVG(f.RATING) ASC
LIMIT 5;

-- Combined query using UNION:
(
    SELECT 
        'TOP 5 BY VIEWERS' AS CATEGORY,
        RANK() OVER (ORDER BY SUM(e.TOTAL_VIEWERS) DESC) AS RANK_NUM,
        ws.WS_ID,
        ws.WS_NAME,
        FORMAT(COALESCE(SUM(e.TOTAL_VIEWERS), 0), 0) AS METRIC_VALUE
    FROM GRN_WEB_SERIES ws
    LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
    GROUP BY ws.WS_ID, ws.WS_NAME
    ORDER BY SUM(e.TOTAL_VIEWERS) DESC
    LIMIT 5
)
UNION ALL
(
    SELECT 
        'BOTTOM 5 BY RATING' AS CATEGORY,
        RANK() OVER (ORDER BY AVG(f.RATING) ASC) AS RANK_NUM,
        ws.WS_ID,
        ws.WS_NAME,
        CAST(ROUND(AVG(f.RATING), 2) AS CHAR) AS METRIC_VALUE
    FROM GRN_WEB_SERIES ws
    JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
    GROUP BY ws.WS_ID, ws.WS_NAME
    ORDER BY AVG(f.RATING) ASC
    LIMIT 5
);

-- A2) Sample Result:
-- +--------------------+----------+--------+-----------------+--------------+
-- | CATEGORY           | RANK_NUM | WS_ID  | WS_NAME         | METRIC_VALUE |
-- +--------------------+----------+--------+-----------------+--------------+
-- | TOP 5 BY VIEWERS   | 1        | WS003  | Squid Game      | 293,000,000  |
-- | TOP 5 BY VIEWERS   | 2        | WS001  | Stranger Things | 57,900,000   |
-- | TOP 5 BY VIEWERS   | 3        | WS002  | Game of Thrones | 24,920,000   |
-- | TOP 5 BY VIEWERS   | 4        | WS005  | Breaking Bad    | 13,180,000   |
-- | TOP 5 BY VIEWERS   | 5        | WS004  | The Crown       | 9,800,000    |
-- | BOTTOM 5 BY RATING | 1        | WS009  | The Witcher     | 3.50         |
-- | BOTTOM 5 BY RATING | 2        | WS007  | Money Heist     | 4.00         |
-- | BOTTOM 5 BY RATING | 3        | WS002  | Game of Thrones | 4.50         |
-- | BOTTOM 5 BY RATING | 4        | WS004  | The Crown       | 4.50         |
-- | BOTTOM 5 BY RATING | 5        | WS001  | Stranger Things | 4.50         |
-- +--------------------+----------+--------+-----------------+--------------+

-- A3) Business Explanation:
-- This query provides executive dashboards with key performance extremes.
-- Leadership can quickly identify both star performers for investment and
-- underperforming content that may need improvement or discontinuation.
-- The contrast between high-viewership and low-rating content reveals
-- shows that may be popular but critically divisive.


-- ============================================================================
-- BONUS: ADDITIONAL ANALYTICS QUERIES
-- ============================================================================

-- Monthly Feedback Trend Analysis
SELECT 
    DATE_FORMAT(DATE_RECORDED, '%Y-%m') AS MONTH,
    COUNT(*) AS FEEDBACK_COUNT,
    ROUND(AVG(RATING), 2) AS AVG_RATING,
    SUM(CASE WHEN RATING >= 4 THEN 1 ELSE 0 END) AS POSITIVE_COUNT,
    ROUND(SUM(CASE WHEN RATING >= 4 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS POSITIVE_PCT
FROM GRN_FEEDBACK
GROUP BY DATE_FORMAT(DATE_RECORDED, '%Y-%m')
ORDER BY MONTH;

-- Production House Performance Comparison
SELECT 
    ph.PH_NAME,
    COUNT(DISTINCT ws.WS_ID) AS SERIES_COUNT,
    FORMAT(SUM(e.TOTAL_VIEWERS), 0) AS TOTAL_VIEWERS,
    ROUND(AVG(f.RATING), 2) AS AVG_RATING,
    SUM(c.PER_EP_CHARGE * ws.NUM_OF_EPS) AS TOTAL_CONTRACT_VALUE
FROM GRN_PRODUCTION_HOUSE ph
LEFT JOIN GRN_WEB_SERIES ws ON ph.PH_ID = ws.PH_ID
LEFT JOIN GRN_EPISODE e ON ws.WS_ID = e.WS_ID
LEFT JOIN GRN_FEEDBACK f ON ws.WS_ID = f.WS_ID
LEFT JOIN GRN_CONTRACT c ON ws.WS_ID = c.WS_ID
GROUP BY ph.PH_ID, ph.PH_NAME
ORDER BY SUM(e.TOTAL_VIEWERS) DESC;
