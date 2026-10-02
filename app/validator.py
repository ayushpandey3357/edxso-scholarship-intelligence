import re
from typing import Dict, Any, Tuple, Optional
from app.utils import clean_text, extract_domain

GENERIC_REJECT_TITLES = {
    "navigation", "important information", "government of india", "welcome to ugc",
    "schemes", "general instructions", "regulation", "specifications", "screen reader access",
    "login and registration page", "like us onfacebook", "csc login", "yukti", "home",
    "welcome", "index", "default title", "untitled", "main page", "about us", "contact us",
    "overview", "login", "oops!", "advertisement", "notification", "scheme-wise nodal officers",
    "link for institute / student login", "institutes", "sataarataapa sapaorata",
    "paramaanaikarana saevaaen", "test facilities", "employment generation schemes and programmes",
    "why swayam?", "state bank of india", "indian institute of technology kharagpur",
    "रक्षा अनुसंधान एवं विकास संगठन", "nsp otr", "login and registration", "nodal officers",
    "scholarship eligibility check", "application status", "raise grievance",
    "recruitment agencies/international employer", "employment generation schemes",
    "loans, insurance, investments & financial services prov",
    "welcome to ugc, new delhi, india", "login and registration page",
    "all-scholarships", "all schemes", "nodal officer list"
}

SCHOLARSHIP_KEYWORDS = [
    "scholarship", "fellowship", "stipend", "grant", "financial assistance",
    "financial aid", "bursary", "fee waiver", "mcm", "pragati", "saksham",
    "swanath", "jrf", "pmss", "inspire", "merit-cum-means", "endowment",
    "tuition assistance", "education grant", "freeship", "research associate"
]

def is_actual_scholarship(extracted: Dict[str, Any], page_result: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate whether a discovered candidate represents an actual specific scholarship opportunity.
    Rejects generic portal pages, logins, application status trackers, grievances, homepages, etc.
    Returns (is_valid: bool, rejection_reason: Optional[str]).
    """
    title = clean_text(extracted.get("title", "")).lower()
    disc_title = clean_text(extracted.get("discovered_title", "")).lower()
    url = (extracted.get("official_source_url") or extracted.get("url") or "").lower()
    raw_snippet = clean_text(extracted.get("raw_text_snippet", "")).lower()
    eligibility = clean_text(extracted.get("eligibility", "")).lower()
    amount = clean_text(extracted.get("amount", "")).lower()

    # 1. Login & Registration Portals
    if any(k in url for k in ["/login", "/register", "otrapplication/#/login", "csc-login", "userlogin"]) or \
       any(k in title for k in ["login", "registration page", "user login", "csc login", "link for institute / student login"]):
        return False, "REJECTED_NON_SCHOLARSHIP: Login and registration page"

    # 2. Application Status / Tracking Pages
    if any(k in url for k in ["onlinesanctionedlist", "checkstatus", "track-status", "applicationstatus"]) or \
       any(k in title for k in ["application status", "scholarship eligibility check", "online sanctioned list", "sanctioned list"]):
        return False, "REJECTED_NON_SCHOLARSHIP: Application status page"

    # 3. Grievance & Helpdesk Pages
    if any(k in url for k in ["grievance", "helpdesk"]) or any(k in title for k in ["grievance", "raise grievance", "contact us", "helpdesk"]):
        return False, "REJECTED_NON_SCHOLARSHIP: Grievance or helpdesk page"

    # 4. Accessibility & Screen Reader Pages
    if any(k in title for k in ["screen reader access", "specifications", "like us onfacebook", "social media", "contact us", "overview"]):
        return False, "REJECTED_NON_SCHOLARSHIP: Accessibility or administrative page"

    # 5. Recruitment & Employment Pages
    if any(k in title for k in ["recruitment", "employment generation", "international employer", "jobs toggle", "nairayaata"]):
        return False, "REJECTED_NON_SCHOLARSHIP: Recruitment or employer page"

    # 6. Generic Scheme Listings & Faculty/Institutional Development Pages
    if any(k in title for k in ["faculty development", "institutional development", "research & innovations development"]):
        return False, "REJECTED_NON_SCHOLARSHIP: Faculty or institutional development scheme"

    # 7. Generic Organization / Government Homepage Check
    domain = extract_domain(url)
    url_path = url.split(domain)[-1].strip("/") if domain in url else ""
    if not url_path or url_path in ["", "index.html", "index.php", "home.php", "default.aspx"]:
        if any(k in title for k in ["government of india", "state bank of india", "university of delhi", "defense research", "infosys foundation", "swayam", "ncs", "drdo", "home"]):
            return False, "REJECTED_NON_SCHOLARSHIP: Generic organization homepage"

    # 8. Generic Title Check
    if title in GENERIC_REJECT_TITLES or disc_title in GENERIC_REJECT_TITLES or len(title) <= 3:
        return False, f"REJECTED_NON_SCHOLARSHIP: Generic organization homepage or portal title ('{extracted.get('title')}')"

    # 9. Core Scholarship Terminology & Concept Check
    combined_content = f"{title} {disc_title} {raw_snippet[:600]} {eligibility} {amount}".lower()
    has_scholarship_term = any(kw in combined_content for kw in SCHOLARSHIP_KEYWORDS)

    if not has_scholarship_term:
        return False, "REJECTED_NON_SCHOLARSHIP: Missing core scholarship concepts and terminology"

    return True, None
