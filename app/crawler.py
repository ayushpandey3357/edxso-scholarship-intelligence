import time
import requests
from typing import Dict, Any, Optional
from app.config import USER_AGENT, DEFAULT_TIMEOUT
from app.utils import normalize_url

def fetch_page(url: str, timeout: int = DEFAULT_TIMEOUT, max_retries: int = 2) -> Dict[str, Any]:
    """
    Fetch a web page using HTTP GET with realistic headers and retry logic for transient errors.
    Preserves redirects and final redirected URL.
    Distinguishes temporary network failures from permanent 404/410 errors.
    """
    normalized_url = normalize_url(url)
    if normalized_url == "Not specified":
        return {
            "url": url,
            "final_url": url,
            "status_code": 0,
            "success": False,
            "html": "",
            "content_type": "",
            "content_length": 0,
            "error": "Invalid URL"
        }

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

    session = requests.Session()

    for attempt in range(max_retries + 1):
        try:
            start_time = time.time()
            response = session.get(normalized_url, headers=headers, timeout=timeout, allow_redirects=True)
            elapsed = round(time.time() - start_time, 2)

            # Retry transient server errors or rate limiting
            if response.status_code in [408, 429, 500, 502, 503, 504] and attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue

            return {
                "url": url,
                "final_url": response.url,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "html": response.text if response.status_code == 200 else "",
                "content_type": response.headers.get("Content-Type", ""),
                "content_length": len(response.content) if response.status_code == 200 else 0,
                "response_time_sec": elapsed,
                "error": "" if response.status_code == 200 else f"HTTP {response.status_code}"
            }
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            err_name = "Request Timeout" if isinstance(e, requests.exceptions.Timeout) else "Connection Failed / Host Unreachable"
            status_code = 408 if isinstance(e, requests.exceptions.Timeout) else 503
            return {
                "url": url,
                "final_url": url,
                "status_code": status_code,
                "success": False,
                "html": "",
                "content_type": "",
                "content_length": 0,
                "error": err_name
            }
        except Exception as e:
            return {
                "url": url,
                "final_url": url,
                "status_code": 500,
                "success": False,
                "html": "",
                "content_type": "",
                "content_length": 0,
                "error": str(e)
            }
