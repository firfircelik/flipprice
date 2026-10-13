"""Gemma (open-weight) listing writer via Ollama, with offline fallback."""
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")
# Local open-weight fallbacks (first hit wins) — keeps the demo genuinely
# model-powered even when the preferred model isn't pulled yet.
FALLBACK_MODELS = ("llama3.2:1b", "qwen2.5:7b")


def _ollama_generate(model: str, prompt: str, timeout: int = 120) -> str:
    import urllib.request, json

    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode()).get("response", "").strip()


def describe_item(name: str, brand: str, category: str, condition: str, notes: str = "") -> dict:
    """Try Ollama/Gemma, fall back to a template so the demo never breaks."""
    prompt = (
        f"Write an Etsy/eBay listing for a second-hand item. "
        f"Item: {name}, Brand: {brand}, Category: {category}, Condition: {condition}. "
        f"Notes: {notes}. IMPORTANT: reply with ONLY the listing title on line 1 "
        f"(max 80 chars, no preamble, no quotes), then a 3-sentence honest "
        f"description plus 5 search keywords on the following lines."
    )
    import re
    preamble = re.compile(r"^(here is|here'?s|of course|sure\b|certainly|.*possible listing)", re.I)

    def clean(text: str):
        lines = [ln.strip(" *#") for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]
        lines = [ln for ln in lines if not preamble.match(ln)]
        lines = [re.sub(r"^(title\s*:\s*)", "", ln, flags=re.I) for ln in lines]
        return lines
    for model in (OLLAMA_MODEL, *FALLBACK_MODELS):
        try:
            text = _ollama_generate(model, prompt)
        except Exception:
            continue
        if text:
            lines = clean(text)
            if not lines:
                continue
            title = lines[0].strip().strip("\"'")[:80]
            if brand.lower() not in title.lower():  # marketplace SEO: brand first
                title = f"{brand} {title}"[:80]
            return {"title": title, "description": text, "engine": f"ollama:{model}"}
    title = f"{brand} {name} — {condition} ({category})".strip()[:80]
    desc = (
        f"Second-hand {name} from {brand} in {condition} condition. "
        f"Category: {category}. {notes or 'Tested and cleaned, ships fast.'} "
        f"Great value vs new — feel free to ask for extra photos."
    )
    return {"title": title, "description": desc, "engine": "fallback-template (start Ollama for Gemma)"}
