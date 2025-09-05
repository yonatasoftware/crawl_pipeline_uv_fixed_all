import asyncio
from urllib.parse import urljoin

async def crawl(
    url: str,
    depth: int,
    max_depth: int,
    saved: list,
    limits,
    html_fetcher,
    fetch_and_save_html,
    link_extractor,
    req,
    visited: set
):
    """
    Crawl a URL up to a given depth, saving HTML and following links.
    """

    # avoid revisiting same URL
    if url in visited:
        return
    visited.add(url)

    # stop if we've hit max file limit
    if len(saved) >= limits.max_files:
        return

    print(f"📌 Crawling: {url} (depth={depth})")

    # 1) fetch HTML (content + save)
    try:
        ct, html = await html_fetcher.fetch_html(url, timeouts=req.timeouts, retry=req.retry)
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return

    root_item = await fetch_and_save_html(url, html)
    if root_item:
        saved.append(root_item)

    if depth >= max_depth:
        return


    try:
        links = link_extractor.extract(url, html)
        if not links:
            print(f"⚠️ No links found with {html_fetcher.__class__.__name__}, retrying with Playwright...")
            from crawl_pipeline.ports.playwright_fetcher import PlaywrightHtmlFetcher
            alt_fetcher = PlaywrightHtmlFetcher()
            _, html = await alt_fetcher.fetch_html(url)
            links = link_extractor.extract(url, html)
    except Exception as e:
        print(f"⚠️ Failed to extract links from {url}: {e}")
        links = []

    print(f"🔗 Extracted {len(links)} links from {url}")


    # 3) normalize & recurse
    for link in links:
        full_url = urljoin(url, link)  # resolve relative links
        await crawl(
            full_url,
            depth + 1,
            max_depth,
            saved,
            limits,
            html_fetcher,
            fetch_and_save_html,
            link_extractor,
            req,
            visited,
        )


async def run_crawl(request, html_fetcher, fetch_and_save_html, link_extractor, limits):
    """
    Entry point for crawl pipeline.
    """
    saved = []
    visited = set()

    
    await crawl(
        request.url,
        depth=0,
        max_depth=request.depth,
        saved=saved,
        limits=limits,
        html_fetcher=html_fetcher,
        fetch_and_save_html=fetch_and_save_html,
        link_extractor=link_extractor,
        req=request,
        visited=visited,
    )
    return saved
