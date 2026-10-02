import pytest
from app.utils import clean_text, normalize_url, extract_domain, compute_hash, generate_scholarship_key

def test_clean_text():
    assert clean_text("  Hello   World \n\n ") == "Hello World"
    assert clean_text("") == "Not specified"
    assert clean_text(None) == "Not specified"

def test_normalize_url():
    assert normalize_url("https://scholarships.gov.in/path") == "https://scholarships.gov.in/path"
    assert normalize_url("/schemes", base_url="https://aicte-india.org") == "https://aicte-india.org/schemes"
    assert normalize_url("invalid-url") == "Not specified"
    assert normalize_url("#") == "Not specified"

def test_extract_domain():
    assert extract_domain("https://scholarships.gov.in/main.html") == "scholarships.gov.in"
    assert extract_domain("http://www.iitb.ac.in/") == "www.iitb.ac.in"
    assert extract_domain("") == ""

def test_compute_hash():
    h1 = compute_hash("test string")
    h2 = compute_hash("test string")
    assert h1 == h2
    assert len(h1) == 64

def test_generate_scholarship_key():
    key1 = generate_scholarship_key("NSP Scholarship", "Govt", "https://scholarships.gov.in")
    key2 = generate_scholarship_key("NSP Scholarship", "Govt", "https://scholarships.gov.in")
    assert key1 == key2
    assert len(key1) == 16
