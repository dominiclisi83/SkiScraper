from __future__ import annotations

import math
import re
import time
from datetime import date
from decimal import Decimal
from urllib.parse import urljoin

import httpx

from ..models import Listing, SearchConfig

WEBSITE_URL = "https://www.skisolutions.com"
API_URL = "https://pms.skisolutions.com"
RESORTS = {"val thorens": (39, 45.2979, 6.5806)}
PROPERTY_TYPES = {2: "hotel", 3: "apartment"}


class SkiSolutionsProvider:
    """Collect dated guide prices from Ski Solutions' public search application."""

    name = "skisolutions"

    def __init__(self, delay_seconds: float = 1.5) -> None:
        self.delay_seconds = delay_seconds
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "SkiScraper/0.1 (+https://github.com/dominiclisi83/SkiScraper)",
                "Accept": "application/json",
            },
        )

    def search(self, config: SearchConfig) -> list[Listing]:
        resort = RESORTS.get(config.resort.casefold())
        if not resort:
            raise ValueError(f"Ski Solutions provider does not yet support resort: {config.resort}")
        resort_id, resort_lat, resort_lng = resort
        token = self._public_app_token()
        time.sleep(self.delay_seconds)
        response = self.client.get(
            f"{API_URL}/api/properties/search",
            params={
                "resort_ids": resort_id,
                "type_ids": "2,3",
                "sort": "recommended",
                "per_page": 100,
                "page": 1,
                "guests": config.adults + config.children,
                "start_date": config.check_in.isoformat(),
                "date_length": config.nights,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code in {401, 403, 429}:
            raise RuntimeError(
                f"Ski Solutions refused collection with HTTP {response.status_code}"
            )
        response.raise_for_status()
        return [
            listing
            for item in response.json().get("data", [])
            if (listing := self._parse_item(item, config, resort_lat, resort_lng)) is not None
        ]

    def _public_app_token(self) -> str:
        """Read the same short-lived/public client token used by the site's JavaScript."""
        page = self.client.get(
            f"{WEBSITE_URL}/ski-holidays/france-resorts/val-thorens/accommodations"
        )
        page.raise_for_status()
        script_match = re.search(r'src="([^"]+/js/app\.[^"]+\.js)"', page.text)
        if not script_match:
            raise RuntimeError("Could not locate the Ski Solutions search application")
        time.sleep(self.delay_seconds)
        script = self.client.get(urljoin(WEBSITE_URL, script_match.group(1)))
        script.raise_for_status()
        token_match = re.search(r'i="([^"]+)",o="https://pms\.skisolutions\.com/"', script.text)
        if not token_match:
            raise RuntimeError("Could not locate the Ski Solutions public client token")
        return token_match.group(1)

    @staticmethod
    def _parse_item(
        item: dict, config: SearchConfig, resort_lat: float, resort_lng: float
    ) -> Listing | None:
        estimate = item.get("estimate") or {}
        type_id = item.get("type")
        if type_id not in PROPERTY_TYPES or not estimate.get("value"):
            return None
        if date.fromisoformat(estimate["date"]) != config.check_in:
            return None
        if int(estimate.get("duration", 0)) != config.nights:
            return None

        capacity = config.adults + config.children
        per_person = Decimal(str(estimate["value"])) / Decimal(100)
        facilities = set(item.get("filterable_tag_ids") or [])
        centre_distance = _distance_metres(
            float(item.get("lat") or resort_lat),
            float(item.get("lng") or resort_lng),
            resort_lat,
            resort_lng,
        )
        if 13 in facilities:
            lift_distance = 0
        elif 14 in facilities:
            lift_distance = 300
        else:
            lift_distance = 1000
        board = _normalise_board(str(item.get("boardBasis") or "any"))
        return Listing(
            provider="skisolutions",
            provider_listing_id=str(item["id"]),
            property_name=str(item["name"]),
            resort=config.resort,
            check_in=config.check_in,
            nights=config.nights,
            total_price=per_person * capacity,
            currency=str(estimate.get("currency") or "GBP"),
            capacity=capacity,
            bedrooms=max(config.bedrooms, 1),
            accommodation_type=PROPERTY_TYPES[type_id],
            quality=float(item.get("rating") or 3),
            review_score=None,
            review_count=0,
            distance_to_lift_m=lift_distance,
            distance_to_centre_m=centre_distance,
            board_basis=board,
            cancellable=False,
            booking_url=str(item.get("url_website") or WEBSITE_URL),
            price_basis="package_per_person",
            inclusions=("Ski package guide price", str(item.get("boardBasis") or "Board unspecified")),
        )


def _normalise_board(value: str) -> str:
    values = {
        "bed & breakfast": "breakfast",
        "self catered": "self-catering",
        "half board": "half-board",
    }
    return values.get(value.casefold(), value.casefold().replace(" ", "-"))


def _distance_metres(lat: float, lng: float, target_lat: float, target_lng: float) -> int:
    radius = 6_371_000
    lat1, lat2 = math.radians(lat), math.radians(target_lat)
    delta_lat = math.radians(target_lat - lat)
    delta_lng = math.radians(target_lng - lng)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    )
    return round(radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value)))
