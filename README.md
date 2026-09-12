# SkiScraper

An explainable, free-tier-first ski accommodation deal finder. It separates collection,
normalisation, comparable-property selection and deal scoring so a cheap broom cupboard
three villages away is not crowned the bargain of the century.

## What works now

- Web configuration page for resort searches
- Append-only SQLite price observations
- Pluggable provider interface
- Deterministic demo provider for end-to-end testing
- Live Skiworld and Ski Solutions collectors for Val Thorens UK packages
- Comparable-property filtering by resort, date, type, quality, lift distance, occupancy and board
- Explainable discount, classification and confidence
- HTML dashboard and report
- Daily GitHub Actions schedule plus CI

The demo provider is intentional: live travel sites require a provider-specific review of their
API, affiliate programme, robots policy and terms before enabling collection.

The scheduled workflow uses Skiworld's public resort listings and Ski Solutions' public search
application. Package prices are labelled and
only compared with other packages on the same date, for the same party size, accommodation type,
quality band, board basis and approximate slope proximity. Flights/transfers are retained as
inclusions rather than silently treated as accommodation-only pricing.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
skiscraper init
skiscraper seed
skiscraper run
uvicorn skiscraper.web:app --reload
```

Open <http://127.0.0.1:8000>. Alternatively run `docker compose up --build`.

Run both live providers with
`SKISCRAPER_PROVIDERS=skiworld,skisolutions skiscraper run`.

## Architecture

```text
Configuration UI -> search_configs -> scheduled collectors -> observations
                                                     |-> comparable matcher
                                                     |-> deal_scores -> dashboard/report
```

`skiscraper/providers/base.py` defines the contract each legitimate provider adapter must
implement. The scorer does not depend on provider-specific HTML.

## Next deployment step

SQLite is correct for development. Before hosting the config page and scheduled scraper on
different machines, replace `Database` with a shared free-tier database adapter (Cloudflare D1
behind a signed Worker API, or hosted PostgreSQL). The current separation keeps that migration
small and prevents provider code from knowing where results are stored.

## Safety and data quality

- Never commit provider credentials; use GitHub Actions secrets.
- Respect provider terms, robots directives and rate limits.
- Prefer official APIs and affiliate feeds.
- Store total price and inclusions, not only an advertised nightly rate.
- Do not alert on a deal with fewer than two comparable properties.
