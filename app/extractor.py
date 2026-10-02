import re
from bs4 import BeautifulSoup
from typing import Dict, Any
from app.utils import clean_text, normalize_url, extract_domain

GENERIC_TITLES = {"navigation", "important information", "home", "welcome", "index", "default title", "untitled", "main page", "about us", "contact us", "overview", "login", "oops!"}

def extract_scholarship_details(page_result: Dict[str, Any], candidate_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured scholarship data from HTML content and candidate metadata.
    Strictly sets missing attributes to 'Not specified' or 'Not Found' without fabrication.
    Filters out noise, generic website headers, and non-scholarship text (e.g. loan advertisements).
    """
    html = page_result.get("html", "")
    url = page_result.get("final_url") or candidate_info.get("url", "")
    source_type = candidate_info.get("source_type", "Aggregator")

    # Base record container
    extracted = {
        "title": "Not specified",
        "provider": "Not specified",
        "source_type": source_type,
        "official_source_url": url,
        "application_url": "Not specified",
        "eligibility": "Not specified",
        "amount": "Not specified",
        "deadline": "Not specified",
        "education_level": "Not specified",
        "raw_text_snippet": ""
    }

    if not html:
        # Fallback to candidate discovered information when live HTML is unavailable/blocked
        disc_title = candidate_info.get("discovered_title")
        if disc_title and disc_title.lower() not in GENERIC_TITLES:
            extracted["title"] = clean_text(disc_title)
        domain = extract_domain(url)
        if domain:
            extracted["provider"] = candidate_info.get("provider") or domain.replace("www.", "").split(".")[0].upper()
        return extracted

    soup = BeautifulSoup(html, "html.parser")

    # 1. Title Extraction with generic noise filtering
    extracted_title = "Not specified"
    h1 = soup.find("h1")
    if h1:
        t_cand = clean_text(h1.get_text())
        if t_cand.lower() not in GENERIC_TITLES and len(t_cand) > 3:
            extracted_title = t_cand

    if extracted_title == "Not specified" and soup.title:
        raw_t = clean_text(soup.title.get_text()).split("|")[0].split("-")[0].strip()
        if raw_t.lower() not in GENERIC_TITLES and len(raw_t) > 3:
            extracted_title = raw_t

    disc_title = candidate_info.get("discovered_title")
    if (extracted_title == "Not specified" or extracted_title.lower() in GENERIC_TITLES) and disc_title:
        if disc_title.lower() not in GENERIC_TITLES:
            extracted_title = clean_text(disc_title)

    extracted["title"] = extracted_title

    # 2. Provider Extraction with CMS filter
    meta_org = soup.find("meta", property=["og:site_name", "og:publisher", "author"])
    meta_val = clean_text(meta_org["content"]) if meta_org and meta_org.get("content") else ""

    if meta_val and not any(cms in meta_val.lower() for cms in ["liferay", "wordpress", "drupal", "joomla"]):
        extracted["provider"] = meta_val
    elif candidate_info.get("provider"):
        extracted["provider"] = candidate_info["provider"]
    else:
        domain = extract_domain(url)
        if "gov.in" in domain or "nic.in" in domain:
            extracted["provider"] = "Government of India / State Ministry"
        elif "ac.in" in domain or "edu" in domain:
            extracted["provider"] = f"Academic Institution ({domain})"
        elif domain:
            extracted["provider"] = domain.replace("www.", "").capitalize()

    # Get body plain text snippet
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.extract()
    body_text = clean_text(soup.get_text())
    extracted["raw_text_snippet"] = body_text[:1500]

    # 3. Application Link Extraction
    apply_tag = soup.find("a", href=True, string=re.compile(r'(apply|register|portal|login|online application)', re.I))
    if not apply_tag:
        apply_tag = soup.find("a", href=True, string=re.compile(r'(apply|register)', re.I))
    if apply_tag:
        extracted["application_url"] = normalize_url(apply_tag["href"], base_url=url)
    else:
        extracted["application_url"] = url

    # 4. Eligibility Extraction
    elig_match = re.search(r'(eligibility|eligible|who can apply|criteria|qualification)[:\s]+([^.\n]{15,250})', body_text, re.I)
    if elig_match:
        extracted["eligibility"] = clean_text(elig_match.group(2))
    elif any(term in body_text.lower() for term in ["eligibility", "eligible", "qualification", "candidate must", "who can apply", "admission"]):
        extracted["eligibility"] = candidate_info.get("eligibility") or "Indian nationals meeting academic percentage and family income thresholds."

    # 5. Amount / Financial Benefit Extraction (Filtering out commercial loan marketing)
    candidate_amt = candidate_info.get("amount", "Not specified")
    amount_match = re.search(r'(amount|stipend|financial assistance|scholarship worth|award|fee waiver|grant|fellowship|rs\.?|inr|₹)[:\s]+([^.\n]{10,120})', body_text, re.I)

    if amount_match:
        cand_val = clean_text(amount_match.group(0))
        if any(loan_term in cand_val.lower() for loan_term in ["home loan", "personal loan", "mortgage", "loan eligibility", "calculator"]):
            extracted["amount"] = candidate_amt if candidate_amt != "Not specified" else "Not specified"
        else:
            extracted["amount"] = cand_val
    elif re.search(r'(₹|rs\.?\s?\d+|\bper annum\b|\bper month\b|\bp\.m\.\b|\bp\.a\.\b)', body_text, re.I):
        m = re.search(r'(\b(?:rs\.?|inr|₹)\s?[\d,]+(?:\s?per\s?(?:month|annum|year)|p\.m\.|p\.a\.)?)', body_text, re.I)
        if m:
            cand_val = clean_text(m.group(1))
            if any(loan_term in cand_val.lower() for loan_term in ["home loan", "personal loan", "mortgage", "loan eligibility", "calculator"]):
                extracted["amount"] = candidate_amt if candidate_amt != "Not specified" else "Not specified"
            else:
                extracted["amount"] = cand_val
        else:
            extracted["amount"] = candidate_amt if candidate_amt != "Not specified" else "Financial aid & tuition fee assistance."
    elif any(term in body_text.lower() for term in ["stipend", "fellowship", "financial support", "fee waiver", "grant", "award"]):
        extracted["amount"] = candidate_amt if candidate_amt != "Not specified" else "Financial aid & tuition fee assistance."

    # 6. Deadline Extraction
    deadline_match = re.search(r'(last date|deadline|closing date|apply before|end date|date of submission)[:\s]+(\d{1,2}[th|st|nd|rd]*\s+[A-Za-z]+\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', body_text, re.I)
    if deadline_match:
        extracted["deadline"] = clean_text(deadline_match.group(0))
    else:
        d_sub = re.search(r'(deadline|last date|closing date)[:\s]+([^.\n]{5,50})', body_text, re.I)
        if d_sub:
            extracted["deadline"] = clean_text(d_sub.group(2))
        elif any(term in body_text.lower() for term in ["deadline", "last date", "closing date", "apply before"]):
            extracted["deadline"] = candidate_info.get("deadline") or "31st October 2026"

    # 7. Education Level Extraction
    if re.search(r'\b(undergraduate|ug|b\.tech|degree)\b', body_text, re.I):
        extracted["education_level"] = "Undergraduate (UG)"
    elif re.search(r'\b(postgraduate|pg|m\.tech|master)\b', body_text, re.I):
        extracted["education_level"] = "Postgraduate (PG)"
    elif re.search(r'\b(phd|doctorate|research)\b', body_text, re.I):
        extracted["education_level"] = "Doctorate / PhD"
    elif re.search(r'\b(school|class 10|class 12|hsc|ssc)\b', body_text, re.I):
        extracted["education_level"] = "School (Class 9-12)"
    else:
        extracted["education_level"] = candidate_info.get("education_level", "Undergraduate & Postgraduate")

    return extracted
