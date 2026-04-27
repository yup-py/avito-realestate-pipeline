import os
import time
import re
import pandas as pd
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import your new custom logger
from utils.logger import setup_logger

logger = setup_logger(__name__)

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
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(5)

        listing_cards = driver.find_elements(By.CSS_SELECTOR, "a, article, div[class*='listingCard']")
        logger.info(f"Found {len(listing_cards)} elements on the page.")
        
        scraped_data = []
        for card in listing_cards:
            val = card.text
            if val and "DH" in val and len(val) > 20:
                # Cleaning the text
                lines = [l.strip() for l in val.split('\n') if l.strip()]
                
                # Logic to pull specific numbers from the text
                surface_match = re.search(r'(\d+)\s*m²', val)
                rooms_match = re.search(r'(\d+)\s*chambre', val)
                bath_match = re.search(r'(\d+)\s*sdb', val)

                scraped_data.append({
                    "title": lines[0],
                    "price": next((l for l in lines if "DH" in l), "0 DH"),
                    "city": next((l for l in lines if "dans " in l), "Unknown"),
                    "surface": surface_match.group(1) if surface_match else "N/A",
                    "rooms": rooms_match.group(1) if rooms_match else "N/A",
                    "bathrooms": bath_match.group(1) if bath_match else "N/A",
                    "details": val[:200].replace('\n', ' ')
                })

        df = pd.DataFrame(scraped_data).drop_duplicates()
        
        if not df.empty:
            # We use 'staging' schema. Ensure you ran the ALTER TABLE command!
            df.to_sql('raw_annonces', engine, schema='staging', if_exists='append', index=False)
            logger.info(f"✅ SUCCESSFULLY saved {len(df)} listings to Database.")
        else:
            logger.warning("No valid listings found. Check error_view.png")
            driver.save_screenshot("logs/error_view.png")

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {str(e)}", exc_info=True)
    
    finally:
        if driver:
            driver.quit()
            logger.info("Pipeline finished.")

if __name__ == "__main__":
    scrape_avito_real_estate()