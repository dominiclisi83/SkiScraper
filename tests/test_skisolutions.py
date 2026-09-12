from datetime import date

from skiscraper.models import SearchConfig
from skiscraper.providers.skisolutions import SkiSolutionsProvider, _normalise_board


def test_parses_matching_four_person_apartment_price() -> None:
    config = SearchConfig(None, "Test", "Val Thorens", date(2027, 1, 30), 7, 4)
    item = {
        "id": 13613,
        "name": "Residence Koh-I Nor",
        "type": 3,
        "rating": 5,
        "boardBasis": "Self Catered",
        "estimate": {
            "value": 219500,
            "currency": "GBP",
            "date": "2027-01-30",
            "duration": 7,
        },
        "lat": "45.298",
        "lng": "6.581",
        "filterable_tag_ids": [13, 19],
        "url_website": "https://www.skisolutions.com/example",
    }

    listing = SkiSolutionsProvider._parse_item(item, config, 45.2979, 6.5806)

    assert listing is not None
    assert listing.accommodation_type == "apartment"
    assert listing.total_price == 8780
    assert listing.capacity == 4
    assert listing.distance_to_lift_m == 0
    assert listing.board_basis == "self-catering"
    assert listing.price_basis == "package_per_person"


def test_rejects_wrong_date_and_normalises_board() -> None:
    config = SearchConfig(None, "Test", "Val Thorens", date(2027, 2, 6), 7, 4)
    item = {
        "id": 1,
        "name": "Hotel",
        "type": 2,
        "estimate": {"value": 100000, "date": "2027-01-30", "duration": 7},
    }
    assert SkiSolutionsProvider._parse_item(item, config, 45.2979, 6.5806) is None
    assert _normalise_board("Bed & Breakfast") == "breakfast"
