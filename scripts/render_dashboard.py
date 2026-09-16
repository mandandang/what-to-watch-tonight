"""
Regenerates ONLY dashboard/index.html from the data already in data/film_dashboard.csv, without
downloading or recomputing anything (unlike build_dashboard.py). Use it after updating some rows
of data/film_dashboard.csv by hand (or via the update-cinema skill), to immediately reflect the
changes in the dashboard.

Usage:
    python scripts/render_dashboard.py
"""

import sys

from dashboard_lib import render_html


def main():
    output = render_html()
    print(f"Done: {output} regenerated with the updated data.")


if __name__ == "__main__":
    sys.exit(main())
