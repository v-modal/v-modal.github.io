"""Render a topic and its generated body into the site's HTML.

The output matches the existing hand-written articles: a standalone page under
`articles/` using the shared template, plus a list item for `index.html`. The body
text (from the AI source or the topic fallback) is markdown-ish, so a small,
dependency-free converter turns ## / ### headings, bullet lists, and paragraphs into
the same tags the existing articles use.
"""
import re

MONTHS = ["", "January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(text: str) -> str:
    """Escape HTML, then apply inline markdown: `code`, **bold**, *em* / _em_."""
    out = _escape(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", out)
    out = re.sub(r"_([^_]+)_", r"<em>\1</em>", out)
    return out


def _is_bullet(line: str) -> bool:
    s = line.lstrip()
    return s.startswith("- ") or s.startswith("* ")


def render_body_html(markdown_text: str, indent: str = "      ") -> str:
    """Convert markdown-ish body text into the article's inner HTML."""
    lines = (markdown_text or "").replace("\r\n", "\n").split("\n")
    blocks = []
    para: list = []
    bullets: list = []

    def flush_para():
        if para:
            blocks.append(f"{indent}<p>{_inline(' '.join(para).strip())}</p>")
            para.clear()

    def flush_bullets():
        if bullets:
            items = "\n".join(f"{indent}  <li>{_inline(b)}</li>" for b in bullets)
            blocks.append(f"{indent}<ul>\n{items}\n{indent}</ul>")
            bullets.clear()

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_para()
            flush_bullets()
            continue
        if stripped.startswith("### "):
            flush_para(); flush_bullets()
            blocks.append(f"{indent}<h3>{_inline(stripped[4:].strip())}</h3>")
        elif stripped.startswith("## "):
            flush_para(); flush_bullets()
            blocks.append(f"{indent}<h2>{_inline(stripped[3:].strip())}</h2>")
        elif stripped.startswith("# "):
            flush_para(); flush_bullets()
            blocks.append(f"{indent}<h2>{_inline(stripped[2:].strip())}</h2>")
        elif _is_bullet(stripped):
            flush_para()
            bullets.append(stripped[2:].strip())
        else:
            flush_bullets()
            para.append(stripped)

    flush_para()
    flush_bullets()
    return "\n\n".join(blocks)


def month_year(dt) -> str:
    return f"{MONTHS[dt.month]} {dt.year}"


def meta_line(dt, tags) -> str:
    parts = [month_year(dt)] + list(tags or [])
    return " &middot; ".join(parts)


def article_filename(dt, slug: str) -> str:
    return f"{dt.strftime('%Y%m%d')}-{slug}.html"


def render_article_page(topic, body_markdown: str, dt) -> str:
    body_html = render_body_html(body_markdown)
    meta = meta_line(dt, topic.tags)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_escape(topic.title)} &ndash; VModal Blog</title>
  <link rel="stylesheet" href="../style.css" />
</head>
<body>
  <header>
    <a href="../index.html">V-Modal AI Blog</a>
  </header>

  <main>
    <a class="back-link" href="../index.html">&larr; Back to all articles</a>

    <div class="article-body">
      <h1>{_escape(topic.title)}</h1>
      <p style="color:#888; font-size:0.9rem; margin-bottom:1.5rem;">{meta}</p>

{body_html}
    </div>
  </main>

  <footer>
    &copy; {dt.year} VModal Blog
  </footer>
</body>
</html>
"""


def render_index_li(topic, dt, filename: str) -> str:
    meta = meta_line(dt, topic.tags)
    return (
        "      <li>\n"
        f"        <a href=\"articles/{filename}\">{_escape(topic.title)}</a>\n"
        f"        <div class=\"summary\">{_escape(topic.summary)}</div>\n"
        f"        <div class=\"meta\">{meta}</div>\n"
        "      </li>"
    )
