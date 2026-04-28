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
from utils.helpers import get_driver, extract_listing_data

logger = setup_logger(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def scrape_avito_real_estate(pages_per_category=10): 
    categories = {
        "Appartement": "https://www.avito.ma/fr/maroc/appartement",
        "Maison": "https://www.avito.ma/fr/maroc/maisons-%C3%A0_vendre",
        "Villa_Riad": "https://www.avito.ma/fr/maroc/villas_riad-%C3%A0_vendre",
        "Bureau_Plateau": "https://www.avito.ma/fr/maroc/bureaux_et_plateaux-%C3%A0_vendre",
        "Commerce": "https://www.avito.ma/fr/maroc/magasins_et_commerces-%C3%A0_vendre",
        "Terrain_Ferme": "https://www.avito.ma/fr/maroc/terrains_et_fermes-%C3%A0_vendre",
        "Autre": "https://www.avito.ma/fr/maroc/autres_immobilier-%C3%A0_vendre"
    }

    driver = None
    all_extracted_data = [] 
    
    try:
        driver = get_driver()
        category_list = list(categories.keys())
        random.shuffle(category_list)
        
        for category_name in category_list:
            base_url = categories[category_name]
            logger.info(f"🚀 Category: {category_name}")
            
            for page in range(1, pages_per_category + 1):
                url = f"{base_url}?p={page}"
                logger.info(f"🔎 {category_name} - Page {page}...")
                
                time.sleep(random.uniform(9.0, 15.0))
                driver.get(url)
                
                try:
                    WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.htm']")))
                except:
                    logger.warning(f"⚠️ Page failed. Skipping category.")
                    break

                cards = driver.find_elements(By.CSS_SELECTOR, "a[href$='.htm']")
                page_data = [] 
                
                for card in cards:
                    try:
                        href = card.get_attribute("href")
                        text = card.text
                        if text and len(text) > 10:
                            entry = extract_listing_data(text, href, category_name)
                            page_data.append(entry)
                            all_extracted_data.append(entry)
                    except: continue

                # --- BUILD-UP SAVE ---
                if page_data:
                    # Save only the NEW listings from this page to DB
                    pd.DataFrame(page_data).to_sql('raw_annonces', engine, schema='staging', if_exists='append', index=False)
                    
                    # Update CSV with everything found so far[cite: 5]
                    os.makedirs('data', exist_ok=True)
                    pd.DataFrame(all_extracted_data).to_csv('data/rawdata.csv', index=False)
                    logger.info(f"💾 Page {page} secured. Total: {len(all_extracted_data)}")

            time.sleep(random.uniform(30, 50))

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    scrape_avito_real_estate()