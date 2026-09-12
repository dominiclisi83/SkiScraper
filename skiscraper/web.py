from __future__ import annotations

import os
from datetime import date

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .db import Database
from .models import SearchConfig

app = FastAPI(title="SkiScraper", version="0.1.0")


def get_db() -> Database:
    db = Database(os.getenv("SKISCRAPER_DB", "data/skiscraper.db"))
    db.initialise()
    return db


def page(body: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width'><title>SkiScraper</title>
<style>body{{font:16px system-ui;background:#f4f7fa;color:#102a43;margin:0}}main{{max-width:1100px;margin:auto;padding:2rem}}
nav{{background:#102a43;padding:1rem}}nav a{{color:white;margin-right:1rem}}form,.card{{background:white;padding:1rem;border-radius:12px;margin:1rem 0}}
label{{display:block;margin:.6rem 0}}input,select{{padding:.6rem;width:min(420px,90%)}}button{{padding:.7rem 1.2rem;background:#087f5b;color:white;border:0;border-radius:7px}}
table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:.7rem;text-align:left;border-bottom:1px solid #ddd}}</style></head>
<body><nav><a href='/'>Deals</a><a href='/config'>Search configuration</a></nav><main>{body}</main></body></html>""")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    deals = get_db().latest_deals()
    rows = "".join(
        f"<tr><td>{d['property_name']}</td><td>{d['resort']}</td><td>{d['currency']} {d['total_price']}</td>"
        f"<td>{d['discount_percent']:.1f}%</td><td>{d['classification']}</td><td>{d['confidence']}</td></tr>"
        for d in deals
    ) or "<tr><td colspan='6'>No results yet. Add a search and run the collector.</td></tr>"
    return page(f"<h1>Best ski deals</h1><table><tr><th>Property</th><th>Resort</th><th>Total</th><th>Below peers</th><th>Deal</th><th>Confidence</th></tr>{rows}</table>")


@app.get("/config", response_class=HTMLResponse)
def config() -> HTMLResponse:
    searches = get_db().list_searches()
    cards = "".join(
        f"<div class='card'><strong>{s.name}</strong> — {s.resort}, {s.check_in}, "
        f"{s.nights} nights, {s.adults + s.children} guests</div>" for s in searches
    )
    form = """<h1>Search configuration</h1><form method='post'>
    <label>Name <input name='name' required placeholder='January escape'></label>
    <label>Resort <input name='resort' required placeholder='Tignes'></label>
    <label>Check in <input type='date' name='check_in' required></label>
    <label>Nights <input type='number' name='nights' value='7' min='1' required></label>
    <label>Adults <input type='number' name='adults' value='2' min='1' required></label>
    <label>Children <input type='number' name='children' value='0' min='0'></label>
    <label>Bedrooms <input type='number' name='bedrooms' value='1' min='1'></label>
    <label>Maximum distance to lift (m) <input type='number' name='max_distance_m' value='1500'></label>
    <label>Minimum quality <input type='number' step='.5' name='min_quality' value='3'></label>
    <label>Board <select name='board_basis'><option>any</option><option>self-catering</option><option>breakfast</option><option>half-board</option></select></label>
    <button>Add search</button></form>"""
    return page(form + cards)


@app.post("/config")
def add_config(name: str = Form(), resort: str = Form(), check_in: date = Form(),
               nights: int = Form(), adults: int = Form(), children: int = Form(0),
               bedrooms: int = Form(1), max_distance_m: int = Form(1500),
               min_quality: float = Form(3), board_basis: str = Form("any")) -> RedirectResponse:
    get_db().add_search(SearchConfig(None, name, resort, check_in, nights, adults, children,
                                     bedrooms, max_distance_m, min_quality, board_basis))
    return RedirectResponse("/config", status_code=303)
