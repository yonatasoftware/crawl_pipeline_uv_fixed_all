from playwright.async_api import async_playwright

class PlaywrightHtmlFetcher:
    async def fetch_html(self, url: str, **kwargs):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            html = await page.content()
            await browser.close()
        return "text/html", html.encode("utf-8")
