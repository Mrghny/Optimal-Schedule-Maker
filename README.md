# 📅 Optimal Schedule Maker

A schedule optimization tool for **AASTMT students** that generates all possible
conflict-free schedules from your selected courses and ranks them based on your preferences.

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
| Preferred Lecturer | +5pts per session with that lecturer |

---

## Versions

### 🌐 Flask Web App
A full UI where you select your courses and preferences and view the ranked schedules.

> **Note:** The included schedule files are samples. To use your own courses, save
> the schedule HTML page for each subject from the AASTMT student portal (`Ctrl+S`)
> and place them in the `schedule_maker/Schedules/` folder.

**Screenshots:**
<img width="1319" height="565" alt="image" src="https://github.com/user-attachments/assets/ef4466e4-57ff-424c-be49-6355f8c77a6b" />

<img width="1319" height="603" alt="image" src="https://github.com/user-attachments/assets/fe57e8a3-2767-4942-9b2d-6cda72d8d7b7" />

<img width="1319" height="599" alt="image" src="https://github.com/user-attachments/assets/67bde71c-142e-4b1f-9bde-1e9b66be2bf2" />

#### Setup
```bash
git clone https://github.com/<USERNAME>/<REPO>.git
cd <REPO>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask --app main run
```
Then open `http://localhost:5000` in your browser.

---

### 💻 CLI Version
A standalone terminal version with 7 sample subjects included to try out immediately.
Outputs a paginated `schedules.html` file with all ranked schedule options.

#### Download
[⬇️ Download ScheduleMaker.exe](https://github.com/<USERNAME>/<REPO>/releases/latest/download/ScheduleMaker.exe)

> Windows only. On first run, click **"More info" → "Run anyway"** if Windows Defender
> shows a warning.

#### Or run from source
```bash
git clone https://github.com/<USERNAME>/<REPO>.git
cd <REPO>/cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## Adding Your Own Schedules

1. Log in to the AASTMT student portal
2. Navigate to the schedule page for a subject
3. Press `Ctrl+S` and save the **full webpage** (not just HTML)
4. Place the saved file in the `Schedules/` folder
5. Run the app

---

## Tech Stack
- Python
- BeautifulSoup4 (scraping)
- Flask (web version)
- Backtracking algorithm (schedule generation)
- Vanilla JS + HTML/CSS (frontend)
