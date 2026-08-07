"""Tie the pieces together: pick a topic, generate the body, render the files.

`publish()` is pure with respect to time and network (both are injectable) so it can
be exercised offline. It writes the new article and the updated index only on a real
run; a dry run returns the rendered output without touching disk.
"""
import os
from datetime import datetime, timezone

import requests

from . import content as content_mod
from . import render
from . import topics as topics_mod
from .index_update import insert_article


def _existing_article_files(articles_dir: str):
    if not os.path.isdir(articles_dir):
        return []
    return sorted(f for f in os.listdir(articles_dir) if f.endswith(".html"))


def used_slugs(files, topic_list):
    used = set()
    for f in files:
        for t in topic_list:
            if f.endswith(f"-{t.slug}.html"):
                used.add(t.slug)
    return used


def pick_topic(config, files):
    if config.topic_slug:
        t = topics_mod.get_topic(config.topic_slug)
        if t is None:
            raise ValueError(f"unknown TOPIC_SLUG: {config.topic_slug!r}")
        return t
    every = topics_mod.all_topics()
    return topics_mod.select_topic(used_slugs(files, every), rotation_index=len(files))


def publish(config, now=None, get=requests.get, post=requests.post) -> dict:
    dt = now or datetime.now(timezone.utc)
    files = _existing_article_files(config.articles_dir)

    # One article per day: an automatic run does nothing once today's article exists.
    # A manually forced topic (TOPIC_SLUG) is still allowed through.
    today_prefix = dt.strftime("%Y%m%d") + "-"
    todays = [f for f in files if f.startswith(today_prefix)]
    if todays and not config.topic_slug:
        return {"status": "exists", "topic": "", "title": "",
                "filename": todays[0],
                "path": os.path.join(config.articles_dir, todays[0])}

    topic = pick_topic(config, files)
    filename = render.article_filename(dt, topic.slug)
    article_path = os.path.join(config.articles_dir, filename)
    href = f"articles/{filename}"
    branch = f"article/{dt.strftime('%Y%m%d')}-{topic.slug}"

    if os.path.exists(article_path):
        return {"status": "exists", "topic": topic.slug, "title": topic.title,
                "filename": filename, "path": article_path, "branch": branch}

    body = content_mod.generate_article_body(topic, config, get=get, post=post)
    page_html = render.render_article_page(topic, body, dt)
    li_html = render.render_index_li(topic, dt, filename)

    with open(config.index_path, "r", encoding="utf-8") as fh:
        index_html = fh.read()
    new_index = insert_article(index_html, li_html, href=href)

    result = {"topic": topic.slug, "title": topic.title, "filename": filename,
              "path": article_path, "href": href, "branch": branch,
              "page_html": page_html, "index_html": new_index}

    if config.dry_run:
        result["status"] = "dry-run"
        return result

    with open(article_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page_html)
    with open(config.index_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_index)
    result["status"] = "published"
    return result
