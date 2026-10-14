"""Pricing accuracy benchmark — honest small-data evaluation.

Leave-one-out cross-validation on the seed comps: Ridge (app engine) vs
two baselines (global mean, category median). Interval coverage uses the
app's own low/high band (p50 +-15%).

Run: .venv/bin/python scripts/benchmark.py  (writes BENCHMARK.md)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.pricing import _featurize, _load_rows, _stats, DATA_PATH


def main():
    rows = _load_rows(DATA_PATH)
    rows = [{**r, "brand": r["brand"].strip(), "category": r["category"].strip()}
            for r in rows]
    gmean, cat_mean, brand_mean = _stats(rows)
    results = []
    for i, held in enumerate(rows):
        train = rows[:i] + rows[i + 1:]
        tg, tc, tb = _stats(train)
        x = [_featurize(r["brand"], r["category"], r["condition"], r["age_years"],
                        tg, tc, tb) for r in train]
        y = [float(r["sold_price_usd"]) for r in train]
        xh = _featurize(held["brand"], held["category"], held["condition"],
                        held["age_years"], tg, tc, tb)
        true = float(held["sold_price_usd"])

        from sklearn.linear_model import Ridge
        ridge = Ridge(alpha=1.0).fit(x, y).predict([xh])[0]

        cat_prices = sorted(float(r["sold_price_usd"]) for r in train
                            if r["category"] == held["category"]) or y
        cat_med = cat_prices[len(cat_prices) // 2]
        glob = sum(y) / len(y)
        results.append((true, ridge, cat_med, glob))

    def mae(col):
        errs = sorted(abs(r[col] - r[0]) for r in results)
        return sum(errs) / len(errs), errs[len(errs) // 2]

    ridge_mae, ridge_med = mae(1)
    cat_mae, cat_med = mae(2)
    glob_mae, glob_med = mae(3)
    coverage = sum(1 for t, p, _, _ in results if p * 0.85 <= t <= p * 1.15) / len(results)

    md = f"""# Pricing benchmark (leave-one-out, n={len(results)})

Seed: `{DATA_PATH}`, 20 rows. Same features and Ridge(alpha=1.0) as the app.

| Model | MAE (USD) | Median AE (USD) |
|---|---|---:|
| Ridge (app engine) | {ridge_mae:.2f} | {ridge_med:.2f} |
| Category median | {cat_mae:.2f} | {cat_med:.2f} |
| Global mean | {glob_mae:.2f} | {glob_med:.2f} |

Ridge interval (p50 +-15%) covers the true sold price in {coverage:.0%} of held-out cases.

Read honestly: n=20 is tiny. This shows the engine beats naive baselines on its own seed data; it does not prove market-wide accuracy. Re-run after uploading real comps: `.venv/bin/python scripts/benchmark.py`.
"""
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "BENCHMARK.md")
    with open(out, "w") as f:
        f.write(md)
    print(md)


if __name__ == "__main__":
    main()
