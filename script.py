import pandas as pd
import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

SERPER_API_KEY = "4280f7a7430cc52dbddaa12ade4e97087ae37340"
LLM_ENDPOINT = "http://localhost:11434/api/generate"	# Llama 3.2 local
	
def search_web(query):
	headers = {
		"X-API-KEY": SERPER_API_KEY,
		"Content-Type": "application/json"
	}
	payload = {
		"q": query,
		"num": 5
	}
	r = requests.post("https://google.serper.dev/search", json=payload, headers=headers)
	return r.json()

def run_llm_summary(text, label, tags):
	prompt = f"""
		You are generating a short initiative description for a spreadsheet.
		
		Write **only** a 3–4 sentence description of the initiative.
		Do NOT include:
		- introductions
		- explanations
		- phrases like "Here is a description"
		- meta-text of any kind
		
		Context:
		Label: {label}
		Tags: {tags}
		
		Information from search:
		{text}
		"""
	
	body = {
		"model": "llama3.2",
		"prompt": prompt
	}
	resp = requests.post(LLM_ENDPOINT, json=body, stream=True)

	full_text = ""

	# Ollama sometimes returns NDJSON (one JSON per line)
	for line in resp.iter_lines():
		if not line:
			continue
		try:
			obj = json.loads(line.decode("utf-8"))
			full_text += obj.get("response", "")
		except:
			# fallback for lines that are already plain text
			full_text += line.decode("utf-8")

	return full_text.strip()

	# resp = requests.post(LLM_ENDPOINT, json=body).json()
	# return resp.get("response", "").strip()

def process_excel(path):
	df = pd.read_excel(path)
	MAX_ROWS = 10
	count = 0

	for idx, row in df.iterrows():
		if count >= MAX_ROWS:
			break
		count += 1

		description = str(row["Description"]).strip()
		
		if description == "" or description.lower() == "nan":
			
			label = str(row["Label"])
			tags = str(row["Tags"])
			date_str = str(row["Date"])
			
			# Handle missing dates gracefully
			try:
				date = pd.to_datetime(date_str)
			except:
				date = None
			# Build time window if Date is valid
			if date is not None:
				start = date - relativedelta(months=1)
				end = date + relativedelta(months=2)
				query = (
					f"{label} {tags} news updates between {start.date()} and {end.date()}"
				)
			else:
				query = f"{label} {tags} initiative news"
			print(f"Searching: {query}")
			search_data = search_web(query)
			snippets = ""
			top_source = ""
			if "organic" in search_data:
				for item in search_data["organic"]:
					title = item.get("title", "")
					snippet = item.get("snippet", "")
					link = item.get("link", "")
					
					if top_source == "":
						top_source = link
					
					snippets += f"{title}: {snippet}\n"
			if snippets.strip() == "":
				snippets = "No data found online."
			summary = run_llm_summary(snippets, label, tags)
			df.at[idx, "Description"] = summary
			df.at[idx, "Source_1"] = top_source
			
	df.to_excel("6gconnections-new.xlsx", index=False)
	
	print("Completed: 6gconnections-new.xlsx")

if __name__ == "__main__":
	process_excel("6gconnections-new.xlsx")
