"""
Rigenera data/film_dashboard.csv e dashboard/index.html a partire da data/film.csv.

Cosa fa, in ordine:
1. Scarica (o riusa se gia scaricati) i dataset pubblici e gratuiti di IMDb, che contengono
   titolo/anno e voto medio per milioni di film. Vengono salvati in data/.imdb_cache/ e non
   vanno modificati a mano.
2. Legge data/film.csv (colonne: movieId, title, genres — title include l'anno tra parentesi,
   es. "Toy Story (1995)"; genres e una lista separata da "|").
3. Cerca ogni film nei dati IMDb per titolo+anno, per recuperare il voto medio reale.
4. Assegna un "mood" (che tipo di serata e adatta a quel film) in base al genere, con una
   regola fissa — non e un giudizio esatto, e un'euristica ragionevole.
5. Scrive data/film_dashboard.csv (leggibile anche in Excel) e dashboard/index.html (la
   dashboard vera e propria, un unico file HTML autonomo, senza bisogno di internet per
   funzionare una volta generato).

Uso:
    python scripts/build_dashboard.py

Non serve rilanciarlo se non cambia data/film.csv: dashboard/index.html e gia pronto e
funzionante cosi com'e.
"""

import csv
import gzip
import re
import sys
import urllib.request
from pathlib import Path

from dashboard_lib import render_html

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
CACHE = DATA / ".imdb_cache"
DASHBOARD = PROJECT / "dashboard"

IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"
IMDB_RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"

TITLE_YEAR_RE = re.compile(r"^(.*)\s\((\d{4})\)\s*$")

MOOD_ORDER = ["Venerdi leggero", "Comfort movie", "Adrenalina", "Mente accesa",
              "Da vedere in due", "Domenica impegnativa"]


def download_if_missing(url, dest):
    if dest.exists():
        print(f"  (gia presente) {dest.name}")
        return
    print(f"  scarico {url} ...")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def parse_title_year(raw_title):
    m = TITLE_YEAR_RE.match(raw_title.strip())
    if not m:
        return raw_title.strip(), None
    return m.group(1).strip(), int(m.group(2))


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def assign_mood(genres):
    g = set(genres)
    if g & {"Horror", "Thriller", "Crime", "War"}:
        return "Adrenalina"
    if "Romance" in g:
        return "Da vedere in due"
    if g & {"Documentary", "Film-Noir"}:
        return "Domenica impegnativa"
    if "Drama" in g and not (g & {"Comedy", "Animation", "Children", "Musical"}):
        return "Domenica impegnativa"
    if g & {"Mystery", "Sci-Fi"}:
        return "Mente accesa"
    if g & {"Comedy", "Children", "Animation", "Musical"}:
        return "Comfort movie"
    return "Venerdi leggero"


def main():
    print("1. Dataset IMDb (scarico solo se mancanti)...")
    basics_path = CACHE / "title.basics.tsv.gz"
    ratings_path = CACHE / "title.ratings.tsv.gz"
    download_if_missing(IMDB_BASICS_URL, basics_path)
    download_if_missing(IMDB_RATINGS_URL, ratings_path)

    print("2. Leggo data/film.csv...")
    with open(DATA / "film.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        our_movies = []
        for row in reader:
            name, year = parse_title_year(row["title"])
            our_movies.append({
                "movieId": row["movieId"],
                "name": name,
                "year": year,
                "genres": [g for g in row["genres"].split("|") if g and g != "(no genres listed)"],
            })
    print(f"   {len(our_movies)} film letti.")

    wanted_keys = {(norm(m["name"]), m["year"]) for m in our_movies if m["year"] is not None}

    print("3. Cerco i voti in title.basics.tsv.gz (puo richiedere un paio di minuti)...")
    key_to_tconst = {}
    with gzip.open(basics_path, "rt", encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {name: i for i, name in enumerate(header)}
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if parts[idx["titleType"]] not in ("movie", "tvMovie"):
                continue
            start_year = parts[idx["startYear"]]
            if start_year == r"\N":
                continue
            year = int(start_year)
            tconst = parts[idx["tconst"]]
            for t in (parts[idx["primaryTitle"]], parts[idx["originalTitle"]]):
                key = (norm(t), year)
                if key in wanted_keys and key not in key_to_tconst:
                    key_to_tconst[key] = tconst

    needed_tconsts = set(key_to_tconst.values())
    ratings = {}
    with gzip.open(ratings_path, "rt", encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {name: i for i, name in enumerate(header)}
        for line in f:
            parts = line.rstrip("\n").split("\t")
            tconst = parts[idx["tconst"]]
            if tconst in needed_tconsts:
                ratings[tconst] = (float(parts[idx["averageRating"]]), int(parts[idx["numVotes"]]))

    print("4. Assegno voto e mood a ogni film...")
    movies = []
    matched = 0
    for m in our_movies:
        rating, votes = None, None
        if m["year"] is not None:
            tconst = key_to_tconst.get((norm(m["name"]), m["year"]))
            if tconst and tconst in ratings:
                rating, votes = ratings[tconst]
                matched += 1
        movies.append({
            "id": int(m["movieId"]),
            "t": m["name"],
            "y": m["year"],
            "g": m["genres"],
            "r": rating,
            "v": votes,
            "m": assign_mood(m["genres"]),
            "rt": None,
            "mo": "",
        })
    print(f"   Voto trovato per {matched} / {len(movies)} film.")

    print("5. Scrivo data/film_dashboard.csv...")
    with open(DATA / "film_dashboard.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["movieId", "title", "anno", "genres", "voto_imdb", "num_voti_imdb",
                          "mood", "voto_rotten_tomatoes", "motivazione_mood"])
        for m in movies:
            writer.writerow([m["id"], m["t"], m["y"] or "", "|".join(m["g"]),
                              m["r"] or "", m["v"] or "", m["m"], "", ""])

    print("6. Genero dashboard/index.html...")
    render_html(movies)

    print("Fatto. Apri dashboard/index.html nel browser per vedere il risultato.")


if __name__ == "__main__":
    sys.exit(main())
