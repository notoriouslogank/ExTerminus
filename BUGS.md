# BUGS

## Open

- [BUG-1022] Bug Report Format
  Opened: 2025-08-09 • Branch: `fix/bug-1022-bug-report-format`
- [BUG-1020] Two Man Jobs
  Opened: 2025-08-09 • Branch: `fix/bug-1020-two-man-jobs`
- [BUG-1017] Missing Audit Trail
  Opened: 2025-08-09 • Branch: `fix/bug-1017-missing-audit-trail`
- [BUG-1016] Chronology II
  Opened: 2025-08-09 • Branch: `fix/bug-1016-chronology-ii`
- [BUG-1015] Chronology
  Opened: 2025-08-09 • Branch: `fix/bug-1015-chronology`
- [BUG-1014] Time Off
  Opened: 2025-08-09 • Branch: `fix/bug-1014-time-off`
- [BUG-1013] Time Picker
  Opened: 2025-08-09 • Branch: `fix/bug-1013-time-picker`
- [BUG-1012] Force Password Update
  Opened: 2025-08-09 • Branch: `fix/bug-1012-force-password-updat`
- [BUG-1011] Invalid Username Password
  Opened: 2025-08-09 • Branch: `fix/bug-1011-invalid-username-pas`
- [BUG-1010] Holidays
  Opened: 2025-08-09 • Branch: `fix/bug-1010-holidays`
- [BUG-1009] Nameless Job
  Opened: 2025-08-09 • Branch: `fix/bug-1009-nameless-job`
- [BUG-1008] Locked Day Failure
  Opened: 2025-08-09 • Branch: `fix/bug-1008-locked-day-failure`
- [BUG-1005] Multi-Day Arrows
  Opened: 2025-08-09 • Branch: `fix/bug-1005-multi-day-arrows`
- [BUG-1004] Edit Job Crash
  Opened: 2025-08-09 • Branch: `fix/bug-1004-edit-job-crash`
- [BUG-1002] Job Edit Auth
  Opened: 2025-08-09 • Branch: `fix/bug-1002-job-edit-auth`
- [BUG-1001] Type Abbreviations
  Opened: 2025-08-09 • Branch: `fix/bug-1001-type-abbreviations`

## Resolved

- [BUG-1003] Unauthorized Lock Toggle
  Opened: 2025-08-09 • Branch: `fix/bug-1003-unauthorized-lock-to`
- [BUG-1019] Too Many Jobs
  Opened: 2025-08-09 • Branch: `fix/bug-1019-too-many-jobs`
- [BUG-1018] End Before Start
  Opened: 2025-08-09 • Branch: `fix/bug-1018-end-before-start`
- [BUG-1006] REIs
  Opened: 2025-08-09 • Branch: `fix/bug-1006-reis`
- [BUG-1007] Clickable Days
  Opened: 2025-08-09 • Branch: `fix/bug-1007-clickable-days`

---

### BUG-1001 - Type Abbreviations

**Area:** calendar
**Severity:** Low
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Type Abbreviations

#### Steps to Reproduce

Create a job (for instance, 10 REIs on a date); view the calendar.

#### Expected

Should abbreviate to "REIs" in the job card

#### Actual

Abbreviates to "R" on the job card

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1002 - Job Edit Auth

**Area:** jobs
**Severity:** High
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Job Edit Auth

#### Steps to Reproduce

While logged out, click a date in the calendar view to open the day view; look at the options available.

#### Expected

An unauth'd user shouldn't be able to edit/delete jobs.

#### Actual

Unauth'd user is able to edit/delete individual jobs.

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1003 - Unauthorized Lock Toggle

**Area:** auth
**Severity:** Critical
**Status:** Fixed
**Opened:** 2025-08-09
**Fixed:** 2025-08-10

#### Summary

Logged-out users (or users without proper role) could lock/unlock days via direct HTTP route access.

#### Steps to Reproduce

While logged out, attempt to toggle Lock/Unlock Day.

#### Expected

Lock/Unlock Day toggle should not appear at all.

#### Actual

Lock/Unlock Day toggle is clickable, and works.

#### Resolution

- Added `@login_required` and `@role_required('admin', 'manager', 'technician')` to `toggle_lock`.
- Updated templates to hide lock/unlock controls from unauthorized users.
- Route now redirects to login if unauthenticated and blocks with a flash/redirect if role is insufficient.

#### Verification

- Logged-out user -> redirected to login when hitting the route or UI.
- Logged-in non-admin/manager -> sees no toggle; direct route access flashes "not allowed" and redirects.
- Admin/manager/technician -> can toggle successfully from the UI.

#### Fix PR

- PR: bug-1003-unauthorized-lock-to
- Fix commit: `3304e9a`
- Released in: dev (pending)

