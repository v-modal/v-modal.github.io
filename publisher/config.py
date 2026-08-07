"""Runtime configuration for the article publisher.

Values come from environment variables. In Actions they are provided as repository
secrets; for local runs a .env file (gitignored) is loaded here if present. Nothing in
this module ever writes secrets to disk or logs them.
"""
import os
from dataclasses import dataclass


def load_dotenv(path=".env"):
    """Load KEY=VALUE lines from a .env file into os.environ (does not overwrite
    variables that are already set). Missing file is a no-op. No dependency needed."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


@dataclass
class Config:
    brightdata_api_key: str = ""
    serpapi_key: str = ""
    articles_dir: str = "articles"
    index_path: str = "index.html"
    # Optional: force a specific topic by slug instead of the automatic rotation.
    topic_slug: str = ""
    dry_run: bool = False

    @property
    def brightdata_enabled(self) -> bool:
        return bool(self.brightdata_api_key)

    @property
    def serpapi_enabled(self) -> bool:
        return bool(self.serpapi_key)


def _truthy(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def load_config(env=None) -> Config:
    """Build a Config from the environment (after loading .env for local runs)."""
    if env is None:
        load_dotenv()
        env = os.environ
    return Config(
        brightdata_api_key=env.get("BRIGHT_DATA_API_KEY", "").strip(),
        serpapi_key=env.get("SERP_API_KEY", "").strip(),
        articles_dir=(env.get("ARTICLES_DIR") or "articles").strip(),
        index_path=(env.get("INDEX_PATH") or "index.html").strip(),
        topic_slug=env.get("TOPIC_SLUG", "").strip(),
        dry_run=_truthy(env.get("DRY_RUN")),
    )
