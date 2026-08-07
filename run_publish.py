"""Entry point for the daily article publisher.

Reads configuration from the environment, publishes one article (or, in dry-run mode,
renders it without writing), logs a summary, and — when running in GitHub Actions —
exposes the result as step outputs so the workflow can open a pull request.
"""
import logging
import os
import sys

from publisher.config import load_config
from publisher.publish import publish

log = logging.getLogger("vmx_blog")


def _write_outputs(result):
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        return
    created = "true" if result.get("status") == "published" else "false"
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(f"created={created}\n")
        fh.write(f"slug={result.get('topic', '')}\n")
        fh.write(f"title={result.get('title', '')}\n")
        fh.write(f"filename={result.get('filename', '')}\n")
        fh.write(f"branch={result.get('branch', '')}\n")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = load_config()
    result = publish(config)
    status = result.get("status")
    log.info("status=%s topic=%s file=%s", status, result.get("topic"), result.get("filename"))
    if status == "dry-run":
        log.info("DRY RUN, would publish:\n%s", result.get("page_html", ""))
    _write_outputs(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
