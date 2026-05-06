
-- REAL ESTATE PIPELINE VALIDATION SUITE

-- 1. RECORD COUNT CONSISTENCY
-- Purpose: Ensure no data loss between cleaning and warehouse layers.
SELECT 'Clean Layer' as layer, COUNT(*) FROM clean.annonces
UNION ALL
SELECT 'Fact Table' as layer, COUNT(*) FROM bi_schema.fact_annonces;

-- 2. LOCALISATION INTEGRITY
-- Purpose: Check for "Unknown" districts to assess scraping quality.
SELECT 
    city, 
    COUNT(*) as total_listings,
    SUM(CASE WHEN district = 'Unknown' THEN 1 ELSE 0 END) as unknown_districts,
    ROUND(AVG(CASE WHEN district = 'Unknown' THEN 1 ELSE 0 END) * 100, 2) || '%' as missing_rate
FROM bi_schema.fact_annonces
GROUP BY city
ORDER BY total_listings DESC;

-- 3. ORPHANED RECORDS CHECK
-- Purpose: Ensure every fact has a matching dimension (Critical for Power BI).
-- This result should be 0.
SELECT COUNT(*) as orphaned_records
FROM bi_schema.fact_annonces f
LEFT JOIN bi_schema.dim_localisation d 
    ON f.city = d.city AND f.district = d.district
WHERE d.city IS NULL;

-- 4. PRICE SANITY CHECK
-- Purpose: Ensure IQR filtering worked and OBT/Fact tables are aligned.
SELECT 
    'Fact Table' as source, 
    MIN(price_dh) as min_p, 
    MAX(price_dh) as max_p, 
    ROUND(AVG(price_dh), 2) as avg_p 
FROM bi_schema.fact_annonces
UNION ALL
SELECT 
    'ML OBT' as source, 
    MIN(price_dh), 
    MAX(price_dh), 
    ROUND(AVG(price_dh), 2) 
FROM ml_schema.obt_annonces;