---

### BUG-1004 - Edit Job Crash

**Area:** jobs
**Severity:** Critical
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Edit Job Crash

#### Steps to Reproduce

While logged in, attempt to Edit Job via day-view job card.

#### Expected

Edit Job page should open, Save Changes should redirect to the calendar view.

#### Actual

Crash when Save Changes is clicked.

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1005 - Multi-Day Arrows

**Area:** calendar
**Severity:** Low
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Multi-Day Arrows

#### Steps to Reproduce

Create a multi-day job, then view it on the calendar view.

#### Expected

Should print an arrow (->) on each day of a multi-day job.

#### Actual

Only prints an arrow on the first day.

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1006 - REIs

**Area:** calendar
**Severity:** High
**Status:** Fixed
**Opened:** 2025-08-09
**Fixed:** 2025-08-09

#### Summary

REI jobs displayed incorrectly in calendar view, showing "R - Unknown" instead of proper REIs label, quantity, and city.

#### Steps to Reproduce

Add REIs of any quantity and with any zipcode to any day.

#### Expected

Calendar view should display "REIs" - "Technician" - "Quantity" - "City Name".

#### Actual

Calendar simply displays "R - Unknown" for the created job(s)

#### Resolution

- Normalized job type check in `index.html` to accept both `"rei"` and `"reis"` (and handle `job.job_type`).
- Corrected display logic to show REIs tag, quantity, city, and technician.
- Removed stray closing `</div>` that broke layout inside REIs branch.

#### Verification

- REI jobs now display correct label, quantity, city, and technician initials.
- Non-REI jobs unaffected.

#### Fix PR

- PR: fix/bug-1018-end-before-start
- Fix commit: `feffa64`
- Released in: dev (pending)

---

### BUG-1007 - Clickable Days

**Area:** calendar
**Severity:** Low
**Status:** Fixed
**Opened:** 2025-08-09
**Fixed:** 2025-08-09

#### Summary

Only the date number inside a day cell was clickable to open the day view.

#### Steps to Reproduce

On calendar view, click anywhere in a date cell except directly on the date numerals.

#### Expected

Should be able to click ANYWHERE on a date to open the day view

#### Actual

Must click on the actual date numerals

#### Resolution

- Added `.cell-overlay` anchor spanning the full calendar cell in `index.html`.
- Updated CSS to make the overlay block-level and cover the cell without breaking inner controls.
- Ensured overlay inherits styles to keep the calendar appearance unchanged.

#### Verification

- Clicking anywhere in a cell now opens the day view.
- Existing links/buttons inside the cell (e.g., job edit, lock toggles) remain functional.

#### Fix PR

- PR: fix/bug-1018-end-before-start
- Fix commit: `feffa64`
- Released in: dev (pending)

---

### BUG-1008 - Locked Day Failure

**Area:** auth
**Severity:** Medium
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Locked Day Failure

#### Steps to Reproduce

While logged in as any user, attempt to add a job to a locked day.

#### Expected

Should fail, but show a popup.

#### Actual

Redirects to a poorly-styled flashbang page.

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1009 - Nameless Job

**Area:** jobs
**Severity:** High
**Status:** Fixed
**Opened:** 2025-08-09
**Fixed:** 2025-08-09

#### Summary

Jobs could be created without a title, resulting in empty or unclear job cards in the calendar and day views.

#### Steps to Reproduce

Leave Title field blank while creating a new job.

#### Expected

Title should be a required field.

#### Actual

Job creation proceeds with no title provided.

#### Resolution

- Updated `add_job` and `edit_job` in `job_routes.py` to require non-empty title for all non-REI jobs.
- Trimmed whitespace before validation to prevent titles that were only spaces.
- Left REIs exempt from title requirement, as they display standardized info.

#### Verification

- Attempting to create/edit non-REI job with blank title -> blocked, flash message shown.
- Creating/editing REI jobs without a title works and displays standardized label.
- Valid titled jobs save and display correctly.

#### Fix PR

- PR: fix/bug-1018-end-before-start
- Fix commit: `feffa64`
- Released in: dev (pending)

---

### BUG-1010 - Holidays

**Area:** calendar
**Severity:** Low
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Holidays

#### Steps to Reproduce

View calendar view on a month inlcuding a Federal holiday

#### Expected

Should show the holiday on the date

#### Actual

Holidays don't appear on the calendar view.

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1011 - Invalid Username Password

**Area:** auth
**Severity:** Low
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Invalid Username Password

#### Steps to Reproduce

Provide incorrect credentials during login

#### Expected

Should flash a box/message re: invalid credentials

#### Actual

Displays text in upper left -- hard to notice.

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1012 - Force Password Update

