import pytest
from run import run_pipeline
from app.database import get_all_scholarships

def test_full_pipeline_execution():
    records = run_pipeline()
    assert len(records) > 0
    valid_statuses = {"VERIFIED", "REVIEW_REQUIRED", "STALE", "NO_LONGER_VERIFIABLE", "EXPIRED"}
    assert all(r["status"] in valid_statuses for r in records)
    source_types = set(r["source_type"] for r in records)
    assert len(source_types) >= 2

