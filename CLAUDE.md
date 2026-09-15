# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Cos'è questo progetto

Un progetto per decidere cosa guardare la sera, a partire da una lista di film reale fornita da un
tutor esterno (dataset in stile "MovieLens": quasi 9000 film con titolo, anno e generi).

L'utente non è uno sviluppatore: nelle risposte in questo repository, spiega sempre le scelte
tecniche in modo semplice, senza dare per scontato che sappia leggere codice.

**Stato dei dati:** `data/film.csv` è il file originale del tutor: colonne `movieId, title,
genres` (il titolo include l'anno tra parentesi, es. `"Toy Story (1995)"`; i generi sono separati
da `|`). Non contiene voti né altre informazioni.

Da questo file, `scripts/build_dashboard.py` genera `data/film_dashboard.csv`: gli stessi film con
in più il **voto IMDb reale** (recuperato dai dataset pubblici e gratuiti di IMDb, incrociando
titolo+anno — non da 9000 ricerche web una per una, sarebbe troppo lento) e un **mood** assegnato
con una regola fissa basata sul genere (non è un giudizio "intelligente" per singolo film, è
un'euristica: vedi la funzione `assign_mood` nello script). Il voto non è disponibile per tutti i
film (circa 5850 su 8927 al momento) — quelli meno noti o con titolo leggermente diverso tra le due
fonti restano senza voto, mostrato come "N/D".

Da `data/film_dashboard.csv`, lo stesso script genera `dashboard/index.html`: la dashboard vera e
propria, pronta da aprire.

## Come si esegue

**Dashboard (il modo principale di esplorare i film):** apri semplicemente
[dashboard/index.html](dashboard/index.html) con un doppio click, o trascinandolo in un browser.
È un unico file autonomo (dati inclusi), non serve internet né un server per usarlo.

Per rigenerarlo dopo un aggiornamento di `data/film.csv` (es. arrivano più film, o cambiano i
dati):
```bash
python scripts/build_dashboard.py
```
La prima volta scarica ~230MB di dati IMDb pubblici in `data/.imdb_cache/` (ci mette qualche
minuto); le volte successive riusa quelli già scaricati.

**App Streamlit (`src/app.py`, creata in una fase precedente del progetto):** ⚠️ è basata sul
vecchio schema di `data/film.csv` (`titolo, anno, genere, durata_minuti, voto_imdb, piattaforma,
trama`), che non esiste più da quando è arrivato il file vero dal tutor — **non funziona più così
com'è**. Va aggiornata per leggere `data/film_dashboard.csv` (o rimossa, se la dashboard HTML basta)
prima di poterla rilanciare con:
```bash
pip install -r requirements.txt
streamlit run src/app.py
```

Non ci sono test né linter configurati in questo progetto (è un progetto didattico, semplice).

## Struttura delle cartelle

```
SheTech/
├── .claude/skills/aggiorna-cinema/
│   └── SKILL.md               # skill /aggiorna-cinema: arricchisce altri 20 film alla volta
├── data/
│   ├── film.csv               # file originale del tutor: movieId, title, genres
│   ├── film_dashboard.csv     # generato: + anno estratto, voto_imdb, num_voti_imdb, mood, ...
│   └── .imdb_cache/            # dataset IMDb scaricati (grossi, rigenerabili, non modificare a mano)
├── dashboard/
│   ├── template.html           # struttura/stile/logica della dashboard, senza dati
│   └── index.html              # dashboard finale pronta da aprire (template + dati incorporati)
├── scripts/
│   ├── dashboard_lib.py        # funzioni condivise: leggere il CSV, generare l'HTML finale
│   ├── build_dashboard.py      # pipeline completa da zero: scarica IMDb, join, mood, HTML
│   ├── render_dashboard.py     # rigenera SOLO dashboard/index.html dal CSV gia' presente
│   ├── select_next20.py        # trova i prossimi 20 film senza voto (usato da aggiorna-cinema)
│   └── merge_enrichment.py     # unisce i risultati dei 3 agenti nel CSV (usato da aggiorna-cinema)
├── src/
│   └── app.py                   # vecchia app Streamlit, da aggiornare (vedi sopra) o rimuovere
└── requirements.txt             # librerie Python necessarie (streamlit, pandas)
```

La separazione `data/` vs `src/`/`scripts/` è intenzionale: i dati (che cambiano quando il tutor
manda aggiornamenti) restano separati dal codice.

## Schema di `data/film.csv` (originale, dal tutor)

Colonne: `movieId, title, genres`. `title` include l'anno tra parentesi (es. `"Jumanji (1995)"`);
`genres` è una lista di generi separati da `|` (es. `Adventure|Children|Fantasy`). Non ha voti né
altre informazioni.

**Attenzione ai campi con virgole:** in generale, se un testo in un CSV contiene una virgola, va
racchiuso tra virgolette doppie, altrimenti la riga viene letta come se avesse una colonna in più
e il testo si tronca. Meglio generare/modificare questi file con uno script Python (modulo `csv`)
piuttosto che a mano.

## Schema di `data/film_dashboard.csv` (generato)

Colonne: `movieId, title, anno, genres, voto_imdb, num_voti_imdb, mood, voto_rotten_tomatoes,
motivazione_mood`. Generato da `scripts/build_dashboard.py` — non modificarlo a mano, si
perderebbe al prossimo rigeneramento (usa invece `scripts/merge_enrichment.py`, vedi sotto).

Il campo `mood` usa esattamente una di queste 6 categorie: `Venerdi leggero`, `Comfort movie`,
`Adrenalina`, `Mente accesa`, `Da vedere in due`, `Domenica impegnativa`. All'inizio sono
assegnate da una regola basata sul genere (funzione `assign_mood` in `build_dashboard.py`) — non
un giudizio caso per caso (con quasi 9000 film non è praticabile analizzarli uno a uno). Le
colonne `voto_rotten_tomatoes` e `motivazione_mood` partono vuote e vengono riempite a poco a
poco dalla skill `aggiorna-cinema` (vedi sotto), film per film, insieme a un `mood` più accurato
per quei film specifici (che sovrascrive quello assegnato dalla regola generica).

## Skill `aggiorna-cinema`

Definita in [`.claude/skills/aggiorna-cinema/SKILL.md`](.claude/skills/aggiorna-cinema/SKILL.md),
invocabile con `/aggiorna-cinema`. Prende i prossimi 20 film di `film_dashboard.csv` ancora senza
`voto_imdb`, li fa arricchire da tre agenti in parallelo (voto IMDb reale via ricerca web, voto
Rotten Tomatoes via ricerca web, mood + motivazione), aggiorna il CSV e rigenera la dashboard.
Pensata per essere rilanciata più volte: ogni volta avanza di altri 20 film, finché non ne restano
senza voto. Usa `scripts/select_next20.py` e `scripts/merge_enrichment.py` — leggi il file della
skill per la procedura esatta, coi prompt precisi da dare ai tre agenti.

## Come funziona `dashboard/index.html`

`dashboard/template.html` contiene tutto l'HTML/CSS/JavaScript della dashboard, con un
segnaposto `/*__MOVIES_JSON__*/` al posto dei dati. La funzione `render_html` in
`scripts/dashboard_lib.py` lo legge, sostituisce il segnaposto con i dati di tutti i film (in
formato JSON), e scrive il risultato in `dashboard/index.html`. Per questo `index.html` è un
unico file autonomo (circa 1MB, dati compresi) che funziona anche offline, senza bisogno di un
server: aprendo `template.html` invece di `index.html` non si vede nulla, perché non contiene
dati. Sia `build_dashboard.py` (pipeline completa) sia `render_dashboard.py` (solo rigenerazione,
usato da `aggiorna-cinema`) richiamano questa stessa funzione — non duplicare questa logica altrove.

Se serve modificare grafica o comportamento della dashboard (colori, filtri, come sono mostrate le
card), modificare `dashboard/template.html` e poi rilanciare `python scripts/render_dashboard.py`
(veloce, non riscarica nulla) per rigenerare `index.html` — non modificare `index.html`
direttamente, verrebbe sovrascritto.

## Architettura dell'app (`src/app.py`)

Un unico script Streamlit, letto dall'alto in basso:

1. **Caricamento dati** — legge `data/film.csv` in una tabella (`pandas.DataFrame`) a ogni
   caricamento della pagina.
2. **Filtri (barra laterale)** — genere, durata massima, voto minimo, piattaforma: l'utente li
   sceglie con menu a tendina e slider.
3. **Filtraggio** — i filtri scelti vengono applicati tutti insieme alla tabella dei film.
4. **Suggerimento** — il pulsante "Suggeriscimi un film" estrae una riga a caso tra i film
   filtrati e ne mostra i dettagli; se nessun film rispetta i filtri, mostra un avviso.
5. **Elenco completo** — un pannello a comparsa mostra tutti i film che rispettano i filtri
   correnti, in forma di tabella.

Non ci sono altri moduli o file di codice: qualunque nuova funzionalità va aggiunta direttamente
in `src/app.py`, a meno che non cresca abbastanza da giustificare di spezzarla in più file (in tal
caso, spiegare il perché all'utente prima di farlo).
