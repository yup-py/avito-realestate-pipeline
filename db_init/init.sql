-- 1 Create the Schemas
CREATE SCHEMA IF NOT EXISTS staging;     -- For raw, untouched data
CREATE SCHEMA IF NOT EXISTS clean;       -- For cleaned data
CREATE SCHEMA IF NOT EXISTS bi_schema;   -- For Power BI (Star Schema)
CREATE SCHEMA IF NOT EXISTS ml_schema;   -- For Machine Learning (One Big Table)

-- 2 Create the Staging Table (The first place data lands)
CREATE TABLE IF NOT EXISTS staging.raw_annonces (
    id SERIAL PRIMARY KEY,
    category TEXT,
    title TEXT,
    price TEXT,
    city TEXT,
    surface TEXT,
    rooms TEXT,
    bathrooms TEXT,
    floor TEXT,
    build_year TEXT,
    link TEXT,
    details TEXT,          -- Stores the full raw text for analysis
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create an index on the link to make searching faster later
CREATE INDEX IF NOT EXISTS idx_annonce_link ON staging.raw_annonces(link);