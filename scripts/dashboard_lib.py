"""
Funzioni condivise tra build_dashboard.py, render_dashboard.py e la skill aggiorna-cinema:
leggere data/film_dashboard.csv e generare dashboard/index.html a partire da
dashboard/template.html. Non e pensato per essere eseguito direttamente.
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
    """Legge data/film_dashboard.csv e lo trasforma nella lista di film che la dashboard si aspetta."""
    csv_path = csv_path or DASHBOARD_CSV
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    movies = []
    for row in rows:
        movies.append({
            "id": int(row["movieId"]),
            "t": row["title"],
            "y": int(row["anno"]) if row["anno"] else None,
            "g": [g for g in row["genres"].split("|") if g],
            "r": float(row["voto_imdb"]) if row.get("voto_imdb") else None,
            "v": int(row["num_voti_imdb"]) if row.get("num_voti_imdb") else None,
            "m": row["mood"],
            "rt": int(row["voto_rotten_tomatoes"]) if row.get("voto_rotten_tomatoes") else None,
            "mo": row.get("motivazione_mood") or "",
        })
    return movies


def render_html(movies=None, template_path=None, output_path=None):
    """Inietta la lista di film (come JSON) nel template HTML e scrive dashboard/index.html.

    Se `movies` non e passato, lo legge da data/film_dashboard.csv. Ogni film e un dizionario
    con le chiavi: id, t (titolo), y (anno), g (lista generi), r (voto imdb o None),
    v (numero voti imdb o None), m (mood), rt (voto rotten tomatoes o None), mo (motivazione
    del mood o stringa vuota).
    """
    movies = movies if movies is not None else load_dashboard_csv()
    template_path = template_path or TEMPLATE_HTML
    output_path = output_path or OUTPUT_HTML

    template = template_path.read_text(encoding="utf-8")
    data_json = json.dumps(movies, ensure_ascii=False, separators=(",", ":"))
    final_html = template.replace("/*__MOVIES_JSON__*/", data_json)
    output_path.write_text(final_html, encoding="utf-8")
    return output_path
