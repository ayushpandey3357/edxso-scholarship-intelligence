import hashlib
import re
from urllib.parse import urlparse, urljoin

def clean_text(text: str) -> str:
    """Clean extra whitespaces, newlines, and unprintable characters."""
    if not text:
        return "Not specified"
    cleaned = re.sub(r'\s+', ' ', str(text)).strip()
    return cleaned if cleaned else "Not specified"

def normalize_url(url: str, base_url: str = None) -> str:
    """Normalize relative or raw URLs to absolute HTTP/HTTPS URLs."""
    if not url or url.strip() in ["#", "", "None", "javascript:void(0)"]:
        return "Not specified"
    url = url.strip()
    if base_url and not url.startswith(("http://", "https://")):
        url = urljoin(base_url, url)
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return "Not specified"
    return parsed.geturl()

def extract_domain(url: str) -> str:
    """Extract registered host domain from URL."""
    if not url or url == "Not specified":
        return ""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""

def compute_hash(data: str) -> str:
    """Compute SHA-256 hash of a string content."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def generate_scholarship_key(title: str, provider: str, url: str) -> str:
    """Generate a deterministic unique key for a scholarship entity."""
    raw = f"{clean_text(title).lower()}|{clean_text(provider).lower()}|{extract_domain(url)}"
    return compute_hash(raw)[:16]
