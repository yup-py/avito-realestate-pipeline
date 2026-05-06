import os
import time
import schedule
import pandas as pd
from sqlalchemy import create_engine, text
from utils.logger import setup_logger
from scraper.main import run_scraper 

logger = setup_logger("Orchestrator")

def run_sql(filename):
    logger.info(f"Running database task: {filename}")
    engine = create_engine(os.getenv("DATABASE_URL"))
    with open(f"db_init/{filename}", 'r') as f:
        query = f.read()
    try:
        with engine.begin() as conn:
            # Use text(query) to wrap the string safely
            conn.execute(text(query)) 
    except Exception as e:
        logger.error(f"❌ SQL Error in {filename}: {str(e).split('[SQL:')[0]}")
        raise e

def export_clean_data():
    """Exports the final warehouse data to a CSV for analysis."""
    logger.info("📊 Exporting the SQL-cleaned data to data/clean_data.csv...")
    try:
        engine = create_engine(os.getenv("DATABASE_URL"))
        # Reads from the 'clean' schema defined in your SQL files[cite: 17]
        df = pd.read_sql("SELECT * FROM clean.annonces", engine)
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/clean_data.csv', index=False)
        logger.info(f"Successfully saved {len(df)} rows to data/clean_data.csv")
    except Exception as e:
        logger.error(f"⚠️ CSV Export failed: {e}")

def autonomous_pipeline():
    """The main automated logic"""
    ALL_CATEGORIES = [
        "Appartement", "Villa_Riad", "Maison", "Bureau_Plateau", "Commerce", "Terrain_Ferme"
    ]
    PAGES_PER_CAT = 50
    
    try:
        logger.info("🚀 Starting Automated Industrial Pipeline...")
        
        # Step 0: Initialize Schemas and Tables
        # Filename corrected to match your 'db_init/init.sql'
        logger.info("Step 0: Initializing Database...")
        run_sql("init.sql") 
        
        # Step 1: Sequential Extraction
        for category in ALL_CATEGORIES:
            logger.info(f"Step 1: Scraping {PAGES_PER_CAT} pages for {category}...")
            run_scraper(category, PAGES_PER_CAT)
        
        # Step 2: Clean and Filter in SQL
        logger.info("Step 2: Running SQL Cleaning...")
        run_sql("cleaning.sql")
        
        # Step 3: Populate Warehouse Schemas
        logger.info("Step 3: Loading Warehouse...")
        run_sql("warehouse.sql")
        
        # Step 4: Export to CSV
        export_clean_data()
        
        # Step 5: Purge Staging Area
        logger.info("Step 5: Purging Staging Area...")
        run_sql("purge_staging.sql")

        logger.info("✅ Pipeline Execution Successful!")
    except Exception as e:
        logger.error(f"❌ Pipeline Failed: {e}")

if __name__ == "__main__":
    # Execute immediately on start
    autonomous_pipeline()
    
    # Schedule for daily execution at 02:12 AM
    schedule.every().day.at("02:12").do(autonomous_pipeline)
    
    logger.info("🤖 Scheduler Active. Keeping container alive...")
    while True:
        schedule.run_pending()
        time.sleep(60)