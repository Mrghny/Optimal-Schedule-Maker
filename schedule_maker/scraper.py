from bs4 import BeautifulSoup
import json
import os
# 1) bit mask timings
# 2) Sort courses by fewest groups first before backtracking

DAY_INDEX = {
    "Saturday": 0,
    "Sunday": 1,
    "Monday": 2,
    "Tuesday": 3,
    "Wednesday": 4,
    "Thursday": 5,
    "Friday": 6,
}

PERIODS_PER_DAY = 17

def sessionMask(day: str, start: int, end: int) -> int:
    day_idx = DAY_INDEX[day]
    mask = 0

    for period in range(start, end+1):
        bit = day_idx * PERIODS_PER_DAY + period
        mask |= (1 << bit)

    return mask

def groupMask(sessions: list[dict]) -> int:
    
    mask = 0
    for sess in sessions:
        mask |= sessionMask(sess["Day"], sess["start-time"], sess["end-time"])

    # print(mask)
    return mask

def attachMasks(courses: dict) -> dict:
    for department, course in courses.items():

        # print(f"{course}\n")
        for course_name, groups in course.items():

            
            for grp_letter, sessions in groups.items():
                mask = groupMask(sessions)
                
                groups[grp_letter] = {
                    "sessions": sessions,
                    "_mask": str(mask)
                }
                
                

    return courses
                

def extractSubjects(filepath):

    with open(f"{filepath}") as fp:
        soup = BeautifulSoup(fp, 'html.parser')

    table = soup.find(id="ctl00_ContentPlaceHolder1_Schedule1")
    rows = table.find_all("tr")
    
    dropdown = soup.find('select', id='ctl00_ContentPlaceHolder1_ddl_Department')

    selected_option = dropdown.find('option', selected=True)

    if selected_option:
        value = selected_option.get('value')
        department = selected_option.text.strip()
        

    sem_dropdown = soup.find('tr', id='ctl00_ContentPlaceHolder1_TR_Period').find_all('td')[1].find('select')
    selected_sem = sem_dropdown.find('option', selected=True) 
    if selected_sem:
        semester = selected_sem.text.strip()

        

    # Getting Course Code & Name
    course = soup.find(id="ctl00_ContentPlaceHolder1_lbl_Title").get_text(strip=True).split(":")
    course = course[1].strip().split("- ")
    course_code = course[1]
    course_name = course[0]





    # build grid
    grid = {}
    occupied = {}
    for r_idx, tr in enumerate(rows):
        c_idx = 0
        for td in tr.find_all(["th", "td"]):
            while (r_idx, c_idx) in occupied:
                c_idx += 1
            colspan = min(int(td.get('colspan', 1)),50)
            rowspan = min(int(td.get('rowspan', 1)),50)
            for dr in range(rowspan):
                for dc in range(colspan):
                    grid[(r_idx + dr, c_idx + dc)] = td
                    if dr > 0 or dc > 0:
                        occupied[(r_idx + dr, c_idx + dc)] = True
            c_idx += colspan



    def extractData(td):
        data = list(td.stripped_strings)
        # print(data)
        if len(data) < 2:
            return None
        if 'Group: ' not in data[0]:
            return None

        group = data[0].split("Group: ")[1]
        type = data[1]
        if(len(data) > 2):
            instructor = data[2]
        else:
            instructor = "N/A"
        if(type == "Sec."):
            type = "Section"
        elif(type == "Lect."):
            type = "Lecture"
        else:
            type = "Lab"
        data = {
            "Group" : group,
            "Instructor": instructor,
            "Type": type,
            "Department": department,
            "Semester" : semester
        }
        return data


    if grid:
        max_row = max(r for r, c in grid.keys())
        max_col = max(c for r, c in grid.keys())

    cnt = 1
    subjects = []

    def search(data):
        for idx, subject in enumerate(subjects):
            if(data["Group"] == subject["Group"] and data["Type"] == subject["Type"] and data["Day"] == subject["Day"]):
                return idx
            
        return None

    for r in range(max_row+1):
        for c in range(max_col+1):
            cell = grid.get((r,c))
            data = extractData(cell)
            if(data):
                # print(cell)
                data["Course"] = f"{course_code} - {course_name}"
                data["Day"] = grid.get((r,0)).find("span").get_text(strip=True)
                data["start-time"] = c
                
                idx = search(data)

                
                if(idx is not None):
                    dupe = subjects[idx]
                    if(data["start-time"] > dupe["start-time"]):
                        dupe["end-time"] = data["start-time"]
                        subjects[idx] = dupe

                else:
                    subjects.append(data)

    # Adjusting start and end times because they don't align with column idx
    for subject in subjects:
        subject["start-time"] -= 1
        subject["end-time"] -= 1

        # print(subject)


    return subjects  
                    


def getOutput(default = "./schedule_maker/Schedules"):
    file_names = []
    for (dirpath, dirnames, filenames) in os.walk(default):
        file_names.extend(filenames)
        break

    all_courses = {}

    for file in file_names:
        filepath = os.path.join(default, file)
        current_course = extractSubjects(filepath)
        
        department = current_course[0]["Department"]
        course = current_course[0]["Course"]
        
        if department not in all_courses:
            all_courses[current_course[0]["Department"]] = {}

        all_courses[department][course] = current_course



    organized_courses = {}

    # Group Slots by group (a course's lecture/section/lab are now grouped)
    for department in all_courses.keys():
        for course_name, slots in all_courses[department].items():
            groups = {}
            for slot in slots:
                gp_id = slot["Group"]
                if gp_id not in groups:
                    groups[gp_id] = []
                groups[gp_id].append(slot)
            if department not in organized_courses:
                 organized_courses[department] = {}
            organized_courses[department][course_name] = groups


    attachMasks(organized_courses)
    return organized_courses
