"""Shared pytest fixtures for the sisifus-analytics test suite."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest


@pytest.fixture
def sample_classified_emails() -> list[dict[str, Any]]:
    """A small, deterministic dataset of already-classified emails.

    Shape mirrors what ``EmailClassifier.classify_emails`` produces and what
    ``AnalyticsGenerator`` consumes. Useful as a stand-in for a real
    Google-Takeout-derived mbox without I/O.
    """
    base = datetime(2026, 1, 1, 9, 0, 0)
    return [
        {
            "subject": "Application submitted",
            "body": "Thanks for applying",
            "from": "hr@alpha.com",
            "date": base,
            "status": "applied",
            "confidence": 0.8,
            "company": "Alpha",
        },
        {
            "subject": "First Interview",
            "body": "Phone screen",
            "from": "hr@alpha.com",
            "date": base + timedelta(days=3),
            "status": "interview_1",
            "confidence": 0.7,
            "company": "Alpha",
        },
        {
            "subject": "Application submitted",
            "body": "Thanks for applying",
            "from": "hr@bravo.io",
            "date": base + timedelta(days=1),
            "status": "applied",
            "confidence": 0.9,
            "company": "Bravo",
        },
        {
            "subject": "Update on your application",
            "body": "We regret to inform you we will not be moving forward.",
            "from": "hr@bravo.io",
            "date": base + timedelta(days=10),
            "status": "rejected",
            "confidence": 0.85,
            "company": "Bravo",
        },
        {
            "subject": "Job Offer",
            "body": "We are pleased to offer you the position",
            "from": "manager@charlie.dev",
            "date": base + timedelta(days=15),
            "status": "offer",
            "confidence": 0.95,
            "company": "Charlie",
        },
        {
            "subject": "Black Friday Sale",
            "body": "50% off everything",
            "from": "promo@store.com",
            "date": base + timedelta(days=2),
            "status": "not_job_related",
            "confidence": 0.0,
            "company": "Unknown",
        },
    ]


@pytest.fixture
def empty_email_list() -> list[dict[str, Any]]:
    """An empty list, for boundary-condition tests."""
    return []
