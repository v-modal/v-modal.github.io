"""Generate the article text for a topic.

Content generation prefers Bright Data's Google AI Mode API when configured, and
otherwise falls back to SerpApi's Google AI Overview (a two-step call: a Google search
yields an ai_overview, either inline or via a short-lived page_token that is then
fetched from the AI-overview engine). Google only returns an AI answer for some
queries, so when there is none (or neither provider is configured) we fall back to the
topic's own self-contained body so the publisher always produces a complete article.
"""
from typing import Any, Dict

import requests

SERPAPI_SEARCH = "https://serpapi.com/search"

# Bright Data Google AI Mode dataset (synchronous scrape endpoint).
BRIGHTDATA_SCRAPE = "https://api.brightdata.com/datasets/v3/scrape"
BRIGHTDATA_AIMODE_DATASET = "gd_mcswdt6z2elth3zqr2"
# Keys most likely to hold the AI answer in Bright Data's response, in priority order.
_AIMODE_TEXT_KEYS = (
    "answer_text", "answer", "ai_overview", "overview",
    "markdown", "text", "content", "response", "result",
)


def _overview_text(ai_overview: Dict[str, Any]) -> str:
    """Flatten SerpApi ai_overview.text_blocks into plain text (markdown-ish)."""
    parts = []
    for block in ai_overview.get("text_blocks") or []:
        snippet = str(block.get("snippet") or "").strip()
        if snippet:
            parts.append(snippet)
        for item in block.get("list") or []:
            s = str(item.get("snippet") or "").strip()
            if s:
                parts.append(f"- {s}")
    return "\n".join(parts).strip()


def fetch_ai_overview(query: str, api_key: str, get=requests.get) -> str:
    """Return Google's AI Overview text for `query`, or "" when there is none."""
    if not api_key:
        return ""
    resp = get(SERPAPI_SEARCH, params={"engine": "google", "q": query, "api_key": api_key}, timeout=30)
    resp.raise_for_status()
    data = resp.json() or {}
    ai = data.get("ai_overview") or {}
    text = _overview_text(ai)
    if text:
        return text
    token = str(ai.get("page_token") or "").strip()
    if not token:
        return ""
    resp2 = get(
        SERPAPI_SEARCH,
        params={"engine": "google_ai_overview", "page_token": token, "api_key": api_key},
        timeout=30,
    )
    resp2.raise_for_status()
    data2 = resp2.json() or {}
    return _overview_text(data2.get("ai_overview") or {})


def _extract_aimode_text(data) -> str:
    """Best-effort pull of the readable AI answer out of Bright Data's response.

    The scrape endpoint returns a list of result objects; the exact schema for the
    Google AI Mode dataset varies, so walk it and take the first non-empty string under
    a known answer key (recursing into nested dicts/lists)."""
    items = data if isinstance(data, list) else [data]
    for item in items:
        if isinstance(item, str):
            if item.strip():
                return item.strip()
            continue
        if not isinstance(item, dict):
            continue
        for key in _AIMODE_TEXT_KEYS:
            val = item.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
            if isinstance(val, (list, dict)):
                nested = _extract_aimode_text(val if isinstance(val, list) else [val])
                if nested:
                    return nested
    return ""


def fetch_ai_mode(query: str, api_key: str, post=requests.post) -> str:
    """Return Google AI Mode text for `query` via Bright Data, or "" when unavailable.
    `post` is injectable for tests."""
    if not api_key:
        return ""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "input": [{"url": "https://google.com/aimode", "prompt": query, "hl": "en", "country": ""}],
        "limit_per_input": None,
    }
    resp = post(
        BRIGHTDATA_SCRAPE,
        params={"dataset_id": BRIGHTDATA_AIMODE_DATASET, "notify": "false", "include_errors": "true"},
        headers=headers, json=payload, timeout=60,
    )
    resp.raise_for_status()
    return _extract_aimode_text(resp.json())


def generate_article_body(topic, config, get=requests.get, post=requests.post) -> str:
    """Return the article body (markdown-ish text) for a topic.

    Uses the Google AI answer when available (Bright Data preferred, SerpApi as a
    fallback), otherwise the topic's own self-contained body. Never raises on a
    missing or failing provider."""
    query = topic.prompt
    overview = ""
    if getattr(config, "brightdata_enabled", False):
        try:
            overview = fetch_ai_mode(query, config.brightdata_api_key, post=post)
        except Exception:
            overview = ""
    if not overview and getattr(config, "serpapi_enabled", False):
        try:
            overview = fetch_ai_overview(query, config.serpapi_key, get=get)
        except Exception:
            overview = ""
    return overview.strip() if overview else topic.fallback_body()
