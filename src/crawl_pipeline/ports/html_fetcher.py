from typing import Protocol, Tuple
from ..config import Timeouts, RetryPolicy

class HtmlFetcher(Protocol):
    #async def fetch_html(self, url: str, *, timeouts: Timeouts, retry: RetryPolicy) -> Tuple[str, bytes]:
    async def fetch_html(self, url: str, timeouts: int = 30, retry: int = 3) -> Tuple[str, str]:
        """Return (content_type, html_bytes)."""
        ...
