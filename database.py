import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = os.environ.get("DB_PATH", "ocr_app.db")

# Danh sách doc_type có model thực tế trên https://huggingface.co/ngocthanhdoan
# key phải khớp chính xác với doc_type VietNerm nhận vào ner.extract(doc_type=...)
SEED_DOCTYPES = [
    ("cccd",           "Căn cước công dân", "cccd,id_card",         True),
    ("giay_ra_vien",       "Giấy ra viện",          "giay_ra_vien",    True),
    ("gplx",           "Giấy phép lái xe",  "gplx",      True),
    ("giay_khai_sinh", "Giấy khai sinh",    "giay_khai_sinh",    True),
    ("vehicle_registration",     "Đăng ký xe",        "vehicle_registration", True),
]

# Các key KHÔNG có model public — migration sẽ xóa khỏi DB cũ
INVALID_KEYS = ["cmnd", "driving_license", "birth_certificate", "vehicle_registration"]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS doctypes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                key        TEXT UNIQUE NOT NULL,
                label      TEXT NOT NULL,
                aliases    TEXT DEFAULT '',
                enabled    INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_type   TEXT NOT NULL,
                filename   TEXT,
                raw_text   TEXT,
                ner_result TEXT,
                success    INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Migration: xóa các key không có model để tránh lỗi lúc scan ──────
        for bad_key in INVALID_KEYS:
            conn.execute("DELETE FROM doctypes WHERE key=?", (bad_key,))

        # ── Seed các doctype hợp lệ ───────────────────────────────────────────
        for key, label, aliases, enabled in SEED_DOCTYPES:
            conn.execute("""
                INSERT OR IGNORE INTO doctypes (key, label, aliases, enabled)
                VALUES (?, ?, ?, ?)
            """, (key, label, aliases, int(enabled)))

        conn.commit()
    print("[DB] init_db OK — invalid keys removed, valid doctypes seeded.")


def get_all_doctypes() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM doctypes ORDER BY enabled DESC, label ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_enabled_doctypes() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM doctypes WHERE enabled=1 ORDER BY label ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def add_doctype(key: str, label: str, aliases: str = "", enabled: bool = True) -> Dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO doctypes (key, label, aliases, enabled) VALUES (?, ?, ?, ?)",
            (key.strip().lower(), label.strip(), aliases.strip(), int(enabled))
        )
        conn.commit()
        row = conn.execute("SELECT * FROM doctypes WHERE key=?", (key,)).fetchone()
        return dict(row)


def update_doctype(doctype_id: int, label: str = None, aliases: str = None, enabled: bool = None):
    with get_connection() as conn:
        if label is not None:
            conn.execute("UPDATE doctypes SET label=? WHERE id=?", (label, doctype_id))
        if aliases is not None:
            conn.execute("UPDATE doctypes SET aliases=? WHERE id=?", (aliases, doctype_id))
        if enabled is not None:
            conn.execute("UPDATE doctypes SET enabled=? WHERE id=?", (int(enabled), doctype_id))
        conn.commit()


def delete_doctype(doctype_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM doctypes WHERE id=?", (doctype_id,))
        conn.commit()


def save_scan_history(doc_type: str, filename: str, raw_text: str, ner_result: str, success: bool):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO scan_history (doc_type, filename, raw_text, ner_result, success) VALUES (?,?,?,?,?)",
            (doc_type, filename, raw_text, ner_result, int(success))
        )
        conn.commit()


def get_scan_history(limit: int = 20) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scan_history ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]