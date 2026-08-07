"""HTML rendering matches the site template."""
from datetime import datetime, timezone

from publisher import render
from publisher import topics as topics_mod

DT = datetime(2026, 8, 7, tzinfo=timezone.utc)


def test_body_html_headings_paragraphs_and_lists():
    md = "Intro paragraph.\n\n## A Section\n\nSome text.\n\n- one\n- two\n\n### Sub\n\nMore."
    html = render.render_body_html(md)
    assert "<p>Intro paragraph.</p>" in html
    assert "<h2>A Section</h2>" in html
    assert "<h3>Sub</h3>" in html
    assert "<ul>" in html and "<li>one</li>" in html and "<li>two</li>" in html


def test_body_html_inline_markup_and_escaping():
    md = "Use **bold**, *em*, and `code` with a < b & c."
    html = render.render_body_html(md)
    assert "<strong>bold</strong>" in html
    assert "<em>em</em>" in html
    assert "<code>code</code>" in html
    assert "&lt; b &amp; c" in html
    assert "< b & c" not in html


def test_filename_uses_yyyymmdd_and_slug():
    assert render.article_filename(DT, "edge-inference") == "20260807-edge-inference.html"


def test_meta_line_month_and_tags():
    assert render.meta_line(DT, ["AI", "Search"]) == "August 2026 &middot; AI &middot; Search"


def test_article_page_has_template_scaffold():
    topic = topics_mod.get_topic("edge-inference")
    page = render.render_article_page(topic, "## Local compute\n\nBody.", DT)
    assert page.startswith("<!DOCTYPE html>")
    assert '<link rel="stylesheet" href="../style.css" />' in page
    assert '<a href="../index.html">V-Modal AI Blog</a>' in page
    assert '<a class="back-link" href="../index.html">' in page
    assert f"<h1>{topic.title}</h1>" in page
    assert "August 2026 &middot; AI &middot; Edge" in page
    assert "&copy; 2026 VModal Blog" in page
    assert "<h2>Local compute</h2>" in page


def test_index_li_links_and_summary():
    topic = topics_mod.get_topic("ann-indexing")
    li = render.render_index_li(topic, DT, "20260807-ann-indexing.html")
    assert '<a href="articles/20260807-ann-indexing.html">' in li
    assert topic.title in li
    assert f'<div class="summary">{topic.summary}</div>' in li
    assert '<div class="meta">August 2026 &middot; AI &middot; Search</div>' in li
