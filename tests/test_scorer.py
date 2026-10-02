import pytest
from app.scorer import calculate_confidence_score
from app.verifier import verify_scholarship

def test_verifier_evidence():
    extracted = {
        "official_source_url": "https://scholarships.gov.in/main",
        "source_type": "Government",
        "provider": "Ministry of Education",
        "eligibility": "Class 12 pass with 80% marks",
        "amount": "₹12,000 per annum",
        "deadline": "31st October 2026",
        "application_url": "https://scholarships.gov.in/apply"
    }
    page_res = {
        "status_code": 200,
        "content_length": 5000
    }

    evidence = verify_scholarship(extracted, page_res)
    assert evidence["official_domain_verified"] is True
    assert evidence["http_status_ok"] is True
    assert evidence["provider_found"] is True
    assert evidence["eligibility_found"] is True
    assert evidence["amount_found"] is True
    assert evidence["deadline_found"] is True
    assert evidence["application_link_valid"] is True

def test_scorer_verified():
    evidence = {
        "official_domain_verified": True,   # +35
        "http_status_ok": True,             # +15
        "provider_found": True,             # +10
        "eligibility_found": True,          # +15
        "amount_found": True,               # +10
        "application_link_valid": True,     # +10
        "deadline_found": True              # +5
    }                                       # Total = 100%

    score, status = calculate_confidence_score(evidence)
    assert score == 100.0
    assert status == "VERIFIED"

def test_scorer_review_required():
    evidence = {
        "official_domain_verified": False,  # 0
        "http_status_ok": True,             # +15
        "provider_found": True,             # +10
        "eligibility_found": True,          # +15
        "amount_found": False,              # 0
        "application_link_valid": True,     # +10
        "deadline_found": False             # 0
    }                                       # Total = 50%

    score, status = calculate_confidence_score(evidence)
    assert score == 50.0
    assert status == "REVIEW_REQUIRED"
