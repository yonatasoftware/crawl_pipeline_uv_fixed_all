import argparse, asyncio
from crawl_pipeline.models import CrawlRequest
from crawl_pipeline.adapters.simple_html_fetcher import SimpleHtmlFetcher
from crawl_pipeline.adapters.links_basic import extract as extract_links
from crawl_pipeline.adapters.storage_selector import get_storage
from crawl_pipeline.pipeline.crawl import run_crawl
from crawl_pipeline.config import Limits


class BasicLinkExtractor:
    def extract(self, base_url: str, html: bytes):
        return extract_links(base_url, html)


async def fetch_and_save_html(url: str, html: bytes, storage, storage_root: str):
    """Save given HTML bytes to storage."""
    if not html:
        return None

    # Save using storage_fs.save_bytes API
    saved_path = storage.save_bytes(
        content=html,
        url=url,
        canonical_type="html",
        root=storage_root
    )

    print(f"✅ Saved {url} -> {saved_path}")

    return {
        "url": url,
        "status": 200,
        "content_type": "text/html",
        "path": saved_path,
    }








def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--max-files", type=int, default=100)
    ap.add_argument("--storage-root", default="./downloads", help="fs path or s3:// or gs://")
    args = ap.parse_args()
# Creates a CrawlRequest with limits.
    req = CrawlRequest(
        url=args.url,
        depth=args.depth,
        limits=Limits(max_files=args.max_files),
        storage_root=args.storage_root,
    )

    storage = get_storage(req.storage_root)
    link_extractor = BasicLinkExtractor()
    html_fetcher = SimpleHtmlFetcher()

    results = asyncio.run(
    run_crawl(
        req,
        html_fetcher=html_fetcher,
        fetch_and_save_html=lambda u, h: fetch_and_save_html(u, h, storage, req.storage_root),
        link_extractor=link_extractor,
        limits=req.limits,
    )
)


    for r in results:
        print(r["status"], r["content_type"], r["url"], "->", r["path"])


if __name__ == "__main__":
    main()
