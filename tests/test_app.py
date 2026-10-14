"""FlipPrice journey tests — each one acts like a real reseller would.

Run: .venv/bin/python -m pytest tests/ -q
Fixtures isolate disk state (tmp store + tmp comps) so tests never touch
the developer's real inventory.
"""
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient

import app.pricing as pricing_mod
import app.store as store_mod
from app import describer
from app.main import app
from app.pricing import estimate_price, net_payout

COMPS_CSV = """brand,category,condition,age_years,sold_price_usd
canon,camera,like_new,1,260
canon,camera,good,3,185
canon,camera,fair,5,120
levis,jacket,like_new,1,88
levis,jacket,good,3,55
sony,headphones,good,2,75
"""


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """App with isolated inventory + comps, and no network model (offline mode)."""
    monkeypatch.setattr(store_mod, "LOCAL_PATH", str(tmp_path / "items.json"))
    monkeypatch.setattr(pricing_mod, "ACTIVE_PATH", str(tmp_path / "active_comps.csv"))
    monkeypatch.setattr(describer, "OLLAMA_HOST", "http://127.0.0.1:9")  # dead port
    store_mod._write_local([])
    yield TestClient(app)


def upload_comps(c, csv_text=COMPS_CSV):
    return c.post("/api/comps", files={"file": ("sold.csv", io.BytesIO(csv_text.encode()), "text/csv")})


def test_saturday_market_journey(client):
    """Ayse sells vintage: uploads her history, appraises 2 finds, checks profit, deletes a mistake."""
    r = upload_comps(client)
    assert r.status_code == 200, r.text
    assert r.json()["rows"] == 6

    cam = client.post("/api/appraise", json={
        "name": "Canon AE-1 film camera", "brand": "canon", "category": "camera",
        "condition": "good", "age_years": 3, "buy_cost": 50}).json()
    assert cam["price"]["p50"] > 0 and cam["payout"]["net"] > 0
    assert "canon" in cam["listing"]["title"].lower()

    jacket = client.post("/api/appraise", json={
        "name": "Levis denim trucker", "brand": "levis", "category": "jacket",
        "condition": "like_new", "age_years": 1, "buy_cost": 20}).json()
    assert jacket["price"]["p50"] > jacket["price"]["low"]

    s = client.get("/api/stats").json()
    assert s["count"] == 2
    assert s["total_net"] == round(cam["payout"]["net"] + jacket["payout"]["net"], 2)

    assert client.delete(f"/api/items/{cam['id']}").status_code == 200
    assert client.get("/api/stats").json()["count"] == 1
    assert client.delete(f"/api/items/{cam['id']}").status_code == 404  # already gone


def test_no_signal_at_the_market(client):
    """Offline (no Ollama server): appraisal still works via template fallback."""
    r = client.post("/api/appraise", json={
        "name": "Sony Walkman WM-2", "brand": "sony", "category": "headphones",
        "condition": "fair", "age_years": 8, "buy_cost": 10})
    assert r.status_code == 201
    body = r.json()
    assert "fallback-template" in body["listing"]["engine"]
    assert body["price"]["p50"] > 0


def test_sloppy_inputs_get_helpful_errors(client):
    """Real users mistype: every bad input must explain itself."""
    assert client.post("/api/appraise", json={"name": "x"}).status_code == 422  # too short
    bad = {"name": "Canon AE-1", "condition": "broken"}  # not a real grade
    assert client.post("/api/appraise", json=bad).status_code == 422
    neg = {"name": "Canon AE-1", "condition": "good", "buy_cost": -5}
    assert client.post("/api/appraise", json=neg).status_code == 422
    fee = {"name": "Canon AE-1", "condition": "good", "fee_pct": 99}
    assert client.post("/api/appraise", json=fee).status_code == 422

    exe = client.post("/api/photos", files={"file": ("evil.exe", b"MZ", "application/octet-stream")})
    assert exe.status_code == 400 and ".png" in exe.json()["detail"]

    big = client.post("/api/photos", files={"file": ("big.png", b"x" * (2 * 1024 * 1024 + 1), "image/png")})
    assert big.status_code == 400 and "2 MB" in big.json()["detail"]

    missing_col = "brand,category\ncanon,camera\n"
    r = client.post("/api/comps", files={"file": ("s.csv", io.BytesIO(missing_col.encode()), "text/csv")})
    assert r.status_code == 400 and "missing columns" in r.json()["detail"]

    tiny = "brand,category,condition,age_years,sold_price_usd\ncanon,camera,good,3,185\n"
    r = client.post("/api/comps", files={"file": ("s.csv", io.BytesIO(tiny.encode()), "text/csv")})
    assert r.status_code == 400 and "at least 5" in r.json()["detail"]


