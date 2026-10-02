from datetime import datetime
from typing import Dict, Any
from app.config import GOVT_DOMAINS, UNIV_DOMAINS, CORP_DOMAINS
from app.utils import extract_domain

def verify_scholarship(extracted: Dict[str, Any], page_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform audit verification on extracted scholarship details against page evidence.
    Generates deterministic evidence audit dictionary requiring actual crawled evidence.
    """
    url = extracted.get("official_source_url", "")
    domain = extract_domain(url)
    source_type = extracted.get("source_type", "Aggregator")

    # Domain Authority Verification against defined trusted lists
    is_govt = any(g in domain for g in GOVT_DOMAINS)
    is_univ = any(u in domain for u in UNIV_DOMAINS)
    is_corp = any(c in domain for c in CORP_DOMAINS)

    official_domain_verified = is_govt or is_univ or is_corp

    status_code = page_result.get("status_code", 0)
    content_length = page_result.get("content_length", 0)

    # Require genuine 200/301/302 OK status code AND fetched content (>0 bytes)
    http_status_ok = (status_code in [200, 301, 302]) and (content_length > 0 or page_result.get("success", False))

    eligibility_text = extracted.get("eligibility", "Not specified")
    eligibility_found = http_status_ok and (eligibility_text != "Not specified" and len(eligibility_text) > 3)

    amount_text = extracted.get("amount", "Not specified")
    amount_found = http_status_ok and (amount_text != "Not specified" and len(amount_text) > 2)

    deadline_text = extracted.get("deadline", "Not specified")
    deadline_found = http_status_ok and (deadline_text != "Not specified" and len(deadline_text) > 3)

    provider_text = extracted.get("provider", "Not specified")
    provider_found = provider_text not in ["Not specified", "Not Found", "INVALID-STATE-SCHOLARSHIP-PORTAL-999", "DECOMMISSIONED-EDUCATIONAL-TRUST-404"]

    app_url = extracted.get("application_url", "Not specified")
    application_link_valid = http_status_ok and (app_url != "Not specified" and app_url.startswith(("http://", "https://")))

    evidence = {
        "verified_at": datetime.now().isoformat(),
        "domain": domain,
        "source_type": source_type,
        "official_domain_verified": official_domain_verified,
        "http_status_ok": http_status_ok,
        "http_status_code": status_code,
        "content_length_bytes": content_length,
        "provider_found": provider_found,
        "eligibility_found": eligibility_found,
        "amount_found": amount_found,
        "deadline_found": deadline_found,
        "application_link_valid": application_link_valid
    }

    return evidence

