import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from googlesearch import search

BASE_URL = "https://smart-networks.europa.eu"
CALL1_URL = "https://smart-networks.europa.eu/sns-call-1/"

OUTPUT_FILE = "sns_deep_scrape.csv"
MAX_PROJECTS = 5

HEADERS = {"User-Agent": "Mozilla/5.0"}


# =========================
# BASICS
# =========================

def get_soup(url):
	try:
		res = requests.get(url, headers=HEADERS, timeout=10)
		res.raise_for_status()
		return BeautifulSoup(res.text, "html.parser")
	except:
		return None


# =========================
# STEP 1: GET PROJECTS
# =========================

def extract_projects():
	soup = get_soup(CALL1_URL)

	projects = []
	seen = set()

	for a in soup.find_all("a", href=True):
		name = a.get_text(strip=True)
		href = a["href"]

		if not name or "#" not in href:
			continue

		if not re.match(r'^[A-Za-z0-9\-]{4,}$', name):
			continue

		if name in seen:
			continue

		seen.add(name)

		full_url = BASE_URL + href if href.startswith("/") else href

		projects.append({
			"name": name,
			"url": full_url
		})

		if len(projects) >= MAX_PROJECTS:
			break

	return projects


# =========================
# STEP 2: FIND REAL WEBSITE
# =========================

def find_project_website(project_name):
	query = f"{project_name} 6G project EU"

	try:
		for url in search(query, num_results=5):
			if any(x in url for x in [".eu", ".org", ".com"]):
				return url
	except:
		return ""

	return ""


# =========================
# STEP 3: EXTRACT DATA
# =========================

def extract_description(soup):
	paragraphs = soup.find_all("p")
	texts = []

	for p in paragraphs[:5]:
		t = p.get_text(strip=True)
		if len(t) > 50:
			texts.append(t)

	return " ".join(texts[:2])


def extract_full_name(soup, fallback):
	title = soup.find("title")
	if title:
		t = title.get_text(strip=True)
		if len(t) > len(fallback):
			return t

	h1 = soup.find("h1")
	if h1:
		t = h1.get_text(strip=True)
		if len(t) > len(fallback):
			return t

	return fallback


def extract_participants(soup):
	participants = set()

	for img in soup.find_all("img", alt=True):
		alt = img.get("alt", "").strip()
		if alt and len(alt) > 3:
			if not any(x in alt.lower() for x in ["logo", "icon"]):
				participants.add(alt)

	return "|".join(list(participants)[:10])


# =========================
# MAIN ENRICH
# =========================

def enrich_project(project):
	print(f"🔎 Searching: {project['name']}")

	site = find_project_website(project["name"])

	if not site:
		return {
			"name": project["name"],
			"full_name": project["name"],
			"date": "2023",
			"participants": "",
			"url": project["url"],
			"description": ""
		}

	print(f"→ Found site: {site}")

	soup = get_soup(site)

	if not soup:
		return None

	full_name = extract_full_name(soup, project["name"])
	description = extract_description(soup)
	participants = extract_participants(soup)

	return {
		"name": project["name"],
		"full_name": full_name,
		"date": "2023",
		"participants": participants,
		"url": site,
		"description": description
	}


# =========================
# RUN
# =========================

def main():
	projects = extract_projects()
	rows = []

	for p in projects:
		data = enrich_project(p)
		if data:
			rows.append(data)
		time.sleep(2)  # avoid blocking

	with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=[
			"name", "full_name", "date", "participants", "url", "description"
		])
		writer.writeheader()
		writer.writerows(rows)

	print(f"\n✅ Deep dataset saved to {OUTPUT_FILE}")


if __name__ == "__main__":
	main()