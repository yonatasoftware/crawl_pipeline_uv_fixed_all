from __future__ import annotations
from yarl import URL
from typing import Callable
from ..ports.storage import Storage
from . import storage_fs

class _FsStorage:
    save_bytes = staticmethod(storage_fs.save_bytes)
    save_stream = staticmethod(storage_fs.save_stream)

def get_storage(storage_root: str) -> Storage:
    try:
        u = URL(storage_root)
        scheme = (u.scheme or "").lower()
    except Exception:
        scheme = ""
    if scheme in {"s3", "s3a", "s3n"}:
        from . import storage_s3
        class _S3:  # minimal adapter object matching Storage Protocol via staticmethods
            save_bytes = staticmethod(lambda **kw: storage_s3.save_bytes(root=storage_root, **kw))
            save_stream = staticmethod(lambda **kw: storage_s3.save_stream(root=storage_root, **kw))
        return _S3()  # type: ignore[return-value]
    if scheme in {"gs", "gcs"}:
        from . import storage_gcs
        class _GCS:
            save_bytes = staticmethod(lambda **kw: storage_gcs.save_bytes(root=storage_root, **kw))
            save_stream = staticmethod(lambda **kw: storage_gcs.save_stream(root=storage_root, **kw))
        return _GCS()  # type: ignore[return-value]
    return _FsStorage()  # type: ignore[return-value]
