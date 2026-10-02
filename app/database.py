import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import DB_PATH

def get_connection(db_path: Optional[Path] = None):
    """Obtain a SQLite database connection with row factory."""
    target_path = db_path or DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[Path] = None):
    """Initialize database schema tables."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Scholarships table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scholarships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scholarship_key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        provider TEXT NOT NULL,
        source_type TEXT NOT NULL,
        official_source_url TEXT NOT NULL,
        application_url TEXT NOT NULL,
        eligibility TEXT NOT NULL,
        amount TEXT NOT NULL,
        deadline TEXT NOT NULL,
        education_level TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        status TEXT NOT NULL,
        verification_evidence TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        last_verified_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Scholarship history table for change detection and versioning
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scholarship_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scholarship_id INTEGER NOT NULL,
        field_name TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        change_type TEXT NOT NULL,
        changed_at TEXT NOT NULL,
        FOREIGN KEY(scholarship_id) REFERENCES scholarships(id) ON DELETE CASCADE
    );
    """)

    # Crawl execution audit log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crawl_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        source_type TEXT NOT NULL,
        status_code INTEGER NOT NULL,
        items_extracted INTEGER NOT NULL,
        error_message TEXT,
        crawled_at TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def save_scholarship(item: Dict[str, Any], db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Save or update scholarship record and log changes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute("SELECT * FROM scholarships WHERE scholarship_key = ?", (item["scholarship_key"],))
    existing = cursor.fetchone()

    evidence_json = json.dumps(item.get("verification_evidence", {}))

    if existing is None:
        cursor.execute("""
        INSERT INTO scholarships (
            scholarship_key, title, provider, source_type, official_source_url,
            application_url, eligibility, amount, deadline, education_level,
            confidence_score, status, verification_evidence, content_hash,
            last_verified_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["scholarship_key"], item["title"], item["provider"], item["source_type"],
            item["official_source_url"], item["application_url"], item["eligibility"],
            item["amount"], item["deadline"], item.get("education_level", "Not specified"),
            item["confidence_score"], item["status"], evidence_json, item["content_hash"],
            now, now, now
        ))
        scholarship_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO scholarship_history (scholarship_id, field_name, old_value, new_value, change_type, changed_at)
        VALUES (?, 'record', NULL, 'Initial Record Created', 'CREATED', ?)
        """, (scholarship_id, now))
        conn.commit()
        conn.close()
        return {"id": scholarship_id, "action": "INSERTED"}
    else:
        existing_dict = dict(existing)
        scholarship_id = existing_dict["id"]
        changes = []

        track_fields = ["title", "provider", "eligibility", "amount", "deadline", "application_url", "confidence_score", "status"]
        for field in track_fields:
            new_val = str(item.get(field, ""))
            old_val = str(existing_dict.get(field, ""))
            if new_val != old_val:
                changes.append((field, old_val, new_val))

        if changes or existing_dict["content_hash"] != item["content_hash"]:
            cursor.execute("""
            UPDATE scholarships SET
                title = ?, provider = ?, source_type = ?, official_source_url = ?,
                application_url = ?, eligibility = ?, amount = ?, deadline = ?,
                education_level = ?, confidence_score = ?, status = ?,
                verification_evidence = ?, content_hash = ?, last_verified_at = ?, updated_at = ?
            WHERE id = ?
            """, (
                item["title"], item["provider"], item["source_type"], item["official_source_url"],
                item["application_url"], item["eligibility"], item["amount"], item["deadline"],
                item.get("education_level", "Not specified"), item["confidence_score"], item["status"],
                evidence_json, item["content_hash"], now, now, scholarship_id
            ))

            for field, old_val, new_val in changes:
                change_type = "EXPIRED" if field == "status" and new_val == "EXPIRED" else (
                    "STALE" if field == "status" and new_val == "STALE" else "UPDATED"
                )
                cursor.execute("""
                INSERT INTO scholarship_history (scholarship_id, field_name, old_value, new_value, change_type, changed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (scholarship_id, field, old_val, new_val, change_type, now))

        conn.commit()
        conn.close()
        return {"id": scholarship_id, "action": "UPDATED" if changes else "NO_CHANGE", "changes_count": len(changes)}

def get_all_scholarships(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieve all scholarships with evidence decoded."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scholarships ORDER BY confidence_score DESC, updated_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for r in rows:
        try:
            r["verification_evidence"] = json.loads(r["verification_evidence"])
        except Exception:
            r["verification_evidence"] = {}
    return rows

def get_scholarship_history(scholarship_id: int, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Get history audit logs for a scholarship."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scholarship_history WHERE scholarship_id = ? ORDER BY changed_at DESC", (scholarship_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def log_crawl_run(url: str, source_type: str, status_code: int, items_extracted: int, error_message: str = "", db_path: Optional[Path] = None):
    """Log crawl execution results."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO crawl_logs (url, source_type, status_code, items_extracted, error_message, crawled_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (url, source_type, status_code, items_extracted, error_message, now))
    conn.commit()
    conn.close()
