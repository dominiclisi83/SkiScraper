from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .models import Deal, Listing, SearchConfig

SCHEMA = """
CREATE TABLE IF NOT EXISTS search_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  resort TEXT NOT NULL,
  check_in TEXT NOT NULL,
  nights INTEGER NOT NULL,
  adults INTEGER NOT NULL,
  children INTEGER NOT NULL DEFAULT 0,
  bedrooms INTEGER NOT NULL DEFAULT 1,
  max_distance_m INTEGER NOT NULL DEFAULT 1500,
  min_quality REAL NOT NULL DEFAULT 3,
  board_basis TEXT NOT NULL DEFAULT 'any',
  enabled INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  search_config_id INTEGER NOT NULL,
  provider TEXT NOT NULL,
  provider_listing_id TEXT NOT NULL,
  property_name TEXT NOT NULL,
  resort TEXT NOT NULL,
  check_in TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  total_price TEXT NOT NULL,
  currency TEXT NOT NULL,
  listing_json TEXT NOT NULL,
  UNIQUE(provider, provider_listing_id, check_in, observed_at),
  FOREIGN KEY(search_config_id) REFERENCES search_configs(id)
);
CREATE TABLE IF NOT EXISTS deal_scores (
  observation_id INTEGER PRIMARY KEY,
  comparable_count INTEGER NOT NULL,
  comparable_median TEXT NOT NULL,
  discount_percent REAL NOT NULL,
  confidence TEXT NOT NULL,
  classification TEXT NOT NULL,
  FOREIGN KEY(observation_id) REFERENCES observations(id)
);
"""


class Database:
    def __init__(self, path: str = "data/skiscraper.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialise(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def add_search(self, config: SearchConfig) -> int:
        values = asdict(config)
        values.pop("id")
        values["check_in"] = config.check_in.isoformat()
        values["enabled"] = int(config.enabled)
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        with self.connect() as connection:
            cursor = connection.execute(
                f"INSERT INTO search_configs ({columns}) VALUES ({placeholders})",
                tuple(values.values()),
            )
            return int(cursor.lastrowid)

    def list_searches(self, enabled_only: bool = False) -> list[SearchConfig]:
        query = "SELECT * FROM search_configs"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY check_in, resort"
        with self.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [
            SearchConfig(
                id=row["id"], name=row["name"], resort=row["resort"],
                check_in=date.fromisoformat(row["check_in"]), nights=row["nights"],
                adults=row["adults"], children=row["children"], bedrooms=row["bedrooms"],
                max_distance_m=row["max_distance_m"], min_quality=row["min_quality"],
                board_basis=row["board_basis"], enabled=bool(row["enabled"]),
            )
            for row in rows
        ]

    def save_listing(self, search_id: int, listing: Listing) -> int:
        payload = asdict(listing)
        payload["check_in"] = listing.check_in.isoformat()
        payload["total_price"] = str(listing.total_price)
        payload["observed_at"] = listing.observed_at.isoformat()
        with self.connect() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO observations
                (search_config_id, provider, provider_listing_id, property_name, resort,
                 check_in, observed_at, total_price, currency, listing_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (search_id, listing.provider, listing.provider_listing_id,
                 listing.property_name, listing.resort, listing.check_in.isoformat(),
                 listing.observed_at.isoformat(), str(listing.total_price), listing.currency,
                 json.dumps(payload)),
            )
            if cursor.lastrowid:
                return int(cursor.lastrowid)
            row = connection.execute(
                """SELECT id FROM observations WHERE provider=? AND provider_listing_id=?
                   AND check_in=? AND observed_at=?""",
                (listing.provider, listing.provider_listing_id, listing.check_in.isoformat(),
                 listing.observed_at.isoformat()),
            ).fetchone()
            return int(row["id"])

    def save_deal(self, observation_id: int, deal: Deal) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO deal_scores VALUES (?, ?, ?, ?, ?, ?)""",
                (observation_id, deal.comparable_count, str(deal.comparable_median),
                 deal.discount_percent, deal.confidence, deal.classification),
            )

    def latest_deals(self, limit: int = 100) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT o.*, d.comparable_count, d.comparable_median,
                          d.discount_percent, d.confidence, d.classification
                   FROM observations o JOIN deal_scores d ON d.observation_id=o.id
                   ORDER BY d.discount_percent DESC, o.observed_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
