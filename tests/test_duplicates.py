"""
tests/test_duplicates.py

Tests the duplicate detection components:
1. Text similarity
2. Location distance
3. Time difference
4. Final duplicate decision
"""

import json

from preprocessing.cleaner import clean_text
from duplicate_detection.embeddings import get_embedding
from duplicate_detection.similarity import text_similarity
from duplicate_detection.location import distance_km
from duplicate_detection.clustering import (
    time_difference_minutes,
    are_duplicates
)


# --------------------------------------------------
# Load sample reports
# --------------------------------------------------

with open("data/sample_reports.json", "r", encoding="utf-8") as file:
    reports = json.load(file)


# --------------------------------------------------
# TEST 1: Text Similarity
# --------------------------------------------------

report_a = reports[0]   # Heavy rain in Whitefield
report_b = reports[1]   # Heavy rainfall in Whitefield

text_a = clean_text(report_a["text"])
text_b = clean_text(report_b["text"])

embedding_a = get_embedding(text_a)
embedding_b = get_embedding(text_b)

similarity = text_similarity(
    embedding_a,
    embedding_b
)

print("\n--- Test 1: Text Similarity ---")
print("Report A:", report_a["text"])
print("Report B:", report_b["text"])
print("Similarity:", round(similarity, 4))

assert similarity >= 0.70

print("PASS")


# --------------------------------------------------
# TEST 2: Location Distance
# --------------------------------------------------

location_a = (
    report_a["location"]["latitude"],
    report_a["location"]["longitude"]
)

location_b = (
    report_b["location"]["latitude"],
    report_b["location"]["longitude"]
)

distance = distance_km(
    location_a,
    location_b
)

print("\n--- Test 2: Location Distance ---")
print("Distance:", round(distance, 3), "km")

assert distance <= 5.0

print("PASS")


# --------------------------------------------------
# TEST 3: Time Difference
# --------------------------------------------------

time_difference = time_difference_minutes(
    report_a["timestamp"],
    report_b["timestamp"]
)

print("\n--- Test 3: Time Difference ---")
print("Time difference:", time_difference, "minutes")

assert time_difference <= 180

print("PASS")


# --------------------------------------------------
# TEST 4: Final Duplicate Decision
# --------------------------------------------------

duplicate = are_duplicates(
    similarity=similarity,
    distance_km=distance,
    time_difference=time_difference
)

print("\n--- Test 4: Final Duplicate Decision ---")
print("Are reports duplicates?", duplicate)

assert duplicate is True

print("PASS")


# --------------------------------------------------
# Final Result
# --------------------------------------------------

print("\n================================")
print("ALL DUPLICATE TESTS PASSED!")
print("================================")