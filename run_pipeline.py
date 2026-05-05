import os
import time
import schedule
import pandas as pd
from sqlalchemy import create_engine, text
from utils.logger import setup_logger
from scraper.main import run_scraper 

logger = setup_logger("Orchestrator")

def run_sql(filename):
    """Executes SQL scripts from the db_init folder."""
    logger.info(f"Running database task: {filename}")
    engine = create_engine(os.getenv("DATABASE_URL"))
    with open(f"db_init/{filename}", 'r') as f:
        query = f.read()
    with engine.begin() as conn:
        conn.execute(text(query))

def export_clean_data():
    """Exports the final warehouse data to a CSV for analysis[cite: 9]."""
    logger.info("📊 Exporting the SQL-cleaned data to data/clean_data.csv...")
    try:
        engine = create_engine(os.getenv("DATABASE_URL"))
        df = pd.read_sql("SELECT * FROM clean.annonces", engine)
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/clean_data.csv', index=False)
        logger.info(f"Successfully saved {len(df)} rows to data/clean_data.csv")
    except Exception as e:
        logger.error(f"⚠️ CSV Export failed: {e}")

def autonomous_pipeline():
    """The main automated logic: No menus, no inputs[cite: 9]."""
    # 🎯 AUTOMATED FILTERS
    ALL_CATEGORIES = [
        "Appartement", "Maison", "Villa_Riad", 
        "Bureau_Plateau", "Commerce", "Terrain_Ferme"
    ]
    PAGES_PER_CAT = 3 # Your requested 30 pages
    
    try:
        logger.info("🚀 Starting Automated Industrial Pipeline...")
        
        # Step 1: Sequential Extraction for all categories[cite: 7]
        for category in ALL_CATEGORIES:
            logger.info(f"Step 1: Scraping 30 pages for {category}...")
            run_scraper(category, PAGES_PER_CAT)
        
        # Step 2: Clean and Filter in SQL[cite: 1]
        logger.info("Step 2: Running SQL Cleaning and Filtering...")
        run_sql("cleaning.sql")
        
        # Step 3: Populate BI and ML Warehouse Schemas[cite: 4]
        logger.info("Step 3: Loading Warehouse Schemas...")
        run_sql("warehouse.sql")
        
        # Step 4: Export to CSV
        export_clean_data()
        
        # Step 5: Purge Staging Area (Clean up for the next run)
        logger.info("Step 5: Purging Staging Area...")
        run_sql("purge_staging.sql")

        logger.info("✅ Pipeline Execution Successful! Next run in 24 hours.")
    except Exception as e:
        logger.error(f"❌ Pipeline Failed: {e}")

if __name__ == "__main__":
    # Run once immediately when the container starts
    autonomous_pipeline()
    
    # Schedule to run automatically every night at 2:00 AM
    schedule.every().day.at("12:40").do(autonomous_pipeline)
    
    logger.info("🤖 Scheduler Active. Keeping container alive...")
    while True:
        schedule.run_pending()
        time.sleep(60)