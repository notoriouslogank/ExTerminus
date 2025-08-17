# BUGS

_Source of truth for **open** bugs. Resolved items live in [Changelog](../CHANGELOG.md)._

## Legend

- **Severity:** P0 (blocker) · P1 (major) · P2 (minor) · P3 (nit)
- **Status:** Open · Triaged · In Progress · Blocked · Needs Verify

---

## Open Bugs (summary)
<!-- BUGS:SUMMARY START -->
| ID        | Title                   | Severity | Status        | Opened      | Owner | Target |
|-----------|-------------------------|----------|---------------|-------------|-------|--------|
| BUG-1005  | Multi-Day Arrows        | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1010  | Holidays not shown      | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1011  | Invalid Username/Passwo | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1013  | Time Picker             | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1015  | Chronology              | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1016  | Chronology II           | P2       | Open          | 2025-08-09  |       | v0.1.1 |
| BUG-1034  | Remove Time Off         | P3       | Open          | 2025-08-16  |       | v0.2.0 |
| BUG-1036  | MULTI-DAY ARROWS        | P1       | Open          | 2025-08-16  |       | v0.2.0 |
| BUG-1038  | Admin Delete Job        | P0       | Open          | 2025-08-16  |       | v0.2.0 |
<!-- BUGS:SUMMARY END -->
---

## Details
<!-- BUGS:DETAILS START -->

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

### BUG-1034 — Remove Time Off

- **Severity:** P3 · **Status:** Open · **Affects:** misc
- **Repro:** Create Time Off for a technician.
- **Expected/Actual:** Should have an option to REMOVE Time Off. / There is no method of removing Time Off once scheduled.
- **Notes:** -
- **Owner:**
- **Target:** v0.2.0

### BUG-1036 — MULTI-DAY ARROWS

- **Severity:** P1 · **Status:** Open · **Affects:** calendar
- **Repro:** Create a multi-day job and go to Calendar View.
- **Expected/Actual:** Should show an arrow for each day except the last one. / Shows an arrow only on the FIRST day of a multi-day job.
- **Notes:** -
- **Owner:**
- **Target:** v0.2.0

### BUG-1038 — Admin Delete Job

- **Severity:** P0 · **Status:** Open · **Affects:** jobs
- **Repro:** Login as admin and attempt to delete any job.
- **Expected/Actual:** Should be able to successfully delete any job as admin. / "You are not allowed to do that."
- **Notes:** -
- **Owner:**
- **Target:** v0.2.0

<!-- BUGS:DETAILS END -->
---

## Recently Resolved → see CHANGELOG.md
