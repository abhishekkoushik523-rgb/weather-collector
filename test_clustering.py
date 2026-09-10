import json

import numpy as np

from preprocessing.cleaner import clean_text
from duplicate_detection.embeddings import get_embedding
from duplicate_detection.duplicate_checker import check_duplicate
from duplicate_detection.clustering import cluster_duplicate_reports


# Load reports
with open("data/sample_reports.json", "r", encoding="utf-8") as file:
    reports = json.load(file)


# Prepare reports
prepared_reports = []

for report in reports:

    cleaned_text = clean_text(report["text"])
    embedding = get_embedding(cleaned_text)

    coordinates = (
        report["location"]["latitude"],
        report["location"]["longitude"]
    )

    prepared_reports.append({
        "report_id": report["report_id"],
        "embedding": embedding,
        "coordinates": coordinates,
        "timestamp": report["timestamp"]
    })


# Number of reports
n = len(prepared_reports)


# Create a matrix.
# 0 = likely duplicate
# 1 = not duplicate
duplicate_matrix = np.ones((n, n))


# A report is identical to itself
np.fill_diagonal(duplicate_matrix, 0)


# Compare every pair of reports
for i in range(n):

    for j in range(i + 1, n):

        report_a = prepared_reports[i]
        report_b = prepared_reports[j]

        result = check_duplicate(
            report_a["embedding"],
            report_b["embedding"],
            report_a["coordinates"],
            report_b["coordinates"],
            report_a["timestamp"],
            report_b["timestamp"]
        )

        if result["is_duplicate"]:
            duplicate_matrix[i][j] = 0
            duplicate_matrix[j][i] = 0


# Run DBSCAN
labels = cluster_duplicate_reports(duplicate_matrix)


print("\n--- Clustering Test ---")

for i, report in enumerate(prepared_reports):
    print(
        report["report_id"],
        "→ Cluster",
        labels[i]
    )


print("\nDuplicate Matrix:")
print(duplicate_matrix)