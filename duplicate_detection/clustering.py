"""
duplicate_detection/clustering.py

Groups reports that have already been identified as duplicates
using DBSCAN clustering.

The duplicate decision itself is handled by duplicate_checker.py.
This file is responsible only for grouping duplicate reports.
"""

from sklearn.cluster import DBSCAN


def cluster_duplicate_reports(duplicate_matrix):
    """
    Group duplicate reports using DBSCAN.

    Parameters:
        duplicate_matrix:
            A square matrix where:
            - 0 = reports are considered duplicates
            - 1 = reports are not considered duplicates

    Returns:
        numpy.ndarray:
            Cluster label for each report.

            Reports with the same cluster label belong to the
            same duplicate/event group.
    """

    dbscan = DBSCAN(
        eps=0.5,
        min_samples=1,
        metric="precomputed"
    )

    labels = dbscan.fit_predict(duplicate_matrix)

    return labels


if __name__ == "__main__":
    """
    Simple standalone test.

    0 = duplicate relationship
    1 = not a duplicate relationship

    Expected result:
    - Reports 1, 2, and 3 → same cluster
    - Report 4 → separate cluster
    """

    duplicate_matrix = [
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 0]
    ]

    labels = cluster_duplicate_reports(duplicate_matrix)

    print("Cluster labels:", labels)