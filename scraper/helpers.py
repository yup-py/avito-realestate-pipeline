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

# Add 'card_snippet' as a new parameter
def extract_listing_data(card_text, href, category_name):
    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
    
    # Price and City from Card[cite: 11]
    price_match = re.search(r'([\d\s]+)\s*DH', card_text, re.IGNORECASE)
    price_val = price_match.group(1).replace(" ", "").strip() if price_match else "N/A"
    
    city = "N/A"
    city_match = re.search(r'dans\s+(.*)', card_text)
    if city_match:
        city = city_match.group(1).strip()
    
    # Technical specs (Best effort from snippet)[cite: 11]
    surface = re.search(r'(\d+)\s*m²', card_text)
    rooms = re.search(r'(\d+)\s*chambre', card_text, re.IGNORECASE)
    bath_match = re.search(r'(\d+)\s*(?:sdb|sdbs|salle[s]?\s*de\s*bain)', card_text, re.IGNORECASE)
    
    # Note: Floor and Age will mostly be 'N/A' in this mode[cite: 1, 2]
    floor = re.search(r'(\d+)\s*[Ée]tage', card_text, re.IGNORECASE)
    
    return {
        "category": category_name,
        "title": lines[0] if lines else "N/A",
        "price": price_val,
        "city": city,
        "surface": surface.group(1) if surface else "N/A",
        "rooms": rooms.group(1) if rooms else "N/A",
        "bathrooms": bath_match.group(1) if bath_match else "N/A",
        "floor": floor.group(1) if floor else "N/A",
        "build_year": "N/A", # Hard to find on search cards[cite: 1]
        "link": href,
        "details": card_text
    }