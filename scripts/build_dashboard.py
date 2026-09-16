"""
Regenerates data/film_dashboard.csv and dashboard/index.html from data/film.csv.

What it does, in order:
1. Downloads (or reuses if already downloaded) IMDb's free public datasets, which contain
   title/year and average rating for millions of movies. Saved in data/.imdb_cache/ and should
   not be edited by hand.
2. Reads data/film.csv (columns: movieId, title, genres — title includes the year in
   parentheses, e.g. "Toy Story (1995)"; genres is a list separated by "|").
3. Looks up each movie in the IMDb data by title+year, to recover its real average rating.
4. Assigns a "mood" (what kind of movie night this is) based on genre, using a fixed rule —
   not an exact judgment, a reasonable heuristic.
5. Writes data/film_dashboard.csv (also readable in Excel) and dashboard/index.html (the actual
   dashboard, a single self-contained HTML file that needs no internet connection to work once
   generated).

Usage:
    python scripts/build_dashboard.py

No need to rerun it unless data/film.csv changes: dashboard/index.html is already built and
working as is.
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

MOOD_ORDER = ["Friday Light", "Comfort Movie", "Adrenaline", "Mind On",
              "Date Night", "Heavy Sunday"]


def download_if_missing(url, dest):
    if dest.exists():
        print(f"  (already present) {dest.name}")
        return
    print(f"  downloading {url} ...")
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
        return "Adrenaline"
    if "Romance" in g:
        return "Date Night"
    if g & {"Documentary", "Film-Noir"}:
        return "Heavy Sunday"
    if "Drama" in g and not (g & {"Comedy", "Animation", "Children", "Musical"}):
        return "Heavy Sunday"
    if g & {"Mystery", "Sci-Fi"}:
        return "Mind On"
    if g & {"Comedy", "Children", "Animation", "Musical"}:
        return "Comfort Movie"
    return "Friday Light"


def main():
    print("1. IMDb datasets (downloading only if missing)...")
    basics_path = CACHE / "title.basics.tsv.gz"
    ratings_path = CACHE / "title.ratings.tsv.gz"
    download_if_missing(IMDB_BASICS_URL, basics_path)
    download_if_missing(IMDB_RATINGS_URL, ratings_path)

    print("2. Reading data/film.csv...")
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
    print(f"   {len(our_movies)} movies read.")

    wanted_keys = {(norm(m["name"]), m["year"]) for m in our_movies if m["year"] is not None}

    print("3. Looking up ratings in title.basics.tsv.gz (can take a couple of minutes)...")
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

    print("4. Assigning rating and mood to each movie...")
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
    print(f"   Rating found for {matched} / {len(movies)} movies.")

    print("5. Writing data/film_dashboard.csv...")
    with open(DATA / "film_dashboard.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["movieId", "title", "year", "genres", "imdb_rating", "imdb_votes",
                          "mood", "rotten_tomatoes", "mood_reason"])
        for m in movies:
            writer.writerow([m["id"], m["t"], m["y"] or "", "|".join(m["g"]),
                              m["r"] or "", m["v"] or "", m["m"], "", ""])

    print("6. Generating dashboard/index.html...")
    render_html(movies)

    print("Done. Open dashboard/index.html in a browser to see the result.")


if __name__ == "__main__":
    sys.exit(main())
