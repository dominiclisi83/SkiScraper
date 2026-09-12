from datetime import date
from decimal import Decimal

from skiscraper.models import Listing
from skiscraper.scoring import score_market


def listing(name: str, price: str) -> Listing:
    return Listing("test", name, name, "Tignes", date(2027, 1, 9), 7,
                   Decimal(price), "GBP", 4, 2, "hotel", 4, 8.5, 100,
                   300, 400, "breakfast", True, "https://example.com")


def test_underpriced_listing_is_identified() -> None:
    market = [listing("deal", "700"), listing("a", "1400"), listing("b", "1500"),
              listing("c", "1450"), listing("d", "1550"), listing("e", "1425")]
    deal = next(item for item in score_market(market) if item.listing.property_name == "deal")
    assert deal.classification == "exceptional"
    assert deal.confidence == "high"
    assert deal.discount_percent > 45

