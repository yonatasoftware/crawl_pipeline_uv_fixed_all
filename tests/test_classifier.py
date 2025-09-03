from crawl_pipeline.classify import canonical_type

def test_canonical_from_header():
    assert canonical_type("text/html; charset=utf-8", "https://x") == "html"
    assert canonical_type("application/pdf", "https://x") == "pdf"

def test_canonical_from_ext():
    assert canonical_type(None, "https://x/a/b/c.PDF") == "pdf"
    assert canonical_type(None, "https://x/a/readme.htm") == "html"
