from typing import Dict, Any, Tuple
from app.config import CONFIDENCE_THRESHOLD

def calculate_confidence_score(evidence: Dict[str, Any]) -> Tuple[float, str]:
    """
    Calculate deterministic confidence score (0-100%) strictly from audit evidence.
    Returns (score, status_label).
    """
    score = 0.0

    # 1. Primary / Official Domain Verification (35%)
    if evidence.get("official_domain_verified"):
        score += 35.0

    # 2. HTTP Response 200 OK & Content Validity (15%)
    if evidence.get("http_status_ok"):
        score += 15.0

    # 3. Explicit Provider / Organization Identified (10%)
    if evidence.get("provider_found"):
        score += 10.0

    # 4. Eligibility Criteria Verified (15%)
    if evidence.get("eligibility_found"):
        score += 15.0

    # 5. Amount / Financial Benefit Specified (10%)
    if evidence.get("amount_found"):
        score += 10.0

    # 6. Valid Application URL / Portal Present (10%)
    if evidence.get("application_link_valid"):
        score += 10.0

    # 7. Deadline / Period Specified (5%)
    if evidence.get("deadline_found"):
        score += 5.0

    score = round(min(100.0, max(0.0, score)), 1)

    # Determine status (VERIFIED requires both >= CONFIDENCE_THRESHOLD score and live http_status_ok)
    if score >= CONFIDENCE_THRESHOLD and evidence.get("http_status_ok", False):
        status = "VERIFIED"
    else:
        status = "REVIEW_REQUIRED"

    return score, status

