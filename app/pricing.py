"""Price estimation: TabPFN first (featured category), Ridge fallback.

Resellers can upload their own sold-comps CSV (same columns as seed file);
it becomes the active training set until replaced.
"""
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_PATH = os.path.join(DATA_DIR, "seed_sales.csv")
ACTIVE_PATH = os.path.join(DATA_DIR, "active_comps.csv")
REQUIRED_COLUMNS = {"brand", "category", "condition", "age_years", "sold_price_usd"}
COND_SCORE = {"sealed": 1.0, "like_new": 0.85, "good": 0.65, "fair": 0.45, "poor": 0.3}


def active_comps_path() -> str:
    return ACTIVE_PATH if os.path.exists(ACTIVE_PATH) else DATA_PATH


def validate_comps_csv(path: str) -> int:
    """Raise ValueError with a human message when the CSV is unusable."""
    with open(path, newline="") as f:
        try:
            rows = list(csv.DictReader(f))
        except Exception:
            raise ValueError("could not parse CSV — is it comma-separated?")
    if not rows:
        raise ValueError("CSV is empty — add at least 5 sold rows")
    missing = REQUIRED_COLUMNS - set(rows[0].keys() or [])
    if missing:
        raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
    if len(rows) < 5:
        raise ValueError(f"only {len(rows)} rows — add at least 5 for a stable estimate")
    for i, r in enumerate(rows, start=2):
        try:
            float(r["age_years"])
            price = float(r["sold_price_usd"])
        except (TypeError, ValueError):
            raise ValueError(f"row {i}: age_years and sold_price_usd must be numbers")
        if price <= 0:
            raise ValueError(f"row {i}: sold_price_usd must be positive")
    return len(rows)


def _load_rows(path: str):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _stats(rows):
    prices = [float(r["sold_price_usd"]) for r in rows]
    gmean = sum(prices) / len(prices)
    cat, brand = {}, {}
    for r in rows:
        cat.setdefault(r["category"], []).append(float(r["sold_price_usd"]))
        brand.setdefault(r["brand"], []).append(float(r["sold_price_usd"]))
    return gmean, {k: sum(v) / len(v) for k, v in cat.items()}, \
        {k: sum(v) / len(v) for k, v in brand.items()}


def _featurize(brand, category, condition, age_years, gmean, cat_mean, brand_mean):
    return [COND_SCORE.get(condition, 0.5), float(age_years or 0),
            cat_mean.get(category, gmean), brand_mean.get(brand, gmean)]


def estimate_price(brand: str, category: str, condition: str, age_years: float = 1.0) -> dict:
    rows = _load_rows(active_comps_path())
    gmean, cat_mean, brand_mean = _stats(rows)
    X = [_featurize(r["brand"], r["category"], r["condition"], r["age_years"],
                    gmean, cat_mean, brand_mean) for r in rows]
    y = [float(r["sold_price_usd"]) for r in rows]
    x_new = [_featurize(brand, category, condition, age_years,
                        gmean, cat_mean, brand_mean)]

    # 1) TabPFN — open-source tabular foundation model (Prior Labs).
    try:
        from tabpfn import TabPFNRegressor

        reg = TabPFNRegressor()
        reg.fit(X, y)
        pred = float(reg.predict(x_new)[0])
        return {"p50": round(pred, 2), "low": round(pred * 0.85, 2),
                "high": round(pred * 1.15, 2), "engine": "tabpfn"}
    except Exception:
        pass
    # 2) Ridge fallback: on 20-row reseller CSVs a linear model learns the
    # condition->price gradient where tree ensembles memorize noise.
    try:
        from sklearn.linear_model import Ridge

        reg = Ridge(alpha=1.0)
        reg.fit(X, y)
        pred = float(reg.predict(x_new)[0])
        engine = "sklearn-ridge-fallback (pip install tabpfn for TabPFN)"
    except Exception:
        avg = sum(y) / len(y)
        pred, engine = avg, "mean-fallback"
    return {"p50": round(pred, 2), "low": round(pred * 0.85, 2),
            "high": round(pred * 1.15, 2), "engine": engine}


def net_payout(list_price: float, buy_cost: float = 0.0, fee_pct: float = 13.0) -> dict:
    fee = list_price * fee_pct / 100.0
    net = list_price - fee - buy_cost
    return {"list_price": list_price, "fees": round(fee, 2),
            "buy_cost": buy_cost, "net": round(net, 2),
            "margin_pct": round(net / list_price * 100, 1) if list_price else 0}
