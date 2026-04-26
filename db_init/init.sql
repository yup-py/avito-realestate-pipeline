-- 1 Create the Schemas
CREATE SCHEMA IF NOT EXISTS staging;     -- For raw, untouched data
CREATE SCHEMA IF NOT EXISTS clean;       -- For cleaned data
CREATE SCHEMA IF NOT EXISTS bi_schema;   -- For Power BI (Star Schema)
CREATE SCHEMA IF NOT EXISTS ml_schema;   -- For Machine Learning (One Big Table)

-- 2 Create the Staging Table (The first place data lands)
CREATE TABLE IF NOT EXISTS staging.raw_annonces (
    id SERIAL PRIMARY KEY,
    title TEXT,
    price TEXT,
    city TEXT,
    surface TEXT,
    details JSONB,
    scrape_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);