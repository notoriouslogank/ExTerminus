# BUGS

## Open

- [BUG-1006] REIs
  Opened: 2025-08-09 • Branch: `fix/bug-1006-reis`
- [BUG-1005] Multi-Day Arrows
  Opened: 2025-08-09 • Branch: `fix/bug-1005-multi-day-arrows`
- [BUG-1004] Edit Job Crash
  Opened: 2025-08-09 • Branch: `fix/bug-1004-edit-job-crash`
- [BUG-1003] Unauthorized Lock Toggle
  Opened: 2025-08-09 • Branch: `fix/bug-1003-unauthorized-lock-to`
- [BUG-1002] Job Edit Auth
  Opened: 2025-08-09 • Branch: `fix/bug-1002-job-edit-auth`
- [BUG-1001] Type Abbreviations
  Opened: 2025-08-09 • Branch: `fix/bug-1001-type-abbreviations`
## Resolved

---

## BUG-1001 - Type Abbreviations
**Area:** calendar
**Severity:** Low
**Status:** Open
**Opened:** 2025-08-09

### Summary
Type Abbreviations

### Steps to Reproduce
Create a job (for instance, 10 REIs on a date); view the calendar.

### Expected
Should abbreviate to "REIs" in the job card

### Actual
Abbreviates to "R" on the job card

### Notes / Suspicions
-

### Fix PR
- PR: -
- Fix commit: -
- Released in: -

---

## BUG-1002 - Job Edit Auth
**Area:** jobs
**Severity:** High
**Status:** Open
**Opened:** 2025-08-09

### Summary
Job Edit Auth

### Steps to Reproduce
While logged out, click a date in the calendar view to open the day view; look at the options available.

### Expected
An unauth'd user shouldn't be able to edit/delete jobs.

### Actual
Unauth'd user is able to edit/delete individual jobs.

### Notes / Suspicions
-

### Fix PR
- PR: -
- Fix commit: -
- Released in: -

---

## BUG-1003 - Unauthorized Lock Toggle
**Area:** auth
**Severity:** Critical
**Status:** Open
**Opened:** 2025-08-09

### Summary
Unauthorized Lock Toggle

### Steps to Reproduce
While logged out, attempt to toggle Lock/Unlock Day.

### Expected
Lock/Unlock Day toggle should not appear at all.

### Actual
Lock/Unlock Day toggle is clickable, and works.

### Notes / Suspicions
-

### Fix PR
- PR: -
- Fix commit: -
- Released in: -

---

## BUG-1004 - Edit Job Crash
**Area:** jobs
**Severity:** Critical
**Status:** Open
**Opened:** 2025-08-09

### Summary
Edit Job Crash

### Steps to Reproduce
While logged in, attempt to Edit Job via day-view job card.

### Expected
Edit Job page should open, Save Changes should redirect to the calendar view.

### Actual
Crash when Save Changes is clicked.

### Notes / Suspicions
-

### Fix PR
- PR: -
- Fix commit: -
- Released in: -

---

## BUG-1005 - Multi-Day Arrows
**Area:** calendar
**Severity:** Low
**Status:** Open
**Opened:** 2025-08-09

### Summary
Multi-Day Arrows

### Steps to Reproduce
Create a multi-day job, then view it on the calendar view.

### Expected
Should print an arrow (->) on each day of a multi-day job.

### Actual
Only prints an arrow on the first day.

### Notes / Suspicions
-

### Fix PR
- PR: -
- Fix commit: -
- Released in: -

---

## BUG-1006 - REIs
**Area:** calendar
**Severity:** High
**Status:** Open
**Opened:** 2025-08-09

### Summary
REIs

### Steps to Reproduce
Add REIs of any quantity and with any zipcode to any day.

### Expected
Calendar view should display "REIs" - "Technician" - "Quantity" - "City Name".

### Actual
Calendar simply displays "R - Unknown" for the created job(s)

### Notes / Suspicions
-

### Fix PR
- PR: -
- Fix commit: -
- Released in: -
