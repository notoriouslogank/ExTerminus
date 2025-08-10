# ExTerminus

**ExTerminus** is a Flask-based job scheduling and calendar management application designed for pest control operations but adaptable to any field service workflow.
It supports multi-day jobs, technician assignments, time off tracking, role-based authentication, and an audit trail for accountability.

---

## Features

- **Interactive Calendar View** - Month and day view with click-through to job details.
- **Role-Based Access Control** - Limit sensitive actions (locking days, editing jobs) to authorized roles.
- **Job Management**
  - Multi-day jobs with optional arrows in calendar view.
  - REIs with qunatity, city, and technician display.
  - Optional "two techs" designation.
- **Time Off Tracking** - Record technician unavailability alongside job assignments.
- **Authentication** - Secure login with password hashing and first-login password change enforcement.
- **Audit Trail** - See who created and last modified each job, with timestamps.
- **Responsive UI** - Dark mode styling by default, designed for mobile and desktop use.

---

## Tech Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite
- **Frontend:** HTML + Jinja2 templates, CSS, minimal JavaScript
- **Logging:** Python `logging` module
- **Auth:** `werkzeug.security` password hashing

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/notoriouslogank/ExTerminus.git
cd exterminus
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Init the database

```bash
python3 -m db.py
```

## Running the Application

### Development Server

```bash
flask --app app run --debug
```

### Access in Browser

```bash
http://127.0.0.1:5000
```

### Ngrok

Forward to `ngrok` (sold separately) to publish online.

This works best inside a multiplexed terminal -- like `tmux` -- with two windows.  On one, you startup the app; then, you launch `ngrok` with:

```bash
ngrok http 5000
```

## License

This project is proprietary and not licensed for redistribution.  Please contact the repository owner for usage rights.

## Changelog

See BUGS.md for a list of tracked and resolved issues.
