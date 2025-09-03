from dataclasses import dataclass

@dataclass(frozen=True)
class Timeouts:
    connect_s: float = 10.0
    read_s: float = 60.0
    total_s: float = 90.0

@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    backoff_base_s: float = 0.5
    backoff_max_s: float = 8.0
    jitter_s: float = 0.2

@dataclass(frozen=True)
class Limits:
    max_files: int = 100
    max_pages: int = 500
    max_total_bytes: int = 200 * 1024 * 1024  # 200 MB budget
    max_item_bytes: int = 50 * 1024 * 1024    # 50 MB per file
    max_concurrency_total: int = 16
    max_concurrency_html: int = 8
    max_concurrency_bin: int = 8
    multipart_threshold: int = 8 * 1024 * 1024  # 8 MB
    multipart_chunk_size: int = 4 * 1024 * 1024 # 4 MB
