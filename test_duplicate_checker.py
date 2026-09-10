import json

from preprocessing.cleaner import clean_text
from duplicate_detection.embeddings import get_embedding
from duplicate_detection.duplicate_checker import check_duplicate


# Load reports
with open("data/sample_reports.json", "r", encoding="utf-8") as file:
    reports = json.load(file)


def prepare_report(report):
    cleaned_text = clean_text(report["text"])
    embedding = get_embedding(cleaned_text)

    coordinates = (
        report["location"]["latitude"],
        report["location"]["longitude"]
    )

    return {
        "report_id": report["report_id"],
        "text": report["text"],
        "embedding": embedding,
        "coordinates": coordinates,
        "timestamp": report["timestamp"]
    }


prepared_reports = [prepare_report(report) for report in reports]


# Pairs that should represent the same event
duplicate_pairs = [
    ("RPT_001", "RPT_002"),
    ("RPT_001", "RPT_003"),
    ("RPT_001", "RPT_009"),
    ("RPT_002", "RPT_003"),
    ("RPT_002", "RPT_009"),
    ("RPT_003", "RPT_009"),
    ("RPT_004", "RPT_010"),
]


# Test duplicate pairs
print("\n--- Likely Duplicate Pairs ---")

for id_a, id_b in duplicate_pairs:

    report_a = next(r for r in prepared_reports if r["report_id"] == id_a)
    report_b = next(r for r in prepared_reports if r["report_id"] == id_b)

    result = check_duplicate(
        report_a["embedding"],
        report_b["embedding"],
        report_a["coordinates"],
        report_b["coordinates"],
        report_a["timestamp"],
        report_b["timestamp"]
    )

    print(f"\n{id_a} + {id_b}")
    print("Similarity      :", result["similarity_score"])
    print("Location        :", result["location_distance_km"], "km")
    print("Location score  :", result["location_score"])
    print("Time            :", result["time_difference_minutes"], "minutes")
    print("Time score      :", result["time_score"])
    print("Duplicate score :", result["duplicate_score"])
    print("Decision        :", "DUPLICATE" if result["is_duplicate"] else "NOT DUPLICATE")
        # Pairs that should NOT represent the same event
non_duplicate_pairs = [
    ("RPT_001", "RPT_004"),
    ("RPT_005", "RPT_006"),
    ("RPT_007", "RPT_008"),
    ("RPT_003", "RPT_010"),
]


print("\n\n--- Likely Non-Duplicate Pairs ---")

for id_a, id_b in non_duplicate_pairs:

    report_a = next(r for r in prepared_reports if r["report_id"] == id_a)
    report_b = next(r for r in prepared_reports if r["report_id"] == id_b)

    result = check_duplicate(
        report_a["embedding"],
        report_b["embedding"],
        report_a["coordinates"],
        report_b["coordinates"],
        report_a["timestamp"],
        report_b["timestamp"]
    )

    print(f"\n{id_a} + {id_b}")
    print("Similarity      :", result["similarity_score"])
    print("Location        :", result["location_distance_km"], "km")
    print("Location score  :", result["location_score"])
    print("Time            :", result["time_difference_minutes"], "minutes")
    print("Time score      :", result["time_score"])
    print("Duplicate score :", result["duplicate_score"])
    print("Decision        :", "DUPLICATE" if result["is_duplicate"] else "NOT DUPLICATE")