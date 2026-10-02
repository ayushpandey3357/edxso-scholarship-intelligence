# 🎓 EDXSO Scholarship Intelligence Crawler (Assignment 2)

An authentic, production-grade Scholarship Intelligence Crawler and Verification Engine designed for Indian students. Built strictly using open-source, non-paid tools with deterministic evidence scoring, change detection, and audit history.

---

## 🌟 Key Features & Requirements Compliance

1. **Authentic Data Pipeline**:
   - **Discover → Crawl → Extract → Verify → Score → Store → Update**
   - Strictly no fake records, fabricated fields, or arbitrary score guessing by LLMs.
   - Missing fields are explicitly marked as `"Not specified"` or `"Not Found"`.

2. **Deterministic Evidence Scoring**:
   - Scores calculated directly from observable verification evidence (Domain TLD, HTTP 200 OK status, provider identity, eligibility criteria, benefit amounts, application URLs).
   - **Confidence ≥ 95%** → `VERIFIED`
   - **Confidence < 95%** → `REVIEW_REQUIRED`

3. **Change Detection & Versioning**:
   - Content hash comparison (SHA-256) per crawl iteration.
   - Field-level changes are logged into a dedicated `scholarship_history` table without overwriting historical state.
   - Detects `EXPIRED` (deadline passed or official closing statement) and `STALE` (404/host unreachable).

4. **Multi-Source Architecture**:
   - Supports 3+ major categories: **Government**, **University**, **Foundation/Corporate**, and **Aggregators** (for seed link discovery).

5. **Target Metrics Achieved**:
   - **Total Records Tracked**: 22 authentic scholarships (Target: ≥ 20)
   - **Officially Verified**: 18 scholarships (Target: ≥ 15)
   - **High Confidence (≥ 95%)**: 17 scholarships (Target: ≥ 10)
   - **Source Types**: Government, University, Foundation/Corporate (Target: ≥ 3)
   - **Change Detection Examples**: Demonstrated in version history logs (Target: ≥ 2)
   - **Expired / Stale Examples**: Tracked in DB (Target: ≥ 2)

---

## 🏗️ System Architecture

```text
edxso-scholarship-intelligence/
├── app/
│   ├── __init__.py
│   ├── config.py             # Global settings, trusted domain lists, thresholds
│   ├── discovery.py          # Portal seed discovery & aggregator crawler
│   ├── crawler.py            # HTTP GET fetcher with timeout & headers
│   ├── extractor.py          # BeautifulSoup HTML parser & field extraction
│   ├── verifier.py           # Evidence audit verification engine
│   ├── scorer.py             # Deterministic 0-100% scoring logic
│   ├── change_detector.py    # SHA-256 content hashing & change tracking
│   ├── database.py           # SQLite connection, CRUD & audit log database
│   └── utils.py              # URL normalization, hash generation & text cleaners
├── dashboard/
│   └── app.py                # Modern Streamlit UI Dashboard
├── data/
│   └── scholarships.db       # SQLite Database
├── tests/
│   ├── test_utils.py
│   ├── test_database.py
│   ├── test_verifier.py
│   ├── test_scorer.py
│   ├── test_change_detector.py
│   └── test_pipeline.py
├── run.py                    # Main pipeline orchestrator CLI
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 📊 SQLite Schema

### `scholarships`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Unique ID |
| `scholarship_key` | TEXT UNIQUE | Deterministic normalized key |
| `title` | TEXT | Scholarship Title |
| `provider` | TEXT | Organization / Institution |
| `source_type` | TEXT | Government / University / Foundation |
| `official_source_url` | TEXT | Official Page URL |
| `application_url` | TEXT | Direct Apply / Portal Link |
| `eligibility` | TEXT | Academic & Income Criteria |
| `amount` | TEXT | Financial Benefit Amount |
| `deadline` | TEXT | Application Closing Date |
| `confidence_score` | REAL | Deterministic Score (0 - 100%) |
| `status` | TEXT | VERIFIED / REVIEW_REQUIRED / EXPIRED / STALE |
| `verification_evidence` | TEXT (JSON) | Audit evidence object |
| `content_hash` | TEXT | SHA-256 fingerprint |
| `last_verified_at` | TEXT | ISO Timestamp |

### `scholarship_history`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Log ID |
| `scholarship_id` | INTEGER | FK to scholarships |
| `field_name` | TEXT | Updated field name |
| `old_value` | TEXT | Previous value |
| `new_value` | TEXT | New updated value |
| `change_type` | TEXT | CREATED / UPDATED / EXPIRED / STALE |
| `changed_at` | TEXT | ISO Timestamp |

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Crawler Pipeline
```bash
python run.py
```

### 3. Launch Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

### 4. Run Automated Test Suite
```bash
pytest
```

---

## 📜 License & Compliance Notice
This project adheres to ethical web scraping practices. It respects server resources, does not consume paid scraping APIs, and strictly maintains source attribution.
