from __future__ import annotations

from .db import Database
from .providers import DemoProvider, Provider
from .scoring import score_market


def run(db: Database, providers: list[Provider] | None = None) -> dict[str, int]:
    providers = providers or [DemoProvider()]
    searches = db.list_searches(enabled_only=True)
    listing_count = deal_count = 0
    for search in searches:
        listings = [listing for provider in providers for listing in provider.search(search)]
        listing_count += len(listings)
        observation_ids = {
            (listing.provider, listing.provider_listing_id): db.save_listing(search.id or 0, listing)
            for listing in listings
        }
        for deal in score_market(listings):
            key = (deal.listing.provider, deal.listing.provider_listing_id)
            db.save_deal(observation_ids[key], deal)
            deal_count += 1
    return {"searches": len(searches), "listings": listing_count, "deals": deal_count}

