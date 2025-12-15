import pandas as pd
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ---------- CONFIG ----------
INPUT_XLSX = "6gconnections-new.xlsx"
OUTPUT_CYPHER = "import_graph.cypher"
# ----------------------------


# Escape ALL Cypher string values (including long descriptions)
def cypher_escape(s):
	if s is None:
		return "null"
	if not isinstance(s, str):
		s = str(s)

	s = s.strip()

	# Remove accidental triple-quoted or double-quoted Excel wrappers
	if s.startswith('"""') and s.endswith('"""'):
		s = s[3:-3].strip()
	if s.startswith('"') and s.endswith('"'):
		s = s[1:-1].strip()

	# Collapse whitespace (convert all newlines to single spaces)
	s = " ".join(s.split())

	# Escape single quotes for Cypher
	s = s.replace("'", "''")

	# Remove control characters
	s = re.sub(r'[\x00-\x1f\x7f]', ' ', s)

	return f"'{s}'"


# Sanitize relationship type
def sanitize_reltype(label):
	if label is None:
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


def normalize_name(name):
	if pd.isna(name):
		return ""
	return str(name).strip()


def format_date_for_cypher(date_val):
	if pd.isna(date_val) or date_val is None or str(date_val).strip() == "":
		return "null"
	try:
		ts = pd.to_datetime(date_val)
		return cypher_escape(ts.date().isoformat())
	except Exception:
		return cypher_escape(str(date_val).strip())


def generate_cypher(df):
	lines = []

	# Constraints
	lines.append("// Create uniqueness constraint on Entity.name (if not exists)")
	lines.append("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE;")
	lines.append("")

	for idx, row in df.iterrows():
		from_name = normalize_name(row.get("From", ""))
		to_name   = normalize_name(row.get("To", ""))
		label     = normalize_name(row.get("Label", ""))
		description = row.get("Description", "")
		role = normalize_name(row.get("Role", ""))
		technologies = normalize_name(row.get("Technologies", ""))
		year = normalize_name(row.get("Year ©", row.get("Year", "")))
		abbrev = normalize_name(row.get("Abbreviation", ""))

		if from_name == "" or to_name == "":
			continue

		# ----------- NODE A -----------
		lines.append(f"MERGE (a:Entity {{name: {cypher_escape(from_name)}}})")
		lines.append("ON CREATE SET a.entity_type = 'Entity';")
		lines.append("")

		# ----------- NODE B -----------
		lines.append(f"MERGE (b:Entity {{name: {cypher_escape(to_name)}}})")
		lines.append("ON CREATE SET b.entity_type = 'Entity';")
		lines.append("")

		# -------- RELATIONSHIP STRUCTURE --------
		reltype = sanitize_reltype(label)
		date_literal = format_date_for_cypher(row.get("Date", None))

		lines.append(f"MERGE (a)-[r:{reltype}]->(b)")

		# -------- NON-DESCRIPTION PROPS --------
		non_desc_props = []

		if role:
			non_desc_props.append(f"role: {cypher_escape(role)}")
		if technologies:
			non_desc_props.append(f"technologies: {cypher_escape(technologies)}")
		if year:
			non_desc_props.append(f"year: {cypher_escape(year)}")
		if abbrev:
			non_desc_props.append(f"abbreviation: {cypher_escape(abbrev)}")
		if date_literal != "null":
			non_desc_props.append(f"date: {date_literal}")

		if non_desc_props:
			props_map = "{ " + ", ".join(non_desc_props) + " }"
			lines.append(f"SET r += {props_map};")

		# -------- DESCRIPTION --------
		if description and str(description).strip() != "":
			desc_literal = cypher_escape(str(description))
			lines.append(f"SET r.description = {desc_literal};")

		lines.append("")

	return "\n".join(lines)


if __name__ == "__main__":
	df = pd.read_excel(INPUT_XLSX)
	cypher_text = generate_cypher(df)

	with open(OUTPUT_CYPHER, "w", encoding="utf-8") as f:
		f.write("// Cypher generated from Excel\n")
		f.write(f"// Source: {INPUT_XLSX}\n\n")
		f.write(cypher_text)

	print(f"Written {OUTPUT_CYPHER} ({len(cypher_text.splitlines())} lines)")
