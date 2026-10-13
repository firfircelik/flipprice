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
