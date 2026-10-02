import pytest
from app.change_detector import compute_scholarship_content_hash, evaluate_stale_or_expired

def test_content_hash():
    ext = {
        "title": "Scholarship A",
        "provider": "Ministry A",
        "eligibility": "Income < 2L",
        "amount": "10k",
        "deadline": "2026-10-31",
        "official_source_url": "https://gov.in/a"
    }
    h1 = compute_scholarship_content_hash(ext)
    h2 = compute_scholarship_content_hash(ext)
    assert h1 == h2
    
    ext["deadline"] = "2026-11-30"
    h3 = compute_scholarship_content_hash(ext)
    assert h1 != h3

def test_evaluate_stale_or_expired():
    ext = {
        "raw_text_snippet": "Applications closed for this session",
        "deadline": "Expired 2022"
    }
    page_res = {"status_code": 200}
    status, reason = evaluate_stale_or_expired(ext, page_res, "VERIFIED")
    assert status == "EXPIRED"

    # Dead link 404
    page_res_404 = {"status_code": 404}
    status2, reason2 = evaluate_stale_or_expired(ext, page_res_404, "VERIFIED")
    assert status2 == "STALE"
