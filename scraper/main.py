import os
import time
import logging
import pandas as pd
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper/pipeline.log"), # Saves to a file
        logging.StreamHandler() # Also prints to your terminal
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)

def scrape_avito_real_estate():
    driver = None
    try:
        logger.info("Starting Scraper...")
        driver = get_driver()
        url = "https://www.avito.ma/fr/maroc/immobilier-%C3%A0_vendre"
        
        driver.get(url)
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(8)

        listing_cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/vi/']")
        logger.info(f"Found {len(listing_cards)} listing cards on the page.")
        
        scraped_data = []
        for card in listing_cards:
            text = card.text
            if text and "\n" in text:
                parts = text.split("\n")
                if len(parts) >= 2:
                    scraped_data.append({
                        "title": parts[0],
                        "price": parts[-1],
                        "city": parts[-2] if len(parts) > 2 else "Unknown",
                        "surface": "N/A",
                        "details": " ".join(parts[1:-2]) if len(parts) > 3 else None
                    })

        df = pd.DataFrame(scraped_data).drop_duplicates()
        
        if not df.empty:
            df = df[df['price'].str.contains('DH', na=False)]
            df.to_sql('raw_annonces', engine, schema='staging', if_exists='append', index=False)
            logger.info(f"✅ SUCCESSFULLY saved {len(df)} listings to Database.")
        else:
            logger.warning("No valid listings found during this run.")

    except Exception as e:
        # This is the "Magic" part: it catches ANY error and records it
        logger.error(f"❌ CRITICAL ERROR: {str(e)}", exc_info=True)
    
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed. Pipeline finished.")

if __name__ == "__main__":
    scrape_avito_real_estate()