from flask import Flask, request, render_template, jsonify
import json, os
from schedule_maker.scraper import getOutput
from schedule_maker.backtracking import filterCourses, score_schedules, excludeGroups, placeCourse, sortBySmallestGroups
import course_store
from upload_routes import upload_bp
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.register_blueprint(upload_bp)                  
course_store.reload_courses()                       


EFFORT_CAPS = {
    "fast": 5000,
    "balanced": 50000,
    "thorough": 300000,
}

@app.route("/api/courses")
def get_courses():
    return jsonify(course_store.all_courses)        

@app.route("/api/optimize/")
def get_schedules():
    selected_courses = request.args.getlist('courses')
    selected_preferences = request.args.getlist('preferences')
    selected_free_days = request.args.getlist('free_days')
    lecturer_input = request.args.get('lecturer', '')
    number = request.args.get('num_schedules')
    exc = request.args.get('excluded_groups')

    

    effort = request.args.get('effort', 'balanced')
    max_raw_results = EFFORT_CAPS.get(effort, EFFORT_CAPS['balanced'])

    if not number:
        number = 0

    if not selected_courses:
        return jsonify({"error": "No courses selected"}), 400
    if len(selected_courses) > 8:
        return jsonify({"error": "Too many courses selected"}), 400
    
    organized_courses = filterCourses(course_store.all_courses, selected_courses)
    organized_courses = excludeGroups(organized_courses,exc)
    subject_ordering = sortBySmallestGroups(organized_courses)

    if not organized_courses:
        return jsonify({"error": "No matching courses found"}), 404


    
    result = []
    placeCourse(0, [], organized_courses, subject_ordering, result, max_results=max_raw_results)
    
    if not result:
        return jsonify({"schedule": []})

    scored = score_schedules(
        result,
        selected_preferences,
        selected_free_days=selected_free_days if selected_free_days else None,
        lecturer_input=lecturer_input if lecturer_input else None
    )


    return jsonify({"schedule": [s["schedule"] for s in scored[:int(number)]]})

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=False)