# FlipPrice — know what it's worth before you list it

> Side Hustle entry for the [Hacktoberfest Open-Source AI Challenge: Week 2](https://dev.to/challenges/hacktoberfest-week2-2026-10-12) (Oct 12–18, 2026).
> Repo: https://github.com/firfircelik/flipprice · Tests: 5/5 pytest green

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/firfircelik/flipprice)

![FlipPrice demo](https://raw.githubusercontent.com/firfircelik/flipprice/main/demo.gif)

Vintage / second-hand resellers live on margins: buy low at flea markets, list fast on Etsy/eBay, don't lose money to fees. FlipPrice turns a photo + 4 fields into a listing draft + fair-price range + net payout — with **zero per-listing API cost**.

## Why open matters (the core of the entry)

- **Cost:** closed vision+LLM APIs charge per image + per token. A reseller listing 50 items/week can't pay $0.05–0.15 per listing. Local **Gemma 3 via Ollama** makes unit cost ~$0, so the business actually works.
- **Privacy/offline:** flea markets have no signal. Local inference works offline; sellers' sourcing spots and costs never leave the laptop.
- **Niche fit:** generic price guides fail on vintage condition quirks. **TabPFN** (open-source tabular foundation model, Prior Labs) learns fair price from *your* sold comps CSV — small data, no tuning.

## Stack

- Python + FastAPI (`app/main.py`), static HTML demo
- Open-weight: Gemma 3 via Ollama (`OLLAMA_MODEL=gemma3:1b`, falls back to local `llama3.2:1b`/`qwen2.5:7b`) — `app/describer.py`. Verified live: `ollama:llama3.2:1b` writes real listings; Gemma pull in progress for the Gemma prize category.
- Open-source AI: TabPFN regressor, Ridge fallback tuned for 20-row reseller CSVs — `app/pricing.py`
- Storage: local JSON, upgrades to MongoDB Atlas if `MONGODB_URI` set — `app/store.py` (Best Use of MongoDB Atlas path)
- Deploy: Render-ready (`render.yaml` + Deploy button above)

## Run

```bash
pip install -r requirements.txt
# for the real open models:
ollama pull gemma3:1b && ollama serve
# pip install tabpfn pymongo
uvicorn app.main:app --reload --port 8000
# open http://localhost:8000
```

## Test

```bash
.venv/bin/python -m pytest tests/ -q   # 5 passed
```

Covers: price shape + bounds, condition monotonicity (better condition prices
higher — caught and fixed a real RandomForest bug during development), payout
math, describer contract, and full API round-trip.

API: `POST /api/appraise` `{name, brand, category, condition, age_years, buy_cost, notes}` → `{price{p50,low,high,engine}, listing{title,description,engine}, payout{net,margin_pct}}`

## Architecture

```mermaid
flowchart LR
  UI[static/index.html] --> API[FastAPI /api/appraise]
  API --> G[Gemma 3 via Ollama\nlisting draft]
  API --> T[TabPFN / sklearn\nprice range from sold comps]
  API --> M[MongoDB Atlas or local JSON]
  G -.fallback.-> Template
  T -.fallback.-> sklearn
```

## Prize categories entered

- Best Use of Gemma (featured) — listing writer runs on Gemma 3
- Best Use of TabPFN (featured) — price estimator runs TabPFN when installed
- Best Use of MongoDB Atlas (partner, optional) — set `MONGODB_URI`
- Best Use of Render (featured, optional) — deploy via `render.yaml`

## License

MIT — see LICENSE.
