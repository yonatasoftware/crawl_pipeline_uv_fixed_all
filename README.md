# crawl-pipeline (uv-ready)

Functional, hexagonal crawler pipeline layered on **Crawl4AI (Playwright)**.
- **Small (<1000)**: `crawl-small` CLI (inline async).
- **Medium (100–10k)**: use Prefect flow (or your serverless shim) — same ports.
- **No factories**: ports are Protocols; everything is injected; all code is functional.

## Install & run (small)
```bash
uv venv
uv pip install -e .
uv run python -m crawl4ai setup
uv run crawl-small https://example.com --max-files 50 --depth 2
```

## Storage
- Default: local FS `./downloads`
- Cloud: set `--storage-root s3://bucket/prefix` or `--storage-root gs://bucket/prefix`
```bash
uv pip install -e ".[cloud]"
```

## Guarantees
- **Retries**: exponential backoff w/ jitter on idempotent GETs (429/5xx, timeouts).
- **Timeouts**: connect/read/total per stage.
- **Limits**: max files/pages/total bytes & per-item size; concurrency budgets.
- **Binary**: streamed save; range-based multipart when server supports `Accept-Ranges`.
- **Security**: scheme allowlist (http/https), SSRF guards (no private/link-local), path hardening.
- **Observability**: JSON logs, counters.

## CLI
```bash
uv run crawl-small https://example.com --max-files 100 --depth 2 --storage-root ./downloads
```

## Tests
```bash
uv pip install -e ".[dev]"
pytest -m "not integration"
```

## Layout
```
src/crawl_pipeline/
  config.py            # Timeouts, RetryPolicy, Limits
  url_utils.py         # normalization, scope, SSRF guards
  classify.py          # canonical type detection
  logging.py           # JSON logger
  pipeline/crawl.py    # pure composition of ports
  ports/               # HtmlFetcher, BinaryFetcher, LinkExtractor, Storage, Transformer
  adapters/            # crawl4ai_html, aiohttp_binary, links_basic, storage_fs/s3/gcs, transform_noop
  cli.py               # crawl-small entrypoint
orchestration/prefect_flow.py  # optional (not wired to CLI)
```

## Medium
Use the Prefect flow in `src/crawl_pipeline/orchestration/prefect_flow.py`. Same contracts.
