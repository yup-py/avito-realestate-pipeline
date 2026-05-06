-- 1. CLEAN LAYER: Standardized data table structure
CREATE TABLE IF NOT EXISTS clean.annonces (
    id SERIAL PRIMARY KEY,
    category TEXT,
    title TEXT,
    price_dh NUMERIC,
    city TEXT,
    district TEXT, --
    surface_m2 INTEGER,
    rooms INTEGER,
    bathrooms INTEGER,
    floor INTEGER,
    property_age_years INTEGER,
    price_per_m2 NUMERIC, 
    announcement_date DATE, 
    link TEXT UNIQUE,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Clean, Calculate IQR, and Insert in one flow
WITH parsed_data AS (
    SELECT 
        link,
        category,
        -- Keep title clean by removing phone numbers
        REGEXP_REPLACE(TRIM(title), '\d{10}', '[PHONE_REDACTED]', 'g') AS title_clean,

        -- Handle dynamic date strings
        CASE 
            WHEN date_posted ILIKE '%%minute%%' OR date_posted ILIKE '%%heure%%' THEN CURRENT_DATE
            WHEN date_posted ILIKE '%%jour%%' THEN 
                CURRENT_DATE - (NULLIF(regexp_replace(date_posted, '[^0-9]', '', 'g'), '')::INT * INTERVAL '1 day')
            WHEN date_posted ILIKE '%%mois%%' THEN 
                CURRENT_DATE - (NULLIF(regexp_replace(date_posted, '[^0-9]', '', 'g'), '')::INT * INTERVAL '1 month')
            WHEN date_posted ~ '^\d{1,2} [[:alpha:]]+' THEN 
                TO_DATE(date_posted || ' ' || EXTRACT(YEAR FROM CURRENT_DATE), 'DD Month YYYY')
            ELSE CURRENT_DATE
        END AS date_val,

        NULLIF(regexp_replace(price, '[^0-9]', '', 'g'), '')::NUMERIC AS price_val,
        city AS city_clean,
        district AS district_clean, -- Added: Directly from staging
        NULLIF(surface, 'N/A')::INTEGER AS surf_val,
        NULLIF(rooms, 'N/A')::INTEGER AS rooms_val,
        NULLIF(bathrooms, 'N/A')::INTEGER AS bath_val,
        NULLIF(floor, 'N/A')::INTEGER AS floor_val,
        CASE WHEN build_year ~ '^\d{4}$' THEN 2026 - build_year::INTEGER ELSE NULL END AS age_val
    FROM staging.raw_annonces
),
stats AS (
    SELECT 
        category,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY price_val) as q1,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY price_val) as q3
    FROM parsed_data
    WHERE price_val > 100000 
    GROUP BY category
),
fences AS (
    SELECT 
        category,
        (q1 - 1.5 * (q3 - q1)) as lower_bound,
        (q3 + 1.5 * (q3 - q1)) as upper_bound
    FROM stats
)
INSERT INTO clean.annonces (
    category, title, price_dh, city, district, surface_m2, rooms, bathrooms, 
    floor, property_age_years, price_per_m2, announcement_date, link
)
SELECT 
    p.category, 
    p.title_clean, 
    p.price_val, 
    p.city_clean, 
    p.district_clean, -- Added to the insert[cite: 4]
    p.surf_val, 
    p.rooms_val, 
    p.bath_val, 
    p.floor_val, 
    p.age_val,
    (p.price_val / p.surf_val) AS price_per_m2,
    p.date_val,
    p.link
FROM parsed_data p
JOIN fences f ON p.category = f.category
WHERE 
    -- 1. Validity Check
    p.price_val IS NOT NULL 
    AND p.surf_val IS NOT NULL 
    AND p.surf_val > 0
    AND p.date_val IS NOT NULL
    -- 2. Price Floor
    AND p.price_val > 100000 
    -- 3. Anomaly Filtering
    AND p.price_val BETWEEN f.lower_bound AND f.upper_bound
    -- 4. Category-Specific Logic[cite: 4]
    AND CASE 
        WHEN p.category = 'Appartement' THEN p.surf_val BETWEEN 20 AND 1000
        WHEN p.category = 'Villa_Riad' THEN p.surf_val > 80
        WHEN p.category = 'Terrain_Ferme' THEN p.surf_val > 50
        WHEN p.category IN ('Bureau_Plateau', 'Commerce') THEN p.surf_val > 10
        ELSE TRUE
    END
ON CONFLICT (link) DO NOTHING;

-- 3. LOGGING
SELECT 
    city,
    district,
    COUNT(*) as listings_count,
    ROUND(AVG(price_per_m2), 0) as avg_price_m2
FROM clean.annonces 
GROUP BY city, district
ORDER BY listings_count DESC;