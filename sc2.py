import pandas as pd
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta

SERPER_API_KEY = "4280f7a7430cc52dbddaa12ade4e97087ae37340"


# -----------------------------------------
# Utility: Safe string
# -----------------------------------------
def safe_str(value):
	v = str(value).strip()
	return "" if v.lower() == "nan" else v


# -----------------------------------------
# SERPER (Google) Search
# -----------------------------------------
def google_search(query):
	headers = {
		"X-API-KEY": SERPER_API_KEY,
		"Content-Type": "application/json"
	}
	payload = {
		"q": query,
		"num": 10   # get more results for better summaries
	}

	r = requests.post("https://google.serper.dev/search", json=payload)

	try:
		return r.json()
	except:
		print("\n[SERPER ERROR] Non-JSON response:")
		print(r.text[:500])
		return {}


# -----------------------------------------
# Build 3–4 sentence summary from SERPER
# -----------------------------------------
def build_summary_from_snippets(organic_results):
	snippets = []

	for item in organic_results:
		title = item.get("title", "")
		snippet = item.get("snippet", "")
		if snippet:
			snippets.append(f"{title}: {snippet}")

	if not snippets:
		return "No online summary or snippet information was available."

	# Combine into a readable paragraph
	summary_text = " ".join(snippets)

	# Limit to ~3–4 sentences
	sentences = summary_text.split(". ")
	return ". ".join(sentences[:4]).strip() + "."


# -----------------------------------------
# Process Excel
# -----------------------------------------
def process_excel(path):
	df = pd.read_excel(path)

	for idx, row in df.iterrows():
		description = str(row["Description"]).strip()

		# Skip rows that already have a Description
		if description and description.lower() != "nan":
			continue

		label = safe_str(row["Label"])
		tags  = safe_str(row["Tags"])
		date_str = str(row["Date"])

		# Parse the date
		date = pd.to_datetime(date_str, errors="coerce")

		# Build query with date window
		if not pd.isna(date):
			start = date - relativedelta(months=1)
			end = date + relativedelta(months=2)
			query = f"{label} {tags} news between {start.date()} and {end.date()}"
		else:
			query = f"{label} {tags} initiative news"

		print(f"Searching Google via SERPER: {query}")

		search_data = google_search(query)

		# Handle missing results
		if "organic" in search_data and search_data["organic"]:
			organic = search_data["organic"]

			# top source URL
			source = organic[0].get("link", "")

			# summary
			summary = build_summary_from_snippets(organic)
		else:
			source = ""
			summary = "No online summary found."

		# Write back into DataFrame
		df.at[idx, "Description"] = summary
		df.at[idx, "Source_1"]   = source

	# Save result
	df.to_excel("6gconnections-new.xlsx", index=False)
	print("Completed: 6gconnections-new.xlsx")


if __name__ == "__main__":
	process_excel("6gconnections-new.xlsx")
