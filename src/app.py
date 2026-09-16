"""App to decide what to watch tonight, based on the movie list in data/film.csv."""

import pandas as pd
import streamlit as st

MOVIES_PATH = "data/film.csv"

st.set_page_config(page_title="What to Watch Tonight?", page_icon="🎬")
st.title("🎬 What to Watch Tonight?")

# Load the CSV file into a table (DataFrame) that we can filter easily.
movies = pd.read_csv(MOVIES_PATH)

# --- Sidebar filters ---
st.sidebar.header("Filters")

available_genres = sorted(movies["genre"].unique())
selected_genres = st.sidebar.multiselect(
    "Genre", available_genres, default=available_genres
)

max_duration = st.sidebar.slider(
    "Max duration (minutes)", min_value=60, max_value=200, value=200
)

min_rating = st.sidebar.slider(
    "Minimum rating (IMDb)", min_value=0.0, max_value=10.0, value=0.0, step=0.1
)

available_platforms = sorted(movies["platform"].unique())
selected_platforms = st.sidebar.multiselect(
    "Platform", available_platforms, default=available_platforms
)

# Apply all the chosen filters to the movie list.
filtered_movies = movies[
    movies["genre"].isin(selected_genres)
    & (movies["duration_minutes"] <= max_duration)
    & (movies["imdb_rating"] >= min_rating)
    & movies["platform"].isin(selected_platforms)
]

st.write(f"Movies matching these filters: **{len(filtered_movies)}**")

# --- Movie suggestion ---
if st.button("🎲 Suggest a movie"):
    if filtered_movies.empty:
        st.warning("No movies match the selected filters. Try widening them.")
    else:
        pick = filtered_movies.sample(1).iloc[0]
        st.subheader(pick["title"])
        st.write(
            f"**Year:** {pick['year']}  |  **Genre:** {pick['genre']}  |  "
            f"**Duration:** {pick['duration_minutes']} min  |  **IMDb rating:** {pick['imdb_rating']}  |  "
            f"**Where to watch:** {pick['platform']}"
        )
        st.write(pick["plot"])

with st.expander("See all movies matching the filters"):
    st.dataframe(filtered_movies, use_container_width=True)
