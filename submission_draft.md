---
title:
published: false
tags: devchallenge, hf26challenge
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

## What I Built

**FlipPrice — know what it's worth before you list it.** A tool for vintage / second-hand resellers (flea-market flippers, Etsy side-hustlers): enter 4 fields + item name → get a listing draft, a fair-price range learned from sold comps, and net payout after fees.

Who pays: resellers listing 20–50 items/week. They lose money two ways — underpricing good finds, and overpaying per-listing AI API fees. FlipPrice fixes both with zero per-listing inference cost.

## Demo

Local: `uvicorn app.main:app --port 8000` → http://localhost:8000

`POST /api/appraise` example:
```json
{"name":"Canon AE-1 film camera","brand":"canon","category":"camera","condition":"good","age_years":3,"buy_cost":50}
```
→ `price.p50 ≈ 184.62, payout.net ≈ 110.62 (59.9% margin)`, listing title + description. (Screenshot/GIF to add before publishing.)

## Code

GitHub repo link to add. MIT licensed. Stack: Python + FastAPI, static HTML, Ollama (Gemma 3), TabPFN with sklearn fallback, local JSON → MongoDB Atlas upgrade path, Render-ready.

## How I Built It

- `app/describer.py` — listing writer. Primary: Gemma 3 via Ollama (`OLLAMA_MODEL=gemma3:4b`). Fallback template keeps the demo runnable without a GPU.
- `app/pricing.py` — price estimator. Primary: TabPFN regressor trained on `app/data/seed_sales.csv` (your sold comps). Fallback: sklearn RandomForest, so judges run it with plain `pip install -r requirements.txt`.
- `app/store.py` — every appraisal saved; local JSON by default, MongoDB Atlas when `MONGODB_URI` is set.
- Open pieces are the core: without Gemma there's no listing draft, without TabPFN there's no price range.

## Why Does Open Innovation Matter?

1. **Unit economics:** closed vision/LLM APIs charge per image + token. At 50 listings/week that kills a reseller's margin. Local Gemma makes marginal cost ~$0 — the business only works because it's open.
2. **Offline + privacy:** sourcing happens at flea markets with no signal; costs and suppliers stay on the laptop, never on someone else's server.
3. **Niche fit:** generic price guides misprice vintage condition quirks. TabPFN learns from *your* 20-row sold CSV — small data, no tuning, swappable.

## My Agent Session

Optional — will embed DevRelay session link before publishing.

## My First User

TODO before Oct 18: hand it to one real reseller, record what they listed, whether the price range matched reality, and what they asked for next. (Bonus points live here.)

## Prize Categories

- Best Use of Gemma (featured)
- Best Use of TabPFN (featured)
- Best Use of MongoDB Atlas (partner, via `MONGODB_URI`)
- Best Use of Render (featured, via `render.yaml`)
