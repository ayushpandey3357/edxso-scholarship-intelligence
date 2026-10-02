import pytest
import sqlite3
from pathlib import Path
from app.database import init_db, save_scholarship, get_all_scholarships, get_scholarship_history, log_crawl_run

@pytest.fixture
def tmp_db(tmp_path):
    db_file = tmp_path / "test_scholarships.db"
    init_db(db_file)
    return db_file

def test_init_db(tmp_db):
    assert tmp_db.exists()
    conn = sqlite3.connect(tmp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert "scholarships" in tables
    assert "scholarship_history" in tables
    assert "crawl_logs" in tables

def test_save_and_retrieve_scholarship(tmp_db):
    sample = {
        "scholarship_key": "key123456",
        "title": "Test National Scholarship",
        "provider": "Test Govt Ministry",
        "source_type": "Government",
        "official_source_url": "https://scholarships.gov.in/test",
        "application_url": "https://scholarships.gov.in/apply",
        "eligibility": "Annual family income < ₹2.5 Lakh",
        "amount": "₹10,000 per annum",
        "deadline": "31st October 2026",
        "education_level": "Undergraduate",
        "confidence_score": 98.0,
        "status": "VERIFIED",
        "verification_evidence": {"http_status_ok": True},
        "content_hash": "hash123"
    }

    res1 = save_scholarship(sample, tmp_db)
    assert res1["action"] == "INSERTED"

    records = get_all_scholarships(tmp_db)
    assert len(records) == 1
    assert records[0]["title"] == "Test National Scholarship"
    assert records[0]["confidence_score"] == 98.0

    history = get_scholarship_history(records[0]["id"], tmp_db)
    assert len(history) == 1
    assert history[0]["change_type"] == "CREATED"

def test_change_detection_logging(tmp_db):
    sample = {
        "scholarship_key": "key123456",
        "title": "Test National Scholarship",
        "provider": "Test Govt Ministry",
        "source_type": "Government",
        "official_source_url": "https://scholarships.gov.in/test",
        "application_url": "https://scholarships.gov.in/apply",
        "eligibility": "Annual family income < ₹2.5 Lakh",
        "amount": "₹10,000 per annum",
        "deadline": "31st October 2026",
        "education_level": "Undergraduate",
        "confidence_score": 98.0,
        "status": "VERIFIED",
        "verification_evidence": {"http_status_ok": True},
        "content_hash": "hash123"
    }

    save_scholarship(sample, tmp_db)

    # Update deadline
    updated_sample = sample.copy()
    updated_sample["deadline"] = "15th November 2026"
    updated_sample["content_hash"] = "hash999"

    res2 = save_scholarship(updated_sample, tmp_db)
    assert res2["action"] == "UPDATED"

    records = get_all_scholarships(tmp_db)
    assert records[0]["deadline"] == "15th November 2026"

    history = get_scholarship_history(records[0]["id"], tmp_db)
    assert len(history) == 2
    updated_logs = [h for h in history if h["field_name"] == "deadline"]
    assert len(updated_logs) == 1
    assert updated_logs[0]["old_value"] == "31st October 2026"
    assert updated_logs[0]["new_value"] == "15th November 2026"
