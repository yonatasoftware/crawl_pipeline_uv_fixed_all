from __future__ import annotations
import asyncio
from typing import AsyncIterator, Sequence, Set, List
from yarl import URL

from ..models import CrawlRequest, SavedItem
from ..config import Limits
from ..logging import log
from ..url_utils import normalize, same_scope, guard_ssrf
from ..classify import canonical_type
from ..ports.html_fetcher import HtmlFetcher
from ..ports.binary_fetcher import BinaryFetcher
from ..ports.link_extractor import LinkExtractor
from ..ports.storage import Storage
from ..ports.transformer import Transformer
from ..adapters.simple_html_fetcher import SimpleHtmlFetcher as HtmlFetcher



async def _stream_to_storage(storage: Storage, *, chunks: AsyncIterator[bytes], url: str,
                             typ: str, root: str, size_hint: int | None) -> SavedItem:
    path = await storage.save_stream(chunks=chunks, url=url, canonical_type=typ, root=root, size_hint=size_hint)
    # we don't know size/hash unless storage adds metadata; treat as unknown here
    return SavedItem(url=url, path=path, content_type=typ, size=-1, sha256="unknown")

async def run_crawl(req: CrawlRequest, *, html_fetcher: HtmlFetcher, binary_fetcher: BinaryFetcher,
                    link_extractor: LinkExtractor, storage: Storage, transformer: Transformer | None = None
                   ) -> Sequence[SavedItem]:
    limits: Limits = req.limits
    # sanity on root
    root = normalize(req.url)
    guard_ssrf(URL(root).host or "localhost")
    log("crawl_start", root=root, depth=req.depth, max_files=limits.max_files)

    saved: List[SavedItem] = []
    seen: Set[str] = set([root])
    q: List[tuple[str,int]] = [(root, 0)]
    total_bytes = 0

    sem_html = asyncio.Semaphore(limits.max_concurrency_html)
    sem_bin = asyncio.Semaphore(limits.max_concurrency_bin)

    async def fetch_and_save_html(u: str) -> SavedItem | None:
        nonlocal total_bytes
        async with sem_html:
            ct, html = await html_fetcher.fetch_html(url=u, timeouts=req.timeouts, retry=req.retry)
            if html is None:
                print(f"Failed to fetch {u}")
                return None
        typ = canonical_type(ct, u) or "html"
        # enforce per-item size
        if len(html) > limits.max_item_bytes:
            log("skip_too_large_html", url=u, size=len(html))
            return None
        # save bytes
        path = storage.save_bytes(content=html, url=u, canonical_type=typ, root=req.storage_root)
        total_bytes += len(html)
        return SavedItem(url=u, path=path, content_type=typ, size=len(html), sha256="unknown")

    async def fetch_and_save_binary(u: str) -> SavedItem | None:
        nonlocal total_bytes
        async with sem_bin:
            ct, chunks, clen = await binary_fetcher.fetch_binary(u, timeouts=req.timeouts, retry=req.retry)
        typ = canonical_type(ct, u)
        if typ is None or typ not in req.file_types:
            return None
        if clen is not None and clen > limits.max_item_bytes:
            log("skip_too_large_binary", url=u, size=clen)
            return None
        item = await _stream_to_storage(storage, chunks=chunks, url=u, typ=typ, root=req.storage_root, size_hint=clen)
        total_bytes += max(0, 0 if clen is None else clen)
        return item

    # 1) fetch root HTML
    root_item = await fetch_and_save_html(root)
    if root_item:
        saved.append(root_item)
    if len(saved) >= limits.max_files:
        return saved

    # 2) extract links
    links = link_extractor.extract(root, root_item.path.encode("utf-8") if root_item else b"")
    # NOTE: above uses saved HTML path; a real impl should pass html bytes from html_fetcher.
    # To avoid re-fetch, we can log and continue with empty if no html saved.
    # For now assume we fetched root html.

    # Let's correct this: re-fetch html bytes for extraction if needed
    if not links:
        ct, html = await html_fetcher.fetch_html(root, timeouts=req.timeouts, retry=req.retry)
        links = link_extractor.extract(root, html)

    # 3) BFS by depth with filters
    def in_scope(u: str) -> bool:
        try:
            s = normalize(u)
            return same_scope(root, s, same_domain=req.same_domain_only, under_path=req.under_path_only)
        except Exception:
            return False

    frontier = [(normalize(u), 1) for u in links if in_scope(u)]
    # dedupe
    tmp = []
    for u,d in frontier:
        if u not in seen:
            tmp.append((u,d)); seen.add(u)
    frontier = tmp

    while frontier:
        if len(saved) >= limits.max_files or total_bytes >= limits.max_total_bytes:
            log("caps_reached", files=len(saved), total_bytes=total_bytes)
            break
        u, depth = frontier.pop(0)
        if depth > req.depth:
            continue
        guard_ssrf(URL(u).host or "localhost")

        # Decide likely type from URL
        guess = canonical_type(None, u)
        if guess == "html":
            item = await fetch_and_save_html(u)
            if item:
                saved.append(item)
                if depth < req.depth:
                    # Extract links to go deeper (fetch bytes just once here)
                    ct, html = await html_fetcher.fetch_html(u, timeouts=req.timeouts, retry=req.retry)
                    sublinks = link_extractor.extract(u, html)
                    for su in sublinks:
                        try:
                            s = normalize(su)
                        except Exception:
                            continue
                        if not same_scope(root, s, same_domain=req.same_domain_only, under_path=req.under_path_only):
                            continue
                        if s not in seen:
                            frontier.append((s, depth+1))
                            seen.add(s)
        else:
            item = await fetch_and_save_binary(u)
            if item:
                saved.append(item)

    # Optional lazy transform
    if req.transform:
        out: List[SavedItem] = []
        for it in saved:
            # transformer may be None
            out_path = it.path
            # In this baseline, keep noop to avoid surprises; real transform plugged later
            out.append(it if out_path == it.path else SavedItem(url=it.url, path=out_path,
                                                                content_type=it.content_type,
                                                                size=it.size, sha256=it.sha256,
                                                                status=it.status, meta=it.meta))
        saved = out

    log("crawl_done", files=len(saved))
    return saved
