"""Insert a new article's list item into index.html.

The homepage lists articles inside `<ul class="article-list">`. A new article is
added as the first item so the newest is shown at the top, leaving the rest of the
page untouched.
"""

LIST_OPEN = '<ul class="article-list">'


class IndexFormatError(ValueError):
    """Raised when index.html does not contain the expected article list."""


def insert_article(index_html: str, li_html: str, href: str = "") -> str:
    """Return index_html with li_html inserted as the first list item.

    If `href` is given and already present in the page, the html is returned
    unchanged (idempotent — a re-run does not duplicate the entry)."""
    if href and f'"{href}"' in index_html:
        return index_html
    pos = index_html.find(LIST_OPEN)
    if pos == -1:
        raise IndexFormatError(f"could not find {LIST_OPEN!r} in index.html")
    # Insert right after the end of the line that opens the list.
    line_end = index_html.find("\n", pos)
    if line_end == -1:
        raise IndexFormatError("malformed article list in index.html")
    insert_at = line_end + 1
    return index_html[:insert_at] + li_html + "\n" + index_html[insert_at:]
