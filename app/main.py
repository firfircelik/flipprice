import os
import shutil
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import pricing
from app.describer import describe_item
from app.pricing import estimate_price, net_payout, validate_comps_csv
from app.store import calibration, delete_item, list_items, record_sale, save_item, stats

app = FastAPI(title="FlipPrice — vintage reseller side hustle")

if os.getenv("SENTRY_DSN"):
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], traces_sample_rate=0.1)
    except Exception:
        pass
BASE = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_PHOTOS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


class AppraiseIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    brand: str = Field(default="unbranded", max_length=60)
    category: str = Field(default="misc", max_length=60)
    condition: Literal["sealed", "like_new", "good", "fair", "poor"]
    age_years: float = Field(default=1.0, ge=0, le=100)
    buy_cost: float = Field(default=0.0, ge=0, le=1_000_000)
    fee_pct: float = Field(default=13.0, ge=0, le=50)
    notes: str = Field(default="", max_length=500)
    photo_url: str = Field(default="", max_length=200)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "flipprice"}


@app.post("/api/appraise", status_code=201)
def appraise(inp: AppraiseIn):
    price = estimate_price(inp.brand.strip() or "unbranded", inp.category.strip() or "misc",
                           inp.condition, inp.age_years)
    listing = describe_item(inp.name.strip(), inp.brand.strip() or "unbranded",
                            inp.category.strip() or "misc", inp.condition, inp.notes.strip())
    payout = net_payout(price["p50"], inp.buy_cost, inp.fee_pct)
    return save_item({"name": inp.name.strip(), "brand": inp.brand.strip(),
                      "category": inp.category.strip(), "condition": inp.condition,
                      "age_years": inp.age_years, "notes": inp.notes.strip(),
                      "photo_url": inp.photo_url, "fee_pct": inp.fee_pct,
                      "price": price, "listing": listing, "payout": payout})


@app.get("/api/items")
def items():
    return list_items()


class SaleIn(BaseModel):
    sold_price: float = Field(ge=0, le=10_000_000)


@app.patch("/api/items/{item_id}")
def record_item_sale(item_id: str, sale: SaleIn):
    item = record_sale(item_id, sale.sold_price)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return item


@app.get("/api/calibration")
def accuracy():
    return calibration()


@app.delete("/api/items/{item_id}")
def remove_item(item_id: str):
    if not delete_item(item_id):
        raise HTTPException(status_code=404, detail="item not found — was it already deleted?")
    return {"deleted": item_id}


FEE_PRESETS = {"etsy": 6.5, "ebay": 13.0, "depop": 10.0, "flat": 0.0}


@app.get("/api/fees")
def fee_presets():
    return FEE_PRESETS


@app.get("/api/items.csv")
def export_items_csv():
    import csv
    import io as _io

    buf = _io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", "brand", "category", "condition", "p50", "low", "high",
                "buy_cost", "fees", "net", "margin_pct", "engine"])
    for i in list_items():
        p, pay = i.get("price", {}), i.get("payout", {})
        w.writerow([i.get("name"), i.get("brand"), i.get("category"), i.get("condition"),
                    p.get("p50"), p.get("low"), p.get("high"), pay.get("buy_cost"),
                    pay.get("fees"), pay.get("net"), pay.get("margin_pct"),
                    (p.get("engine") or "").split(" (")[0]])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=flipprice-inventory.csv"})


@app.get("/api/stats")
def dashboard_stats():
    return stats()


@app.post("/api/photos")
async def upload_photo(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_PHOTOS:
        raise HTTPException(status_code=400, detail="photo must be .png or .jpg")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty file — pick a real photo")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="photo over 2 MB — resize and retry")
    safe = "".join(c for c in os.path.basename(file.filename) if c.isalnum() or c in "._-")
    dest = os.path.join(UPLOAD_DIR, safe or "photo.png")
    with open(dest, "wb") as f:
        f.write(data)
    return {"photo_url": f"/uploads/{os.path.basename(dest)}"}


@app.post("/api/comps")
async def upload_comps(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="comps must be a .csv file")
    tmp = pricing.ACTIVE_PATH + ".tmp"
    with open(tmp, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        rows = validate_comps_csv(tmp)
    except ValueError as e:
        os.remove(tmp)
        raise HTTPException(status_code=400, detail=str(e))
    os.replace(tmp, pricing.ACTIVE_PATH)
    return {"rows": rows, "active": True,
            "note": "price estimates now learn from your sales history"}


app.mount("/", StaticFiles(directory=os.path.join(BASE, "static"), html=True), name="static")
