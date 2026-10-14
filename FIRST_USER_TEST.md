# Dogfood test (agent-run simulation, NOT an external user)

Date: 2026-10-14. Server: local. Model: Ollama open-weight. Pricing: Ridge fallback (no TABPFN_TOKEN).

[
  {
    "item": "Canon AE-1 film camera",
    "title": "Canon AE-1 Film Camera – Good Condition",
    "engine": "ollama:gemma3:1b",
    "p50": 286.34,
    "low": 243.39,
    "high": 329.29,
    "pengine": "sklearn-ridge-fallback (accept TabPFN license + set TABPFN_TOKEN for TabPFN)",
    "net": 189.12,
    "margin": 66.0
  },
  {
    "item": "Levis 501 jeans",
    "title": "levis Levi’s 501 – Like New – Denim Jeans",
    "engine": "ollama:gemma3:1b",
    "p50": 108.85,
    "low": 92.52,
    "high": 125.18,
    "pengine": "sklearn-ridge-fallback (accept TabPFN license + set TABPFN_TOKEN for TabPFN)",
    "net": 79.7,
    "margin": 73.2
  },
  {
    "item": "Sony WH-1000XM3 headphones",
    "title": "Sony WH-1000XM3 Headphones - Good Condition - Pads Replaced, Case Included",
    "engine": "ollama:gemma3:1b",
    "p50": 116.82,
    "low": 99.3,
    "high": 134.34,
    "pengine": "sklearn-ridge-fallback (accept TabPFN license + set TABPFN_TOKEN for TabPFN)",
    "net": 61.63,
    "margin": 52.8
  }
]
