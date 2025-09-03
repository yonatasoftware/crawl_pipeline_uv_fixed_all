import argparse, asyncio
#from .models import CrawlRequest
# Replace with absolute import
from .models import CrawlRequest

from .adapters.crawl4ai_html import fetch_html as html_fetcher
from .adapters.aiohttp_binary import fetch_binary as binary_fetcher
from .adapters.links_basic import extract as extract_links
from .adapters.storage_selector import get_storage
from .adapters.transform_noop import transform as transform_noop
from .pipeline.crawl import run_crawl
from .config import Limits
from .adapters.simple_html_fetcher import SimpleHtmlFetcher
from .adapters.simple_binary_fetcher import SimpleBinaryFetcher



html_fetcher = SimpleHtmlFetcher()
binary_fetcher = SimpleBinaryFetcher()

class BasicLinkExtractor:
    def extract(self, base_url: str, html: bytes):
        return extract_links(base_url, html)

link_extractor = BasicLinkExtractor()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--max-files", type=int, default=100)
    ap.add_argument("--storage-root", default="./downloads", help="fs path or s3:// or gs://")
    args = ap.parse_args()
  #limits=Limits.crawl_pipeline.config.Limits(max_files=args.max_files)
    req = CrawlRequest(url=args.url, depth=args.depth, limits=Limits(max_files=args.max_files),
                       storage_root=args.storage_root)
    storage = get_storage(req.storage_root)

    results = asyncio.run(run_crawl(req, html_fetcher=html_fetcher, binary_fetcher=binary_fetcher,
                                    link_extractor=link_extractor, storage=storage, transformer=None))
    for r in results:
        print(r.status, r.content_type, r.url, "->", r.path)

if __name__ == "__main__":
    main()
