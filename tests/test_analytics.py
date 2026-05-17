"""Tests for the AnalyticsGenerator core analysis function.

These exercise the reusable analytics layer with a deterministic in-memory
fixture, so no real mbox / IMAP / filesystem state is required. Sankey HTML
rendering is excluded to keep the suite hermetic and fast.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from src.analytics import AnalyticsGenerator


class TestAnalyticsGenerator:
    """Behavioural tests for the summary / statistics surface."""

    def test_summary_total_applications_excludes_non_job(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        gen = AnalyticsGenerator(sample_classified_emails)
        summary = gen.generate_summary()

        # 6 emails total, 1 is "not_job_related" => 5 application emails
        assert summary["total_applications"] == 5
        assert summary["not_job_related_count"] == 1

    def test_summary_status_breakdown_matches_input(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        gen = AnalyticsGenerator(sample_classified_emails)
        summary = gen.generate_summary()

        breakdown = summary["status_breakdown"]
        assert breakdown["applied"] == 2
        assert breakdown["interview_1"] == 1
        assert breakdown["rejected"] == 1
        assert breakdown["offer"] == 1
        assert breakdown["not_job_related"] == 1

    def test_summary_interview_and_outcome_counts(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        gen = AnalyticsGenerator(sample_classified_emails)
        summary = gen.generate_summary()

        assert summary["interviews_count"] == 1
        assert summary["rejected_count"] == 1
        assert summary["offers_count"] == 1
        assert summary["accepted_count"] == 0
        assert summary["withdrew_count"] == 0

    def test_summary_company_count_excludes_unknown_only_emails(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        gen = AnalyticsGenerator(sample_classified_emails)
        summary = gen.generate_summary()

        # Alpha, Bravo, Charlie are job-related; "Unknown" only appears on
        # the non-job-related newsletter, so it should be excluded.
        assert summary["total_companies"] == 3

    def test_date_range_is_iso_formatted(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        gen = AnalyticsGenerator(sample_classified_emails)
        summary = gen.generate_summary()

        earliest = summary["date_range"]["earliest"]
        latest = summary["date_range"]["latest"]
        assert earliest is not None
        assert latest is not None
        assert earliest.startswith("2026-01-01")
        assert latest.startswith("2026-01-16")

    def test_accuracy_is_percentage(self, sample_classified_emails: list[dict[str, Any]]) -> None:
        gen = AnalyticsGenerator(sample_classified_emails)
        accuracy = gen.calculate_accuracy()
        # 5 of 6 emails have confidence > 0.5 => 83.33%
        assert 0.0 <= accuracy <= 100.0
        assert accuracy == pytest.approx(83.33, abs=0.01)

    def test_accuracy_job_related_only_in_summary(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        gen = AnalyticsGenerator(sample_classified_emails)
        summary = gen.generate_summary()
        # All 5 job-related emails have confidence > 0.5 => 100%
        assert summary["accuracy_percentage"] == pytest.approx(100.0)

    def test_empty_input_does_not_explode(self, empty_email_list: list[dict[str, Any]]) -> None:
        gen = AnalyticsGenerator(empty_email_list)
        summary = gen.generate_summary()
        assert summary["total_applications"] == 0
        assert summary["total_companies"] == 0
        assert gen.calculate_accuracy() == 0.0

    def test_summary_is_json_serialisable(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        """The summary is persisted to JSON, so it must be json-friendly."""
        import json

        gen = AnalyticsGenerator(sample_classified_emails)
        summary = gen.generate_summary()
        # status_breakdown is a Counter - must round-trip through json
        json.dumps(summary)


class TestAnalyticsDataFrameShape:
    """Smoke check that classified-email records project cleanly into pandas.

    This is the lightweight stand-in for a pandera schema - it locks the
    expected column set without pulling pandera as a hard runtime dep.
    """

    EXPECTED_COLUMNS = {
        "subject",
        "body",
        "from",
        "date",
        "status",
        "confidence",
        "company",
    }

    def test_dataframe_columns(self, sample_classified_emails: list[dict[str, Any]]) -> None:
        df = pd.DataFrame(sample_classified_emails)
        assert self.EXPECTED_COLUMNS.issubset(set(df.columns))

    def test_confidence_in_unit_interval(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        df = pd.DataFrame(sample_classified_emails)
        assert (df["confidence"] >= 0.0).all()
        assert (df["confidence"] <= 1.0).all()

    def test_status_is_in_known_vocabulary(
        self, sample_classified_emails: list[dict[str, Any]]
    ) -> None:
        df = pd.DataFrame(sample_classified_emails)
        known = {
            "applied",
            "confirmation",
            "interview_1",
            "interview_2",
            "interview_3",
            "interview_4",
            "interview_5",
            "offer",
            "accepted",
            "rejected",
            "withdrew",
            "no_reply",
            "not_job_related",
        }
        assert set(df["status"]).issubset(known)


class TestPanderaSchema:
    """Optional pandera-based schema validation.

    Skipped automatically when pandera is not installed (it is in the dev
    extras but not in core runtime deps).
    """

    def test_pandera_validation(self, sample_classified_emails: list[dict[str, Any]]) -> None:
        pandera = pytest.importorskip("pandera")
        pa = pandera
        from pandera.typing import Series  # noqa: F401

        schema = pa.DataFrameSchema(
            {
                "subject": pa.Column(str, nullable=False),
                "from": pa.Column(str, nullable=False),
                "status": pa.Column(
                    str,
                    checks=pa.Check.isin(
                        [
                            "applied",
                            "confirmation",
                            "interview_1",
                            "interview_2",
                            "interview_3",
                            "interview_4",
                            "interview_5",
                            "offer",
                            "accepted",
                            "rejected",
                            "withdrew",
                            "no_reply",
                            "not_job_related",
                        ]
                    ),
                ),
                "confidence": pa.Column(float, checks=pa.Check.in_range(0.0, 1.0)),
                "company": pa.Column(str, nullable=False),
            },
            strict=False,
        )
        df = pd.DataFrame(sample_classified_emails)
        validated = schema.validate(df)
        assert len(validated) == len(sample_classified_emails)
