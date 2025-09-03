from typing import Protocol, AsyncIterator

class Storage(Protocol):
    def save_bytes(self, *, content: bytes, url: str, canonical_type: str, root: str
                  ) -> str: ...
    async def save_stream(self, *, chunks: AsyncIterator[bytes], url: str, canonical_type: str,
                          root: str, size_hint: int | None = None) -> str: ...
