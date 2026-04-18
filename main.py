from flask import Flask, request, render_template, jsonify
import json, os
from schedule_maker.scraper import getOutput
from schedule_maker.backtracking import placeCourse, filterCourses, score_schedules


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

data = getOutput()

@app.route("/api/courses")
def get_courses():
    return jsonify(data)

@app.route("/api/optimize/")
def get_schedules():
    selected_courses = request.args.getlist('courses')
    selected_preferences = request.args.getlist('preferences')
    selected_free_days = request.args.getlist('free_days')
    lecturer_input = request.args.get('lecturer', '')

    if not selected_courses:
        return jsonify({"error": "No courses selected"}), 400

    organized_courses = filterCourses(data, selected_courses)

    if not organized_courses:
        return jsonify({"error": "No matching courses found"}), 404

    result = []
    placeCourse(0, [], organized_courses, selected_courses, result)

    if not result:
        return jsonify({"schedule": []})

    scored = score_schedules(
        result,
        selected_preferences,
        selected_free_days=selected_free_days if selected_free_days else None,
        lecturer_input=lecturer_input if lecturer_input else None
    )

    return jsonify({"schedule": [s["schedule"] for s in scored[:100]]})

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=False)