"""
duplicate_detection/time_difference.py

Calculates the time difference between two weather reports.
"""

from datetime import datetime


def time_difference_minutes(timestamp_a: str, timestamp_b: str) -> float:
    """
    Calculate the absolute time difference between two timestamps.

    Returns:
        Difference in minutes.
    """

    if not timestamp_a or not timestamp_b:
        return float("inf")

    time_a = datetime.fromisoformat(timestamp_a.replace("Z", "+00:00"))
    time_b = datetime.fromisoformat(timestamp_b.replace("Z", "+00:00"))

    difference = abs((time_a - time_b).total_seconds()) / 60

    return difference


if __name__ == "__main__":
    timestamp_a = "2026-08-29T10:00:00Z"
    timestamp_b = "2026-08-29T10:30:00Z"

    difference = time_difference_minutes(timestamp_a, timestamp_b)

    print("Time difference:", difference, "minutes")