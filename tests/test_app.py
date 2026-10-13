"""FlipPrice test suite — run: .venv/bin/python -m pytest tests/ -q"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.pricing import estimate_price, net_payout
from app.describer import describe_item


def test_price_shape_and_bounds():
    p = estimate_price("canon", "camera", "good", 3)
    assert {"p50", "low", "high", "engine"} <= set(p)
    assert p["low"] < p["p50"] < p["high"]
    assert p["p50"] > 0


def test_price_condition_monotonic():
    like_new = estimate_price("canon", "camera", "like_new", 1)["p50"]
    fair = estimate_price("canon", "camera", "fair", 1)["p50"]
    assert like_new > fair, "better condition should price higher"


def test_payout_math():
    n = net_payout(200.0, 50.0, 13.0)
    assert n == {"list_price": 200.0, "fees": 26.0, "buy_cost": 50.0,
                 "net": 124.0, "margin_pct": 62.0}


def test_describer_always_returns():
    d = describe_item("AE-1 film camera", "canon", "camera", "good", "shutter works")
    assert d["title"] and d["description"] and d["engine"]


def test_api_end_to_end():
    from fastapi.testclient import TestClient
    from app.main import app

    c = TestClient(app)
    assert c.get("/api/health").json() == {"ok": True, "service": "flipprice"}
    r = c.post("/api/appraise", json={
        "name": "Canon AE-1 film camera", "brand": "canon",
        "category": "camera", "condition": "good", "age_years": 3, "buy_cost": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["price"]["p50"] > 0 and body["payout"]["net"] > 0
    assert "canon" in body["listing"]["title"].lower()
    items = c.get("/api/items").json()
    assert any(i["name"] == "Canon AE-1 film camera" for i in items)
