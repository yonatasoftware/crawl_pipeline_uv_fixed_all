import aiohttp
import asyncio, random
from crawl_pipeline.config import RetryPolicy, Timeouts

class SimpleHtmlFetcher:
    async def fetch_html(self, url: str, timeouts: Timeouts, retry: RetryPolicy):
        aio_timeout = aiohttp.ClientTimeout(
            total=timeouts.read_s,
            connect=timeouts.connect_s,
        )

        async with aiohttp.ClientSession(timeout=aio_timeout) as session:
            for attempt in range(retry.max_attempts):
                try:
                    async with session.get(url) as resp:
                        ct = resp.headers.get("content-type", "")
                        html = await resp.text()
                        return ct, html
                except Exception as e:
                    if attempt == retry.max_attempts - 1:
                        raise

                    # exponential backoff with jitter
                    sleep_time = min(
                        retry.backoff_base_s * (2 ** attempt),
                        retry.backoff_max_s
                    )
                    sleep_time += random.uniform(0, retry.jitter_s)
                    await asyncio.sleep(sleep_time)
