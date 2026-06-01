# Architecture

Sisifus Analytics is a local-first pipeline that turns an exported email inbox
into job-application analytics. It runs entirely on your machine: no cloud, no
LLM calls, no credentials required for the Google Takeout path.

## High-level flow

```
.mbox export ──import──► raw emails ──classify──► labelled emails ──aggregate──► outputs
   (Takeout)            (dicts)        (status,        (status +              JSON / CSV /
                                        confidence)     company)               Sankey HTML
```

Two ingestion paths feed the same downstream stages:

- **Offline (default):** `EmailImporter` parses a Google Takeout `.mbox` file.
- **Online (optional):** `EmailParser` fetches over IMAP using credentials from
  a local `.env`. Never required for the documented workflow.

## Package layout (`src/`)

| Module | Responsibility |
| --- | --- |
| `config.py` | Resolves project paths via `pathlib` relative to the repo root and creates `input/`/`output/`. Loads `.env`. All output paths (`ANALYTICS_JSON`, `ANALYTICS_CSV`, `SANKEY_HTML`) are defined here. |
| `email_importer.py` | `EmailImporter` - reads `.mbox` files (incl. recursive `auto_import`), decodes headers/bodies robustly, extracts text from HTML via BeautifulSoup. |
| `email_parser.py` | `EmailParser` - IMAP-over-SSL fetching of job-related mail. Network-bound; excluded from CI tests. |
| `email_storage.py` | `EmailStorage` - persists/loads emails as UTF-8 JSON under `input/`, with optional date filtering and metadata. |
| `classifier.py` | `EmailClassifier` - keyword/regex classification into `applied`, `confirmation`, `interview_N`, `offer`, `accepted`, `rejected`, `withdrew`, `no_reply`, `not_job_related`, plus company-name extraction. Pure, deterministic, no I/O. |
| `analytics.py` | `AnalyticsGenerator` - aggregates labelled emails into a summary, builds a Plotly Sankey diagram, and writes JSON/CSV/HTML outputs. |
| `main.py` | CLI entry point (`python -m src.main`) wiring fetch/load -> classify -> analyse -> save. |
| `import_emails.py` / `extract_emails.py` | Thin CLI wrappers around import and IMAP extraction. |

## Classification

`EmailClassifier` first decides whether an email is job-related (keyword and
sender-domain signals minus strong newsletter/promo exclusions), then scores it
against per-status regex pattern sets. Priority rules resolve conflicts
(rejection > offer/accepted > interview > applied). Confidence is derived from
the number of matching patterns, boosted when matches occur in the subject.

## Analytics & visualization

`AnalyticsGenerator.generate_summary()` produces a JSON-serialisable dict of
counts and a date range. `generate_sankey_diagram()` reconstructs each company's
journey (highest interview reached, final outcome) and consolidates outcomes
into `Rejected` / `Withdrew` / `Ghosted` / `Offer` nodes for a clean Sankey.

## Cross-platform design

- **Paths:** every filesystem location is a `pathlib.Path` resolved relative to
  the package (`Path(__file__).parent.parent`); no hardcoded `/tmp`, drive
  letters, or cwd-relative paths. Output directories are created on demand.
- **Encoding:** all `open()`/read/write calls pass `encoding="utf-8"`, so JSON
  and CSV outputs are identical regardless of the platform code page.
- **Console:** the CLI entry points guard `sys.stdout.reconfigure(encoding=
  "utf-8")` in a `try/except` so status glyphs render on Windows consoles and
  degrade gracefully where the stream cannot be reconfigured.

## Testing

The suite under `tests/` is hermetic and OS-agnostic:

- `test_classifier.py` - unit tests of the pure classifier.
- `test_analytics.py` - summary/statistics behaviour plus a pandas/pandera
  schema check on the classified-record shape.
- `test_e2e.py` - end-to-end runs over a synthetic `.mbox` written to
  `tmp_path`: import -> classify -> analyse -> write JSON/CSV/Sankey HTML, and an
  `EmailStorage` save/load round-trip. No live network; all paths are temporary.

`conftest.py` puts `src/` on `sys.path` and supplies shared fixtures.

## CI

`.github/workflows/ci.yml` runs three jobs with least-privilege
`permissions: contents: read`:

- **lint** - ruff check, ruff format check, mypy (Ubuntu, Python 3.12).
- **test** - matrix of `ubuntu-latest` / `macos-latest` / `windows-latest` x
  Python `3.11` / `3.12` / `3.13` (`fail-fast: false`), running pytest with
  coverage; coverage is uploaded once from Ubuntu/3.12.
- **build** - sdist + wheel via `python -m build`, validated with `twine check`.
