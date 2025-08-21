# Changelog

All notable changes to this project will be documented here.

## [0.2.0] - 2025-08-19

### Fixed

- **BUG-1012 - Force Password Update**
  Enforce first-login password reset: added `users.must_reset_password` + `last_password_change`, gated app to `/force-password-reset`, and wired CSRF corrrectly.
- **BUG-1020 - Two Man Jobs**
  Implemented two-man assignment via `jobs.two_man`; create/edit routes handle `__BOTH__`; tech-filtered queries include `OR two_man=1`; displays reflect dual assignment.
- **BUG-1037 - Two-Man Display**
  Month & day views now render "Two Man" on job cards; calendar query selects `jobs.two_man` and binds month params correctly.
- **BUG-1035 - Missing Time Off (Day View)**
  Day view includes "+ Add Time Off" button and shows OFF entries as cards.
- **BUG-1033 - Inconsistent Assignment Formatting**
  Technician display standardized: non-two-man jobs render **F.Lastname** consistently on calendar and day views; REI initials logic preserved; "Two Man" overrides initials where applicable.
- **BUG-1041 - Multi-Day Arrow Alignment**
  Fixed calendar rendering so multi-day jobs correctly span across cells without double and/or missing arrows or overflow glitches.
- Safer logout username logging (avoid constructing dict in `session.get` call).
- Typo fixes and consistent flash messaging.

### Improvements

- Day view job cards: consistent casing/spacing; standardized audit block styling.
- Calendar view: non-REI cards show technician label in footer alongside price/arrow.
- Version footer now displays across all templates; styled to be small, centered, and white.

### Internal

- Fixed SQLite3 binding error in calendar month query (bound `month_start`/`month_end`).

### Added

- Holiday display on calendar view using the `holidays` Python library (US holidays).
- New CSS styling for holiday dates to visually distinguish them on the calendar.
- Backend utility function `holidays_for_month(year, month)` in `utils/holidays_util.py` for retrieving holiday names/dates.
- Integration of holiday data into `calendar_routes` so holidays are passed to the template.
- When assigning technicians to a job, there is now an option to select 'Two Men' rather than an idividual technician
- Google-style docstrings across core modules for clearer IDE hovers and internal docs:
  - `utils/config.py`, `utils/decorators.py`, `utils/holidays_util.py`, `utils/logger.py`
  - `routes/__init__.py`
  - `app.py` (including `fmt_ts`, error handlers, context processors)

### Changed

- Updated `index.html` calendar template to highlight holidays with a distinct style.
- Updated `BUGS.md` to include more known issues
- Standardize password-reset flag field name to `must_reset_password` (previously `force_password_change`) in code and DB DDL.
  - Admin "reset password to changme" now explicitly sets `must_reset_password=1`.
  - Aligns with session key `must_change_pw` and auth flow.

### Developer Experience

- isort + light import normalization in touched files.

### Migration (SQLite)

If your existing DB has **both** columns:

```sql
UPDATE users
SET must_reset_password = COALESCE(must_reset_password, force_password_change, 0);

ALTER TABLE users DROP COLUMN force_password_change; -- If this fails, use rebuild pattern below
```

If your DB only has the old column:

```sql
ALTER TABLE users RENAME COLUMN force_password_change TO must_reset_password;
```

If `DROP COLUMN` isn't supported, rebuild the table:

```sql

BEGIN TRANSACTION;

CREATE TABLE users_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT,
  last_name TEXT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'tech',
  must_reset_password INTEGER NOT NULL DEFAULT 0
);

INSERT INTO users_new (id, first_name, last_name, username, password, role, must_reset_password)
SELECT id, first_name, last_name, username, password, role, COALESCE(must_reset_password, force_password_change, 0)
FROM users;

DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

COMMIT;
```

After migration, verify:

```sql
PRAGMA table_info(users);
SELECT id, username, must_reset_password FROM users LIMIT 10;
```

### Open Issues

- [Bugs](/docs/BUGS.md)

## [0.1.0] - 2025-08-15

### Added

- CSRF protection for all POST forms (Flask-WTF).
- `.env` support (python-dotenv); fail-fast on missing/unsafe `SECRET_KEY` in production
- Role-based route enforcement (`@role_required`).
- Technician auto-sync: when a user becomes a Technician, they're added to the technicians list.
- Custom 404/500 error pages.
- REI workflow:
  - Canonical fields: `rei_quantity`, `rei_zip`, `rei_city_name`.
  - Calendar badges display `REIs N - City [Tech]`.

### Changed

- Standardized REI schema/field names across routes, queries, and templates.
- Calendar queries return technician name and REI fields for display.

### Fixed

- **BUG-1001 - Type Abbreviations**
  Calendar now renders "REIs" properly (no more lonely "R").
- **BUG-1002 - Job Edit Auth**
  Locked down edit/delete to authenticated users with proper roles; hid edit/delete controls in templates for non-authorized users. Direct hits to the endpoints now redirect/flash instead of succeeding.
- **BUG-1003 - Unauthorized Lock Toggle**
  Lock/unlock is now enforced server-side with role checks; CSRF tokens in place so cross-site shenanigans can't flip days.
- **BUG-1004 - Edit Job Crash**
  Corrected schema mismatch in edit flow (`type` -> `job_type`), tightened validation around date fields, and consolidated updates to prevent partial writes. Editing a job no longer explodes on save.
- **BUG-1006 - REIs**
  Canonicalized fields to `rei_quantity`, `rei_zip`, `rei_city_name`; city name auto-resolves from ZIP; calendar badges show `REIs N - City` with ZIP fallback; queries updated (removed legacy `j.rei_qty`).
- **BUG-1007 - Clickable Days**
  Restored day-cell navigation and added graceful handling for invalid dates.
- **BUG-1008 - Locked Day Failure**
  No longer shows raw 403 page on error; user now receives a clear message and lands back on the selected day.
- **BUG-1014 - Time Off**
  Technician dropdown now populates reliably (techs auto-sync when a user's role becomes *Technician* and on a tech user creation). Time-off form lists all techs and saves without error.
- **BUG-1019 - Too Many Jobs**
  Month/day views no longer double-count multi-day jobs; explansion logic and date filters corrected; dates are now scrollable when jobs overflow cell size
- **BUG-1018 - End Before Start**
  Server-side validation prevents end date earlier than start date; REI jobs normalized to single-day where appropriate.
- **BUG-1009 - Nameless Job**
  Require non-empty title for non-REI jobs.
- **BUG-1026 - Fail to Delete:** Authorized job deletions now properly remove jobs from the database and display a success message; unauthorized attempts show a clear error message.
- **BUG-1027 / 1032 - REI Title (Unknown)**
  REI jobs now always display the title "REIs" in Day View instead of showing "(Unknown)" or an empty title.
- **BUG-1017 / BUG-1031 - Job Card Audit Log**
  Job cards in Day View now display complete audit trails, including creator, creation date, last editor, and last modified date, with timestamps formatted in EST.
- Technician dropdown: auto-sync technicians on role change/user creation.
- CSRF: added tokens to all POST forms; friendly error handler.
- SECRET_KEY: fail-fast in prod; .env loading via python-dotenv.
- Inconsistent logger imports (`utils.logger` everywhere).
- Multiple small UI/consistency issues in day/month views.
- Error pages: custom 404/500 instead of Werkz-screams.

### Known/Deferred

- ZIP format validation (server-side) - deferred.
- Session access tidy (dict-style everywhere) - deferred.
