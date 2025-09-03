from crawl_pipeline.url_utils import normalize, same_scope

def test_normalize_scheme_port():
    assert normalize("https://EXAMPLE.com:443/a#frag") == "https://example.com/a"
    assert normalize("http://example.com:80/") == "http://example.com/"

def test_same_scope():
    root = "https://example.com/docs/"
    assert same_scope(root, "https://example.com/docs/page.html", same_domain=True, under_path=True)
    assert not same_scope(root, "https://example.com/other", same_domain=True, under_path=True)
