---
name: update-cinema
description: Enriches the next 20 movies of the "What to Watch Tonight?" project (this repository) that don't have a rating yet with real ratings (IMDb, Rotten Tomatoes) and a mood, then updates dashboard/index.html with the results. Use this skill when the user, working in this project, asks to update/complete/enrich the movie catalog, find more missing ratings, or explicitly says "update-cinema". It's specific to this project, not a generic data-enrichment skill.
---

# Update Cinema

Reproducibly repeats the work originally done by hand to enrich this project's movie catalog:
takes a batch of movies still without a rating, has three agents enrich them in parallel (IMDb
rating, Rotten Tomatoes score, mood), and updates the dashboard.

The project's full architectural context (CSV schema, how the dashboard works, why certain files
exist) is in [`CLAUDE.md`](../../../CLAUDE.md) at the repository root — this skill doesn't repeat
it, and assumes you've read it or will read it if needed.

This project's user is not a developer: when reporting the result, use simple, non-technical
language.

## Procedure

Follow these steps **in order**, one at a time. Don't skip step 3 (waiting for the three
agents): inventing or anticipating their results before they arrive produces fake data in a
project that exists specifically to have real ratings.

### 1. Select the movies to enrich

Run:
```bash
python scripts/select_next20.py
```
This prints the (up to) 20 movies from `data/film_dashboard.csv` that don't have an
`imdb_rating` yet, in the order they appear in the file — i.e. "the next 20". If it prints that
there are none, the catalog is already complete: stop and tell the user, no need to continue.

### 2. Launch the three agents in parallel

Launch **three** calls to the Agent tool (`subagent_type: general-purpose`) **in the same
message**, so they start in parallel. Use exactly these three prompts, replacing
`{MOVIE_LIST}` with the list printed in step 1 (title, year, genres — one movie per line).

**Agent 1 — IMDb rating:**
```
I need the REAL, current IMDb rating (0-10 scale, e.g. 8.8) for each of these movies. Use
WebSearch/WebFetch to verify each rating — don't rely purely on your internal memory, because
ratings can be slightly different from what you recall and accurate numbers are needed.

Movies (title, year):
{MOVIE_LIST}

Return ONLY a clean list, one movie per line, in exactly this format (no intro text, no extra
commentary, no numbering):

Title (Year): rating

Example of a correct line: "Inception (2010): 8.8"
```

**Agent 2 — Rotten Tomatoes score:**
```
I need the REAL Rotten Tomatoes critics score (the "Tomatometer", as a percentage, e.g. 87%) for
each of these movies. Use WebSearch/WebFetch to verify each score — don't rely purely on your
internal memory.

Movies (title, year):
{MOVIE_LIST}

Return ONLY a clean list, one movie per line, in exactly this format (no intro text, no extra
commentary, no numbering):

Title (Year): percentage%

Example of a correct line: "Inception (2010): 87%"
```

**Agent 3 — mood:**
```
I need to classify each of these movies by "mood": what kind of movie night it's suited for.
For each movie pick EXACTLY ONE of these 6 categories (use the exact text, don't invent others):
"Friday Light", "Comfort Movie", "Adrenaline", "Mind On", "Date Night", "Heavy Sunday".

Don't rely only on the listed genre: if you know the movie, use its plot and tone too to pick the
most sensible mood; if you don't know it, do a quick web search before answering.

Movies (title, year, genres):
{MOVIE_LIST}

Return ONLY a clean list, one movie per line, in exactly this format (no intro text, no extra
commentary, no numbering), with the reason in English on one line, max 20 words:

Title (Year): Mood — reason

Example of a correct line: "Inception (2010): Mind On — layered dream-heist plot that demands
constant attention to follow."
```

Launch all three in the background (the Agent tool's default behavior).

### 3. Wait for all three to complete

Don't proceed until **all three** completion notifications have arrived. If one is late, keep
waiting — don't fill the gap with a made-up result.

### 4. Merge the results into the CSV

Save each agent's returned text into three temporary files (use your scratchpad folder), then
run:
```bash
python scripts/merge_enrichment.py --imdb <path_to_imdb.txt> --rt <path_to_rt.txt> --mood <path_to_mood.txt>
```
This script updates `data/film_dashboard.csv` using Python's `csv` module (never by hand — in
this project, an unquoted comma inside a text field once caused a bug that truncated data). It
only updates the rows matching the movies just processed; every other row stays untouched. The
script prints how many rows it updated and flags any movies the agents returned that it couldn't
find in the CSV (slightly different title/year).

### 5. Regenerate the dashboard

```bash
python scripts/render_dashboard.py
```
Regenerates `dashboard/index.html` from the freshly updated data (doesn't re-download or
recompute anything — it's just injecting the data into the template, so it's instant). **Don't
use `scripts/build_dashboard.py` for this step**: it would redo the bulk IMDb join from scratch
and reassign the generic genre-based mood to every movie, wiping out the enrichment just done.

### 6. Show the result

Open `dashboard/index.html` to show the user: start a small local server
(`python -m http.server` inside the `dashboard/` folder), open it in the preview browser, check
that one or two of the just-enriched movies show the new rating/mood, then stop the server and
open the actual file for the user (on Windows: `start "" "dashboard\index.html"`).

### 7. Report the result

In simple language, tell the user: how many of the processed movies found a real rating (some
very obscure titles might not find one even with a search — that's fine, they'll be picked again
automatically next time this skill is used, since a movie without a rating is exactly the
criterion used to reselect it), and that the dashboard has been updated.
