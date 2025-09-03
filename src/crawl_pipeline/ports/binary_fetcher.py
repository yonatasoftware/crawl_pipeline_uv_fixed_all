from typing import Protocol, AsyncIterator, Tuple, Optional
from ..config import Timeouts, RetryPolicy

class BinaryFetcher(Protocol):
    #async def fetch_binary(self, url: str, *, timeouts: Timeouts, retry: RetryPolicy
                          # ) -> Tuple[str, AsyncIterator[bytes], Optional[int]]:
        
    async def fetch_binary(self, url: str, timeouts: int = 30, retry: int = 3) -> bytes:
        """Return (content_type, async_chunk_iter, content_length_or_None)."""
        ...