def test_photo_attached_to_listing(client):
    """Mehmet photographs a chair, uploads it, appraises with the photo attached."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (200, 30, 30)).save(buf, format="PNG")
    up = client.post("/api/photos", files={"file": ("chair.png", buf.getvalue(), "image/png")})
    assert up.status_code == 200
    photo_url = up.json()["photo_url"]

    r = client.post("/api/appraise", json={
        "name": "Ikea Poang armchair", "brand": "ikea", "category": "chair",
        "condition": "good", "age_years": 2, "buy_cost": 15, "photo_url": photo_url})
    assert r.status_code == 201
    items = client.get("/api/items").json()
    assert items[0]["photo_url"] == photo_url


def test_fee_presets_and_csv_export(client):
    """Ayse sells on Etsy, not eBay: presets give her fee, CSV exports her books."""
    fees = client.get("/api/fees").json()
    assert fees["etsy"] == 6.5 and fees["ebay"] == 13.0

    client.post("/api/appraise", json={
        "name": "Levis denim trucker", "brand": "levis", "category": "jacket",
        "condition": "like_new", "age_years": 1, "buy_cost": 20, "fee_pct": fees["etsy"]})
    csv_text = client.get("/api/items.csv").text
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("name,brand,category")
    assert len(lines) == 2 and "Levis denim trucker" in lines[1]


def test_price_condition_monotonic():
    like_new = estimate_price("canon", "camera", "like_new", 1)["p50"]
    fair = estimate_price("canon", "camera", "fair", 1)["p50"]
    assert like_new > fair


def test_payout_math():
    assert net_payout(200.0, 50.0, 13.0) == {
        "list_price": 200.0, "fees": 26.0, "buy_cost": 50.0, "net": 124.0, "margin_pct": 62.0}


def test_sale_calibration_flow(client):
    """Leyla sells the jacket: records the realized price, calibration learns."""
    assert client.get("/api/calibration").json()["n_sold"] == 0
    item = client.post("/api/appraise", json={
        "name": "Levis denim trucker", "brand": "levis", "category": "jacket",
        "condition": "like_new", "age_years": 1, "buy_cost": 20}).json()
    assert client.patch("/api/items/nope", json={"sold_price": 80}).status_code == 404
    sold = client.patch(f"/api/items/{item['id']}", json={"sold_price": 80}).json()
    assert sold["sold_price"] == 80 and "sold_at" in sold
    cal = client.get("/api/calibration").json()
    assert cal["n_sold"] == 1 and cal["mae"] >= 0 and "bias" in cal


def test_live_model_writes_the_listing(tmp_path, monkeypatch):
    """Slow integration: a real local open-weight model writes a real listing."""
    if os.getenv("OLLAMA_LIVE", "1") != "1":
        pytest.skip("needs a local Ollama server (OLLAMA_LIVE=1)")
    monkeypatch.setattr(store_mod, "LOCAL_PATH", str(tmp_path / "items.json"))
    c = TestClient(app)  # real OLLAMA_HOST on purpose
    r = c.post("/api/appraise", json={
        "name": "AE-1 film camera", "brand": "canon", "category": "camera",
        "condition": "good", "age_years": 3, "buy_cost": 50})
    assert r.status_code == 201
    listing = r.json()["listing"]
    assert listing["engine"].startswith("ollama:")
    assert "canon" in listing["title"].lower()
