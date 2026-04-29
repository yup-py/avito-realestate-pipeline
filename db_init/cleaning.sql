-- 4. CLEAN LAYER: Standardized data
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

INSERT INTO clean.annonces (category, title, price_dh, city, surface_m2, rooms, bathrooms, floor, property_age_years, price_per_m2, link)
SELECT 
    category,
    TRIM(title),
    NULLIF(regexp_replace(price, '[^0-9]', '', 'g'), '')::NUMERIC as price_val,
    SPLIT_PART(city, ',', 1), 
    NULLIF(surface, 'N/A')::INTEGER as surf_val,
    NULLIF(rooms, 'N/A')::INTEGER,
    NULLIF(bathrooms, 'N/A')::INTEGER,
    NULLIF(floor, 'N/A')::INTEGER,
    CASE WHEN build_year ~ '^\d{4}$' THEN 2026 - build_year::INTEGER ELSE NULL END,
    CASE 
        WHEN NULLIF(surface, 'N/A')::INTEGER > 0 
        THEN NULLIF(regexp_replace(price, '[^0-9]', '', 'g'), '')::NUMERIC / NULLIF(surface, 'N/A')::INTEGER 
        ELSE NULL 
    END,
    link
FROM staging.raw_annonces
WHERE 
    -- 1. Must have a price and surface
    NULLIF(regexp_replace(price, '[^0-9]', '', 'g'), '') IS NOT NULL
    AND NULLIF(surface, 'N/A') IS NOT NULL
    
    -- 2. Logic: Price per m2 must be "Human"
    -- This removes a 1 DH price or a 1 Billion DH price mistake.
    AND (
        (NULLIF(regexp_replace(price, '[^0-9]', '', 'g'), '')::NUMERIC / NULLIF(surface, 'N/A')::INTEGER) 
        BETWEEN 100 AND 100000 
    )

    -- 3. Category Specific Logic
    AND NOT (category = 'Appartement' AND NULLIF(surface, 'N/A')::INTEGER > 1000) -- No 1000m2 apartments
    AND NOT (category = 'Terrain_Ferme' AND NULLIF(surface, 'N/A')::INTEGER < 50) -- No 20m2 farms
ON CONFLICT (link) DO NOTHING;