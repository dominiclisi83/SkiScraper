from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class SearchConfig:
    id: int | None
    name: str
    resort: str
    check_in: date
    nights: int
    adults: int
    children: int = 0
    bedrooms: int = 1
    max_distance_m: int = 1500
    min_quality: float = 3.0
    board_basis: str = "any"
    enabled: bool = True


@dataclass(frozen=True)
class Listing:
    provider: str
    provider_listing_id: str
    property_name: str
    resort: str
    check_in: date
    nights: int
    total_price: Decimal
    currency: str
    capacity: int
    bedrooms: int
    accommodation_type: str
    quality: float
    review_score: float | None
    review_count: int
    distance_to_lift_m: int
    distance_to_centre_m: int
    board_basis: str
    cancellable: bool
    booking_url: str
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    price_basis: str = "accommodation"
    inclusions: tuple[str, ...] = ()

    @property
    def price_per_person_night(self) -> Decimal:
        return self.total_price / Decimal(self.capacity * self.nights)


@dataclass(frozen=True)
class Deal:
    listing: Listing
    comparable_count: int
    comparable_median: Decimal
    discount_percent: float
    confidence: str
    classification: str