**Area:** auth
**Severity:** High
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Force Password Update

#### Steps to Reproduce

Create a new user or reset a current user's password as admin

#### Expected

Should require password change upon first login

#### Actual

Never requires password change

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1013 - Time Picker

**Area:** jobs
**Severity:** Low
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Time Picker

#### Steps to Reproduce

Provide a time or time range for a job

#### Expected

Should open a time picker similar to the date picker

#### Actual

Does not open time picker; takes input as text

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1014 - Time Off

**Area:** jobs
**Severity:** High
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Time Off

#### Steps to Reproduce

Attempt to Add Time Off

#### Expected

Dropdown list should list all technicians

#### Actual

Dropdown does not show any technicians, and thus unable to add Time Off

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1015 - Chronology

**Area:** calendar
**Severity:** Medium
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Chronology

#### Steps to Reproduce

Add multiple jobs with a timeframe to a given day

#### Expected

Should place all timed jobs at top and order them by time in ascending order

#### Actual

Places the timed jobs in an arbitrary order

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1016 - Chronology II

**Area:** jobs
**Severity:** Medium
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Chronology II

#### Steps to Reproduce

Create multiple timed jobs on the same date

#### Expected

In day view, jobs should be sorted by timed jobs (at top) and then in ascending order of timeframe

#### Actual

Jobs appear in order they were created.

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1017 - Missing Audit Trail

**Area:** jobs
**Severity:** High
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Missing Audit Trail

#### Steps to Reproduce

Create any number of jobs

#### Expected

Job cards (day view) should include information about the job Creator, last modified, etc.

#### Actual

Contains no audit information on any job card

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

### BUG-1018 - End Before Start

**Area:** calendar
**Severity:** High
**Status:** Fixed
**Opened:** 2025-08-09
**Fixed:** 2025-08-09

#### Summary

Jobs could be created or edited with an end date earlier than the start date, leading to incorrect rendering and data inconsistencies.

#### Steps to Reproduce

Create a new job whose start date is after its' end date

#### Expected

Should display an error message and not allow user to proceed

#### Actual

Creates the job on the start date only

#### Resolution

- Added `_parse_date` helper to validate and normalize start/end dates in `job_routes.py`.
- Updated `add_job` and `edit_job` routes to:
  - Require valid start date.
  - Block end date earlier than start date.
  - Store dates in ISO `YYYY-MM-DD` format.
- Added fallback in `move_job` to handle jobs with no end date.

#### Verification

- Attempt to create/edit job with end < start -> blocked, flash message shown.
- Valid start/end saves correctly and displays in multi-day calendar view.
- Jobs without end date can still be moved without errors.

#### Fix PR

- PR: fix/bug-1018-end-before-start
- Fix commit: `feffa64`
- Released in: dev (pending)

---

### BUG-1019 - Too Many Jobs

**Area:** calendar
**Severity:** Medium
**Status:** Fixed
**Opened:** 2025-08-09
**Fixed:** 2025-08-09

#### Summary

Calendar day cells stretched vertically when more than ~6 jobs were present, making the calendar hard to scan.

#### Steps to Reproduce

Add 7+ jobs to a single date in calendar view

#### Expected

The list of job cards on the calendar view should be scrollable

#### Actual

The date on the calendar view continues to grow larger vertically

#### Resolution

- Wrapped per-day job list in `.jobs` container in `index.html`.
- Added CSS max-height and `overflow-y:auto` to `.calendar-cell .jobs`.
- Ensured date and holiday labels remain visible above scroll area.

#### Verification

- Added 10+ jobs to a date -> cell height remains consistent and scroll bar appears for jobs
- Other day cells unaffected.
- Holiday/date display remains fixed at top.

#### Fix PR

- PR: fix/bug-1018-end-before-start
- Fix commit: `feffa64`
- Released in: dev (pending)

---

### BUG-1020 - Two Man Jobs

**Area:** jobs
**Severity:** Low
**Status:** Open
**Opened:** 2025-08-09

#### Summary

Two Man Jobs

#### Steps to Reproduce

Add a job that requires multiple technicians

#### Expected

Should be able to add "2-man" toggle to a given job when creating it

#### Actual

No ability to add more than one technician to a given job

#### Notes / Suspicions

-

#### Fix PR

- PR: -
- Fix commit: -
- Released in: -

---

## BUG-1022 - Bug Report Format
**Area:** misc
**Severity:** Medium
**Status:** Open
**Opened:** 2025-08-09

### Summary
Bug Report Format

### Steps to Reproduce
Simply add a bug.

### Expected
Retain formatting.

### Actual
Doesn't.

### Notes / Suspicions
-

### Fix PR
- PR: -
- Fix commit: -
- Released in: -
