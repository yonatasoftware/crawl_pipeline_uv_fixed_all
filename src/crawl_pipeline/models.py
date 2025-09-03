from dataclasses import dataclass, field
from typing import Sequence, Optional, Literal, Any

from .config import Timeouts, RetryPolicy, Limits

DEFAULT_TYPES = ("html", "pdf", "docx", "pptx")

@dataclass(frozen=True)
class CrawlRequest:
    url: str
    depth: int = 1
    file_types: Sequence[str] = DEFAULT_TYPES
    storage_root: str = "./downloads"
    same_domain_only: bool = True
    under_path_only: bool = True
    transform: Optional[str] = None
    timeouts: Timeouts = field(default_factory=Timeouts)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    limits: Limits = field(default_factory=Limits)

@dataclass(frozen=True)
class SavedItem:
    url: str
    path: str
    content_type: str
    size: int
    sha256: str
    status: Literal["success", "skipped", "failed"] = "success"
    meta: dict[str, Any] = field(default_factory=dict)
