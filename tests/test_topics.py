"""Topic catalogue and rotation."""
from publisher import topics as topics_mod


def test_slugs_are_unique_and_nonempty():
    slugs = [t.slug for t in topics_mod.all_topics()]
    assert all(slugs)
    assert len(slugs) == len(set(slugs))


def test_every_topic_has_title_tags_and_prompt():
    for t in topics_mod.all_topics():
        assert t.title.strip()
        assert t.tags
        assert t.prompt.strip()
        assert t.summary.strip()


def test_fallback_body_is_complete_markdown():
    t = topics_mod.get_topic("multimodal-embeddings")
    body = t.fallback_body()
    assert body.startswith(t.intro.strip()[:20])
    # Every section heading appears as a markdown h2.
    for heading, _ in t.sections:
        assert f"## {heading}" in body


def test_select_prefers_first_unused_topic():
    first = topics_mod.all_topics()[0]
    chosen = topics_mod.select_topic(used_slugs=set(), rotation_index=0)
    assert chosen.slug == first.slug


def test_select_skips_used_topics():
    all_t = topics_mod.all_topics()
    used = {all_t[0].slug, all_t[1].slug}
    chosen = topics_mod.select_topic(used_slugs=used, rotation_index=0)
    assert chosen.slug == all_t[2].slug


def test_select_rotates_when_all_used():
    all_t = topics_mod.all_topics()
    used = {t.slug for t in all_t}
    chosen = topics_mod.select_topic(used_slugs=used, rotation_index=len(all_t) + 2)
    assert chosen.slug == all_t[2].slug


def test_get_topic_unknown_returns_none():
    assert topics_mod.get_topic("does-not-exist") is None
