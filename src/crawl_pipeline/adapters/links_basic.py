from __future__ import annotations
from html.parser import HTMLParser
from typing import List
from yarl import URL

class _HrefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":  # only <a href="...">
            for (k, v) in attrs:
                if k == "href" and v:
                    self.links.append(v)


def extract(base_url: str, html: bytes) -> List[str]:
    p = _HrefParser()
    try:
        p.feed(html.decode("utf-8", errors="ignore"))
    except Exception:
        return []

    base = URL(base_url)
    abs_links: list[str] = []

    for l in p.links:
        if l.startswith("#") or l.startswith(("mailto:", "javascript:", "tel:")):
            continue
        try:
            u = URL(l)
            if not u.is_absolute():
                u = base.join(u)
            if u.scheme in {"http", "https"}:
                abs_links.append(str(u))
        except Exception:
            continue

    return abs_links
