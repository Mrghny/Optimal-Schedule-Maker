import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "db.json")
all_courses = {}   # department -> course -> { group: {sessions, _mask} }


def reload_courses():
    global all_courses

    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    all_courses = data
    return all_courses