from __future__ import annotations

import argparse
import json
import os

from .db import Database
from .models import SearchConfig
from .pipeline import named_providers, run
from .reporting import write_html_report


def main() -> None:
    parser = argparse.ArgumentParser(prog="skiscraper")
    parser.add_argument("command", choices=["init", "seed", "run"])
    parser.add_argument("--db", default="data/skiscraper.db")
    args = parser.parse_args()
    db = Database(args.db)
    db.initialise()
    if args.command == "seed" and not db.list_searches():
        from datetime import date
        resort = os.getenv("SKISCRAPER_SEED_RESORT", "Val Thorens")
        check_in = date.fromisoformat(os.getenv("SKISCRAPER_SEED_CHECK_IN", "2027-01-30"))
        db.add_search(SearchConfig(None, "Val Thorens package watch", resort,
                                   check_in, 7, 4, bedrooms=1))
        print(f"Created search for {resort} on {check_in}")
    elif args.command == "run":
        providers = named_providers(os.getenv("SKISCRAPER_PROVIDERS", "demo"))
        print(json.dumps(run(db, providers), indent=2))
        print(f"Report: {write_html_report(db)}")
    else:
        print(f"Database ready: {db.path}")


if __name__ == "__main__":
    main()
