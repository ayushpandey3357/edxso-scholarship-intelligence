import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "scholarships.db")))

# Crawl & HTTP Settings
DEFAULT_TIMEOUT = 12
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Scoring & Verification Thresholds
CONFIDENCE_THRESHOLD = 95.0  # >= 95% is VERIFIED, < 95% is REVIEW_REQUIRED

# Source Types
SOURCE_TYPE_GOVT = "Government"
SOURCE_TYPE_UNIV = "University"
SOURCE_TYPE_CORP = "Foundation/Corporate"
SOURCE_TYPE_AGGR = "Aggregator"

# Trusted Domain Rules for Verification & Classification
GOVT_DOMAINS = [
    ".gov.in", ".nic.in", "scholarships.gov.in", "aicte-india.org", "aicte.gov.in",
    "ugc.ac.in", "ugc.gov.in", "dst.gov.in", "dbtindia.gov.in", "ncs.gov.in",
    "tribal.nic.in", "minorityaffairs.gov.in", "socialjustice.gov.in", "ksb.gov.in", "csirhrdg.res.in"
]

UNIV_DOMAINS = [
    ".ac.in", ".edu.in", ".edu", "iitb.ac.in", "iitd.ac.in", "iitm.ac.in",
    "iitkgp.ac.in", "iisc.ac.in", "bits-pilani.ac.in", "du.ac.in",
    "jnu.ac.in", "nitt.edu", "vnit.ac.in", "iitr.ac.in"
]

CORP_DOMAINS = [
    "tatatrusts.org", "reliancefoundation.org", "hdfcbank.com",
    "infosys.com", "licindia.in", "kotak.com", "kotak.bank.in", "bank.in", "sbi.co.in",
    "adityabirlacapital.com", "lntedutech.com", "onlinemhrd.gov.in"
]

AGGR_DOMAINS = [
    "buddy4study.com", "nationalportals.in", "scholarshiparena.in", "vidyasaarathi.co.in"
]

