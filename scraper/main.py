import os
import time
import re
import random
import pandas as pd
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import setup_logger

logger = setup_logger(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def get_driver():
    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def scrape_avito_real_estate(max_pages=10): 
    driver = None
    all_extracted_data = [] # List to collect data for CSV export
    
    try:
        logger.info("Starting THE SCRAPER...")
        driver = get_driver()
        
        for page in range(1, max_pages + 1):
            url = f"https://www.avito.ma/fr/maroc/immobilier-%C3%A0_vendre?p={page}"
            logger.info(f"🔎 Gently approaching Page {page}...")
            
            time.sleep(random.uniform(3.5, 7.2))
            driver.get(url)
            
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.htm']"))
                )
            except Exception:
                logger.warning(f"⚠️ Page {page} blocked or empty. Taking a screenshot and pausing.")
                driver.save_screenshot('debug_view.png')
                time.sleep(30) 
                break

            time.sleep(random.uniform(2.1, 4.5)) 
            
            for _ in range(random.randint(5, 8)): 
                scroll_amount = random.randint(400, 900)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(1.0, 3.0))
                
                if random.random() < 0.2:
                    driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
                    time.sleep(random.uniform(0.5, 1.5))
                
            page_listings = {} 
            cards = driver.find_elements(By.CSS_SELECTOR, "a[href$='.htm']")
            
            for card in cards:
                try:
                    href = card.get_attribute("href")
                    val = card.text
                    
                    if val and len(val) > 10 and href not in page_listings:
                        lines = [l.strip() for l in val.split('\n') if l.strip()]
                        
                        raw_price = next((l for l in lines if "DH" in l), "N/A")
                        surface_match = re.search(r'(\d+)\s*m²', val)
                        rooms_match = re.search(r'(\d+)\s*chambre', val)
                        
                        entry = {
                            "title": lines[0] if lines else "N/A",
                            "price": raw_price,
                            "city": next((l for l in lines if "dans " in l), "N/A"),
                            "surface": surface_match.group(1) if surface_match else "N/A",
                            "rooms": rooms_match.group(1) if rooms_match else "N/A",
                            "link": href
                        }
                        page_listings[href] = entry
                        all_extracted_data.append(entry) # Collect for final CSV
                except Exception:
                    continue 
                        
            if not page_listings:
                logger.warning(f"⚠️ No valid data found on Page {page}.")
                break

            df = pd.DataFrame(list(page_listings.values()))
            if not df.empty:
                df.to_sql('raw_annonces', engine, schema='staging', if_exists='append', index=False)
                logger.info(f"✅ Page {page}: Saved {len(df)} listings to Database.")

        # CSV EXPORT
        if all_extracted_data:
            os.makedirs('data', exist_ok=True)
            pd.DataFrame(all_extracted_data).to_csv('data/rawdata.csv', index=False)
            logger.info(f"💾 Successfully saved {len(all_extracted_data)} total listings to data/rawdata.csv")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
            logger.info("Pipeline finished.")

if __name__ == "__main__":
    scrape_avito_real_estate()