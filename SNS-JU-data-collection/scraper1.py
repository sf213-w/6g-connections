import requests
from bs4 import BeautifulSoup
import csv
import time
import re

BASE_URL = "https://smart-networks.europa.eu"
CALL1_URL = "https://smart-networks.europa.eu/sns-call-1/"

OUTPUT_FILE = "sns_call_1_projects.csv"
MAX_PROJECTS = 5

HEADERS = {
	"User-Agent": "Mozilla/5.0"
}


def get_soup(url):
	res = requests.get(url, headers=HEADERS)
	res.raise_for_status()
	return BeautifulSoup(res.text, "html.parser")


def extract_projects():
	soup = get_soup(CALL1_URL)

	projects = []
	seen = set()

	for a in soup.find_all("a", href=True):
		name = a.get_text(strip=True)
		href = a["href"]

		if not name or not href:
			continue

		# ✅ MUST be anchor link (this is key)
		if "#" not in href:
			continue

		# ✅ Must look like a project (acronym-style)
		if not re.match(r'^[A-Za-z0-9\-]{4,}$', name):
			continue

		# ❌ Filter obvious junk
		if name.lower() in [
			"about", "events", "contact", "participate", "home"
		]:
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


def extract_participants(soup):
	participants = []

	# Look for headings that indicate participants
	keywords = ["participants", "partners", "consortium"]

	for header in soup.find_all(["h2", "h3", "h4", "strong"]):
		header_text = header.get_text(strip=True).lower()

		if any(k in header_text for k in keywords):
			# Try to find list under it
			next_block = header.find_next()

			if next_block:
				# Case 1: list
				if next_block.name == "ul":
					for li in next_block.find_all("li"):
						text = li.get_text(strip=True)
						if text:
							participants.append(text)

				# Case 2: paragraph with commas
				elif next_block.name == "p":
					text = next_block.get_text(separator=" ", strip=True)
					parts = [p.strip() for p in text.split(",")]
					participants.extend(parts)

			break  # stop after first match

	# Clean duplicates
	participants = list(set(participants))

	return "|".join(participants)


def enrich_project(project):
	try:
		soup = get_soup(project["url"])

		# Description
		desc_tag = soup.find("p")
		description = desc_tag.get_text(strip=True) if desc_tag else ""

		# Tags
		tags = []
		for tag in soup.find_all("img", alt=True):
			alt = tag.get("alt", "")
			if alt:
				tags.append(alt)

		# External website
		external_link = ""
		for a in soup.find_all("a", href=True):
			href = a["href"]
			if href.startswith("http") and "smart-networks" not in href:
				external_link = href
				break

		# Participants
		participants = extract_participants(soup)

		project["description"] = description
		project["tags"] = ",".join(set(tags))
		project["external_website"] = external_link
		project["participants"] = participants

	except Exception as e:
		print(f"Error processing {project['name']}: {e}")
		project["description"] = ""
		project["tags"] = ""
		project["external_website"] = ""
		project["participants"] = ""

	return project


def main():
	projects = extract_projects()
	print("DEBUG sample:", projects[:5])
	print(f"Found {len(projects)} projects")

	enriched = []
	for p in projects:
		print(f"Processing: {p['name']}")
		enriched.append(enrich_project(p))
		time.sleep(1)

	with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=[
			"name", "url", "external_website", "stream", "tags", "participants", "description"
		])
		writer.writeheader()
		writer.writerows(enriched)

	print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
	main()