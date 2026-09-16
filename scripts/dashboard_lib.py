"""
Shared functions used by build_dashboard.py, render_dashboard.py and the update-cinema skill:
reading data/film_dashboard.csv and generating dashboard/index.html from dashboard/template.html.
Not meant to be run directly.
"""

import csv
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
DASHBOARD = PROJECT / "dashboard"
DASHBOARD_CSV = DATA / "film_dashboard.csv"
TEMPLATE_HTML = DASHBOARD / "template.html"
OUTPUT_HTML = DASHBOARD / "index.html"


def load_dashboard_csv(csv_path=None):
    """Reads data/film_dashboard.csv and turns it into the list of movies the dashboard expects."""
    csv_path = csv_path or DASHBOARD_CSV
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    movies = []
    for row in rows:
        movies.append({
            "id": int(row["movieId"]),
            "t": row["title"],
            "y": int(row["year"]) if row["year"] else None,
            "g": [g for g in row["genres"].split("|") if g],
            "r": float(row["imdb_rating"]) if row.get("imdb_rating") else None,
            "v": int(row["imdb_votes"]) if row.get("imdb_votes") else None,
            "m": row["mood"],
            "rt": int(row["rotten_tomatoes"]) if row.get("rotten_tomatoes") else None,
            "mo": row.get("mood_reason") or "",
        })
    return movies


def render_html(movies=None, template_path=None, output_path=None):
    """Injects the list of movies (as JSON) into the HTML template and writes dashboard/index.html.

    If `movies` isn't passed, it's read from data/film_dashboard.csv. Each movie is a dict with
    these keys: id, t (title), y (year), g (genre list), r (imdb rating or None),
    v (imdb vote count or None), m (mood), rt (rotten tomatoes score or None), mo (mood reason,
    empty string if none).
    """
    movies = movies if movies is not None else load_dashboard_csv()
    template_path = template_path or TEMPLATE_HTML
    output_path = output_path or OUTPUT_HTML

    template = template_path.read_text(encoding="utf-8")
    data_json = json.dumps(movies, ensure_ascii=False, separators=(",", ":"))
    final_html = template.replace("/*__MOVIES_JSON__*/", data_json)
    output_path.write_text(final_html, encoding="utf-8")
    return output_path
