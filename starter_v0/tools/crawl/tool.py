from __future__ import annotations

import os
import time
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def crawl_site(url: str = "", limit: int = 5, max_chars_per_page: int = 2000) -> dict[str, Any]:
    try:
        key = os.getenv("FIRECRAWL_API_KEY")
        if not key:
            raise RuntimeError("Missing FIRECRAWL_API_KEY env var")

        headers = {"Authorization": f"Bearer {key}"}

        response = requests.post(
            "https://api.firecrawl.dev/v1/crawl",
            json={"url": url, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}},
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        job_id = response.json().get("id")
        if not job_id:
            raise RuntimeError("No job ID returned from Firecrawl")

        # Poll until completed (max 90 s)
        deadline = time.time() + 90
        while time.time() < deadline:
            poll = requests.get(
                f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                headers=headers,
                timeout=TIMEOUT,
            )
            poll.raise_for_status()
            data = poll.json()
            if data.get("status") == "completed":
                items = []
                for page in (data.get("data") or [])[:limit]:
                    meta = page.get("metadata") or {}
                    page_url = meta.get("sourceURL") or page.get("url") or url
                    items.append({
                        "title": meta.get("title") or page_url,
                        "url": page_url,
                        "source": domain(page_url),
                        "summary": (page.get("markdown") or "")[:max_chars_per_page],
                    })
                return {"tool": "crawl", "url": url, "items": items}
            time.sleep(3)

        raise TimeoutError("Crawl job did not complete within 90 s")

    except Exception as exc:
        return err("crawl", exc)
