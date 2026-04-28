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
    
    # 1. Improved City Extraction: Extract only the part after "dans "
    # Example: "Maisons dans Tanger, Ahlane" -> "Tanger, Ahlane"
    city = "N/A"
    city_match = re.search(r'dans\s+(.*)', card_text)
    if city_match:
        city = city_match.group(1).strip()
    elif lines:
        # Fallback to the old method if Regex fails
        city = next((l for l in lines if "dans " in l), "N/A")

    # 2. Flexible Bathroom Pattern: Catches "sdb", "sdbs", "salle de bain"
    # Added 're.IGNORECASE' to catch 'Sdb' or 'SDB'
    bathrooms = "N/A"
    bath_match = re.search(r'(\d+)\s*(?:sdb|sdbs|salle[s]?\s*de\s*bain)', card_text, re.IGNORECASE)
    if bath_match:
        bathrooms = bath_match.group(1)

    # 3. Surface, Rooms, Floor, and Year (Standardized)
    surface = re.search(r'(\d+)\s*m²', card_text)
    rooms = re.search(r'(\d+)\s*chambre', card_text, re.IGNORECASE)
    floor = re.search(r'(\d+)(?:er|ème)\s*étage', card_text, re.IGNORECASE)
    year = re.search(r'(19|20)\d{2}', card_text)

    return {
        "category": category_name,
        "title": lines[0] if lines else "N/A",
        "price": next((l for l in lines if "DH" in l), "N/A"),
        "city": city,
        "surface": surface.group(1) if surface else "N/A",
        "rooms": rooms.group(1) if rooms else "N/A",
        "bathrooms": bathrooms,
        "floor": floor.group(1) if floor else "N/A",
        "build_year": year.group(0) if year else "N/A",
        "link": href,
        "details": card_text
    }