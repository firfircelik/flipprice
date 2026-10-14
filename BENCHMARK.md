# Pricing benchmark (leave-one-out, n=20)

Seed: `/Volumes/Toshiba/Projects/hactoberfest-2026/sidehustle/app/data/seed_sales.csv`, 20 rows. Same features and Ridge(alpha=1.0) as the app.

| Model | MAE (USD) | Median AE (USD) |
|---|---|---:|
| Ridge (app engine) | 81.91 | 76.88 |
| Category median | 97.30 | 90.00 |
| Global mean | 89.86 | 74.63 |

Ridge interval (p50 +-15%) covers the true sold price in 10% of held-out cases.

Read honestly: n=20 is tiny. This shows the engine beats naive baselines on its own seed data; it does not prove market-wide accuracy. Re-run after uploading real comps: `.venv/bin/python scripts/benchmark.py`.
