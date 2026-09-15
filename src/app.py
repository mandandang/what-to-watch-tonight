"""App per decidere cosa guardare stasera, a partire dalla lista di film in data/film.csv."""

import pandas as pd
import streamlit as st

PATH_FILM = "data/film.csv"

st.set_page_config(page_title="Cosa guardo stasera?", page_icon="🎬")
st.title("🎬 Cosa guardo stasera?")

# Carichiamo il file CSV in una tabella (DataFrame) che possiamo filtrare facilmente.
film = pd.read_csv(PATH_FILM)

# --- Filtri nella barra laterale ---
st.sidebar.header("Filtri")

generi_disponibili = sorted(film["genere"].unique())
generi_scelti = st.sidebar.multiselect(
    "Genere", generi_disponibili, default=generi_disponibili
)

durata_max = st.sidebar.slider(
    "Durata massima (minuti)", min_value=60, max_value=200, value=200
)

voto_min = st.sidebar.slider(
    "Voto minimo (IMDb)", min_value=0.0, max_value=10.0, value=0.0, step=0.1
)

piattaforme_disponibili = sorted(film["piattaforma"].unique())
piattaforme_scelte = st.sidebar.multiselect(
    "Piattaforma", piattaforme_disponibili, default=piattaforme_disponibili
)

# Applichiamo tutti i filtri scelti alla lista dei film.
film_filtrati = film[
    film["genere"].isin(generi_scelti)
    & (film["durata_minuti"] <= durata_max)
    & (film["voto_imdb"] >= voto_min)
    & film["piattaforma"].isin(piattaforme_scelte)
]

st.write(f"Film trovati con questi filtri: **{len(film_filtrati)}**")

# --- Suggerimento del film ---
if st.button("🎲 Suggeriscimi un film"):
    if film_filtrati.empty:
        st.warning("Nessun film corrisponde ai filtri scelti. Prova ad allargarli.")
    else:
        scelto = film_filtrati.sample(1).iloc[0]
        st.subheader(scelto["titolo"])
        st.write(
            f"**Anno:** {scelto['anno']}  |  **Genere:** {scelto['genere']}  |  "
            f"**Durata:** {scelto['durata_minuti']} min  |  **Voto IMDb:** {scelto['voto_imdb']}  |  "
            f"**Dove guardarlo:** {scelto['piattaforma']}"
        )
        st.write(scelto["trama"])

with st.expander("Vedi tutti i film che rispettano i filtri"):
    st.dataframe(film_filtrati, use_container_width=True)
