from datetime import date

from skiscraper.db import Database
from skiscraper.models import SearchConfig
from skiscraper.pipeline import run


def test_pipeline_persists_observations(tmp_path) -> None:
    db = Database(str(tmp_path / "test.db"))
    db.initialise()
    db.add_search(SearchConfig(None, "Test", "Tignes", date(2027, 1, 9), 7, 4, bedrooms=2))
    result = run(db)
    assert result["searches"] == 1
    assert result["listings"] == 12
    assert db.latest_deals()

