import asyncio
from prefect import flow, task
from ..models import CrawlRequest
from ..adapters.crawl4ai_html import fetch_html as html_fetcher
from ..adapters.aiohttp_binary import fetch_binary as binary_fetcher
from ..adapters.links_basic import extract as link_extractor
from ..adapters.storage_selector import get_storage
from ..pipeline.crawl import run_crawl

@task
async def _run(req: CrawlRequest, storage_root: str):
    storage = get_storage(storage_root)
    return await run_crawl(req, html_fetcher=html_fetcher, binary_fetcher=binary_fetcher,
                           link_extractor=link_extractor, storage=storage, transformer=None)

@flow(name="crawl-medium-flow")
def crawl_medium(url: str, depth: int = 2, max_files: int = 500, storage_root: str = "./downloads"):
    req = CrawlRequest(url=url, depth=depth)
    # override limits in a pure way (new dataclass)
    from ..config import Limits
    req = CrawlRequest(url=req.url, depth=req.depth, file_types=req.file_types, storage_root=req.storage_root,
                       same_domain_only=req.same_domain_only, under_path_only=req.under_path_only,
                       transform=req.transform, timeouts=req.timeouts, retry=req.retry,
                       limits=Limits(max_files=max_files, max_pages=req.limits.max_pages,
                                     max_total_bytes=req.limits.max_total_bytes,
                                     max_item_bytes=req.limits.max_item_bytes,
                                     max_concurrency_total=req.limits.max_concurrency_total,
                                     max_concurrency_html=req.limits.max_concurrency_html,
                                     max_concurrency_bin=req.limits.max_concurrency_bin,
                                     multipart_threshold=req.limits.multipart_threshold,
                                     multipart_chunk_size=req.limits.multipart_chunk_size))
    return asyncio.run(_run.fn(req, storage_root))

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--max-files", type=int, default=500)
    p.add_argument("--storage-root", default="./downloads")
    args = p.parse_args()
    out = crawl_medium(args.url, args.depth, args.max_files, args.storage_root)
    print(out)
