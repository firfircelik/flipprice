"""Storage: local JSON file, upgrades to MongoDB Atlas if MONGODB_URI is set."""
import json, os

LOCAL_PATH = os.path.join(os.path.dirname(__file__), "data", "items.json")


def _read_local():
    try:
        with open(LOCAL_PATH) as f:
            return json.load(f)
    except Exception:
        return []


def _write_local(items):
    os.makedirs(os.path.dirname(LOCAL_PATH), exist_ok=True)
    with open(LOCAL_PATH, "w") as f:
        json.dump(items, f, indent=2)


def save_item(item: dict) -> dict:
    uri = os.getenv("MONGODB_URI")
    if uri:
        try:
            from pymongo import MongoClient

            col = MongoClient(uri)["flipprice"]["items"]
            col.insert_one(item)
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
    uri = os.getenv("MONGODB_URI")
    if uri:
        try:
            from pymongo import MongoClient

            return list(MongoClient(uri)["flipprice"]["items"].find({}, {"_id": 0}))
        except Exception:
            pass
    return _read_local()
