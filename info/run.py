"""
Fetch an article from the Outrank.so API and save as HTML.
Updates index.html with a new article entry.

Usage:
    python info/run.py fetch --url URL [--api_key KEY] [--title TITLE] [--summary SUMMARY] [--tags TAGS]
    python info/run.py fetch_default
"""
from typing import Optional
import os, sys
import datetime
import re
import urllib.request
import urllib.parse
import urllib.error
import fire


ARTICLES_DIR = "articles"
INDEX_HTML    = "index.html"
API_KEY_ENV   = "OUT_API_KEY"


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:60]


def _fetch_html(url: str, api_key: Optional[str]) -> str:
    req = urllib.request.Request(url)
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Accept", "text/html,application/xhtml+xml")
    req.add_header("User-Agent", "vmodal-blog-fetcher/1.0")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        charset = "utf-8"
        ct = resp.headers.get_content_charset()
        if ct:
            charset = ct
        return raw.decode(charset, errors="replace")


def _add_to_index(href: str, title: str, summary: str, tags, ymd: str):
    month_label = datetime.datetime.strptime(ymd, "%Y%m%d").strftime("%b %Y")
    if isinstance(tags, (list, tuple)):
        parts = [str(t).strip() for t in tags]
    else:
        parts = [t.strip() for t in str(tags).split(",")]
    tag_str = " &middot; ".join(p for p in parts if p)

    entry = f"""      <li>
        <a href="{href}">{title}</a>
        <div class="summary">{summary}</div>
        <div class="meta">{month_label} &middot; {tag_str}</div>
      </li>"""

    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    marker = "</ul>"
    if marker not in html:
        print(f"WARNING: could not find {marker!r} in {INDEX_HTML} — skipping update")
        return

    # insert before the last </ul> in the article-list block
    idx = html.rfind(marker)
    html = html[:idx] + entry + "\n    " + html[idx:]

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"index.html updated with: {title}")


def fetch(
    url: str = "https://www.outrank.so/docs/api",
    api_key: Optional[str] = None,
    title: str = "Outrank.so API Documentation",
    summary: str = "Full API reference for the Outrank.so content generation platform.",
    tags: str = "AI, API, SEO",
):
    """Fetch article HTML and add entry to index.html."""
    key = api_key or os.environ.get(API_KEY_ENV)
    ymd = datetime.date.today().strftime("%Y%m%d")
    slug = _slugify(title)
    filename = f"{ymd}_{slug}.html"
    dest = os.path.join(ARTICLES_DIR, filename)

    os.makedirs(ARTICLES_DIR, exist_ok=True)

    print(f"Fetching: {url}")
    html = _fetch_html(url, key)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {dest}")

    _add_to_index(f"articles/{filename}", title, summary, tags, ymd)
    return dest


def fetch_default():
    """Fetch using defaults — convenience wrapper for CI."""
    return fetch()


if __name__ == "__main__":
    fire.Fire({
        "fetch":         fetch,
        "fetch_default": fetch_default,
    })
