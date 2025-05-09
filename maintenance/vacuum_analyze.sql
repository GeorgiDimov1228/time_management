-- PostgreSQL VACUUM ANALYZE Maintenance Script
-- ------------------------------------------------
-- This script performs VACUUM ANALYZE on all tables in the database
-- to reclaim storage and update statistics for query planning.

\echo 'Starting VACUUM ANALYZE maintenance'

-- Set client_min_messages to reduce verbosity
SET client_min_messages TO 'warning';

-- VACUUM ANALYZE all tables in the database
VACUUM ANALYZE;

-- For more aggressive cleaning, use VACUUM FULL (use cautiously - it locks tables)
-- Uncomment the following section if needed for specific tables

/*
\echo 'Running VACUUM FULL on specific tables'

-- First, vacuum the most frequently modified tables
VACUUM (FULL, ANALYZE) attendance;
VACUUM (FULL, ANALYZE) employee;
*/

-- Vacuum specific tables with more options
\echo 'Running targeted VACUUM operations'

-- Vacuum attendance table (likely to have frequent updates/deletes)
VACUUM (VERBOSE, ANALYZE) attendance;

-- For large tables that get frequent updates
-- VACUUM (ANALYZE, VERBOSE) <table_name>;

-- Show tables with high dead tuple count
\echo 'Tables with high dead tuple counts:'
SELECT schemaname, relname, n_dead_tup, last_vacuum, last_autovacuum,
       pg_size_pretty(pg_relation_size(schemaname || '.' || relname)) as size
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

\echo 'VACUUM ANALYZE maintenance completed' 