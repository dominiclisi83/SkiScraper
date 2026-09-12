from __future__ import annotations

import argparse
import json

from .db import Database
from .models import SearchConfig
from .pipeline import run
from .reporting import write_html_report


def main() -> None:
    parser = argparse.ArgumentParser(prog="skiscraper")
    parser.add_argument("command", choices=["init", "seed", "run"])
    parser.add_argument("--db", default="data/skiscraper.db")
    args = parser.parse_args()
    db = Database(args.db)
    db.initialise()
    if args.command == "seed" and not db.list_searches():
        from datetime import UTC, datetime, timedelta
        db.add_search(SearchConfig(None, "Demo ski week", "Tignes",
                                   datetime.now(UTC).date() + timedelta(days=120),
                                   7, 4, bedrooms=2))
        print("Created demo search")
    elif args.command == "run":
        print(json.dumps(run(db), indent=2))
        print(f"Report: {write_html_report(db)}")
    else:
        print(f"Database ready: {db.path}")


if __name__ == "__main__":
    main()
