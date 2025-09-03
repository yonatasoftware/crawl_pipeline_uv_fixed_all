from __future__ import annotations
from typing import Tuple
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from ..config import Timeouts, RetryPolicy
from ..backoff import async_retry

async def fetch_html(url: str, *, timeouts: Timeouts, retry: RetryPolicy) -> Tuple[str, bytes]:
    async def _do():
        async with AsyncWebCrawler() as crawler:
            cfg = CrawlerRunConfig()  # rely on library defaults
            r = await crawler.arun(url, config=cfg)
            html = getattr(r, "html", "") or ""
            ct = "text/html"
            return ct, html.encode("utf-8", errors="ignore")
    return await async_retry(_do, attempts=retry.max_attempts, base=retry.backoff_base_s,
                             max_s=retry.backoff_max_s, jitter=retry.jitter_s)
