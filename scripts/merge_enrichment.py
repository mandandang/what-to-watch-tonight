"""
Aggiorna data/film_dashboard.csv con i risultati dei tre agenti di arricchimento (voto IMDb,
voto Rotten Tomatoes, mood + motivazione). Usato dalla skill aggiorna-cinema — non e pensato
per essere lanciato a mano, ma si puo fare per capire/debuggare cosa succede.

Ognuno dei tre input e un file di testo con una riga per film, ESATTAMENTE nel formato che i tre
agenti restituiscono:
  --imdb: righe "Titolo (Anno): voto"            es. "Inception (2010): 8.8"
  --rt:   righe "Titolo (Anno): percentuale%"     es. "Inception (2010): 87%"
  --mood: righe "Titolo (Anno): Mood — motivazione"

Il match tra le righe di questi file e le righe di data/film_dashboard.csv avviene su
titolo+anno, ignorando maiuscole/minuscole e punteggiatura (cosi piccole differenze di
formattazione tra quello che scrive l'agente e quello che c'e nel CSV non rompono tutto).

Aggiorna SOLO le righe il cui titolo+anno viene trovato in questi file; tutte le altre righe del
CSV restano invariate. Aggiunge le colonne voto_rotten_tomatoes e motivazione_mood se non
esistono ancora (capita se il CSV e stato generato da una versione vecchia di build_dashboard.py).

Uso:
    python scripts/merge_enrichment.py --imdb imdb.txt --rt rt.txt --mood mood.txt
"""

import argparse
import csv
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = DATA / "film_dashboard.csv"

LINE_RE = re.compile(r"^\s*(.+?)\s\((\d{4})\)\s*:\s*(.+?)\s*$")
MOOD_SEPARATORS = (" — ", " - ", "—", "-")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def parse_lines(path):
    result = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = LINE_RE.match(line)
            if not m:
                continue
            title, year, value = m.groups()
            result[(norm(title), int(year))] = value
    return result


def parse_mood_value(value):
    for sep in MOOD_SEPARATORS:
        if sep in value:
            mood, _, motivazione = value.partition(sep)
            return mood.strip(), motivazione.strip()
    return value.strip(), ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--imdb", required=True, help="file di testo con i voti IMDb")
    parser.add_argument("--rt", required=True, help="file di testo con i voti Rotten Tomatoes")
    parser.add_argument("--mood", required=True, help="file di testo con mood + motivazione")
    args = parser.parse_args()

    imdb = parse_lines(args.imdb)
    rt = parse_lines(args.rt)
    mood = {k: parse_mood_value(v) for k, v in parse_lines(args.mood).items()}

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    for col in ("voto_rotten_tomatoes", "motivazione_mood"):
        if col not in fieldnames:
            fieldnames.append(col)
        for row in rows:
            row.setdefault(col, "")

    updated = 0
    all_keys_seen = set(imdb) | set(rt) | set(mood)
    matched_keys = set()
    for row in rows:
        if not row.get("anno"):
            continue
        key = (norm(row["title"]), int(row["anno"]))
        touched = False
        if key in imdb:
            row["voto_imdb"] = imdb[key]
            touched = True
        if key in rt:
            row["voto_rotten_tomatoes"] = rt[key].rstrip("%")
            touched = True
        if key in mood:
            row["mood"], row["motivazione_mood"] = mood[key]
            touched = True
        if touched:
            updated += 1
            matched_keys.add(key)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Aggiornate {updated} righe in {CSV_PATH.name}.")
    unmatched = all_keys_seen - matched_keys
    if unmatched:
        print(f"Attenzione: {len(unmatched)} film restituiti dagli agenti non hanno trovato "
              f"una corrispondenza esatta nel CSV (titolo o anno leggermente diversi?).")


if __name__ == "__main__":
    sys.exit(main())
