# ExTerminus

Calendar-driven scheduling for pest control operations.  Fast to run, simple to deploy, opinionated where it counts.

> TL;DR: Python + Flask + SQLite. Create jobs (incl. REIs), assign technicians, lock out dates, and view everything on a compact month/day UI.

---

## Features

- Month + day views with multi-day job expansion
- Lock/unlock dates (admins/managers/techs)
- Role-based access (admin/manager/technician/sales)
- REI workflow
  - `rei_quantity` + `rei_zip` -> auto-resolves `rei_city_name`
  - Calendar badges: `REIs N - City [Tech]`
- Technician assignment + basic technician management
- Security hardening for v0.1.0
  - CSRF protection on all POST forms
  - SECRET_KEY enforcement via `.env`
  - Server-side role checks
  - Custom 404/500 error pages

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

---

## Known Limitations (v0.1.0)

- No full-text search or advanced filtering yet.
- No email/notification system.
- No migration; schema changes require a rebuild of the SQLite DB.
- Basic login rate-limiting TBD.

---

## Roadmap

- Search & filters (tech/date/type)
- Notifications (daily digest, lock alerts)
- Proper migration path (Alembic)
- Dockerfile + compose for one-command deployment

---

## Contributing

PRs welcome.  Keep commits scoped; prefer branches like `feat/*`, `fix/*`, `sec/*`, `docs/*`.

## License

This project is proprietary and not licensed for redistribution.  Please contact the repository owner for usage rights.
