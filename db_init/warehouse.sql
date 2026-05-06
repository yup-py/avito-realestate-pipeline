-- 5. BI SCHEMA: Star Schema (Fact and Dimensions)

-- A. Create structures if they don't exist
CREATE TABLE IF NOT EXISTS bi_schema.dim_localisation (
    city TEXT,
    district TEXT,
    PRIMARY KEY (city, district)
);

CREATE TABLE IF NOT EXISTS bi_schema.dim_temps (
    date_key INTEGER PRIMARY KEY,
    full_date DATE,
    year NUMERIC,
    month NUMERIC,
    month_name TEXT
);

CREATE TABLE IF NOT EXISTS bi_schema.dim_categories (
    category_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bi_schema.fact_annonces (
    id INTEGER PRIMARY KEY,
    date_key INTEGER,
    category TEXT,
    price_dh NUMERIC,
    city TEXT,
    district TEXT,
    surface_m2 INTEGER
);

-- B. Load Dimensions
-- Using COALESCE to handle NULL districts (e.g., Bouznika)
INSERT INTO bi_schema.dim_localisation (city, district)
SELECT DISTINCT 
    city, 
    COALESCE(district, 'Unknown') 
FROM clean.annonces
ON CONFLICT (city, district) DO NOTHING;

INSERT INTO bi_schema.dim_temps (date_key, full_date, year, month, month_name)
SELECT DISTINCT 
    TO_CHAR(announcement_date, 'YYYYMMDD')::INTEGER,
    announcement_date,
    EXTRACT(YEAR FROM announcement_date),
    EXTRACT(MONTH FROM announcement_date),
    TO_CHAR(announcement_date, 'Month')
FROM clean.annonces
ON CONFLICT (date_key) DO NOTHING;

INSERT INTO bi_schema.dim_categories (category_name)
SELECT DISTINCT category FROM clean.annonces
ON CONFLICT (category_name) DO NOTHING;

-- C. Load Fact Table
TRUNCATE bi_schema.fact_annonces;
INSERT INTO bi_schema.fact_annonces (id, date_key, category, price_dh, city, district, surface_m2)
SELECT 
    id, 
    TO_CHAR(announcement_date, 'YYYYMMDD')::INTEGER,
    category,
    price_dh, 
    city,
    COALESCE(district, 'Unknown'), -- Match the Dimension table
    surface_m2
FROM clean.annonces;

-- 6. ML SCHEMA: One Big Table (OBT) for Features

-- A. Create structure if it doesn't exist
CREATE TABLE IF NOT EXISTS ml_schema.obt_annonces (
    category TEXT, 
    price_dh NUMERIC, 
    city TEXT, 
    district TEXT,
    surface_m2 INTEGER, 
    rooms INTEGER, 
    bathrooms INTEGER, 
    floor INTEGER, 
    property_age_years INTEGER,
    price_per_m2 NUMERIC
);

-- B. Refresh the OBT table
TRUNCATE ml_schema.obt_annonces;
INSERT INTO ml_schema.obt_annonces
SELECT 
    category, 
    price_dh, 
    city, 
    COALESCE(district, 'Unknown'),
    surface_m2, 
    rooms, 
    bathrooms, 
    floor, 
    property_age_years,
    price_per_m2
FROM clean.annonces;