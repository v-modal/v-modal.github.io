"""Content generation: provider preference and safe fallback."""
from publisher import content as content_mod
from publisher import topics as topics_mod
from publisher.config import Config

TOPIC = topics_mod.get_topic("multimodal-embeddings")


class FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_prefers_brightdata_when_configured():
    cfg = Config(brightdata_api_key="bd", serpapi_key="serp")

    def fake_post(url, **kwargs):
        return FakeResp([{"answer_text": "bright data answer"}])

    def fake_get(url, **kwargs):
        raise AssertionError("serpapi should not be called when brightdata answers")

    body = content_mod.generate_article_body(TOPIC, cfg, get=fake_get, post=fake_post)
    assert body == "bright data answer"


def test_falls_back_to_serpapi_when_brightdata_empty():
    cfg = Config(brightdata_api_key="bd", serpapi_key="serp")

    def fake_post(url, **kwargs):
        return FakeResp([{"unrelated": "no answer here"}])

    def fake_get(url, **kwargs):
        payload = {"ai_overview": {"text_blocks": [{"snippet": "serpapi answer"}]}}
        return FakeResp(payload)

    body = content_mod.generate_article_body(TOPIC, cfg, get=fake_get, post=fake_post)
    assert body == "serpapi answer"


def test_falls_back_to_topic_body_when_no_provider():
    cfg = Config()  # no keys
    body = content_mod.generate_article_body(TOPIC, cfg)
    assert body == TOPIC.fallback_body()
    assert "## Why a shared space" in body


def test_provider_error_does_not_raise():
    cfg = Config(brightdata_api_key="bd", serpapi_key="serp")

    def boom(url, **kwargs):
        raise RuntimeError("network down")

    body = content_mod.generate_article_body(TOPIC, cfg, get=boom, post=boom)
    assert body == TOPIC.fallback_body()
