"""Gemma (open-weight) listing writer via Ollama, with offline fallback."""
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")


def describe_item(name: str, brand: str, category: str, condition: str, notes: str = "") -> dict:
    """Try Ollama/Gemma, fall back to a template so the demo never breaks."""
    prompt = (
        f"Write an Etsy/eBay listing for a second-hand item. "
        f"Item: {name}, Brand: {brand}, Category: {category}, Condition: {condition}. "
        f"Notes: {notes}. Return a catchy title (max 80 chars) and a 3-sentence "
        f"honest description plus 5 search keywords."
    )
    try:
        import urllib.request, json

        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/generate",
            data=json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
        text = body.get("response", "").strip()
        if text:
            lines = text.splitlines()
            return {"title": lines[0][:80], "description": text, "engine": f"ollama:{OLLAMA_MODEL}"}
    except Exception:
        pass
    title = f"{brand} {name} — {condition} ({category})".strip()[:80]
    desc = (
        f"Second-hand {name} from {brand} in {condition} condition. "
        f"Category: {category}. {notes or 'Tested and cleaned, ships fast.'} "
        f"Great value vs new — feel free to ask for extra photos."
    )
    return {"title": title, "description": desc, "engine": "fallback-template (start Ollama for Gemma)"}
