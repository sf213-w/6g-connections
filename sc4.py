import pandas as pd
import re

INPUT_XLSX = "6gconnections-new.xlsx"
OUTPUT_CSV = "6g_graph_import.csv"
ROW_LIMIT = None   # <-- Set to None for all rows

def sanitize_reltype(label):
	"""Convert to valid Cypher-safe form."""
	if pd.isna(label):
		return "RELATED_TO"
	s = str(label).strip()
	s = re.sub(r'[^0-9A-Za-z]', '_', s)
	s = re.sub(r'_+', '_', s)
	s = s.strip('_')
	if s == "":
		s = "RELATED_TO"
	if re.match(r'^\d', s):
		s = "_" + s
	return s.upper()

# --- Read Excel ---
df = pd.read_excel(INPUT_XLSX)

# --- Apply row limit if defined ---
if ROW_LIMIT is not None:
	df = df.head(ROW_LIMIT)

out = pd.DataFrame({
	"from": df["From"],
	"to": df["To"],
	"rel_label": df["Label"].apply(sanitize_reltype),
	"description": df["Description"].fillna(""),
	"role": df["Role"].fillna(""),
	"technologies": df["Technologies"].fillna(""),
	"year": df["Year ©"].fillna(""),
	"abbreviation": df["Abbreviation"].fillna(""),
	"date": df["Date"].apply(lambda d: "" if pd.isna(d) else pd.to_datetime(d).date())
})

# --- Remove empty rows ---
out = out[(out["from"] != "") & (out["to"] != "")]

# --- Optional: Limit output rows too (in case blank removal changes size) ---
if ROW_LIMIT is not None:
	out = out.head(ROW_LIMIT)

# --- Write ---
out.to_csv(OUTPUT_CSV, index=False)
print("Written:", OUTPUT_CSV, "| Rows:", len(out))
