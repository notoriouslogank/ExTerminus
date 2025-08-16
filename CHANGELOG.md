# Changelog

All notable changes to this project will be documented here.

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

- **BUG-1001 - Type Abbreviations:** Calendar now renders "REIs" properly (no more lonely "R").
- **BUG-1002 - Job Edit Auth:** Locked down edit/delete to authenticated users with proper roles; hid edit/delete controls in templates for non-authorized users. Direct hits to the endpoints now redirect/flash instead of succeeding.
- **BUG-1003 - Unauthorized Lock Toggle:** Lock/unlock is now enforced server-side with role checks; CSRF tokens in place so cross-site shenanigans can't flip days.
- **BUG-1004 - Edit Job Crash:** Corrected schema mismatch in edit flow (`type` -> `job_type`), tightened validation around date fields, and consolidated updates to prevent partial writes. Editing a job no longer explodes on save.
- **BUG-1006 - REIs:** Canonicalized fields to `rei_quantity`, `rei_zip`, `rei_city_name`; city name auto-resolves from ZIP; calendar badges show `REIs N - City` with ZIP fallback; queries updated (removed legacy `j.rei_qty`).
- **BUG-1007 - Clickable Days:** Restored day-cell navigation and added graceful handling for invalid dates.
- **BUG-1008 - Locked Day Failure:** No longer shows raw 403 page on error; user now receives a clear message and lands back on the selected day.
- **BUG-1014 - Time Off:** Technician dropdown now populates reliably (techs auto-sync when a user's role becomes *Technician* and on a tech user creation). Time-off form lists all techs and saves without error.
- **BUG-1019 - Too Many Jobs:** Month/day views no longer double-count multi-day jobs; explansion logic and date filters corrected; dates are now scrollable when jobs overflow cell size
- **BUG-1018 - End Before Start:** Server-side validation prevents end date earlier than start date; REI jobs normalized to single-day where appropriate.
- **BUG-1009 - Nameless Job:** Require non-empty title for non-REI jobs.
- **BUG-1026 - Fail to Delete:** Authorized job deletions now properly remove jobs from the database and display a success message; unauthorized attempts show a clear error message.
- **BUG-1027 / 1032 - REI Title (Unknown):** REI jobs now always display the title "REIs" in Day View instead of showing "(Unknown)" or an empty title.
- **BUG-1017 / BUG-1031 - Job Card Audit Log:** Job cards in Day View now display complete audit trails, including creator, creation date, last editor, and last modified date, with timestamps formatted in EST.
- Technician dropdown: auto-sync technicians on role change/user creation.
- CSRF: added tokens to all POST forms; friendly error handler.
- SECRET_KEY: fail-fast in prod; .env loading via python-dotenv.
- Inconsistent logger imports (`utils.logger` everywhere).
- Multiple small UI/consistency issues in day/month views.
- Error pages: custom 404/500 instead of Werkz-screams.

### Known/Deferred

- ZIP format validation (server-side) - deferred.
- Session access tidy (dict-style everywhere) - deferred.
