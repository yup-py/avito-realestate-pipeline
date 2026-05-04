-- 5. BI SCHEMA: Star Schema (Fact and Dimensions)
CREATE TABLE IF NOT EXISTS bi_schema.dim_localisation AS 
SELECT DISTINCT city FROM clean.annonces;

CREATE TABLE IF NOT EXISTS bi_schema.dim_temps AS 
SELECT DISTINCT 
    TO_CHAR(scraped_at, 'YYYYMMDD')::INTEGER as date_key,
    scraped_at::DATE as full_date,
    EXTRACT(YEAR FROM scraped_at) as year,
    EXTRACT(MONTH FROM scraped_at) as month,
    EXTRACT(DAY FROM scraped_at) as day,
    TO_CHAR(scraped_at, 'Month') as month_name,
    EXTRACT(QUARTER FROM scraped_at) as quarter
FROM staging.raw_annonces;

CREATE TABLE IF NOT EXISTS bi_schema.fact_annonces AS 
SELECT id, TO_CHAR(scraped_at, 'YYYYMMDD')::INTEGER as date_key, price_dh, surface_m2, rooms, bathrooms, city, price_per_m2 FROM clean.annonces;

-- 6. ML SCHEMA: One Big Table (OBT) for Features
CREATE TABLE IF NOT EXISTS ml_schema.obt_annonces AS 
SELECT 
    category, 
    price_dh, 
    city, 
    surface_m2, 
    rooms, 
    bathrooms, 
    floor, 
    property_age_years,
    price_per_m2
FROM clean.annonces;