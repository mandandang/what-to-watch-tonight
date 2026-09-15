---
name: aggiorna-cinema
description: Arricchisce con voti reali (IMDb, Rotten Tomatoes) e mood i prossimi 20 film del progetto "Cosa guardo stasera?" (questo repository) che non hanno ancora un voto, poi aggiorna dashboard/index.html con i risultati. Usa questa skill quando l'utente, lavorando in questo progetto, chiede di aggiornare/completare/arricchire il catalogo film, di trovare altri voti mancanti, o dice esplicitamente "aggiorna-cinema" / "aggiorna il cinema". È specifica di questo progetto, non una skill generica di arricchimento dati.
---

# Aggiorna Cinema

Ripete, in modo riproducibile, il lavoro fatto manualmente la prima volta per arricchire il
catalogo film di questo progetto: prende un lotto di film ancora senza voto, li fa arricchire da
tre agenti in parallelo (voto IMDb, voto Rotten Tomatoes, mood), e aggiorna la dashboard.

Il contesto architetturale completo del progetto (schema dei CSV, come funziona la dashboard,
perché certi file esistono) è in [`CLAUDE.md`](../../../CLAUDE.md) alla radice del repository —
questa skill non lo ripete, presume che tu l'abbia letto o lo legga se serve.

L'utente di questo progetto non è uno sviluppatore: quando riporti il risultato, usa un italiano
semplice, senza gergo tecnico non necessario.

## Procedura

Segui questi passi **in ordine**, uno alla volta. Non saltare il passo 3 (l'attesa dei tre
agenti): inventare o anticipare i loro risultati prima che arrivino produce dati falsi in un
progetto che esiste apposta per avere voti reali.

### 1. Seleziona i film da arricchire

Esegui:
```bash
python scripts/select_next20.py
```
Questo stampa i (fino a) 20 film di `data/film_dashboard.csv` che non hanno ancora un
`voto_imdb`, nell'ordine in cui compaiono nel file — cioè "i prossimi 20". Se stampa che non ce
ne sono, il catalogo è già completo: fermati e dillo all'utente, non serve continuare.

### 2. Lancia i tre agenti in parallelo

Lancia **tre** chiamate al tool Agent (`subagent_type: general-purpose`) **nello stesso
messaggio**, così partono in parallelo. Usa esattamente questi tre prompt, sostituendo
`{LISTA_FILM}` con l'elenco stampato al passo 1 (titolo, anno, generi — un film per riga).

**Agente 1 — voto IMDb:**
```
Ho bisogno del voto IMDb REALE e attuale (scala 0-10, es. 8.8) per ciascuno di questi film. Usa
WebSearch/WebFetch per verificare ogni voto — non basarti solo sulla tua memoria interna, perché
i voti possono essere leggermente diversi da quelli che ricordi e servono numeri accurati.

Film (titolo, anno):
{LISTA_FILM}

Restituisci SOLO un elenco pulito, un film per riga, in questo formato esatto (nessun testo
introduttivo, nessun commento extra, nessuna numerazione):

Titolo (Anno): voto

Esempio di riga corretta: "Inception (2010): 8.8"
```

**Agente 2 — voto Rotten Tomatoes:**
```
Ho bisogno del punteggio della critica REALE su Rotten Tomatoes (il "Tomatometer", in
percentuale, es. 87%) per ciascuno di questi film. Usa WebSearch/WebFetch per verificare ogni
punteggio — non basarti solo sulla tua memoria interna.

Film (titolo, anno):
{LISTA_FILM}

Restituisci SOLO un elenco pulito, un film per riga, in questo formato esatto (nessun testo
introduttivo, nessun commento extra, nessuna numerazione):

Titolo (Anno): percentuale%

Esempio di riga corretta: "Inception (2010): 87%"
```

**Agente 3 — mood:**
```
Devo classificare ciascuno di questi film secondo il "mood": che tipo di serata è adatta a quel
film. Per ciascun film scegli ESATTAMENTE UNA di queste 6 categorie (usa il testo esatto, non
inventarne altre): "Venerdi leggero", "Comfort movie", "Adrenalina", "Mente accesa",
"Da vedere in due", "Domenica impegnativa".

Non basarti solo sul genere dichiarato: se conosci il film usa anche trama e tono per scegliere
il mood più sensato; se non lo conosci, fai una breve ricerca web prima di rispondere.

Film (titolo, anno, generi):
{LISTA_FILM}

Restituisci SOLO un elenco pulito, un film per riga, in questo formato esatto (nessun testo
introduttivo, nessun commento extra, nessuna numerazione), con la motivazione in italiano su una
riga, massimo 20 parole:

Titolo (Anno): Mood — motivazione

Esempio di riga corretta: "Inception (2010): Mente accesa — trama a incastri sui sogni che
richiede attenzione costante per essere seguita."
```

Lancia tutti e tre in background (comportamento predefinito del tool Agent).

### 3. Aspetta il completamento di tutti e tre

Non procedere finché non sono arrivate **tutte e tre** le notifiche di completamento. Se una
tarda, aspetta ancora — non riempire il buco con un risultato inventato.

### 4. Unisci i risultati nel CSV

Salva il testo restituito da ciascun agente in tre file temporanei (usa la tua cartella
scratchpad), poi esegui:
```bash
python scripts/merge_enrichment.py --imdb <percorso_imdb.txt> --rt <percorso_rt.txt> --mood <percorso_mood.txt>
```
Questo script aggiorna `data/film_dashboard.csv` usando il modulo `csv` di Python (mai a mano —
in questo progetto un campo di testo con una virgola non protetta da virgolette ha già causato un
bug che troncava i dati). Aggiorna solo le righe corrispondenti ai film appena processati; tutte
le altre restano invariate. Lo script stampa quante righe ha aggiornato e segnala eventuali film
che gli agenti hanno restituito ma che non ha trovato nel CSV (titolo/anno leggermente diversi).

### 5. Rigenera la dashboard

```bash
python scripts/render_dashboard.py
```
Rigenera `dashboard/index.html` a partire dai dati appena aggiornati (non riscarica né
ricalcola nulla — è la sola iniezione dei dati nel template, quindi è istantaneo). **Non usare
`scripts/build_dashboard.py` per questo passo**: rifarebbe da zero il join coi dati IMDb in
blocco e riassegnerebbe il mood generico basato solo sul genere a tutti i film, cancellando
l'arricchimento appena fatto.

### 6. Mostra il risultato

Apri `dashboard/index.html` per mostrarlo all'utente: avvia un piccolo server locale
(`python -m http.server` nella cartella `dashboard/`), aprilo nel browser di anteprima, controlla
che uno o due dei film appena arricchiti mostrino il nuovo voto/mood, poi ferma il server e apri
il file vero per l'utente (su Windows: `start "" "dashboard\index.html"`).

### 7. Riporta il risultato

In italiano semplice, di' all'utente: quanti dei film processati hanno trovato un voto reale
(alcuni titoli molto oscuri potrebbero non trovarlo nemmeno con una ricerca — non è un problema,
verranno riproposti automaticamente la prossima volta che si usa questa skill, dato che un film
senza voto è proprio il criterio con cui viene riselezionato), e che la dashboard è aggiornata.
