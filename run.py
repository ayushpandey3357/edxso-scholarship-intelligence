import sys
import time
import argparse
from typing import List, Dict, Any

# Ensure stdout uses UTF-8 encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.config import DB_PATH
from app.database import init_db, save_scholarship, get_all_scholarships, get_scholarship_history, log_crawl_run
from app.discovery import discover_scholarships
from app.crawler import fetch_page
from app.extractor import extract_scholarship_details
from app.verifier import verify_scholarship
from app.scorer import calculate_confidence_score
from app.change_detector import compute_scholarship_content_hash, evaluate_stale_or_expired
from app.utils import generate_scholarship_key

def run_pipeline() -> List[Dict[str, Any]]:
    """Execute full Scholarship Intelligence Pipeline."""
    print("=========================================================")
    print("   EDXSO SCHOLARSHIP INTELLIGENCE CRAWLER PIPELINE       ")
    print("=========================================================\n")

    # 1. Initialize SQLite Database
    init_db()
    print("[1/6] Database initialized at:", DB_PATH)

    # 2. Discovery Phase
    print("[2/6] Running discovery phase...")
    all_candidates = discover_scholarships()
    
    print(f"      Discovered {len(all_candidates)} candidate scholarship opportunities.\n")

    # 3. Crawl, Extract, Verify, Score, Change-Detect & Store Phase
    print("[3/6] Crawling, extracting, verifying, and scoring candidates...")
    processed_count = 0

    for i, candidate in enumerate(all_candidates, 1):
        url = candidate["url"]
        s_type = candidate.get("source_type", "Aggregator")

        # Crawl live page
        page_res = fetch_page(url)

        # Extract structured details
        extracted = extract_scholarship_details(page_res, candidate)

        # Merge fallback details if extracted contains defaults
        if candidate.get("provider") and extracted["provider"] in ["Not specified", "Not Found"]:
            extracted["provider"] = candidate["provider"]
        if candidate.get("eligibility") and extracted["eligibility"] == "Not specified":
            extracted["eligibility"] = candidate.get("eligibility", "Not specified")
        if candidate.get("amount") and extracted["amount"] == "Not specified":
            extracted["amount"] = candidate.get("amount", "Not specified")
        if candidate.get("deadline") and extracted["deadline"] == "Not specified":
            extracted["deadline"] = candidate.get("deadline", "Not specified")
        if candidate.get("education_level") and extracted["education_level"] == "Not specified":
            extracted["education_level"] = candidate.get("education_level", "Undergraduate & Postgraduate")

        # Verify against evidence
        evidence = verify_scholarship(extracted, page_res)

        # Score deterministically
        score, base_status = calculate_confidence_score(evidence)

        # Evaluate Stale / Expired Status
        final_status, reason = evaluate_stale_or_expired(extracted, page_res, base_status)

        # Content hash computation
        extracted["confidence_score"] = score
        extracted["status"] = final_status
        extracted["verification_evidence"] = evidence
        extracted["content_hash"] = compute_scholarship_content_hash(extracted)

        # Generate unique key
        key = generate_scholarship_key(extracted["title"], extracted["provider"], extracted["official_source_url"])
        extracted["scholarship_key"] = key

        # Save to SQLite DB
        db_res = save_scholarship(extracted)

        # Audit crawl log
        log_crawl_run(url, s_type, page_res["status_code"], 1 if extracted["title"] != "Not specified" else 0, page_res["error"])

        processed_count += 1
        print(f"  [{i:03d}/{len(all_candidates):03d}] [{final_status:20s}] Score: {score:5.1f}% | {extracted['title'][:55]}")

    # 4. Demonstrate Repeated Crawl & Change Detection
    print("\n[4/6] Executing second pass to demonstrate change detection & version history...")
    items_before = get_all_scholarships()
    if items_before:
        sample_item = items_before[0]
        
        # Simulate an updated deadline for change detection tracking
        page_res_sim = fetch_page(sample_item["official_source_url"])
        extracted_sim = extract_scholarship_details(page_res_sim, sample_item)
        extracted_sim["deadline"] = "Updated Deadline: 15th December 2026"
        extracted_sim["amount"] = sample_item["amount"]
        extracted_sim["eligibility"] = sample_item["eligibility"]
        extracted_sim["provider"] = sample_item["provider"]
        extracted_sim["title"] = sample_item["title"]
        extracted_sim["source_type"] = sample_item["source_type"]
        extracted_sim["official_source_url"] = sample_item["official_source_url"]
        extracted_sim["application_url"] = sample_item["application_url"]

        evidence_sim = verify_scholarship(extracted_sim, page_res_sim)
        score_sim, status_sim = calculate_confidence_score(evidence_sim)

        extracted_sim["confidence_score"] = score_sim
        extracted_sim["status"] = status_sim
        extracted_sim["verification_evidence"] = evidence_sim
        extracted_sim["content_hash"] = compute_scholarship_content_hash(extracted_sim)
        extracted_sim["scholarship_key"] = sample_item["scholarship_key"]

        save_res = save_scholarship(extracted_sim)
        print(f"      Change detection test result: {save_res['action']} ({save_res.get('changes_count', 0)} fields changed logged to history).")

    # 5. Summarize Metrics & Audit Requirements
    records = get_all_scholarships()
    total_count = len(records)
    verified_count = sum(1 for r in records if r["status"] == "VERIFIED")
    high_conf_count = sum(1 for r in records if r["confidence_score"] >= 95.0)
    source_types = set(r["source_type"] for r in records)
    expired_stale_count = sum(1 for r in records if r["status"] in ["EXPIRED", "STALE", "NO_LONGER_VERIFIABLE"])

    # Count total history changes
    total_history_logs = 0
    for r in records:
        h = get_scholarship_history(r["id"])
        total_history_logs += len(h)

    print("\n=========================================================")
    print("   PIPELINE SUMMARY & AUDIT COMPLIANCE REPORT            ")
    print("=========================================================")
    print(f" Total Authentic Scholarships Stored : {total_count} (Target: >= 20)")
    print(f" Officially Verified Scholarships    : {verified_count} (Target: >= 15)")
    print(f" High Confidence (>= 95%) Records    : {high_conf_count} (Target: >= 10)")
    print(f" Distinct Source Types Represented   : {len(source_types)} ({', '.join(source_types)}) (Target: >= 3)")
    print(f" Expired / Stale Scholarships Tracked: {expired_stale_count} (Target: >= 2)")
    print(f" Versioning / History Change Logs    : {total_history_logs} entries recorded")
    print("=========================================================\n")

    return records

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scholarship Intelligence Pipeline CLI")
    args = parser.parse_args()
    run_pipeline()
