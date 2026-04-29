import os
import pandas as pd
import sys
from sqlalchemy import create_engine, text
from utils.logger import setup_logger
from scraper.main import run_scraper 

logger = setup_logger("Orchestrator")

def get_menu_choice():
    cats = {
        "1": "Appartement", 
        "2": "Maison", 
        "3": "Villa_Riad", 
        "4": "Bureau_Plateau",
        "5": "Commerce",
        "6": "Terrain_Ferme",
        "7": "Autre"
    }
    
    print("\n" + "="*30)
    print("🚀 AVITO PIPELINE MENU")
    print("="*30)
    for k, v in cats.items(): 
        print(f"[{k}] {v}")
    print("[A] All Categories")
    
    # 1. Get Categories
    choice = input("\nEnter numbers separated by commas (e.g., 1,3) or 'A' for all: ").strip().upper()
    
    selected_categories = []
    if choice == 'A':
        selected_categories = list(cats.values())
    else:
        # Split "1,3" into ["1", "3"]
        indices = [i.strip() for i in choice.split(",")]
        for i in indices:
            if i in cats:
                selected_categories.append(cats[i])
    
    if not selected_categories:
        print("⚠️ No valid categories selected. Defaulting to Appartement.")
        selected_categories = ["Appartement"]

    # 2. Get Pages
    pages = input("How many pages to scrape per category?: ").strip()
    pages = int(pages) if pages.isdigit() else 5
    
    return selected_categories, pages

def run_sql(filename):
    logger.info(f"Running database task: {filename}")
    engine = create_engine(os.getenv("DATABASE_URL"))
    with open(f"db_init/{filename}", 'r') as f:
        query = f.read()
    with engine.begin() as conn:
        conn.execute(text(query))

def export_clean_data():
    logger.info("📊 Exporting the SQL-cleaned data to data/clean_data.csv...")
    try:
        engine = create_engine(os.getenv("DATABASE_URL"))
        # We select from the 'clean' table we just populated in SQL
        df = pd.read_sql("SELECT * FROM clean.annonces", engine)
        
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/clean_data.csv', index=False)
        logger.info(f"Successfully saved {len(df)} rows to data/clean_data.csv")
    except Exception as e:
        logger.error(f"⚠️ CSV Export failed: {e}")

def main():
    selected_cats, pages = get_menu_choice()
    
    try:
        # Step 1: Scrape
        for category in selected_cats:
            logger.info(f"Step 1: Starting Scraping for {category}...")
            run_scraper(category, pages)
        
        # Step 2: Clean and Filter in SQL
        logger.info("Step 2: Running SQL Cleaning and Filtering...")
        run_sql("cleaning.sql")
        
        # Step 3: Populate Warehouse
        logger.info("Step 3: Loading BI and ML Schemas...")
        run_sql("warehouse.sql")
        
        # Step 4: Export to CSV
        export_clean_data()
        
        logger.info("✅ Pipeline Execution Successful!")
    except Exception as e:
        logger.error(f"❌ Pipeline Failed: {e}")

if __name__ == "__main__":
     main()