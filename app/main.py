from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from app.describer import describe_item
from app.pricing import estimate_price, net_payout
from app.store import save_item, list_items

app = FastAPI(title="FlipPrice — vintage reseller side hustle")


class AppraiseIn(BaseModel):
    name: str
    brand: str = "unbranded"
    category: str = "misc"
    condition: str = "good"
    age_years: float = 1.0
    buy_cost: float = 0.0
    notes: str = ""


@app.get("/api/health")
def health():
    return {"ok": True, "service": "flipprice"}


@app.post("/api/appraise")
def appraise(inp: AppraiseIn):
    price = estimate_price(inp.brand, inp.category, inp.condition, inp.age_years)
    listing = describe_item(inp.name, inp.brand, inp.category, inp.condition, inp.notes)
    payout = net_payout(price["p50"], inp.buy_cost)
    item = {"name": inp.name, "brand": inp.brand, "category": inp.category,
            "condition": inp.condition, "price": price, "listing": listing, "payout": payout}
    return save_item(item)


@app.get("/api/items")
def items():
    return list_items()


BASE = os.path.dirname(os.path.dirname(__file__))
app.mount("/", StaticFiles(directory=os.path.join(BASE, "static"), html=True), name="static")
