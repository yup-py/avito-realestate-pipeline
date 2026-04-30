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
def extract_listing_data(page_text, href, category_name, card_snippet):
    # --- 1. DATA FROM THE CARD (More reliable for Price/City) ---[cite: 11]
    card_lines = [l.strip() for l in card_snippet.split('\n') if l.strip()]
    
    # Precise Price from Card
    price_match = re.search(r'([\d\s]+)\s*DH', card_snippet, re.IGNORECASE)
    price_val = price_match.group(1).replace(" ", "").strip() if price_match else "N/A"
    
    # Precise City from Card[cite: 11]
    city = "N/A"
    city_match = re.search(r'dans\s+(.*)', card_snippet)
    if city_match:
        city = city_match.group(1).strip()
    elif card_lines:
        city = next((l for l in card_lines if "dans " in l), "N/A")

    # --- 2. DATA FROM THE FULL PAGE (Technical details) ---[cite: 11]
    surface = re.search(r'(\d+)\s*m²', page_text)
    rooms = re.search(r'(\d+)\s*chambre', page_text, re.IGNORECASE)
    bath_match = re.search(r'(\d+)\s*(?:sdb|sdbs|salle[s]?\s*de\s*bain)', page_text, re.IGNORECASE)
    floor = re.search(r'(\d+)\s*(?:[Ée]tage|Nombre d[’\']étage)', page_text, re.IGNORECASE)
    
    # Build Year logic from expanded page[cite: 11]
    age_match = re.search(r'([^\n]+)\n\s*Âge du bien', page_text, re.IGNORECASE)
    year_val = "N/A"
    if age_match:
        age_text = age_match.group(1).strip()
        mapping = {"Moins de 1 an": "2026", "1-5": "2023", "5-10": "2018", "10-20": "2011", "Plus de 20": "2000"}
        for key, val in mapping.items():
            if key in age_text: year_val = val; break

    return {
        "category": category_name,
        "title": card_lines[0] if card_lines else "N/A",
        "price": price_val,
        "city": city,
        "surface": surface.group(1) if surface else "N/A",
        "rooms": rooms.group(1) if rooms else "N/A",
        "bathrooms": bath_match.group(1) if bath_match else "N/A",
        "floor": floor.group(1) if floor else "N/A",
        "build_year": year_val,
        "link": href,
        "details": page_text
    }