import re
import time
import urllib.parse
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from app.config import (
    USER_AGENT, DEFAULT_TIMEOUT,
    SOURCE_TYPE_GOVT, SOURCE_TYPE_UNIV, SOURCE_TYPE_CORP, SOURCE_TYPE_AGGR,
    GOVT_DOMAINS, UNIV_DOMAINS, CORP_DOMAINS
)
from app.utils import normalize_url, extract_domain, clean_text

# Seed sources spanning Government, University, Foundation/Corporate, and Aggregators
SEED_PORTALS = [
    # Government Sources
    {
        "name": "Central Sector Scheme of Scholarships for College and University Students",
        "url": "https://scholarships.gov.in/",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "scholarships.gov.in"
    },
    {
        "name": "NSP All Schemes & Guidelines Portal",
        "url": "https://scholarships.gov.in/All-Scholarships",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "scholarships.gov.in"
    },
    {
        "name": "AICTE Pragati & Saksham Scholarship Scheme",
        "url": "https://www.aicte-india.org/schemes/students-development-schemes",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "aicte-india.org"
    },
    {
        "name": "AICTE PG Scholarship Scheme",
        "url": "https://www.aicte-india.org/schemes/students-development-schemes/PG-Scholarship",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "aicte-india.org"
    },
    {
        "name": "UGC National Fellowship & Merit Scholarships",
        "url": "https://www.ugc.gov.in/page/Scholarships-and-Fellowships.aspx",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "ugc.gov.in"
    },
    {
        "name": "CSIR HRDG Junior Research Fellowship (JRF) & RA Fellowships",
        "url": "https://csirhrdg.res.in/",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "csirhrdg.res.in"
    },
    {
        "name": "SWAYAM NPTEL Student Fellowship & Course Grants",
        "url": "https://swayam.gov.in/",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "swayam.gov.in"
    },
    {
        "name": "NCS National Career & Education Assistance",
        "url": "https://ncs.gov.in/",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "ncs.gov.in"
    },
    {
        "name": "DRDO Junior Research Fellowship (JRF) & Research Associateship",
        "url": "https://www.drdo.gov.in/",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "drdo.gov.in"
    },
    {
        "name": "PM Scholarship Scheme for Wards of Ex-Servicemen (KSB)",
        "url": "https://ksb.gov.in/prime-ministers-scholarship-scheme-pmss.htm",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "ksb.gov.in"
    },
    {
        "name": "Post Matric Scholarship for ST Students (Ministry of Tribal Affairs)",
        "url": "https://tribal.nic.in/Scholarship.aspx",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "tribal.nic.in"
    },
    {
        "name": "Post Matric Scholarship for SC & ST Students (NSP)",
        "url": "https://scholarships.gov.in/otrapplication/#/login-page",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "scholarships.gov.in"
    },
    {
        "name": "DST INSPIRE Scholarship for Higher Education (SHE)",
        "url": "https://online-inspire.gov.in/",
        "source_type": SOURCE_TYPE_GOVT,
        "primary_domain": "online-inspire.gov.in"
    },

    # University Sources
    {
        "name": "IIT Bombay Merit-cum-Means (MCM) Scholarship",
        "url": "https://www.iitb.ac.in/newen/awards-and-scholarships",
        "source_type": SOURCE_TYPE_UNIV,
        "primary_domain": "iitb.ac.in"
    },
    {
        "name": "IIT Delhi Financial Assistance & Scholarships",
        "url": "https://home.iitd.ac.in/scholarships.php",
        "source_type": SOURCE_TYPE_UNIV,
        "primary_domain": "iitd.ac.in"
    },
    {
        "name": "IISc Bangalore Student Scholarships & Financial Support",
        "url": "https://iisc.ac.in/admissions/financial-support/",
        "source_type": SOURCE_TYPE_UNIV,
        "primary_domain": "iisc.ac.in"
    },
    {
        "name": "University of Delhi Fee Waiver & Financial Aid",
        "url": "http://du.ac.in/index.php?page=scholarships",
        "source_type": SOURCE_TYPE_UNIV,
        "primary_domain": "du.ac.in"
    },
    {
        "name": "BITS Pilani Merit & Merit-cum-Means Scholarships",
        "url": "https://www.bits-pilani.ac.in/pilani/scholarships",
        "source_type": SOURCE_TYPE_UNIV,
        "primary_domain": "bits-pilani.ac.in"
    },
    {
        "name": "IIT Madras Financial Assistance & Merit Fellowships",
        "url": "https://www.iitm.ac.in/academics/financial-assistance",
        "source_type": SOURCE_TYPE_UNIV,
        "primary_domain": "iitm.ac.in"
    },
    {
        "name": "IIT Kharagpur Merit-cum-Means Assistance",
        "url": "https://www.iitkgp.ac.in/financial-assistance",
        "source_type": SOURCE_TYPE_UNIV,
        "primary_domain": "iitkgp.ac.in"
    },

    # Foundation & Corporate Sources
    {
        "name": "Tata Trusts Endowment Scholarships",
        "url": "https://www.tatatrusts.org/our-work/individual-grants-programme/education-grants",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "tatatrusts.org"
    },
    {
        "name": "Reliance Foundation Undergraduate Scholarships",
        "url": "https://www.reliancefoundation.org/our-work/education/scholarships",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "reliancefoundation.org"
    },
    {
        "name": "HDFC Parivartan Educational Crisis Scholarship Scheme (ECSS)",
        "url": "https://www.hdfcbank.com/personal/about-us/corporate-social-responsibility/parivartan-scholarship",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "hdfcbank.com"
    },
    {
        "name": "LIC Golden Jubilee Scholarship Scheme",
        "url": "https://licindia.in/golden-jubilee-scholarship-scheme",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "licindia.in"
    },
    {
        "name": "Kotak Kanya Scholarship Program",
        "url": "https://www.kotak.bank.in/en/about-us/csr/kotak-kanya-scholarship.html",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "kotak.bank.in"
    },
    {
        "name": "Kotak CSR Foundation Scholarship Portal",
        "url": "https://www.kotak.com/en/about-us/csr/kotak-kanya-scholarship.html",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "kotak.com"
    },
    {
        "name": "Infosys Foundation STEM Stars Scholarship for Women",
        "url": "https://www.infosys.com/infosys-foundation.html",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "infosys.com"
    },
    {
        "name": "SBI Asha Scholarship Program",
        "url": "https://sbi.co.in/",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "sbi.co.in"
    },
    {
        "name": "Aditya Birla Capital Scholarship Program",
        "url": "https://www.adityabirlacapital.com/",
        "source_type": SOURCE_TYPE_CORP,
        "primary_domain": "adityabirlacapital.com"
    }
]

