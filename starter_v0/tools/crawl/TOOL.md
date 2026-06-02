---
name: crawl
track: core
kind: live_api
provider: Firecrawl
requires_env: [FIRECRAWL_API_KEY]
inputs: [url, limit, max_chars_per_page]
outputs: [items]
side_effect: false
---
# crawl

Crawls multiple pages of a website starting from the given URL. Use when the user wants to read an entire site or section (e.g. all posts under a blog path), not just a single page. For a single URL use `fetch` instead.
