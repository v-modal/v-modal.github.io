"""Daily article publisher for the V-Modal AI Blog.

Picks a topic, generates the article text from Google's AI answer (Bright Data's
Google AI Mode, with SerpApi's Google AI Overview as a fallback, and a self-contained
fallback when neither is configured), renders it into the site's HTML template, writes
it into `articles/`, and links it from `index.html`.
"""