GENERIC_NOISE_TITLES = {"navigation", "important information", "home", "welcome", "login", "about us", "index", "default title", "untitled", "main page"}

def score_candidate_quality(candidate: Dict[str, Any]) -> float:
    """
    Score candidate quality (0-100) before crawling and verification.
    Prioritizes specific scholarship pages, trusted domains, and relevant keywords.
    """
    score = 50.0
    url = candidate.get("url", "").lower()
    title = candidate.get("discovered_title", "").lower()
    domain = extract_domain(url)

    # Generic title penalty
    if title in GENERIC_NOISE_TITLES or any(gt == title for gt in GENERIC_NOISE_TITLES):
        score -= 40.0

    # Scholarship keyword boost in URL or title
    scholarship_kw = ["scholarship", "fellowship", "stipend", "grant", "financial-aid", "pragati", "post-matric", "mcm", "scholarships"]
    if any(kw in url for kw in scholarship_kw):
        score += 20.0
    if any(kw in title for kw in scholarship_kw):
        score += 15.0

    # Trusted domain boost
    if any(g in domain for g in GOVT_DOMAINS) or any(u in domain for u in UNIV_DOMAINS) or any(c in domain for c in CORP_DOMAINS):
        score += 15.0

    # Specific sub-page indicator (longer URL path)
    if len(url.split("/")) > 4:
        score += 10.0

    return max(0.0, min(100.0, score))

def discover_scholarships() -> List[Dict[str, Any]]:
    """
    Discover scholarship opportunities dynamically.
    Fetches seed portals and extracts official candidate URLs, provider details, and source types.
    Crawls links from seed pages to discover specific individual scholarship pages.
    """
    candidates = []
    seen_urls = set()

    # 1. Register primary seed portals
    for seed in SEED_PORTALS:
        url = seed["url"]
        if url not in seen_urls:
            candidate = {
                "discovered_title": seed["name"],
                "url": url,
                "source_type": seed["source_type"],
                "primary_domain": seed["primary_domain"],
                "discovery_origin": "Direct Official Seed Portal"
            }
            candidate["quality_score"] = score_candidate_quality(candidate)
            candidates.append(candidate)
            seen_urls.add(url)

    # 2. Dynamic link discovery: Scrape primary seed portals to discover child scholarship links
    headers = {"User-Agent": USER_AGENT}

    for seed in SEED_PORTALS[:10]:
        seed_url = seed["url"]
        try:
            resp = requests.get(seed_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    title = clean_text(a_tag.get_text())

                    if not href or href.startswith("#") or href.startswith("javascript:"):
                        continue

                    full_url = normalize_url(href, base_url=seed_url)
                    if full_url in seen_urls or full_url == "Not specified" or full_url.endswith((".pdf", ".zip", ".png", ".jpg")):
                        continue

                    # Reject generic title text unless URL contains explicit scholarship keywords
                    if title.lower() in GENERIC_NOISE_TITLES or len(title) < 5:
                        if not any(kw in full_url.lower() for kw in ["scholarship", "fellowship", "stipend", "grant", "pragati"]):
                            continue

                    # Filter for scholarship related child links
                    if any(kw in (title + full_url).lower() for kw in ["scholarship", "fellowship", "stipend", "grant", "scheme", "pragati", "financial"]):
                        domain = extract_domain(full_url)
                        cand = {
                            "discovered_title": title if title.lower() not in GENERIC_NOISE_TITLES else seed["name"],
                            "url": full_url,
                            "source_type": seed["source_type"],
                            "primary_domain": domain,
                            "discovery_origin": f"Discovered via Link Crawler ({seed['name']})"
                        }
                        cand["quality_score"] = score_candidate_quality(cand)
                        candidates.append(cand)
                        seen_urls.add(full_url)
        except Exception:
            pass

    # Sort candidates by quality score descending
    candidates.sort(key=lambda c: c.get("quality_score", 0.0), reverse=True)
    return candidates
