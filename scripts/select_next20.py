"""
Trova i film di data/film_dashboard.csv che non hanno ancora un voto_imdb, e stampa i primi 20
(nell'ordine in cui compaiono nel file) in un formato pronto da usare nei prompt dei tre agenti
di arricchimento. Usato dalla skill aggiorna-cinema.

Uso:
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
    missing = [r for r in rows if not r.get("voto_imdb")]
    return missing[:n]


def main():
    movies = select_next(20)
    if not movies:
        print("Nessun film senza voto: sono gia tutti arricchiti.")
        return
    print(f"{len(movies)} film selezionati (ancora senza voto):\n")
    for i, m in enumerate(movies, 1):
        year = m["anno"] or "?"
        genres = m["genres"].replace("|", ", ")
        print(f"{i}. {m['title']} ({year}) - {genres}")


if __name__ == "__main__":
    sys.exit(main())
