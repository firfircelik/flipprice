# FlipPrice — know what it's worth before you list it

Side Hustle entry for the [Hacktoberfest Open-Source AI Challenge: Week 2](https://dev.to/challenges/hacktoberfest-week2-2026-10-12) (Oct 12–18, 2026).

Vintage / second-hand resellers live on margins: buy low at flea markets, list fast on Etsy/eBay, don't lose money to fees. FlipPrice turns a photo + 4 fields into a listing draft + fair-price range + net payout — with **zero per-listing API cost**.

## Why open matters (the core of the entry)

- **Cost:** closed vision+LLM APIs charge per image + per token. A reseller listing 50 items/week can't pay $0.05–0.15 per listing. Local **Gemma 3 via Ollama** makes unit cost ~$0, so the business actually works.
- **Privacy/offline:** flea markets have no signal. Local inference works offline; sellers' sourcing spots and costs never leave the laptop.
- **Niche fit:** generic price guides fail on vintage condition quirks. **TabPFN** (open-source tabular foundation model, Prior Labs) learns fair price from *your* sold comps CSV — small data, no tuning.

## Stack

- Python + FastAPI (`app/main.py`), static HTML demo
- Open-weight: Gemma 3 via Ollama (`OLLAMA_MODEL=gemma3:4b`) — `app/describer.py`
- Open-source AI: TabPFN regressor, sklearn fallback — `app/pricing.py`
- Storage: local JSON, upgrades to MongoDB Atlas if `MONGODB_URI` set — `app/store.py` (Best Use of MongoDB Atlas path)
- Deploy: Render-ready (`render.yaml` below)

## Run

```bash
pip install -r requirements.txt
# optional, for the real open models:
# ollama pull gemma3:4b && ollama serve
# pip install tabpfn pymongo
uvicorn app.main:app --reload --port 8000
# open http://localhost:8000
```

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
