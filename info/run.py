"""
Fetch the most recent published article from the Outrank.so API.
Skips if the article ID already exists in articles/.
Updates index.html with a new entry.

Usage:
    python info/run.py fetch
    python info/run.py whoami
"""
from typing import Optional
import os, sys, json, re, datetime
import fire
import pandas as pd
import requests
import markdown as md_lib

BASE_URL     = "https://www.outrank.so/api/agent/v1"
ARTICLES_DIR = "articles"
INDEX_HTML   = "index.html"
API_KEY_ENV  = "OUT_API_KEY"
FETCHED_IDS  = "info/fetched_ids.json"


# ── HTTP helpers ─────────────────────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",  # exclude br — requests can't decode Brotli
}


def _session(api_key: str) -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)
    s.headers["Authorization"] = f"Bearer {api_key}"
    return s


def _req(path: str, api_key: str) -> dict:
    url = BASE_URL + path
    resp = _session(api_key).get(url, headers={"Accept": "application/json"}, timeout=30)
    print(f"  {resp.status_code} {url}  (body: {len(resp.content)} bytes)")
    if not resp.ok:
        raise SystemExit(f"API {resp.status_code} on {url}\n{resp.text}")
    if not resp.content:
        return {}
    return resp.json()


def _req_html(path: str, api_key: str, title: str = "") -> str:
    url = BASE_URL + path
    resp = _session(api_key).get(url, headers={"Accept": "application/json"}, timeout=30)
    if not resp.ok:
        raise SystemExit(f"API {resp.status_code} on {url}\n{resp.text}")
    obj  = resp.json()
    data = obj.get("data") or obj
    # prefer explicit html field, else convert markdown content
    html_body = data.get("html") or ""
    if not html_body:
        raw = data.get("content") or ""
        html_body = md_lib.markdown(raw, extensions=["tables", "fenced_code"])
    page_title = data.get("title") or title
    return (
        f"<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        f"  <meta charset='UTF-8'/>\n"
        f"  <meta name='viewport' content='width=device-width, initial-scale=1.0'/>\n"
        f"  <title>{page_title}</title>\n"
        f"  <link rel='stylesheet' href='../style.css'/>\n"
        f"</head>\n<body>\n"
        f"  <header>\n"
        f"    <a href='../index.html'>V-Modal AI Blog: Search, MultiModality, Physical AI</a>\n"
        f"  </header>\n"
        f"  <main>\n"
        f"    <a href='../index.html' class='back-link'>&#8592; Back to articles</a>\n"
        f"    <h1>{page_title}</h1>\n"
        f"    {html_body}\n"
        f"  </main>\n"
        f"  <footer>&copy; 2026 V-Modal AI Blog</footer>\n"
        f"</body>\n</html>"
    )


# ── Slug / dedup ─────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:50]


def _load_ids() -> dict:
    if os.path.exists(FETCHED_IDS):
        with open(FETCHED_IDS) as f:
            return json.load(f)
    return {}


def _save_id(article_id: str, filename: str):
    ids = _load_ids()
    ids[article_id] = filename
    with open(FETCHED_IDS, "w") as f:
        json.dump(ids, f, indent=2)


def _already_saved(article_id: str) -> Optional[str]:
    return _load_ids().get(article_id)


# ── index.html update ────────────────────────────────────────────────────────

def _add_to_index(href: str, title: str, summary: str, tags, published_at: str):
    try:
        dt = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except Exception:
        dt = datetime.datetime.utcnow()
    month_label = dt.strftime("%b %Y")

    if isinstance(tags, (list, tuple)):
        parts = [str(t).strip() for t in tags]
    else:
        parts = [t.strip() for t in str(tags).split(",")]
    tag_str = " &middot; ".join(p for p in parts if p)

    entry = (
        f'      <li>\n'
        f'        <a href="{href}">{title}</a>\n'
        f'        <div class="summary">{summary}</div>\n'
        f'        <div class="meta">{month_label} &middot; {tag_str}</div>\n'
        f'      </li>'
    )

    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    idx = html.rfind("</ul>")
    if idx == -1:
        print(f"WARNING: </ul> not found in {INDEX_HTML} — skipping update")
        return
    html = html[:idx] + entry + "\n    " + html[idx:]
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"index.html updated: {title}")


# ── Commands ─────────────────────────────────────────────────────────────────

def whoami():
    """Verify API key and show org info."""
    key = os.environ.get(API_KEY_ENV) or sys.exit(f"Set {API_KEY_ENV}")
    url = BASE_URL + "/auth/whoami"
    resp = _session(key).get(url, headers={"Accept": "application/json"}, timeout=30)
    print(f"status: {resp.status_code}")
    print(f"headers: {dict(resp.headers)}")
    print(f"body: {resp.text[:2000]}")


