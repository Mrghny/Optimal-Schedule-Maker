"""
Storage layer for crowdsourced course-data uploads.

Currently backed by JSON files under PENDING_DIR. Every function here is
intentionally storage-agnostic in its *signature* so swapping this out for
a real database later (Mongo/Postgres) only means rewriting this file --
nothing in upload_routes.py or main.py needs to change when you do.
"""

import json
import os
import uuid
import time
import tempfile

PENDING_DIR = os.path.join(tempfile.gettempdir(), "pending_data")
# PENDING_DIR = os.path.join(os.path.dirname(__file__), "data", "pending")
INDEX_PATH = os.path.join(PENDING_DIR, "_index.json")

os.makedirs(PENDING_DIR, exist_ok=True)


def _load_index():
    if not os.path.exists(INDEX_PATH):
        return {}
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def save_pending_upload(html_content: str, filename: str, uploader_ip: str, parsed_courses: dict) -> str:
    """
    Stores a new pending upload. Returns its id.
    parsed_courses should already be the output of your existing scrape/organize
    function -- this module only stores the result, it doesn't parse anything.
    """
    upload_id = uuid.uuid4().hex[:12]

    html_path = os.path.join(PENDING_DIR, f"{upload_id}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    data_path = os.path.join(PENDING_DIR, f"{upload_id}.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(parsed_courses, f, indent=2)

    index = _load_index()
    index[upload_id] = {
        "id": upload_id,
        "filename": filename,
        "uploader_ip": uploader_ip,
        "uploaded_at": time.time(),
        "status": "pending",              # pending | approved | rejected
        "num_courses_found": len(parsed_courses),
        "course_names_preview": list(parsed_courses.keys())[:8],
    }
    _save_index(index)
    return upload_id


def list_pending_uploads():
    index = _load_index()
    return sorted(
        [v for v in index.values() if v["status"] == "pending"],
        key=lambda x: x["uploaded_at"],
        reverse=True,
    )


def get_pending_upload_data(upload_id: str):
    data_path = os.path.join(PENDING_DIR, f"{upload_id}.json")
    if not os.path.exists(data_path):
        return None
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def mark_status(upload_id: str, status: str):
    index = _load_index()
    if upload_id not in index:
        return False
    index[upload_id]["status"] = status
    index[upload_id]["reviewed_at"] = time.time()
    _save_index(index)
    return True