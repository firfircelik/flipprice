"""Storage: local JSON file, upgrades to MongoDB Atlas if MONGODB_URI is set."""
import json
import os
import uuid

LOCAL_PATH = os.path.join(os.path.dirname(__file__), "data", "items.json")


def _read_local():
    try:
        with open(LOCAL_PATH) as f:
            items = json.load(f)
            return items if isinstance(items, list) else []
    except Exception:
        return []


def _write_local(items):
    os.makedirs(os.path.dirname(LOCAL_PATH), exist_ok=True)
    with open(LOCAL_PATH, "w") as f:
        json.dump(items, f, indent=2)


def _mongo_collection():
    from pymongo import MongoClient

    return MongoClient(os.environ["MONGODB_URI"])["flipprice"]["items"]


def save_item(item: dict) -> dict:
    item.setdefault("id", uuid.uuid4().hex[:12])
    if os.getenv("MONGODB_URI"):
        try:
            _mongo_collection().insert_one(dict(item))
            item["_store"] = "mongodb-atlas"
            return item
        except Exception:
            pass
    items = _read_local()
    items.append(item)
    _write_local(items)
    item["_store"] = "local-json"
    return item


def list_items() -> list:
    if os.getenv("MONGODB_URI"):
        try:
            return list(_mongo_collection().find({}, {"_id": 0}))
        except Exception:
            pass
    return _read_local()


def record_sale(item_id: str, sold_price: float) -> dict | None:
    """Attach a realized sale to an item; returns updated item or None."""
    import time

    if os.getenv("MONGODB_URI"):
        try:
            col = _mongo_collection()
            col.update_one({"id": item_id},
                           {"$set": {"sold_price": sold_price, "sold_at": int(time.time())}})
            return col.find_one({"id": item_id}, {"_id": 0})
        except Exception:
            pass
    items = _read_local()
    for i in items:
        if i.get("id") == item_id:
            i["sold_price"] = sold_price
            import time as _t
            i["sold_at"] = int(_t.time())
            _write_local(items)
            return i
    return None


def calibration() -> dict:
    """Estimate-vs-realized accuracy over sold items. Empty until sales exist."""
    sold = [i for i in list_items() if isinstance(i.get("sold_price"), (int, float))]
    if not sold:
        return {"n_sold": 0, "note": "record sales to calibrate estimates"}
    errs = [i["price"]["p50"] - i["sold_price"] for i in sold]
    abs_errs = sorted(abs(e) for e in errs)
    return {
        "n_sold": len(sold),
        "mae": round(sum(abs_errs) / len(abs_errs), 2),
        "median_ae": round(abs_errs[len(abs_errs) // 2], 2),
        "bias": round(sum(errs) / len(errs), 2),
    }


def delete_item(item_id: str) -> bool:
    if os.getenv("MONGODB_URI"):
        try:
            res = _mongo_collection().delete_one({"id": item_id})
            if res.deleted_count:
                return True
        except Exception:
            pass
    items = _read_local()
    kept = [i for i in items if i.get("id") != item_id]
    if len(kept) == len(items):
        return False
    _write_local(kept)
    return True


def stats() -> dict:
    items = list_items()
    nets = [i.get("payout", {}).get("net", 0) for i in items]
    margins = [i.get("payout", {}).get("margin_pct", 0) for i in items]
    fees = [i.get("payout", {}).get("fees", 0) for i in items]
    return {
        "count": len(items),
        "total_net": round(sum(nets), 2),
        "avg_margin_pct": round(sum(margins) / len(margins), 1) if margins else 0,
        "total_fees": round(sum(fees), 2),
    }
