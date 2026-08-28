import os
import json
import time
from collections import defaultdict
from functools import wraps
from schedule_maker.scraper import getOutput
import tempfile
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for

import pending_storage as storage

upload_bp = Blueprint("upload_bp", __name__)

# ── Config ───────────────────────────────────────────────────────────────
MAX_UPLOAD_BYTES = 5 * 1024 * 1024          # 5MB
ALLOWED_EXTENSIONS = {".html", ".htm"}
RATE_LIMIT_MAX = 10                          # uploads
RATE_LIMIT_WINDOW_SECONDS = 60 * 60         # per hour, per IP

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")   # set in your environment, never hardcode

# In-memory rate limit store: { ip: [timestamps] }. Resets on server restart --
# fine for now; move to the DB (or Redis) later if this needs to survive restarts.
_upload_log = defaultdict(list)

_login_log = defaultdict(list)

def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    _upload_log[ip] = [t for t in _upload_log[ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(_upload_log[ip]) >= RATE_LIMIT_MAX:
        return True
    _upload_log[ip].append(now)
    return False

def _login_rate_limited(ip:str) -> bool:
    now = time.time()
    _login_log[ip] = [t for t in _login_log[ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(_login_log[ip]) >= RATE_LIMIT_MAX:
        return True
    _login_log[ip].append(now)
    return False

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("upload_bp.admin_login"))
        return fn(*args, **kwargs)
    return wrapper


def api_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return jsonify({"error": "Admin login required."}), 401
        return fn(*args, **kwargs)
    return wrapper

# ── TODO 1: plug in your real scraper here ──────────────────────────────
def parse_html_page(html_content: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, "upload.html")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return getOutput(default=tmp_dir)

import course_store

def merge_into_live_courses(parsed_courses: dict):
    # 1. Retrieve current data (from MongoDB or JSON fallback)
    main_data = course_store.reload_courses() or {}

    # 2. Merge the new parsed courses into main_data
    for department, courses in parsed_courses.items():
        main_data.setdefault(department, {})
        for course_name, course_data in courses.items():
            main_data[department][course_name] = course_data

    # 3. Persist updated data and reload memory
    course_store.save_courses(main_data)
    course_store.reload_courses()


@upload_bp.route("/upload", methods=["GET"])
@admin_required
def upload_page():
    return render_template("upload.html")


@upload_bp.route("/api/upload", methods=["POST"])
@api_admin_required
def api_upload():
    ip = request.remote_addr or "unknown"
    if _is_rate_limited(ip):
        return jsonify({"error": "Too many uploads from this address. Try again later."}), 429

    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No file provided."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Only .html files are accepted."}), 400

    raw = file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        return jsonify({"error": "File too large (max 5MB)."}), 400

    try:
        html_content = raw.decode("utf-8", errors="replace")
    except Exception:
        return jsonify({"error": "Could not read file as text."}), 400

    try:
        parsed_courses = parse_html_page(html_content)
    except NotImplementedError:
        raise  # surface loudly during setup -- don't silently swallow this one
    except Exception as e:
        return jsonify({"error": f"Couldn't parse this page: {e}"}), 400

    if not parsed_courses:
        return jsonify({"error": "No courses were found in this page. Nothing was submitted."}), 400

    upload_id = storage.save_pending_upload(html_content, file.filename, ip, parsed_courses)
    return jsonify({
        "message": "Thanks! Your upload is pending review before it goes live.",
        "upload_id": upload_id,
        "courses_found": len(parsed_courses),
    })



# ── Admin: login ─────────────────────────────────────────────────────────
import hmac

@upload_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    ip = request.remote_addr or "unknown"

    if request.method == "POST":
        if _login_rate_limited(ip):
            return render_template("admin_login.html", error="Too many login attempts. Try again later bozo")
        if not ADMIN_PASSWORD:
            return "ADMIN_PASSWORD is not set on the server.", 500
        if hmac.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD or ""):
            session["is_admin"] = True
            return redirect(url_for("upload_bp.admin_page"))
        return render_template("admin_login.html", error="Wrong password.")
    return render_template("admin_login.html")


@upload_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("upload_bp.admin_login"))


# ── Admin: review page + actions ─────────────────────────────────────────
@upload_bp.route("/admin")
@admin_required
def admin_page():
    pending = storage.list_pending_uploads()
    return render_template("admin.html", pending=pending)


@upload_bp.route("/api/pending/<upload_id>/approve", methods=["POST"])
@api_admin_required
def approve(upload_id):
    parsed = storage.get_pending_upload_data(upload_id)
    if parsed is None:
        return jsonify({"error": "Not found."}), 404
    merge_into_live_courses(parsed)
    storage.mark_status(upload_id, "approved")
    return jsonify({"message": "Approved and merged into live data."})


@upload_bp.route("/api/pending/<upload_id>/reject", methods=["POST"])
@api_admin_required
def reject(upload_id):
    storage.mark_status(upload_id, "rejected")
    return jsonify({"message": "Rejected."})





if __name__ == "__main__":

    # from scraper_module import getOutput
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "test.html"), "w", encoding="utf-8") as f:
            f.write(open("schedule_maker/Schedules/DLD.html", encoding="utf-8").read())
        result = getOutput(default=tmp)
        print(result.keys())                       # should show one department
        print(next(iter(result.values())).keys())   # should show that department's course names