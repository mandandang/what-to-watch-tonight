# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A project for deciding what to watch tonight, based on a real movie list provided by an external
tutor (a "MovieLens"-style dataset: almost 9000 movies with title, year and genres).

The user is not a developer: in responses within this repository, always explain technical
choices simply, without assuming they can read code.

**Data status:** `data/film.csv` is the tutor's original file: columns `movieId, title,
genres` (title includes the year in parentheses, e.g. `"Toy Story (1995)"`; genres are separated
by `|`). It doesn't contain ratings or any other information.

From this file, `scripts/build_dashboard.py` generates `data/film_dashboard.csv`: the same movies
plus a **real IMDb rating** (retrieved from IMDb's free public datasets, matching by title+year —
not from 9000 individual web searches, that would be too slow) and a **mood** assigned by a fixed
rule based on genre (not a per-movie "smart" judgment, it's a heuristic: see the `assign_mood`
function in the script). The rating isn't available for every movie (about 5850 out of 8927 at
the moment) — lesser-known titles, or ones whose title differs slightly between the two sources,
are left without a rating, shown as "N/A".

From `data/film_dashboard.csv`, the same script generates `dashboard/index.html`: the actual
dashboard, ready to open.

## How to run it

**Dashboard (the main way to explore movies):** just open
[dashboard/index.html](dashboard/index.html) with a double-click, or by dragging it into a
browser. It's a single self-contained file (data included) — no internet or server needed to use
it. It has a language switcher (English/Italian) in the top-right corner, defaulting to English;
the choice is remembered per browser via `localStorage`.

To regenerate it after updating `data/film.csv` (e.g. more movies arrive, or data changes):
```bash
python scripts/build_dashboard.py
```
The first time, it downloads ~230MB of public IMDb data into `data/.imdb_cache/` (takes a few
minutes); subsequent runs reuse what's already downloaded.

**Streamlit app (`src/app.py`, created in an earlier phase of the project):** ⚠️ it's based on the
old `data/film.csv` schema (`title, year, genre, duration_minutes, imdb_rating, platform, plot`),
which no longer exists since the tutor's real file arrived — **it doesn't work as is anymore**. It
needs to be updated to read `data/film_dashboard.csv` (or removed, if the HTML dashboard is
enough) before it can be run again with:
```bash
pip install -r requirements.txt
streamlit run src/app.py
```

There are no tests or linters configured in this project (it's a simple, educational project).

## Folder structure

```
SheTech/
├── .claude/skills/update-cinema/
│   └── SKILL.md                # /update-cinema skill: enriches 20 more movies at a time
├── data/
│   ├── film.csv                 # the tutor's original file: movieId, title, genres
│   ├── film_dashboard.csv       # generated: + extracted year, imdb_rating, imdb_votes, mood, ...
│   └── .imdb_cache/               # downloaded IMDb datasets (large, regenerable, don't edit by hand)
├── dashboard/
│   ├── template.html              # dashboard structure/style/logic, no data
│   └── index.html                 # final dashboard, ready to open (template + embedded data)
├── scripts/
│   ├── dashboard_lib.py           # shared functions: reading the CSV, generating the final HTML
│   ├── build_dashboard.py         # full pipeline from scratch: download IMDb, join, mood, HTML
│   ├── render_dashboard.py        # regenerates ONLY dashboard/index.html from the existing CSV
│   ├── select_next20.py           # finds the next 20 movies without a rating (used by update-cinema)
│   └── merge_enrichment.py        # merges the 3 agents' results into the CSV (used by update-cinema)
├── src/
│   └── app.py                      # old Streamlit app, needs updating (see above) or removal
└── requirements.txt                # required Python libraries (streamlit, pandas)
```

The `data/` vs `src/`/`scripts/` separation is intentional: data (which changes whenever the
tutor sends updates) stays separate from code.

## `data/film.csv` schema (original, from the tutor)

Columns: `movieId, title, genres`. `title` includes the year in parentheses (e.g.
`"Jumanji (1995)"`); `genres` is a list of genres separated by `|` (e.g.
`Adventure|Children|Fantasy`). No ratings or other info.

**Watch out for fields containing commas:** in general, if a text value in a CSV contains a
comma, it must be wrapped in double quotes, otherwise the row gets read as if it had one extra
column and the text gets truncated. It's best to generate/edit these files with a Python script
(the `csv` module) rather than by hand.

## `data/film_dashboard.csv` schema (generated)

Columns: `movieId, title, year, genres, imdb_rating, imdb_votes, mood, rotten_tomatoes,
mood_reason`. Generated by `scripts/build_dashboard.py` — don't edit it by hand, it would be lost
on the next regeneration (use `scripts/merge_enrichment.py` instead, see below).

The `mood` field uses exactly one of these 6 categories: `Friday Light`, `Comfort Movie`,
`Adrenaline`, `Mind On`, `Date Night`, `Heavy Sunday`. At first they're assigned by a rule based
on genre (`assign_mood` function in `build_dashboard.py`) — not a per-movie judgment (with almost
9000 movies, analyzing them one by one isn't practical). The `rotten_tomatoes` and `mood_reason`
columns start empty and get filled in gradually by the `update-cinema` skill (see below), movie by
movie, along with a more accurate `mood` for those specific movies (overwriting the one assigned
by the generic rule).

## `update-cinema` skill

Defined in [`.claude/skills/update-cinema/SKILL.md`](.claude/skills/update-cinema/SKILL.md),
invocable with `/update-cinema`. Takes the next 20 movies in `film_dashboard.csv` still without an
`imdb_rating`, has three agents enrich them in parallel (real IMDb rating via web search, real
Rotten Tomatoes score via web search, mood + reason), updates the CSV and regenerates the
dashboard. Meant to be run multiple times: each run advances another 20 movies, until none are
left without a rating. Uses `scripts/select_next20.py` and `scripts/merge_enrichment.py` — read
the skill file for the exact procedure, including the precise prompts given to the three agents.

## How `dashboard/index.html` works

`dashboard/template.html` contains all the dashboard's HTML/CSS/JavaScript, with a
`/*__MOVIES_JSON__*/` placeholder where the data goes. The `render_html` function in
`scripts/dashboard_lib.py` reads it, replaces the placeholder with every movie's data (as JSON),
and writes the result to `dashboard/index.html`. That's why `index.html` is a single
self-contained file (about 1MB, data included) that works offline too, without needing a server:
opening `template.html` instead of `index.html` shows nothing, because it has no data in it. Both
`build_dashboard.py` (full pipeline) and `render_dashboard.py` (regeneration only, used by
`update-cinema`) call this same function — don't duplicate this logic elsewhere.

If you need to change the dashboard's look or behavior (colors, filters, how cards are shown),
edit `dashboard/template.html` and then rerun `python scripts/render_dashboard.py` (fast, doesn't
download anything) to regenerate `index.html` — don't edit `index.html` directly, it would get
overwritten. The UI text itself lives in the `STRINGS` object inside the template's `<script>`
block, keyed by language (`en`/`it`); add a new language by adding another key there and to
`MOOD_LABELS`, plus a button in `#langSwitch`.

## `src/app.py` architecture

A single Streamlit script, read top to bottom:

1. **Data loading** — reads `data/film.csv` into a table (`pandas.DataFrame`) on every page
   load.
2. **Filters (sidebar)** — genre, max duration, minimum rating, platform: the user picks them
   with dropdowns and sliders.
3. **Filtering** — the chosen filters are all applied together to the movie table.
4. **Suggestion** — the "Suggest a movie" button picks a random row among the filtered movies
   and shows its details; if no movie matches the filters, it shows a warning.
5. **Full list** — an expandable panel shows every movie matching the current filters, as a
   table.

There are no other code modules or files: any new feature should be added directly in
`src/app.py`, unless it grows enough to justify splitting it into multiple files (in that case,
explain why to the user before doing it).
