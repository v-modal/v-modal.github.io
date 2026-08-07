"""End-to-end publish flow (offline, no network, injected clock)."""
import os
from datetime import datetime, timezone

from publisher.config import Config
from publisher.publish import publish

DT = datetime(2026, 8, 7, tzinfo=timezone.utc)

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<body>
  <main>
    <h2>List of Blog Articles</h2>
    <ul class="article-list">
      <li>
        <a href="articles/202601-physical-ai-search.html">The Physical AI Software Stack</a>
        <div class="summary">Existing.</div>
        <div class="meta">Jan 2026 &middot; AI &middot; Search</div>
      </li>
    </ul>
  </main>
</body>
</html>
"""


def _setup(tmp_path):
    articles = tmp_path / "articles"
    articles.mkdir()
    (articles / "202601-physical-ai-search.html").write_text("old", encoding="utf-8")
    index = tmp_path / "index.html"
    index.write_text(INDEX_TEMPLATE, encoding="utf-8")
    return Config(articles_dir=str(articles), index_path=str(index))


def test_dry_run_writes_nothing(tmp_path):
    cfg = _setup(tmp_path)
    cfg.dry_run = True
    before_index = (tmp_path / "index.html").read_text(encoding="utf-8")
    result = publish(cfg, now=DT)
    assert result["status"] == "dry-run"
    assert not os.path.exists(result["path"])
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == before_index
    assert result["page_html"].startswith("<!DOCTYPE html>")


def test_real_run_writes_article_and_updates_index(tmp_path):
    cfg = _setup(tmp_path)
    result = publish(cfg, now=DT)
    assert result["status"] == "published"
    # First run picks the first unused topic.
    assert result["topic"] == "multimodal-embeddings"
    assert result["filename"] == "20260807-multimodal-embeddings.html"
    # Article file written with the template.
    page = open(result["path"], encoding="utf-8").read()
    assert page.startswith("<!DOCTYPE html>")
    assert "Joint Embedding Spaces" in page
    # Index links the new article, newest first.
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    new_pos = index.find("20260807-multimodal-embeddings.html")
    old_pos = index.find("202601-physical-ai-search.html")
    assert new_pos != -1 and new_pos < old_pos


def test_second_run_same_day_is_idempotent(tmp_path):
    cfg = _setup(tmp_path)
    publish(cfg, now=DT)
    index_after_first = (tmp_path / "index.html").read_text(encoding="utf-8")
    result2 = publish(cfg, now=DT)
    assert result2["status"] == "exists"
    # No duplicate list entry.
    index_after_second = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert index_after_second == index_after_first
    assert index_after_second.count("20260807-multimodal-embeddings.html") == 1


def test_forced_topic_slug(tmp_path):
    cfg = _setup(tmp_path)
    cfg.topic_slug = "edge-inference"
    result = publish(cfg, now=DT)
    assert result["topic"] == "edge-inference"
    assert result["filename"] == "20260807-edge-inference.html"
