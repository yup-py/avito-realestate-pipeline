import os
import time
import random
import pandas as pd
from sqlalchemy import create_engine
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.logger import setup_logger
from scraper.helpers import get_driver, extract_listing_data

logger = setup_logger(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

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
            time.sleep(random.uniform(5.0, 8.0))
            driver.get(url)
            
            try:
                # Wait for the actual listing links to appear
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='.htm']"))
                )
            except Exception:
                logger.warning(f"⚠️ Timeout waiting for listings on Page {page}. Checking for page content anyway...")

            # Get all potential listing cards
            cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='.htm']")
            
            if not cards:
                logger.warning(f"⚠️ No listings found on Page {page}. Stopping category.")
                break

            page_data = [] 
            for card in cards:
                try:
                    href = card.get_attribute("href")
                    # Ignore internal Avito links that aren't actual listings
                    if "/vi/" not in href and ".htm" not in href:
                        continue

                    raw_text = card.text
                    
                    # Targeted date fix: Look for the 'il y a' pattern inside the card
                    # We use a try/except because not every card might have a visible date
                    try:
                        # Find any element inside the card that mentions time
                        time_element = card.find_element(By.XPATH, ".//*[contains(text(), 'il y a')]")
                        date_str = time_element.text
                    except:
                        date_str = "Date Unknown"

                    # Pass the text and the explicitly found date to your helper
                    entry = extract_listing_data(raw_text, href, target_category)
                    
                    # FORCE correct the date if the helper put a price there
                    if "DH" in str(entry.get('date_posted', '')) or not entry.get('date_posted'):
                        entry['date_posted'] = date_str

                    page_data.append(entry)
                    all_extracted_data.append(entry)

                except Exception:
                    continue

            if page_data:
                # DB Upload
                df = pd.DataFrame(page_data)
                df.to_sql('raw_annonces', engine, schema='staging', if_exists='append', index=False)
                
                # CSV Backup
                file_path = 'data/rawdata.csv'
                os.makedirs('data', exist_ok=True)
                header = not os.path.exists(file_path)
                df.to_csv(file_path, mode='a', index=False, header=header)
                
                logger.info(f"💾 Page {page} secured. Extracted: {len(page_data)} listings.")

        # Cool-down between categories
        time.sleep(random.uniform(10, 15))

    except Exception as e:
        logger.error(f"❌ Critical Scraper Error: {str(e)}")
    finally:
        if driver: 
            driver.quit()