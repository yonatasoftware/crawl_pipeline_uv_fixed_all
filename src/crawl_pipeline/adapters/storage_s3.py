from __future__ import annotations
import io, hashlib, tempfile
from typing import AsyncIterator
from yarl import URL

_EXT = { "html": ".html", "pdf": ".pdf", "docx": ".docx", "pptx": ".pptx" }

def _parse_root(root: str) -> tuple[str,str]:
    u = URL(root)
    return (u.host or "", u.path.lstrip("/"))

def _key(prefix: str, url: str, sha: str, canonical_type: str) -> str:
    from yarl import URL as YURL
    try:
        u = YURL(url)
        host = u.host or "unknown-host"
        parts = [p for p in u.path.split("/") if p]
        sub = "/".join(parts[:2])
    except Exception:
        host = "unknown-host"
        sub = ""
    ext = _EXT.get(canonical_type, "")
    key = "/".join([p for p in [prefix.rstrip('/'), host, sub] if p])
    return f"{key}/{sha[:16]}{ext}" if key else f"{sha[:16]}{ext}"

def save_bytes(*, content: bytes, url: str, canonical_type: str, root: str) -> str:
    import boto3  # lazy
    bucket, prefix = _parse_root(root)
    sha = hashlib.sha256(content).hexdigest()
    key = _key(prefix, url, sha, canonical_type)
    mime = {
        "html":"text/html; charset=utf-8",
        "pdf":"application/pdf",
        "docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx":"application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }.get(canonical_type, "application/octet-stream")
    boto3.client("s3").put_object(Bucket=bucket, Key=key, Body=content, ContentType=mime)
    return f"s3://{bucket}/{key}"

async def save_stream(*, chunks: AsyncIterator[bytes], url: str, canonical_type: str, root: str,
                      size_hint: int | None = None) -> str:
    import boto3
    bucket, prefix = _parse_root(root)
    h = hashlib.sha256()
    tmp = tempfile.SpooledTemporaryFile(max_size=64*1024*1024)  # spill to disk if big
    total = 0
    async for ch in chunks:
        tmp.write(ch); h.update(ch); total += len(ch)
    tmp.seek(0)
    sha = h.hexdigest()
    key = _key(prefix, url, sha, canonical_type)
    mime = {
        "html":"text/html; charset=utf-8",
        "pdf":"application/pdf",
        "docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx":"application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }.get(canonical_type, "application/octet-stream")
    boto3.client("s3").upload_fileobj(tmp, bucket, key, ExtraArgs={"ContentType": mime})
    tmp.close()
    return f"s3://{bucket}/{key}"