def _generated_articles(key: str) -> list:
    data = _req("/articles", key)
    raw = data.get("data") or data
    articles = raw.get("items") or raw if isinstance(raw, dict) else raw
    articles = articles or []
    generated = [article for article in articles if article.get("status") == "generated"]
    return sorted(
        generated,
        key=lambda article: article.get("created_at") or article.get("date_created") or "",
        reverse=True,
    )


def fetch_all_article_title() -> pd.DataFrame:
    """Return generated article IDs, titles, and creation dates."""
    key = os.environ.get(API_KEY_ENV)
    if not key:
        sys.exit(f"ERROR: {API_KEY_ENV} environment variable is not set")

    rows = []
    for article in _generated_articles(key):
        rows.append({
            "article_id": str(article.get("id") or article.get("_id") or "unknown"),
            "title": article.get("title") or "Untitled",
            "date_created": article.get("date_created") or article.get("created_at") or "",
        })
    return pd.DataFrame(rows, columns=["article_id", "title", "date_created"])


def fetch_generated(n: int = 1):
    """Fetch and save the newest n generated articles."""
    key = os.environ.get(API_KEY_ENV)
    if not key:
        sys.exit(f"ERROR: {API_KEY_ENV} environment variable is not set")
    if n < 1:
        raise ValueError("n must be at least 1")

    generated = _generated_articles(key)[:n]
    if not generated:
        print("No generated articles returned from API.")
        return

    for article in generated:
        article_id = str(article.get("id") or article.get("_id") or "unknown")
        title = article.get("title") or "Untitled"
        summary = article.get("summary") or article.get("excerpt") or ""
        created_at = article.get("date_created") or article.get("created_at") or datetime.date.today().isoformat()
        tags = article.get("tags") or article.get("keywords") or ["AI"]

        existing = _already_saved(article_id)
        if existing:
            print(f"Already saved: {existing} — skipping.")
            continue

        print(f"Fetching generated article: [{article_id}] {title}")
        html_content = _req_html(f"/articles/{article_id}/content", key, title)
        try:
            dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            ymd = dt.strftime("%Y%m%d")
        except Exception:
            ymd = datetime.date.today().strftime("%Y%m%d")

        filename = f"{ymd}_{_slugify(title)}.html"
        dest = os.path.join(ARTICLES_DIR, filename)
        os.makedirs(ARTICLES_DIR, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(html_content)
        _save_id(article_id, filename)

        tag_str = ", ".join(str(tag) for tag in tags) if isinstance(tags, list) else str(tags)
        _add_to_index(f"articles/{filename}", title, summary, tag_str, created_at)
        print(f"Saved: {dest}")


def fetch():
    """Fetch the most recent published article; skip if already saved."""
    key = os.environ.get(API_KEY_ENV)
    if not key:
        sys.exit(f"ERROR: {API_KEY_ENV} environment variable is not set")

    # 1. list articles
    print("Fetching article list…")
    data = _req("/articles", key)

    raw = data.get("data") or data
    articles = raw.get("items") or raw if isinstance(raw, dict) else raw
    if not articles:
        print("No articles returned from API.")
        return

    # 2. filter published, sort by published_at desc
    published = [a for a in articles if a.get("status") == "published"]
    if not published:
        # fallback: take all and sort
        published = articles
    published.sort(key=lambda a: a.get("published_at") or a.get("created_at") or "", reverse=True)
    latest = published[0]

    article_id   = str(latest.get("id") or latest.get("_id") or "unknown")
    title        = latest.get("title") or "Untitled"
    summary      = latest.get("summary") or latest.get("excerpt") or ""
    published_at = latest.get("published_at") or latest.get("created_at") or datetime.date.today().isoformat()
    tags         = latest.get("tags") or latest.get("keywords") or ["AI"]

    print(f"Latest article: [{article_id}] {title}")

    # 3. dedup check
    existing = _already_saved(article_id)
    if existing:
        print(f"Already saved: {existing} — nothing to do.")
        return

    # 4. fetch HTML content
    print(f"Fetching content for article {article_id}…")
    try:
        html_content = _req_html(f"/articles/{article_id}/content", key, title)
    except Exception as e:
        raise SystemExit(f"Content fetch failed: {e}")

    # 5. save
    try:
        dt = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        ymd = dt.strftime("%Y%m%d")
    except Exception:
        ymd = datetime.date.today().strftime("%Y%m%d")

    slug     = _slugify(title)
    filename = f"{ymd}_{slug}.html"
    dest     = os.path.join(ARTICLES_DIR, filename)
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved: {dest}")

    _save_id(article_id, filename)

    # 6. update index.html
    if isinstance(tags, list):
        tag_str = ", ".join(str(t) for t in tags)
    else:
        tag_str = str(tags)
    _add_to_index(f"articles/{filename}", title, summary, tag_str, published_at)


if __name__ == "__main__":
    fire.Fire({
        "fetch": fetch,
        "fetch_all_article_title": fetch_all_article_title,
        "fetch_generated": fetch_generated,
        "whoami": whoami,
    })
