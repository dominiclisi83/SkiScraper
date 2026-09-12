from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from random import Random

from ..models import Listing, SearchConfig


class DemoProvider:
    """Deterministic provider used to exercise the pipeline without scraping a live site."""

    name = "demo"

    def search(self, config: SearchConfig) -> list[Listing]:
        seed = int(sha256(f"{config.resort}:{config.check_in}".encode()).hexdigest()[:8], 16)
        rng = Random(seed)
        adjectives = ["Alpine", "Snow", "Summit", "Glacier", "Piste", "Mont"]
        nouns = ["Lodge", "Residence", "Chalet", "Hotel", "Retreat", "Apartments"]
        results: list[Listing] = []
        capacity = config.adults + config.children
        for index in range(12):
            quality = rng.choice([3.0, 3.5, 4.0, 4.5, 5.0])
            distance = rng.randint(80, 2200)
            base = Decimal(430 + quality * 185 + distance / 14 + rng.randint(-170, 260))
            results.append(Listing(
                provider=self.name, provider_listing_id=f"{seed}-{index}",
                property_name=f"{adjectives[index % len(adjectives)]} {nouns[index % len(nouns)]}",
                resort=config.resort, check_in=config.check_in, nights=config.nights,
                total_price=base.quantize(Decimal("0.01")), currency="GBP",
                capacity=capacity, bedrooms=config.bedrooms,
                accommodation_type="hotel" if index % 3 else "apartment", quality=quality,
                review_score=round(rng.uniform(7.2, 9.5), 1), review_count=rng.randint(15, 850),
                distance_to_lift_m=distance, distance_to_centre_m=rng.randint(50, 1800),
                board_basis=rng.choice(["self-catering", "breakfast", "half-board"]),
                cancellable=rng.choice([True, True, False]),
                booking_url="https://example.com/demo", observed_at=datetime.now(UTC),
            ))
        return results
