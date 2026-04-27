import os
import time
import re
import pandas as pd
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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
    return webdriver.Chrome(options=options)

def scrape_avito_real_estate(max_pages=3000): # High limit to get all 107k ads
    driver = None
    try:
        logger.info("🚀 Starting THE ULTIMATE SCRAPER...")
        driver = get_driver()
        
        for page in range(1, max_pages + 1):
            url = f"https://www.avito.ma/fr/maroc/immobilier-%C3%A0_vendre?p={page}"
            logger.info(f"🔎 Scraping Page {page}...")
            driver.get(url)
            time.sleep(3) # Wait for initial load
            
            page_listings = {} # Use a dictionary to prevent saving duplicates
            
            # SLOW SCROLL: Scroll 15 times in small increments
            for _ in range(15): 
                driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(1) # Let the lazy-loaded cards pop into existence
                
                # Target the <a> tags to get the direct link
                cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='.ma/']")
                
                for card in cards:
                    try:
                        href = card.get_attribute("href")
                        val = card.text
                        
                        # Only process if it has text and we haven't seen this exact link yet
                        if val and len(val) > 10 and href not in page_listings:
                            lines = [l.strip() for l in val.split('\n') if l.strip()]
                            
                            surface_match = re.search(r'(\d+)\s*m²', val)
                            rooms_match = re.search(r'(\d+)\s*chambre', val)
                            bath_match = re.search(r'(\d+)\s*sdb', val)
                            floor_match = re.search(r'Étage\s*(\d+|RDC)', val, re.IGNORECASE)
                            year_match = re.search(r'(19\d{2}|20\d{2})', val) 
                            
                            page_listings[href] = {
                                "title": lines[0] if lines else "N/A",
                                "price": next((l for l in lines if "DH" in l), "N/A"),
                                "city": next((l for l in lines if "dans " in l), "N/A"),
                                "surface": surface_match.group(1) if surface_match else "N/A",
                                "rooms": rooms_match.group(1) if rooms_match else "N/A",
                                "bathrooms": bath_match.group(1) if bath_match else "N/A",
                                "floor": floor_match.group(1) if floor_match else "N/A",
                                "build_year": year_match.group(1) if year_match else "N/A",
                                "link": href,
                                "details": val.replace('\n', ' ')[:500]
                            }
                    except Exception:
                        # Ignore "StaleElementReferenceException" when Avito recycles code
                        continue 
                        
            # If the page is completely empty, we reached the end of Avito
            if not page_listings:
                logger.warning(f"⚠️ Page {page} has no listings. Ending scrape.")
                break

            # Save to Database
            df = pd.DataFrame(list(page_listings.values()))
            if not df.empty:
                df.to_sql('raw_annonces', engine, schema='staging', if_exists='append', index=False)
                logger.info(f"✅ Page {page}: Saved {len(df)} listings.")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
            logger.info("Pipeline finished.")

if __name__ == "__main__":
    scrape_avito_real_estate()