"""
duplicate_detection/duplicate_checker.py

Combines text similarity, location distance,
and time difference into an explainable
duplicate score.
"""

from duplicate_detection.similarity import text_similarity
from duplicate_detection.location import distance_km
from duplicate_detection.time_difference import time_difference_minutes


# Maximum ranges used to normalize location and time.
LOCATION_THRESHOLD_KM = 5.0
TIME_THRESHOLD_MINUTES = 60.0

# Weights for the three signals.
TEXT_WEIGHT = 0.50
LOCATION_WEIGHT = 0.25
TIME_WEIGHT = 0.25

# Initial decision threshold.
DUPLICATE_SCORE_THRESHOLD = 0.60


def normalize_location(distance: float) -> float:
    """
    Convert location distance into a 0-1 closeness score.

    0 km  -> 1.0
    5 km  -> 0.0
    """

    if distance == float("inf"):
        return 0.0

    score = 1 - (distance / LOCATION_THRESHOLD_KM)

    return max(0.0, min(1.0, score))


def normalize_time(minutes: float) -> float:
    """
    Convert time difference into a 0-1 closeness score.

    0 minutes  -> 1.0
    60 minutes -> 0.0
    """

    if minutes == float("inf"):
        return 0.0

    score = 1 - (minutes / TIME_THRESHOLD_MINUTES)

    return max(0.0, min(1.0, score))


def check_duplicate(
    embedding_a,
    embedding_b,
    coord_a,
    coord_b,
    timestamp_a,
    timestamp_b
) -> dict:
    """
    Compare two reports using text, location, and time.

    Returns detailed scores and the final decision.
    """

    # Calculate raw signals.
    similarity = text_similarity(
        embedding_a,
        embedding_b
    )

    location_distance = distance_km(
        coord_a,
        coord_b
    )

    time_difference = time_difference_minutes(
        timestamp_a,
        timestamp_b
    )

    # Normalize location and time.
    location_score = normalize_location(
        location_distance
    )

    time_score = normalize_time(
        time_difference
    )

    # Text similarity is already approximately 0-1
    # for our Sentence Transformer cosine similarity.
    text_score = max(0.0, min(1.0, similarity))

    # Calculate weighted duplicate score.
    duplicate_score = (
        text_score * TEXT_WEIGHT
        + location_score * LOCATION_WEIGHT
        + time_score * TIME_WEIGHT
    )

    # Final decision.
    duplicate = duplicate_score >= DUPLICATE_SCORE_THRESHOLD

    return {
        "is_duplicate": duplicate,
        "duplicate_score": round(duplicate_score, 4),
        "similarity_score": round(similarity, 4),
        "location_distance_km": round(location_distance, 3),
        "location_score": round(location_score, 4),
        "time_difference_minutes": round(time_difference, 2),
        "time_score": round(time_score, 4)
    }


def is_duplicate(
    embedding_a,
    embedding_b,
    coord_a,
    coord_b,
    timestamp_a,
    timestamp_b
) -> bool:
    """
    Backwards-compatible function that returns only True/False.
    """

    result = check_duplicate(
        embedding_a,
        embedding_b,
        coord_a,
        coord_b,
        timestamp_a,
        timestamp_b
    )

    return result["is_duplicate"]