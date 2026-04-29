import json

def filterCourses(all_courses, course_names):
    new_courses = {}
    for department in all_courses:
        for name in course_names:
            if name in all_courses[department]:
                new_courses[name] = all_courses[department][name]
    return new_courses


def excludeGroups(result, excGps):
    new_courses = {}
    if excGps:
        excGps = json.loads(excGps)
    else:
        return result
    for course in result:
        excluded = excGps.get(course, [])  # [] if course not in excGps at all
        
        new_courses[course] = {}
        for gp in result[course]:
            if gp not in excluded:
                new_courses[course][gp] = result[course][gp]
        
    return new_courses



def conflictChecker(item1, item2):
    if item1["Day"] == item2["Day"]:
        if item1["start-time"] < item2["end-time"] and item2["start-time"] < item1["end-time"]:
            return True
    return False

def isGroupSafe(group_slots, curr_schedule):
    for new_slot in group_slots:
        for existing_slot in curr_schedule:
            if conflictChecker(new_slot, existing_slot):
                return False
    return True

def build_schedule_dict(schedule):
    day_map = {}
    for item in schedule:
        day_map.setdefault(item["Day"], []).append(item)

    days_on = len(day_map)
    total_gaps = 0
    slot1 = False
    slot9 = False

    for day, slots in day_map.items():
        slots.sort(key=lambda x: x["start-time"])
        for i in range(len(slots) - 1):
            current_end = slots[i]["end-time"]
            next_start = slots[i+1]["start-time"]
            if next_start > current_end + 1:
                total_gaps += (next_start - current_end - 1)

    for item in schedule:
        if item["start-time"] == 1:
            slot1 = True
        if item["start-time"] >= 9:
            slot9 = True

    return {
        "schedule": list(schedule),
        "days_on": days_on,
        "gaps": total_gaps,
        "slot1": slot1,
        "slot9": slot9,
        "score": 0
    }

def placeCourse(courseidx, schedule, organized_courses, subject_ordering, result):
    if courseidx == len(subject_ordering):
        result.append(build_schedule_dict(schedule))
        return

    course_name = subject_ordering[courseidx]
    course_groups = organized_courses[course_name]

    for gp_id, slots in course_groups.items():
        if isGroupSafe(slots, schedule):
            schedule.extend(slots)
            placeCourse(courseidx+1, schedule, organized_courses, subject_ordering, result)
            for i in range(len(slots)):
                schedule.pop()

def score_schedules(result, selected_preferences, selected_free_days=None, lecturer_input=None):

    if "Minimum Days/Gaps" in selected_preferences:
        for s in result:
            s["score"] += -(s["gaps"] * 3) - (s["days_on"] * 10)

    if "Balanced" in selected_preferences:
        for s in result:
            day_map = {}
            for item in s["schedule"]:
                day_map.setdefault(item["Day"], 0)
                day_map[item["Day"]] += 1
            variance = max(day_map.values()) - min(day_map.values())
            s["score"] += -variance

    if "No 8am/4pm Slots" in selected_preferences:
        for s in result:
            score = 0
            if not s["slot1"]:
                score += 5
            if not s["slot9"]:
                score += 5
            s["score"] += score

    if "Free Days" in selected_preferences and selected_free_days:
        for s in result:
            score = 0
            busy_days = set(item["Day"] for item in s["schedule"])
            for day in selected_free_days:
                if day not in busy_days:
                    score += 10
                else:
                    score -= 10
            s["score"] += score

    if "Lecturer" in selected_preferences and lecturer_input:
        for s in result:
            score = 0
            for item in s["schedule"]:
                if lecturer_input.lower() in item["Instructor"].lower():
                    score += 5
            s["score"] += score

    result.sort(key=lambda x: x["score"], reverse=True)
    return result