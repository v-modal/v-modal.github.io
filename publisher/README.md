# Daily article publisher

A scheduled GitHub Action that adds a new article to the blog each day. It picks a
topic, generates the article text, renders it into the site's HTML template, writes it
into `articles/`, links it from `index.html`, and opens a pull request with the change
for review. Nothing goes live until that pull request is merged.

## How it works

1. `run_publish.py` selects a topic from `publisher/topics.py`. It prefers a topic that
   has not been published yet, then rotates through the list, so articles stay varied.
2. It generates the body text, preferring Bright Data's Google AI Mode, falling back to
   SerpApi's Google AI Overview, and finally to the topic's own self-contained body, so
   a well-formed article is produced even before any key is configured.
3. It renders a standalone page under `articles/YYYYMMDD-<slug>.html` using the same
   template as the existing articles and adds a list item to the top of `index.html`.
4. The workflow commits the change on a new branch and opens a pull request. A run is
   idempotent per day: if today's article already exists, it does nothing.

## Configuration

Set these as repository secrets (**Settings → Secrets and variables → Actions**).
Both are optional; with neither set, the publisher uses each topic's built-in body.

| Secret | Purpose |
| --- | --- |
| `BRIGHT_DATA_API_KEY` | Bright Data Google AI Mode content (preferred) |
| `SERP_API_KEY` | SerpApi Google AI Overview content (fallback) |

For the workflow to open pull requests, **Settings → Actions → General → Workflow
permissions** must allow GitHub Actions to create and approve pull requests.

## Running it manually

From the **Actions** tab, pick **publish-article** and **Run workflow**. Tick the
dry-run box to render and log an article without opening a pull request, or set a topic
slug to force a specific topic.

From the command line:

```bash
gh workflow run publish-article.yml                       # real run, opens a PR
gh workflow run publish-article.yml -f dry_run=true       # render and log only
gh workflow run publish-article.yml -f topic_slug=edge-inference
```

## Running locally

```bash
pip install -r requirements-dev.txt
bash test.sh                 # offline tests
DRY_RUN=1 python run_publish.py   # render an article and log it, write nothing
```

## Adding or editing topics

Topics live in `publisher/topics.py`. Each has a stable slug, a title, tags, a one-line
summary, the search prompt sent to the AI source, and a self-contained fallback body.
Add an entry to the `TOPICS` list to expand the rotation.
