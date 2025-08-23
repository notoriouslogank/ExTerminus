# ExTerminus

![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)

Calendar-driven scheduling for pest control operations.  Fast to run, simple to deploy, opinionated where it counts.

> TL;DR: Python + Flask + SQLite. Create jobs (incl. REIs), assign technicians, lock out dates, and view everything on a compact month/day UI.

**Docs:**[Quick Start](#quick-start-2-minutes) · [Common Tasks](#common-tasks) · [Configuration](#configuration) · [Known Limitations](#known-limitations) · [Bugs](./BUGS.md) · [Changelog](./CHANGELOG.md) · [Roadmap](#roadmap)

---

## Features

- Month + day views with multi-day job expansion
- Lock/unlock dates (admins/managers/techs)
- Role-based access (admin/manager/technician/sales)
- REI workflow
  - `rei_quantity` + `rei_zip` -> auto-resolves `rei_city_name`
  - Calendar badges: `REIs N - City [Tech]`
- Technician assignment
  - **Two-Man Jobs**: assign both technicians at once; visible to both; counted once; displays **"Two Man"**
  - Consistent display: technicians shown as **F.Lastname**
- Time Off
  - Add Time Off from Day View
  - OFF entries rendered on Day & Calendar views
- Security hardening
  - CSRF protection on all POST forms
  - Forced password reset on first login
  - SECRET_KEY enforcement via `.env`
  - Server-side role checks
  - Custom 404/500 error pages

---

## New in v0.2.0

- Lock/unlock dates now show "Last edited by NAME at TIMESTAMP (EST)" display for better auditing
- Forced password reset on first login
- Two techs can be assigned to the same job, creating support for Two-Man jobs
- Multi-day job fixes (calendar and day_views)

---

## Tech Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite
- **Frontend:** HTML + Jinja2 templates, CSS, minimal JavaScript
- **Logging:** Python `logging` module
- **Auth:** `werkzeug.security` password hashing

---

## Quick Start (2 minutes)

### Requirements

- Python 3.11+ recommended
- `pip` and `venv`

### 1) Clone & install

```bash
git clone https://github.com/notoriouslogank/ExTerminus.git && cd ExTerminus
python3 -m venv .venv
# Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 2) Configure .env

```bash
cp .env.example .env
# Generate a proper secret:
python3 - <<'PY'
import secrets; print("SECRET_KEY="+secrets.token_hex(32))
PY
# Paste into .env (replace placeholders)
```

`.env.example` fields:

```bash
SECRET_KEY=change_me_in_prod
SESSION_COOKIE_SECURE=0 # set to 1 in production behind HTTPS
```

### 3) Initialize DB (first run)

The app will create the DB on first run and seed a default admin if none exists.
If you ever need to force init:

```bash
python3 - <<'PY'
from exterminus.db import init_db; init_db()
print("DB initialized.")
PY
```

### 4) Run

```bash
export FLASK_APP=app.py
# Linux
export FLASK_ENV=development
# Windows PowerShell
$env:FLASK_ENV="development"

flask run

# On first run, open http:127.0.0.1:5000
# Default admin login:
username: admin
password: changeme # will require reset

```

Open <http://127.0.0.1:5000>

Default admin (first run only):
`username: admin` / `password: changeme`
You'll be prompted to change password on first login.

---

## Common Tasks

### Create a REI job

1. Add Job -> select REIs.
2. Set quantity and ZIP (5 digits). City auto-populates.
3. (Optional) Assign a Technician - dropdown pulls from Technicians.

### Add a Technician

- From Admin Panel: set a user's role to Technician -> they're auto-added to the technicians list.
- Or seed directly in DB:

```sql
INSERT INTO technicians (name) VALUES ('Alice');
```

### Lock a Day

- Day view -> Lock/Unlock.  Locked dates reject new jobs.

### Create a Two-Man Job

1. **Add Job** -> choose a job type.
2. In **Technician**, select **Two Man**.
3. Save. The job appears for both techs and shows **Two Man** on cards.

### Add Time Off from Day View

- Open the Day view -> **+ Add Time Off** -> choose tech & date -> save.
- Time Off shows as an **OFF** card on both Day & Calendar views.

> Please note that Time Off does not yet prevent scheduling jobs for the OFF tech

---

## Configuration

- `SECRET_KEY` must be set in prod (the app fails fast if not).
- Cookies:
  - `SESSION_COOKIE_HTTPONLY=True`
  - `SESSION_COOKIE_SAMESITE="Lax"`
  - `SESSION_COOKIE_SECURE=1` in production (HTTPS)

---

## Development Notes

- CSRF is enabled via Flask-WTF; every POST form includes a hidden token.
- SQLite pragmas set: `foreign_keys=ON`, `journal_mode=WAL`.
- Schema (jobs): `rei_quantity (INT)`, `rei_zip (TEXT)`, `rei_city_name (TEXT)`.
- Lightweight SQL migrations (plain `.sql` files) may be included; no tool-managed migrations yet.

---

## Known Limitations

- Two-man is the ceiling (no 3+ tech assignment yet).
- Time Off does not yet block assigning that tech to other jobs (planned).
- No full-text search or advanced filtering yet.
- No email/notification system.
- Lightweight SQL migrations only; no Alembic tooling.
- Basic login rate-limiting TBD.
- Multi-day arrow behavior still being refinded - see [BUG-1036](./BUGS.md#bug-1036--multi-day-arrows).

---

## Roadmap

- Admin dashboard improvements (audit logs)
- Technician time off: full workflow (approvals, restrictions, deletions, etc.)
- Audit logging
- Mobile polish
- Support for photo attachments in job Notes
- Search & filters (tech/date/type)
- Notifications (daily digest, lock alerts)
- Proper migration path (Alembic)
- Dockerfile + compose for one-command deployment

---

## Contributing

PRs welcome.  Keep commits scoped; prefer branches like `feat/*`, `fix/*`, `sec/*`, `docs/*`.

## License

Copyright © 2025 Logan Aker (ExTerminus Project)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to view, study, and adapt portions of the Software for personal or educational purposes, subject to the following conditions:

1. No Production / Commercial Use Without Consent
   The Software may not be used, deployed, or distributed for commercial purposes -- including use in business operations -- without prior written permission from the copyright holder.

2. Attribution
   Derivative works or references to the Software must provide attribution to the ExTerminus Project.

3. No Warranty
   The Software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, or non-infringement.  In no even shall the authors or copyright holders be liable for any claim, damages, or other liability, arising from, out of, or in connection with the Software.

4. Employer Disclaimer
   This project was created independently and is not sponsored, endorsed, or owned by any employer or affiliated organization.  All rights remain with the author.
