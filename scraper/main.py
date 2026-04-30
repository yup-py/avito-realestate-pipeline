import os
import time
import random
import pandas as pd
from sqlalchemy import create_engine
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import your custom tools
from utils.logger import setup_logger
from scraper.helpers import get_driver, extract_listing_data

logger = setup_logger(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# UPDATED: Now it accepts the specific category chosen in your menu!
def run_scraper(target_category, pages_per_category=10): 
    categories = {
        "Appartement": "https://www.avito.ma/fr/maroc/appartement",
        "Maison": "https://www.avito.ma/fr/maroc/maisons-%C3%A0_vendre",
        "Villa_Riad": "https://www.avito.ma/fr/maroc/villas_riad-%C3%A0_vendre",
        "Bureau_Plateau": "https://www.avito.ma/fr/maroc/bureaux_et_plateaux-%C3%A0_vendre",
        "Commerce": "https://www.avito.ma/fr/maroc/magasins_et_commerces-%C3%A0_vendre",
        "Terrain_Ferme": "https://www.avito.ma/fr/maroc/terrains_et_fermes-%C3%A0_vendre",
        "Autre": "https://www.avito.ma/fr/maroc/autres_immobilier-%C3%A0_vendre"
    }

    # Failsafe: if the category doesn't exist, stop.
    if target_category not in categories:
        logger.error(f"Category {target_category} not found!")
        return

    driver = None
    all_extracted_data = [] 
    
    try:
        driver = get_driver()
        base_url = categories[target_category]
        logger.info(f"🚀 Scraping Category: {target_category}")
        
        for page in range(1, pages_per_category + 1):
            url = f"{base_url}?p={page}"
            logger.info(f"🔎 {target_category} - Page {page}...")
            
            # Anti-bot delay
            time.sleep(random.uniform(9.0, 15.0))
            driver.get(url)
            
            try:
                WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.htm']")))
            except:
                logger.warning(f"⚠️ Page {page} failed to load or no listings found. Stopping this category.")
                break

            cards = driver.find_elements(By.CSS_SELECTOR, "a[href$='.htm']")
            page_data = [] 
            
            for card in cards:
                try:
                    href = card.get_attribute("href")
                    # We only extract from the card text now
                    card_text = card.text 
                    
                    entry = extract_listing_data(card_text, href, target_category)
                    page_data.append(entry)
                    all_extracted_data.append(entry)

                except Exception as e:
                    logger.warning(f"Skipping a card due to error: {e}")
                    continue

            # --- BUILD-UP SAVE ---
            if page_data:
                # Save only the NEW listings from this page to DB
                pd.DataFrame(page_data).to_sql('raw_annonces', engine, schema='staging', if_exists='append', index=False)
                
                # FIX: Append to CSV instead of overwriting
                file_path = 'data/rawdata.csv'
                os.makedirs('data', exist_ok=True)
                
                # If file doesn't exist, write header; if it does, don't.
                header = not os.path.exists(file_path)
                pd.DataFrame(page_data).to_csv(file_path, mode='a', index=False, header=header)
                
                logger.info(f"💾 Page {page} secured. Total extracted for {target_category}: {len(all_extracted_data)}")

        time.sleep(random.uniform(30, 50))

    except Exception as e:
        logger.error(f"❌ Error during scraping: {str(e)}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    # This is just a fallback if you run main.py directly instead of run_pipeline.py
    run_scraper("Appartement", 5)