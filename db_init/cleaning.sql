-- 1. CLEAN LAYER: Standardized data table structure
CREATE TABLE IF NOT EXISTS clean.annonces (
    id SERIAL PRIMARY KEY,
    category TEXT,
    title TEXT,
    price_dh NUMERIC,
    city TEXT,
    district TEXT,
    surface_m2 INTEGER,
    rooms INTEGER,
    bathrooms INTEGER,
    floor INTEGER,
    property_age_years INTEGER,
    price_per_m2 NUMERIC, 
    link TEXT UNIQUE,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Clean, Calculate IQR, and Insert in one flow
WITH parsed_data AS (
    -- Step A: Parse strings into numbers just ONCE
    SELECT 
        link,
        category,
        TRIM(title) AS title_clean,
        NULLIF(regexp_replace(price, '[^0-9]', '', 'g'), '')::NUMERIC AS price_val,
        SPLIT_PART(city, ',', 1) AS city_clean,
        NULLIF(surface, 'N/A')::INTEGER AS surf_val,
        NULLIF(rooms, 'N/A')::INTEGER AS rooms_val,
        NULLIF(bathrooms, 'N/A')::INTEGER AS bath_val,
        NULLIF(floor, 'N/A')::INTEGER AS floor_val,
        CASE WHEN build_year ~ '^\d{4}$' THEN 2026 - build_year::INTEGER ELSE NULL END AS age_val
    FROM staging.raw_annonces
),
stats AS (
    -- Step B: Calculate Q1 and Q3 for prices per category (ignoring rentals < 100,000 DH)
    SELECT 
        category,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY price_val) as q1,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY price_val) as q3
    FROM parsed_data
    WHERE price_val > 100000 
    GROUP BY category
),
fences AS (
    -- Step C: Calculate the IQR Bounds (1.5 multiplier)
    SELECT 
        category,
        (q1 - 1.5 * (q3 - q1)) as lower_bound,
        (q3 + 1.5 * (q3 - q1)) as upper_bound
    FROM stats
)
-- Step D: Insert the filtered data into the final table
INSERT INTO clean.annonces (
    category, title, price_dh, city, surface_m2, rooms, bathrooms, floor, property_age_years, price_per_m2, link
)
SELECT 
    p.category, 
    p.title_clean, 
    p.price_val, 
    p.city_clean, 
    p.surf_val, 
    p.rooms_val, 
    p.bath_val, 
    p.floor_val, 
    p.age_val,
    (p.price_val / p.surf_val) AS price_per_m2,
    p.link
FROM parsed_data p
JOIN fences f ON p.category = f.category
WHERE 
    -- 1. Must have valid price and surface to do math
    p.price_val IS NOT NULL 
    AND p.surf_val IS NOT NULL 
    AND p.surf_val > 0
    
    -- 2. Hard Floor: Filter out monthly rentals
    AND p.price_val > 100000 
    
    -- 3. IQR Anomaly Filter: Price must be inside the "normal" bounds for its category
    AND p.price_val BETWEEN f.lower_bound AND f.upper_bound
    
    -- 4. Category-Specific Surface Safety Nets
    AND CASE 
        WHEN p.category = 'Appartement' THEN p.surf_val BETWEEN 20 AND 1000
        WHEN p.category = 'Villa_Riad' THEN p.surf_val > 80
        WHEN p.category = 'Terrain_Ferme' THEN p.surf_val > 50
        WHEN p.category IN ('Bureau_Plateau', 'Commerce') THEN p.surf_val > 10
        ELSE TRUE
    END
ON CONFLICT (link) DO NOTHING;

-- 3. LOGGING FEATURE: See what survived!
SELECT 
    category, 
    COUNT(*) as clean_listings_kept,
    ROUND(AVG(price_dh), 0) as avg_price,
    ROUND(AVG(price_per_m2), 0) as avg_price_per_m2
FROM clean.annonces 
GROUP BY category
ORDER BY clean_listings_kept DESC;