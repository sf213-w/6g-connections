import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# Updated to include all three Call URLs
CALL_URLS = [
    "https://smart-networks.europa.eu/sns-call-1/",
    "https://smart-networks.europa.eu/sns-call-2/",
    "https://smart-networks.europa.eu/sns-call-3/"
]

OUTPUT_FILE = "sns_deep_scrape_all_calls.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

IGNORE_KEYWORDS = [
    "About us", "Results & Tools", "Journals", "Stream", 
    "Newsletter", "Participate", "Events", "CSAs", "Subscribe",
    "Project Portfolio"
]

def get_soup(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        return BeautifulSoup(res.text, "html.parser")
    except:
        return None

def fetch_deep_metadata(project_name, call_number):
    """
    Mapping dictionary for high-quality data. 
    Added logic to handle default descriptions based on the Call Number.
    """
    mappings = {
        "5G-STARDUST": {
            "full_name": "Satellite and Terrestrial Access for Distributed, Ubiquitous, and Smart Telecommunications",
            "participants": "Thales Alenia Space|Hispasat|Orange|Fraunhofer|CTTC",
            "description": "Aims to create a fully integrated 5G-NTN system with a self-adapting end-to-end connectivity model."
        },
        "6Green": {
            "full_name": "Green Technologies for 5/6G Service-Based Architectures",
            "participants": "Atos|Ericsson|Telenor|Telefonica|Telecom Italia|Orange Romania",
            "description": "Conceives an innovative service-based ecosystem to promote energy efficiency across the 5/6G value-chain."
        },
        "NANCY": {
            "full_name": "An Artificial Intelligent Aided Unified Network for Secure Beyond 5G Long Term Evolution",
            "participants": "NEC Laboratories|Ericsson|Thales|Netcompany|Eight Bells",
            "description": "Develops a secure AI-aided unified network for long-term 5G/6G evolution."
        },
        "6G-NTN": {
            "full_name": "6G Non-Terrestrial Networks",
            "participants": "Eurescom|Thales|ESA|Nokia|Airbus",
            "description": "Focuses on the integration of satellite and terrestrial network components for 6G."
        }
    }

    # Determine date and default description based on Call
    dates = {"1": "2023", "2": "2024", "3": "2025"}
    call_date = dates.get(call_number, "2023")

    if project_name in mappings:
        data = mappings[project_name]
        data["date"] = call_date
        return data
    else:
        return {
            "full_name": project_name, 
            "participants": "Not listed", 
            "date": call_date,
            "description": f"SNS JU Call {call_number} Research Project"
        }

def extract_projects_from_url(url, call_number):
    """Extracts project acronyms from a specific Call page."""
    soup = get_soup(url)
    projects = []
    seen = set()
    if not soup: return []

    for a in soup.find_all("a", href=True):
        name = a.get_text(strip=True)
        href = a['href']
        
        is_junk = any(k.lower() in name.lower() for k in IGNORE_KEYWORDS)
        is_anchor = "#" in href
        is_new = name not in seen
        is_valid_len = len(name) >= 3

        if is_anchor and not is_junk and is_new and is_valid_len:
            projects.append({
                "name": name,
                "sns_url": href if href.startswith("http") else f"https://smart-networks.europa.eu{href}",
                "call_num": call_number
            })
            seen.add(name)
    return projects

def main():
    all_projects_data = []

    for url in CALL_URLS:
        # Extract the call number from the URL string
        call_match = re.search(r'call-(\d+)', url)
        call_num = call_match.group(1) if call_match else "1"
        
        print(f"📡 Scraping Call {call_num} via {url}...")
        
        call_projects = extract_projects_from_url(url, call_num)
        print(f"   Found {len(call_projects)} projects.")

        for p in call_projects:
            meta = fetch_deep_metadata(p['name'], call_num)
            all_projects_data.append({
                "name": p['name'],
                "full_name": meta['full_name'],
                "date": meta['date'],
                "participants": meta['participants'],
                "url": p['sns_url'],
                "description": meta['description']
            })
        
        time.sleep(1) # Polite delay between pages

    # Write all calls to a single CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "full_name", "date", "participants", "url", "description"])
        writer.writeheader()
        writer.writerows(all_projects_data)

    print(f"\n🚀 Success! Total {len(all_projects_data)} projects saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()