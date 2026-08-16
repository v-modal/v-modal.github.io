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
import urllib.request, urllib.error
import fire

BASE_URL     = "https://www.outrank.so/api/agent/v1"
ARTICLES_DIR = "articles"
INDEX_HTML   = "index.html"
API_KEY_ENV  = "OUT_API_KEY"


# ── HTTP helpers ─────────────────────────────────────────────────────────────

def _req(path: str, api_key: str) -> dict:
    url = BASE_URL + path
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept":        "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"API {e.code} {e.reason} on {url}\n{body}")


def _req_html(path: str, api_key: str) -> str:
    url = BASE_URL + path
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept":        "text/html,application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw  = resp.read()
        enc  = resp.headers.get_content_charset() or "utf-8"
        data = raw.decode(enc, errors="replace")
        # if JSON returned, pull out html/content field
        if resp.headers.get_content_type() in ("application/json", "application/json; charset=utf-8"):
            obj = json.loads(data)
            return obj.get("html") or obj.get("content") or json.dumps(obj, indent=2)
        return data


# ── Slug / dedup ─────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:50]


def _already_saved(article_id: str) -> Optional[str]:
    """Return existing filename if article_id is already in articles/."""
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    for fn in os.listdir(ARTICLES_DIR):
        if article_id in fn:
            return fn
    return None


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
    print(json.dumps(_req("/auth/whoami", key), indent=2))


def fetch():
    """Fetch the most recent published article; skip if already saved."""
    key = os.environ.get(API_KEY_ENV)
    if not key:
        sys.exit(f"ERROR: {API_KEY_ENV} environment variable is not set")

    # 1. list articles
    print("Fetching article list…")
    data = _req("/articles", key)

    articles = data if isinstance(data, list) else data.get("articles") or data.get("data") or []
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
        html_content = _req_html(f"/articles/{article_id}/content", key)
    except urllib.error.HTTPError as e:
        print(f"Content endpoint failed ({e.code}), falling back to metadata page.")
        meta = _req(f"/articles/{article_id}", key)
        html_content = f"<html><body><h1>{title}</h1><pre>{json.dumps(meta, indent=2)}</pre></body></html>"

    # 5. save
    try:
        dt = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        ymd = dt.strftime("%Y%m%d")
    except Exception:
        ymd = datetime.date.today().strftime("%Y%m%d")

    slug     = _slugify(title)
    filename = f"{ymd}_{article_id}_{slug}.html"
    dest     = os.path.join(ARTICLES_DIR, filename)
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved: {dest}")

    # 6. update index.html
    if isinstance(tags, list):
        tag_str = ", ".join(str(t) for t in tags)
    else:
        tag_str = str(tags)
    _add_to_index(f"articles/{filename}", title, summary, tag_str, published_at)


if __name__ == "__main__":
    fire.Fire({"fetch": fetch, "whoami": whoami})
