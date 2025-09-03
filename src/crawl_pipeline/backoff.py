import asyncio, random

async def async_retry(fn, *, attempts: int, base: float, max_s: float, jitter: float):
    last_exc = None
    for i in range(attempts):
        try:
            return await fn()
        except Exception as e:
            last_exc = e
            if i == attempts - 1:
                break
            # exponential backoff with jitter
            delay = min(max_s, base * (2 ** i)) + random.random() * jitter
            await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]
