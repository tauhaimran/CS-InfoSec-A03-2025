# Penetration Testing Training Lab

This repository contains a classroom-friendly capture-the-flag web
application. Students log in with their roll numbers, explore intentionally
vulnerable flows (SQL injection, stored XSS, CSRF), harvest flags, and submit
them to track progress.

## Stack

- Backend/UI: Flask 3 + Jinja templates + Bootstrap.
- Database: SQLite (`server/ctf_lab.db`).
- Auth: Cookie session keyed by roll number.
- Deployment: Works locally with `flask run` or on free Python hosts (Render,
  Railway, Deta, etc.). A `static/attacks` folder includes the example CSRF
  exploit page.

## Project Structure

```
info_assign/
├── memory-bank/               # Cursor context files
├── instructions.md            # Instructor-only exploitation guide
├── server/
│   ├── app.py                 # Flask application
│   ├── database.py            # SQLite helper
│   ├── init_db.py             # Schema + seeding script
│   ├── ctf_lab.db             # Generated database
│   ├── requirements.txt
│   ├── data/students_sample.csv
│   ├── templates/             # Jinja pages (landing, labs, flags)
│   └── static/                # CSS + CSRF attack demo
└── README.md
```

## Getting Started Locally

```powershell
cd server
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python init_db.py --csv data/students_sample.csv  # updates data while preserving progress
flask --app app run --debug
```

Visit <http://localhost:5000>, log in with a seeded roll number (see CSV), and
start exploiting the labs. Flags use the `FLAG{...}` format and are submitted
on the “Submit Flags” page inside the app.

### Seeding Real Students
You can use already created user: SEC23001 password: compass123
Provide your class roster as a CSV with columns:

```
roll_no,name,password,email
```

Then run `python init_db.py --csv my_students.csv`. Password hashes are
generated automatically.

## Vulnerability Modules

| Module | Location | Intentional Weakness |
| ------ | -------- | -------------------- |
| SQLi (Leaderboard) | `/sqli` | Unsafely concatenated leaderboard query |
| SQLi (Contracts)   | `/sqli/contracts` | Stacked UNION on executive contract search |
| SQLi (Blind)       | `/sqli/blind` | Vault console returning only granted/denied |
| XSS    | `/xss`   | Stored messages render with `|safe` | 
| CSRF   | `/csrf`  | No CSRF token, accepts cross-origin POST |

### Scoring System

Each flag grants a base number of points (SQLi blind is worth the most). The
score decays by 15 points for every subsequent submission of the same flag,
down to a minimum of 20 points. Cumulative totals are stored in `student_stats`
so the live scoreboard and admin console can show accurate history.

### Admin Console

- Default credentials (change in `init_db.py` or by updating the `admins` table):
  - Username: `root`
  - Password: `4ck-potato!`
- Routes:
  - `/admin/login` – sign in.
  - `/admin` – stats dashboard (student counts, capture feed, scoreboard).
  - `/admin/download-db` – download the SQLite file.
  - `/admin/reset-progress` – button on the admin dashboard that zeroes all captures/scores (irreversible).
- See `instructions.md` for full exploit walk-throughs and payload examples.

## Deploying to Free Hosts

Any host that runs Python/Flask works (Render, Railway, PythonAnywhere, Deta,
etc.). Typical steps:

1. Push this repo to your Git remote.
2. Create a new web service, set the start command to `flask --app app run
   --host=0.0.0.0 --port=$PORT`.
3. Configure environment variable `FLASK_APP=app`.
4. Run `python init_db.py --csv data/students_sample.csv` (add `--reset` only if
   you intentionally want to wipe existing progress).

For Streamlit-style platforms that only support Streamlit scripts, deploy the
Flask app via an alternative free service (Render/Railway) and share the public
URL with students.

## Next Steps

- Hook into your LMS/SSO for automated roster syncing.
- Expand with additional labs (IDOR, SSRF, auth bypass).
- Add instructor dashboard exporting submission logs for grading.

