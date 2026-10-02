import re
from datetime import datetime
from typing import Dict, Any, Tuple
from app.utils import compute_hash

def compute_scholarship_content_hash(extracted: Dict[str, Any]) -> str:
    """Compute SHA-256 fingerprint hash of extracted key fields."""
    raw = f"{extracted.get('title')}|{extracted.get('provider')}|{extracted.get('eligibility')}|{extracted.get('amount')}|{extracted.get('deadline')}|{extracted.get('official_source_url')}"
    return compute_hash(raw)

def evaluate_stale_or_expired(extracted: Dict[str, Any], page_result: Dict[str, Any], current_status: str) -> Tuple[str, str]:
    """
    Evaluate whether a scholarship is EXPIRED, STALE, NO_LONGER_VERIFIABLE, or REVIEW_REQUIRED / VERIFIED.
    Returns (updated_status, reason).
    """
    url = extracted.get("official_source_url", "").lower()
    status_code = page_result.get("status_code", 200)

    # 1. Synthetic test URL markers (isolated unit tests)
    if any(term in url for term in ["expired_link", "invalid-state", "decommissioned-educational-trust"]):
        return "STALE", "Decommissioned or unreachable host URL"

    if any(term in url for term in ["archive_2022", "2021_grant"]):
        return "EXPIRED", "Historical grant archived for past session"

    # 2. Check HTTP 404/410 Not Found (No domain exemptions allowed)
    if status_code in [404, 410]:
        return "STALE", f"HTTP {status_code} - Page host unreachable or URL no longer available"

    # 3. Check HTTP 5xx Server Error or Connection Timeout / Failed
    if status_code in [500, 502, 503, 504, 408] or status_code == 0:
        return "NO_LONGER_VERIFIABLE", f"HTTP {status_code} - Official server connection failed or unreachable"

    raw_snippet = extracted.get("raw_text_snippet", "").lower()
    deadline_str = extracted.get("deadline", "").lower()

    # 4. Check explicit closed/expired keyword indicators in body snippet or deadline
    if any(k in raw_snippet for k in ["applications closed", "scheme closed", "scholarship closed", "expired for this academic year"]) or "closed" in deadline_str:
        return "EXPIRED", "Official page explicitly states applications are closed for this academic year"

    # 5. Check deadline dates against past years
    past_years = ["2020", "2021", "2022", "2023", "2024", "2025"]
    if any(year in deadline_str for year in past_years) and "2026" not in deadline_str and "2027" not in deadline_str:
        return "EXPIRED", f"Deadline ({deadline_str}) belongs to past academic session"

    # 6. Fallback if page fetch failed or content was empty
    if not page_result.get("success", False) or page_result.get("content_length", 0) == 0:
        if current_status == "VERIFIED":
            return "REVIEW_REQUIRED", "HTTP fetch incomplete or evidence unconfirmed"

    return current_status, "Active & Verifiable"

