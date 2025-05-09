-- PostgreSQL REINDEX Maintenance Script
-- ---------------------------------------
-- This script rebuilds indexes to improve performance and
-- reduce index bloat.

\echo 'Starting REINDEX maintenance'

-- Set client_min_messages to reduce verbosity
SET client_min_messages TO 'warning';

-- Show fragmented indexes before reindexing
\echo 'Checking for fragmented indexes before maintenance:'
SELECT
    schemaname || '.' || relname AS table_name,
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS index_scans
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 10;

-- REINDEX specific tables (less disruptive as it's table-by-table)
\echo 'Rebuilding indexes on main tables'

-- Attendance table (heavily used)
REINDEX TABLE attendance;

-- Employee table
REINDEX TABLE employee;

-- Admin users table
REINDEX TABLE admin_user;

-- For other tables, add as needed
-- REINDEX TABLE <table_name>;

/*
-- Alternative: REINDEX entire database (use cautiously - can cause downtime)
-- REINDEX DATABASE time_management_db;
*/

-- Show index statistics after reindexing
\echo 'Index sizes after maintenance:'
SELECT
    schemaname || '.' || relname AS table_name,
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS index_scans
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 10;

\echo 'REINDEX maintenance completed' 