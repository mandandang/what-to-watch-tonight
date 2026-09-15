"""
Rigenera SOLO dashboard/index.html a partire dai dati gia presenti in data/film_dashboard.csv,
senza scaricare o ricalcolare nulla (a differenza di build_dashboard.py). Usalo dopo aver
aggiornato a mano (o tramite la skill aggiorna-cinema) alcune righe di data/film_dashboard.csv,
per rispecchiare subito le modifiche nella dashboard.

Uso:
    python scripts/render_dashboard.py
"""

import sys

from dashboard_lib import render_html


def main():
    output = render_html()
    print(f"Fatto: {output} rigenerato con i dati aggiornati.")


if __name__ == "__main__":
    sys.exit(main())
