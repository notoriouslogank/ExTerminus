--001_backfill_created_by_and_index.sql
-- Backfill jobs.created_by, add index, and guard against NULL on INSERT.

BEGIN;

-- 1) Backfill: prefer an admin, else manager, else lowest user id.
UPDATE jobs
SET created_by = COALESCE (
	( SELECT id FROM users WHERE role IN ('admin', 'manager')
	ORDER BY CASE role WHEN 'admin' THEN 0 ELSE 1 END, id LIMIT 1),
	(SELECT MIN(id) FROM users)
)
WHERE created_by IS NULL;

-- 2) Index for fast lookups by owner (calendar/day views, "my jobs", etc.)
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON jobs(created_by);

-- 3) Forbid NULL on INSERT (keeps new rows sane).
CREATE TRIGGER IF NOT EXISTS trg_jobs_created_by_not_null_ins
BEFORE INSERT ON jobs
WHEN NEW.created_by IS NULL
BEGIN
	SELECT RAISE(ABORT, 'jobs.created_by required');
END;

COMMIT;
