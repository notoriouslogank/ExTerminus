# BUGS

_Source of truth for **open** bugs. Resolved items live in **CHANGELOG.md** (v0.1.0)._

## Legend

- **Severity:** P0 (blocker) · P1 (major) · P2 (minor) · P3 (nit)
- **Status:** Open · Triaged · In Progress · Blocked · Needs Verify

---

## Open Bugs (summary)
<!-- BUGS:SUMMARY START -->
| ID        | Title                   | Severity | Status        | Opened      | Owner | Target |
|-----------|-------------------------|----------|---------------|-------------|-------|--------|
| BUG-1022  | Bug Report Format       | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1020  | Two Man Jobs            | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1017  | Missing Audit Trail     | P1       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1016  | Chronology II           | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1015  | Chronology              | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1013  | Time Picker             | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1012  | Force Password Update   | P1       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1011  | Invalid Username/Passwo | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1010  | Holidays not shown      | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1005  | Multi-Day Arrows        | P2       | Open          | 2025-08-09  |       | v0.1.1 |
<!-- BUGS:SUMMARY END -->
---

## Details
<!-- BUGS:DETAILS START -->
### BUG-1022 — Bug Report Format

- **Severity:** P2 · **Status:** Open · **Affects:** BUGS.md formatting flow
- **Repro:** Add a bug entry → formatting degrades.
- **Expected/Actual:** Keeps structure / loses structure.
- **Notes:** Adopt the template at bottom of this file for new entries.

### BUG-1020 — Two Man Jobs

- **Severity:** P2 · **Status:** Open · **Affects:** job creation
- **Repro:** Create a job that needs 2 techs → can’t select >1.
- **Expected/Actual:** Toggle or multi-select / single tech only.
- **Notes:** Likely needs `jobs_technicians` join table + UI multi-select.

### BUG-1017 — Missing Audit Trail

- **Severity:** P1 · **Status:** Open · **Affects:** day view job cards
- **Repro:** Create/edit jobs → no creator / last modified shown.
- **Expected/Actual:** Audit fields visible / absent.
- **Notes:** DB already has `created_by`, `last_modified`, `last_modified_by`; just render + ensure they’re populated on edit.

### BUG-1016 — Chronology II

- **Severity:** P2 · **Status:** Open · **Affects:** day view ordering
- **Repro:** Multiple timed jobs same day → order is creation-time.
- **Expected/Actual:** Sort by timed first, then ascending time / arbitrary.
- **Notes:** Normalize/parse times; ORDER BY parsed time, then title.

### BUG-1015 — Chronology

- **Severity:** P2 · **Status:** Open · **Affects:** month/day views
- **Repro:** Add multiple time-ranged jobs → ordering inconsistent.
- **Expected/Actual:** Timed at top, ascending / arbitrary.
- **Notes:** Same fix path as 1016; add composite sort.

### BUG-1013 — Time Picker

- **Severity:** P2 · **Status:** Open · **Affects:** job form
- **Repro:** Click time input → no picker.
- **Expected/Actual:** Time widget / plain text box.
- **Notes:** Use `<input type="time">` or a JS timepicker; validate server-side.

### BUG-1012 — Force Password Update

- **Severity:** P1 · **Status:** Open · **Affects:** auth
- **Repro:** Create/reset user → no forced change on first login.
- **Expected/Actual:** Redirect to change-password / normal flow.
- **Notes:** Honor `force_password_change` flag after login.

### BUG-1011 — Invalid Username/Password

- **Severity:** P2 · **Status:** Open · **Affects:** login UX
- **Repro:** Wrong creds → message is tiny/hidden.
- **Expected/Actual:** Prominent flash box / subtle text.
- **Notes:** Style flash; consider small rate-limit.

### BUG-1010 — Holidays

- **Severity:** P2 · **Status:** Open · **Affects:** month view
- **Repro:** View month with federal holiday → not shown.
- **Expected/Actual:** Holiday label in cell / nothing.
- **Notes:** Static list or `holidays` lib; render in cell header.

### BUG-1005 — Multi-Day Arrows

- **Severity:** P2 · **Status:** Open · **Affects:** month view UX
- **Repro:** Multi-day job → arrow only on first day.
- **Expected/Actual:** Arrow on each day / first day only.
- **Notes:** Render prefix/suffix arrows based on start/end.
<!-- BUGS:DETAILS END -->
---

## Recently Resolved → see CHANGELOG.md (v0.1.0)

- **BUG-1002** Job Edit Auth
- **BUG-1003** Unauthorized Lock Toggle
- **BUG-1004** Edit Job Crash
- **BUG-1006** REIs
- **BUG-1007** Clickable Days
- **BUG-1009** Nameless Job
- **BUG-1014** Time Off
- **BUG-1018** End Before Start
- **BUG-1019** Too Many Jobs
- **BUG-1001** Type Abbreviations
