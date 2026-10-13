"""Price estimation: TabPFN first (featured category), sklearn fallback."""
import csv, os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "seed_sales.csv")
COND_SCORE = {"sealed": 1.0, "like_new": 0.85, "good": 0.65, "fair": 0.45, "poor": 0.3}


def _load_rows():
    with open(DATA_PATH, newline="") as f:
        return list(csv.DictReader(f))


def _featurize(brand, category, condition, age_years):
    return [len(brand), len(category), COND_SCORE.get(condition, 0.5), float(age_years or 0)]


def estimate_price(brand: str, category: str, condition: str, age_years: float = 1.0) -> dict:
    rows = _load_rows()
    X = [_featurize(r["brand"], r["category"], r["condition"], r["age_years"]) for r in rows]
    y = [float(r["sold_price_usd"]) for r in rows]
    x_new = [_featurize(brand, category, condition, age_years)]

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
    # 2) sklearn fallback so judges can run without GPU/heavy deps.
    try:
        from sklearn.ensemble import RandomForestRegressor

        reg = RandomForestRegressor(n_estimators=100, random_state=0)
        reg.fit(X, y)
        pred = float(reg.predict(x_new)[0])
        engine = "sklearn-fallback (pip install tabpfn for TabPFN)"
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
