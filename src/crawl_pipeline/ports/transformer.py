from typing import Protocol

class Transformer(Protocol):
    def transform(self, file_path: str, target: str) -> str: ...
