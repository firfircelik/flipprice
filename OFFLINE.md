# Offline verification (network-disabled operation)

Claim: FlipPrice appraises without connectivity (flea-market scenario).

## Procedure

1. Stop Ollama (`ollama stop` or kill the server) and disconnect network.
2. Run: `.venv/bin/python -m pytest tests/test_app.py -q -k "offline or offline_mode or no_signal or condition or payout or presets or photo or market or calibration"`
3. Manually: `uvicorn app.main:app`, POST /api/appraise, confirm 200 with
   `fallback-template` engine and local-JSON persistence.

## Last evidence (2026-10-14, Apple M2)

- Offline round trip: ~1.6 s, HTTP 201, template fallback engine.
- Offline journey tests green with Ollama pointed at a dead port.
- Full suite 8/8 green; live-model test requires OLLAMA_LIVE=1 and is
  skipped in CI (see .github/workflows/ci.yml).

## Gaps

- Photo upload and UI were not exercised under a fully network-disabled OS
  profile, only with the model server down. A complete check needs airplane
  mode plus a cold start.
