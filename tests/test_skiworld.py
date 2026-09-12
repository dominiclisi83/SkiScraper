from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from skiscraper.models import SearchConfig
from skiscraper.providers.skiworld import SkiworldProvider


def test_parses_matching_package_and_rejects_wrong_date() -> None:
    html = Path("tests/fixtures/skiworld_results.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    config = SearchConfig(None, "Test", "Val Thorens", date(2027, 1, 30), 7, 4)
    parsed = [
        item
        for card in soup.select("article.result-item")
        if (item := SkiworldProvider._parse_card(card, config, "apartment"))
    ]
    assert len(parsed) == 1
    assert parsed[0].property_name == "Residence Village Montana"
    assert parsed[0].total_price == 3468
    assert parsed[0].price_basis == "package_per_person"
    assert "London Gatwick – Grenoble" in parsed[0].inclusions
