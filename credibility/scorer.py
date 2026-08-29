"""
credibility/scorer.py

Rule-based 0-100 credibility scoring for a report.

Phase 5 — not built yet. Placeholder so the project structure is ready.

Planned scoring rules:
    Location available          +20
    Photo available              +15
    Timestamp available          +10
    Established source/account   +15
    Detailed description         +10
    Corroborating reports        +30
    Maximum                      100

80-100 HIGH | 60-79 MEDIUM | 40-59 LOW | 0-39 VERY LOW
"""

# TODO: implement after duplicate detection / event grouping is working,
# since corroboration count depends on duplicate_group_id.
