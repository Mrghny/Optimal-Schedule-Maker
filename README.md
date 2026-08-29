# 📅 Optimal Schedule Maker

A schedule optimization tool for **AASTMT students** that generates all possible
conflict-free schedules from your selected courses and ranks them based on the selected preferences.

---

## How It Works

The app scrapes saved HTML pages from the AASTMT student portal, parses the schedule
tables into structured data, then uses a backtracking algorithm to generate every
possible conflict-free combination of your selected courses.

Each generated schedule is then scored based on your selected preferences and ranked
accordingly.

### Scoring Preferences
| Preference | How it scores |
|---|---|
| Minimum Days/Gaps | -10pts per day on campus, -3pts per gap |
| Balanced | Penalizes uneven day distribution |
| No 8am/4pm Slots | +5pts for no early/late slots |
| Free Days | +10pts if a selected day is free, -10pts if not |

---

## Versions

### 🌐 Flask Web App
A full UI where you select your courses and preferences and view the ranked schedules.

> **Note:** The included schedule files are samples. To use your own courses, save
> the schedule HTML page for each subject from the AASTMT student portal (`Ctrl+S`)
> and place them in the `schedule_maker/Schedules/` folder.

**Screenshots:**
<img width="1179" height="661" alt="image" src="https://github.com/user-attachments/assets/4c6ab689-713d-4e3d-8bb1-eac7ad300f7c" />

<img width="1181" height="797" alt="image" src="https://github.com/user-attachments/assets/8156baf1-b783-4e9b-a4d2-587e346fb152" />

<img width="1182" height="610" alt="image" src="https://github.com/user-attachments/assets/f14929b0-57ae-4550-92c3-84848fd3659b" />

#### Setup
```bash
git clone https://github.com/Mrghny/Optimal-Schedule-Maker/
cd Optimal-Schedule-Maker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask --app main run
```
Then open `http://localhost:5000` in your browser.

---

## Adding Your Own Schedules

1. Log in to the AASTMT student portal
2. Navigate to the schedule page for a subject
3. Press `Ctrl+S`and save
4. Change environment variables to set admin password
5. Upload them from the /upload route

---

## Tech Stack
- Python
- BeautifulSoup4 (scraping)
- Flask (web version)
- MongoDB
- Backtracking algorithm (schedule generation)
- Vanilla JS + HTML/CSS (frontend)
