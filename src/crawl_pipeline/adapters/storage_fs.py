from __future__ import annotations
import os, hashlib, tempfile
from pathlib import Path
from typing import AsyncIterator
from yarl import URL

from ..ports.storage import Storage

_EXT = { "html": ".html", "pdf": ".pdf", "docx": ".docx", "pptx": ".pptx" }

def _layout(root: str, url: str, sha: str, canonical_type: str) -> Path:
    try:
        u = URL(url)
        host = u.host or "unknown-host"
        parts = [p for p in u.path.split("/") if p]
        sub = parts[:2]
    except Exception:
        host = "unknown-host"
        sub = []
    base = Path(root) / host
    for s in sub:
        base = base / s
    base.mkdir(parents=True, exist_ok=True)
    ext = _EXT.get(canonical_type, "")
    return base / f"{sha[:16]}{ext}"

def save_bytes(*, content: bytes | str, url: str, canonical_type: str, root: str) -> str:
    # ensure content is always bytes
    if isinstance(content, str):
        content = content.encode("utf-8")

    sha = hashlib.sha256(content).hexdigest()
    path = _layout(root, url, sha, canonical_type)
    tmp = str(path) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return str(path.resolve())


async def save_stream(*, chunks: AsyncIterator[bytes], url: str, canonical_type: str, root: str,
                      size_hint: int | None = None) -> str:
    h = hashlib.sha256()
    # write to temp, then move to content-addressed name
    base_dir = Path(root) / (URL(url).host or "unknown-host")
    base_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=base_dir) as f:
        tmp_path = Path(f.name)
        total = 0
        async for ch in chunks:
            f.write(ch)
            h.update(ch)
            total += len(ch)
        f.flush()
        os.fsync(f.fileno())
    sha = h.hexdigest()
    final = _layout(root, url, sha, canonical_type)
    os.replace(tmp_path, final)
    return str(final.resolve())
