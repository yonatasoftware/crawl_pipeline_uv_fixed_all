from typing import Protocol, List

class LinkExtractor(Protocol):
    def extract(self, base_url: str, html: bytes) -> List[str]:
        ...
