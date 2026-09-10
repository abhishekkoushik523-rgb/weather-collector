import json
from preprocessing.cleaner import clean_text

with open("data/sample_reports.json", "r", encoding="utf-8") as file:
    reports = json.load(file)

for report in reports:
    original = report["text"]
    cleaned = clean_text(original)

    print(f"\nID: {report['report_id']}")
    print("Original:", original)
    print("Cleaned :", cleaned)