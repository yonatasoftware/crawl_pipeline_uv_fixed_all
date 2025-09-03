import os, pathlib, asyncio
from crawl_pipeline.adapters.storage_fs import save_bytes, save_stream

def test_save_bytes(tmp_path):
    p = save_bytes(content=b"hello", url="https://example.com/a", canonical_type="html", root=str(tmp_path))
    assert pathlib.Path(p).exists()

async def _gen():
    for i in range(10):
        yield b"x"*1024

def test_save_stream(tmp_path):
    p = asyncio.get_event_loop().run_until_complete(
        save_stream(chunks=_gen(), url="https://example.com/a", canonical_type="pdf", root=str(tmp_path)))
    assert pathlib.Path(p).exists()
