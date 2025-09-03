from __future__ import annotations
from typing import Tuple, AsyncIterator, Optional
import aiohttp
from ..config import Timeouts, RetryPolicy
from ..backoff import async_retry

async def _head(session: aiohttp.ClientSession, url: str, timeouts: Timeouts):
    async with session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=timeouts.total_s)) as r:
        return r

async def _get(session: aiohttp.ClientSession, url: str, headers: dict | None, timeouts: Timeouts):
    async with session.get(url, headers=headers or {}, allow_redirects=True,
                           timeout=aiohttp.ClientTimeout(total=timeouts.total_s)) as r:
        r.raise_for_status()
        async for chunk in r.content.iter_chunked(1024 * 64):
            if not chunk:
                continue
            yield chunk

async def fetch_binary(url: str, *, timeouts: Timeouts, retry: RetryPolicy
                      ) -> Tuple[str, AsyncIterator[bytes], Optional[int]]:
    async def _do():
        async with aiohttp.ClientSession() as session:
            hr = await _head(session, url, timeouts)
            ct = (hr.headers.get("content-type") or "").split(";")[0].strip().lower() or "application/octet-stream"
            clen = None
            try:
                clen = int(hr.headers.get("content-length", "")) if hr.headers.get("content-length") else None
            except Exception:
                clen = None
            accept_ranges = (hr.headers.get("accept-ranges","").lower() == "bytes")

            # multipart if large AND range supported
            if accept_ranges and clen and clen > 0 and clen >= 8 * 1024 * 1024:
                chunk = 4 * 1024 * 1024
                ranges = [(i, min(i+chunk-1, clen-1)) for i in range(0, clen, chunk)]
                # fetch parts sequentially to preserve order; could parallelize with merge
                async def gen():
                    for start, end in ranges:
                        headers = {"Range": f"bytes={start}-{end}"}
                        async for part in _get(session, url, headers, timeouts):
                            yield part
                return ct, gen(), clen
            else:
                async def gen():
                    async for part in _get(session, url, None, timeouts):
                        yield part
                return ct, gen(), clen

    return await async_retry(_do, attempts=retry.max_attempts, base=retry.backoff_base_s,
                             max_s=retry.backoff_max_s, jitter=retry.jitter_s)
