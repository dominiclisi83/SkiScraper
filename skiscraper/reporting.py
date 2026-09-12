from __future__ import annotations

from html import escape
from pathlib import Path

from .db import Database


def write_html_report(db: Database, path: str = "reports/latest.html") -> Path:
    deals = db.latest_deals()
    rows = "".join(
        f"<tr><td>{escape(d['property_name'])}</td><td>{escape(d['resort'])}</td>"
        f"<td>{escape(d['currency'])} {escape(d['total_price'])}</td><td>{d['discount_percent']:.1f}%</td>"
        f"<td>{escape(d['classification'].title())}</td><td>{escape(d['confidence'])}</td></tr>"
        for d in deals
    )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f"""<!doctype html><html><head><meta charset='utf-8'>
<title>SkiScraper report</title><style>body{{font:16px system-ui;margin:3rem;max-width:1100px}}
table{{border-collapse:collapse;width:100%}}th,td{{padding:.7rem;border-bottom:1px solid #ddd;text-align:left}}
th{{background:#102a43;color:white}}</style></head><body><h1>SkiScraper deals</h1>
<table><thead><tr><th>Property</th><th>Resort</th><th>Total</th><th>Below peers</th>
<th>Deal</th><th>Confidence</th></tr></thead><tbody>{rows}</tbody></table></body></html>""",
        encoding="utf-8",
    )
    return output
