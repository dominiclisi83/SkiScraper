from __future__ import annotations

from decimal import Decimal
from statistics import median

from .models import Deal, Listing


def comparable(a: Listing, b: Listing) -> bool:
    return (
        a is not b
        and a.resort.casefold() == b.resort.casefold()
        and a.check_in == b.check_in
        and a.nights == b.nights
        and a.accommodation_type == b.accommodation_type
        and abs(a.quality - b.quality) <= 0.75
        and abs(a.distance_to_lift_m - b.distance_to_lift_m) <= 750
        and a.capacity == b.capacity
        and (a.board_basis == b.board_basis or "any" in {a.board_basis, b.board_basis})
    )


def score_listing(listing: Listing, market: list[Listing]) -> Deal | None:
    peers = [item for item in market if comparable(listing, item)]
    if len(peers) < 2:
        return None
    benchmark = Decimal(str(median(float(item.price_per_person_night) for item in peers)))
    discount = float((benchmark - listing.price_per_person_night) / benchmark * 100)
    confidence = "high" if len(peers) >= 5 else "medium" if len(peers) >= 3 else "low"
    if discount >= 25 and confidence != "low":
        classification = "exceptional"
    elif discount >= 15:
        classification = "strong"
    elif discount >= 8:
        classification = "good"
    else:
        classification = "normal"
    return Deal(listing, len(peers), benchmark, round(discount, 1), confidence, classification)


def score_market(listings: list[Listing]) -> list[Deal]:
    return [deal for listing in listings if (deal := score_listing(listing, listings))]

