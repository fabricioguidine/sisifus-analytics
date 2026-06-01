"""End-to-end pipeline tests.

These drive the *real* entrypoints - mbox import, keyword classification,
analytics aggregation and on-disk output generation - against synthetic data
written to ``tmp_path``. No network, no fixed paths, so the suite behaves
identically on Linux, macOS and Windows.
"""

from __future__ import annotations

import csv
import json
from email.message import EmailMessage
from mailbox import mbox
from pathlib import Path

import pytest

from src.analytics import AnalyticsGenerator
from src.classifier import EmailClassifier
from src.email_importer import EmailImporter
from src.email_storage import EmailStorage


def _make_message(subject: str, sender: str, body: str, date: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["Date"] = date
    msg.set_content(body)
    return msg


@pytest.fixture
def synthetic_mbox(tmp_path: Path) -> Path:
    """Write a small, deterministic .mbox mirroring a Google Takeout export."""
    path = tmp_path / "inbox.mbox"
    box = mbox(str(path))
    box.lock()
    try:
        box.add(
            _make_message(
                "Application submitted",
                "Careers Team <careers@alpha.com>",
                "Thank you for your application to the Engineer position.",
                "Mon, 06 Jan 2025 09:00:00 +0000",
            )
        )
        box.add(
            _make_message(
                "First Interview Invitation",
                "HR <hr@bravo.io>",
                "We would like to invite you for a phone screen interview.",
                "Wed, 08 Jan 2025 10:00:00 +0000",
            )
        )
        box.add(
            _make_message(
                "We are pleased to offer you the position",
                "Manager <manager@charlie.dev>",
                "We are pleased to offer you the job. Job offer details attached.",
                "Fri, 10 Jan 2025 11:00:00 +0000",
            )
        )
        box.add(
            _make_message(
                "Black Friday Sale",
                "Promotions <promo@store.com>",
                "50% off everything. Unsubscribe from this newsletter anytime.",
                "Sat, 11 Jan 2025 12:00:00 +0000",
            )
        )
        box.flush()
    finally:
        box.unlock()
        box.close()
    return path


def test_importer_reads_synthetic_mbox(synthetic_mbox: Path) -> None:
    importer = EmailImporter()
    emails = importer.import_from_mbox(synthetic_mbox)

    assert len(emails) == 4
    subjects = {e["subject"] for e in emails}
    assert "Application submitted" in subjects
    for e in emails:
        assert set(e).issuperset({"subject", "from", "date", "body"})


def test_auto_import_discovers_mbox_in_tmp_input(tmp_path: Path) -> None:
    """auto_import recursively finds .mbox files - exercise it on a tmp dir."""
    nested = tmp_path / "Takeout" / "Mail"
    nested.mkdir(parents=True)
    box = mbox(str(nested / "All mail.mbox"))
    box.lock()
    try:
        box.add(
            _make_message(
                "Application received",
                "jobs@delta.com",
                "We have received your application.",
                "Mon, 06 Jan 2025 09:00:00 +0000",
            )
        )
        box.flush()
    finally:
        box.unlock()
        box.close()

    importer = EmailImporter(input_dir=tmp_path)
    emails = importer.auto_import()
    assert len(emails) == 1
    assert emails[0]["subject"] == "Application received"


def test_full_pipeline_import_classify_analyse(synthetic_mbox: Path) -> None:
    importer = EmailImporter()
    raw = importer.import_from_mbox(synthetic_mbox)

    classifier = EmailClassifier()
    classified = classifier.classify_emails(raw)
    assert len(classified) == 4
    statuses = {c["status"] for c in classified}
    # The newsletter must be filtered out; at least one real application status.
    assert "not_job_related" in statuses
    assert statuses & {"applied", "interview_1", "offer", "confirmation"}

    summary = AnalyticsGenerator(classified).generate_summary()
    assert summary["not_job_related_count"] == 1
    assert summary["total_applications"] >= 1
    assert 0.0 <= summary["accuracy_percentage"] <= 100.0


def test_save_analytics_writes_all_outputs(
    synthetic_mbox: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The full output side: JSON, CSV and the Sankey HTML are written.

    Output paths are redirected into ``tmp_path`` so the repo's ``output/``
    directory is never touched and the test stays hermetic.
    """
    json_path = tmp_path / "out" / "analytics.json"
    csv_path = tmp_path / "out" / "applications.csv"
    html_path = tmp_path / "out" / "sankey_diagram.html"
    json_path.parent.mkdir(parents=True)

    monkeypatch.setattr("src.analytics.ANALYTICS_JSON", json_path)
    monkeypatch.setattr("src.analytics.ANALYTICS_CSV", csv_path)
    monkeypatch.setattr("src.analytics.SANKEY_HTML", html_path)

    raw = EmailImporter().import_from_mbox(synthetic_mbox)
    classified = EmailClassifier().classify_emails(raw)
    summary = AnalyticsGenerator(classified).save_analytics()

    assert json_path.exists() and csv_path.exists() and html_path.exists()

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["total_applications"] == summary["total_applications"]
    assert "applications" in loaded

    with csv_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(classified)

    html = html_path.read_text(encoding="utf-8")
    assert "Sankey" in html or "plotly" in html.lower()


def test_email_storage_roundtrip_in_tmp(
    synthetic_mbox: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """EmailStorage save/load round-trips through a UTF-8 JSON file on tmp_path."""
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    monkeypatch.setattr("src.email_storage.INPUT_DIR", store_dir)

    raw = EmailImporter().import_from_mbox(synthetic_mbox)
    storage = EmailStorage()
    assert storage.save_emails(raw, overwrite=True) is True
    assert storage.file_exists()

    loaded = storage.load_emails()
    assert loaded is not None
    assert len(loaded) == len(raw)
    meta = storage.get_metadata()
    assert meta is not None and meta["total_emails"] == len(raw)


def test_main_cli_use_input_runs_clean(
    synthetic_mbox: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drive the real ``src.main.main`` CLI headlessly with --use-input.

    Seeds storage from the synthetic mbox, redirects every path into tmp_path,
    and asserts the full classify -> analytics -> write flow completes without
    raising or exiting non-zero.
    """
    import src.main as main_mod

    store_dir = tmp_path / "store"
    out_dir = tmp_path / "out"
    store_dir.mkdir()
    out_dir.mkdir()

    monkeypatch.setattr("src.email_storage.INPUT_DIR", store_dir)
    monkeypatch.setattr("src.analytics.ANALYTICS_JSON", out_dir / "analytics.json")
    monkeypatch.setattr("src.analytics.ANALYTICS_CSV", out_dir / "applications.csv")
    monkeypatch.setattr("src.analytics.SANKEY_HTML", out_dir / "sankey_diagram.html")
    monkeypatch.setattr("src.main.OUTPUT_DIR", out_dir)

    raw = EmailImporter().import_from_mbox(synthetic_mbox)
    assert EmailStorage().save_emails(raw, overwrite=True) is True

    monkeypatch.setattr("sys.argv", ["sisifus", "--use-input", "--year", "2025"])
    main_mod.main()

    assert (out_dir / "analytics.json").exists()
    assert (out_dir / "applications.csv").exists()
    assert (out_dir / "sankey_diagram.html").exists()


def test_filter_emails_by_date_year_and_months() -> None:
    """Pure date-filtering logic, OS-agnostic and network-free."""
    from datetime import datetime, timezone

    from src.main import filter_emails_by_date

    emails = [
        {"date": datetime(2024, 6, 1, tzinfo=timezone.utc)},
        {"date": datetime(2025, 6, 1, tzinfo=timezone.utc)},
        {"date": "2025-02-01T00:00:00+00:00"},
        {"date": None},
    ]
    by_year = filter_emails_by_date(emails, year=2025)
    assert len(by_year) == 2
    assert filter_emails_by_date([], year=2025) == []
