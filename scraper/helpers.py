import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def extract_listing_data(card_text, href, category_name):
    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
    
    # 1. SIMPLE TITLE: Use the first line but remove common patterns like "155m²" or "3 ch"
    raw_title = lines[0] if lines else "N/A"
    simple_title = re.sub(r'\d+\s*(?:m²|ch|sdb|étage).*', '', raw_title, flags=re.IGNORECASE).strip()
    
    # 2. PRICE
    price_match = re.search(r'([\d\s]+)\s*DH', card_text, re.IGNORECASE)
    price_val = price_match.group(1).replace(" ", "").strip() if price_match else "N/A"
    
    # 3. CITY & DISTRICT: Split "dans City, District"
    city, district = "N/A", "N/A"
    loc_match = re.search(r'dans\s+([^,\n]+)(?:,\s*([^,\n]+))?', card_text)
    if loc_match:
        city = loc_match.group(1).strip()
        district = loc_match.group(2).strip() if loc_match.group(2) else "Autre secteur"
    
    # 4. TECHNICAL SPECS
    surface = re.search(r'(\d+)\s*m²', card_text)
    rooms = re.search(r'(\d+)\s*chambre', card_text, re.IGNORECASE)
    bath_match = re.search(r'(\d+)\s*(?:sdb|sdbs|salle[s]?\s*de\s*bain)', card_text, re.IGNORECASE)
    floor = re.search(r'(\d+)\s*[Ée]tage', card_text, re.IGNORECASE)
    
    date_raw = lines[-1] if lines else "N/A"
    
    return {
        "category": category_name,
        "title": simple_title,
        "price": price_val,
        "city": city,
        "district": district,
        "surface": surface.group(1) if surface else "N/A",
        "rooms": rooms.group(1) if rooms else "N/A",
        "bathrooms": bath_match.group(1) if bath_match else "N/A",
        "floor": floor.group(1) if floor else "N/A",
        "build_year": "N/A", 
        "link": href,
        "date_posted": date_raw,
        "details": card_text
    }