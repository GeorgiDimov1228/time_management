-- PostgreSQL Statistics Update Maintenance Script
-- ------------------------------------------------
-- This script updates database statistics to improve query planner performance

\echo 'Starting statistics update maintenance'

-- Set client_min_messages to reduce verbosity
SET client_min_messages TO 'warning';

-- Show current statistics settings
\echo 'Current statistics targets:'
SELECT 
    schemaname, 
    tablename, 
    attname, 
    inherited, 
    n_distinct, 
    correlation
FROM pg_stats
WHERE schemaname NOT LIKE 'pg_%' 
  AND schemaname != 'information_schema'
ORDER BY correlation
LIMIT 10;

-- Update statistics for all tables
\echo 'Updating statistics for all tables'
ANALYZE VERBOSE;

-- For more detailed statistics on specific tables, 
-- especially those with complex queries or large data sets:
\echo 'Updating statistics for critical tables with higher sampling'

-- Attendance table (likely to have complex queries)
ALTER TABLE attendance ALTER COLUMN employee_id SET STATISTICS 1000;
ALTER TABLE attendance ALTER COLUMN timestamp SET STATISTICS 1000;
ALTER TABLE attendance ALTER COLUMN event_type SET STATISTICS 1000;
ANALYZE VERBOSE attendance;

-- Employee table
ALTER TABLE employee ALTER COLUMN rfid_card SET STATISTICS 1000;
ALTER TABLE employee ALTER COLUMN status SET STATISTICS 1000;
ANALYZE VERBOSE employee;

-- Show current statistics after update
\echo 'Updated statistics targets (showing lowest correlations):'
SELECT 
    schemaname, 
    tablename, 
    attname, 
    inherited, 
    n_distinct, 
    correlation
FROM pg_stats
WHERE schemaname NOT LIKE 'pg_%' 
  AND schemaname != 'information_schema'
ORDER BY correlation
LIMIT 10;

\echo 'Statistics update maintenance completed' 