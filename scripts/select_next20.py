"""
Finds the movies in data/film_dashboard.csv that don't have an imdb_rating yet, and prints the
first 20 (in the order they appear in the file) in a format ready to use in the three enrichment
agents' prompts. Used by the update-cinema skill.

Usage:
    python scripts/select_next20.py
"""

import csv
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DASHBOARD_CSV = DATA / "film_dashboard.csv"


def select_next(n=20, csv_path=None):
    csv_path = csv_path or DASHBOARD_CSV
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = [r for r in rows if not r.get("imdb_rating")]
    return missing[:n]


def main():
    movies = select_next(20)
    if not movies:
        print("No movies without a rating: the catalog is already fully enriched.")
        return
    print(f"{len(movies)} movies selected (still without a rating):\n")
    for i, m in enumerate(movies, 1):
        year = m["year"] or "?"
        genres = m["genres"].replace("|", ", ")
        print(f"{i}. {m['title']} ({year}) - {genres}")


if __name__ == "__main__":
    sys.exit(main())
