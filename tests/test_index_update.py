"""Inserting an article into index.html."""
import pytest

from publisher.index_update import insert_article, IndexFormatError

INDEX = """<html><body>
  <main>
    <ul class="article-list">
      <li>
        <a href="articles/old.html">Old</a>
      </li>
    </ul>
  </main>
</body></html>"""


def test_inserts_as_first_item():
    li = '      <li>\n        <a href="articles/new.html">New</a>\n      </li>'
    out = insert_article(INDEX, li, href="articles/new.html")
    new_pos = out.find("articles/new.html")
    old_pos = out.find("articles/old.html")
    assert new_pos != -1 and old_pos != -1
    assert new_pos < old_pos  # newest first


def test_idempotent_when_href_present():
    li = '      <li>\n        <a href="articles/old.html">Old</a>\n      </li>'
    out = insert_article(INDEX, li, href="articles/old.html")
    assert out == INDEX
    assert out.count("articles/old.html") == 1


def test_raises_when_list_marker_missing():
    with pytest.raises(IndexFormatError):
        insert_article("<html><body>no list here</body></html>", "<li/>")
