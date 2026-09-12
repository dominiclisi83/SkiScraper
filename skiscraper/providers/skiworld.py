from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from decimal import Decimal
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from ..models import Listing, SearchConfig

BASE_URL = "https://www.skiworld.co.uk"
RESULTS_ENDPOINT = f"{BASE_URL}/body_incs/lastminute_results_2026.php"
RESORT_PAGES = {
    "val thorens": (
        ("/ski-holidays/france/val-thorens/apartments", "452", "apartment"),
        ("/ski-holidays/france/val-thorens/hotels", "529", "hotel"),
    )
}


class SkiworldProvider:
    """Collect public UK package prices from Skiworld's resort result pages."""

    name = "skiworld"

    def __init__(self, delay_seconds: float = 1.5, max_pages: int = 10) -> None:
        self.delay_seconds = delay_seconds
        self.max_pages = max_pages
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "SkiScraper/0.1 (+https://github.com/dominiclisi83/SkiScraper)",
                "Accept": "application/json",
            },
        )

    def search(self, config: SearchConfig) -> list[Listing]:
        page_specs = RESORT_PAGES.get(config.resort.casefold())
        if not page_specs:
            raise ValueError(f"Skiworld provider does not yet support resort: {config.resort}")
        results: list[Listing] = []
        for page_uri, offer_id, accommodation_type in page_specs:
            results.extend(self._search_page(config, page_uri, offer_id, accommodation_type))
        unique = {(item.provider_listing_id, item.check_in): item for item in results}
        return list(unique.values())

    def _search_page(
        self, config: SearchConfig, page_uri: str, offer_id: str, accommodation_type: str
    ) -> list[Listing]:
        listings: list[Listing] = []
        total_pages = 1
        for page_number in range(1, self.max_pages + 1):
            response = self.client.post(
                RESULTS_ENDPOINT,
                data={
                    "pageURI": page_uri,
                    "parameters[searchOffer]": offer_id,
                    "pageNum": str(page_number),
                },
            )
            if response.status_code in {403, 429}:
                raise RuntimeError(f"Skiworld refused collection with HTTP {response.status_code}")
            response.raise_for_status()
            payload = response.json()
            soup = BeautifulSoup(payload.get("searchResults", ""), "html.parser")
            total_node = soup.select_one(".total-page")
            if total_node and total_node.get("value"):
                total_pages = int(str(total_node["value"]))
            listings.extend(
                item
                for card in soup.select("article.result-item")
                if (item := self._parse_card(card, config, accommodation_type)) is not None
            )
            if page_number >= total_pages:
                break
            time.sleep(self.delay_seconds)
        return listings

    @staticmethod
    def _parse_card(
        card: Tag, config: SearchConfig, accommodation_type: str
    ) -> Listing | None:
        departure = _text(card.select_one(".departure-date"))
        observed_date = _parse_departure_date(departure)
        if observed_date != config.check_in:
            return None

        description = _text(card.select_one(".package-description"))
        people_match = re.search(r"(\d+)\s+people", description, re.IGNORECASE)
        capacity = int(people_match.group(1)) if people_match else 0
        if capacity != config.adults + config.children:
            return None

        link = card.select_one("h3.accom-name a[href]")
        price_text = _text(card.select_one(".now-price .price"))
        total_text = _text(card.select_one(".total"))
        if not link or not price_text:
            return None
        per_person = Decimal(re.sub(r"[^0-9.]", "", price_text.replace(",", "")))
        total_match = re.search(r"£([\d,]+(?:\.\d{2})?)", total_text)
        total = (
            Decimal(total_match.group(1).replace(",", ""))
            if total_match
            else per_person * capacity
        )
        url = urljoin(BASE_URL, str(link["href"]))
        query = parse_qs(urlparse(url).query)
        listing_id = query.get("id_accom_price", [urlparse(url).path.rsplit("/", 1)[-1]])[0]
        features = tuple(_text(node) for node in card.select(".features span") if _text(node))
        transport = tuple(
            _text(node)
            for node in card.select(".transport p")
            if _text(node)
        )
        stars = len(card.select(".accom-rating i.full"))
        board = description.split("|")[-1].strip().casefold() if "|" in description else "any"
        return Listing(
            provider="skiworld",
            provider_listing_id=str(listing_id),
            property_name=_text(link),
            resort=config.resort,
            check_in=config.check_in,
            nights=config.nights,
            total_price=total,
            currency="GBP",
            capacity=capacity,
            bedrooms=max(config.bedrooms, 1),
            accommodation_type=accommodation_type,
            quality=float(stars or 3),
            review_score=None,
            review_count=0,
            distance_to_lift_m=0 if any("ski in/out" in f.casefold() for f in features) else 1000,
            distance_to_centre_m=1000,
            board_basis=board,
            cancellable=False,
            booking_url=url,
            price_basis="package_per_person",
            inclusions=features + transport,
        )


def _text(node: Tag | None) -> str:
    return " ".join(node.stripped_strings) if node else ""


def _parse_departure_date(value: str):
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", value)
    return datetime.strptime(cleaned, "%a %d %b %Y").replace(tzinfo=UTC).date()
