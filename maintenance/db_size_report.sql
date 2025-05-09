-- PostgreSQL Database Size Report
-- ------------------------------------------------
-- This script generates reports on database size and growth

\echo 'Starting database size report'

-- Database Size
\echo '\n=== DATABASE SIZE ==='
\echo 'Overall database size:'

SELECT 
    pg_database.datname AS database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS database_size
FROM pg_database
WHERE pg_database.datname = current_database();

-- Schema Sizes
\echo '\n=== SCHEMA SIZES ==='
\echo 'Size of schemas in the database:'

SELECT 
    nspname AS schema_name,
    pg_size_pretty(sum(pg_relation_size(pg_class.oid))) AS schema_size
FROM pg_class
JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
GROUP BY nspname
ORDER BY sum(pg_relation_size(pg_class.oid)) DESC;

-- Table Sizes
\echo '\n=== TABLE SIZES ==='
\echo 'Top 10 largest tables (including indexes):'

SELECT 
    schemaname || '.' || tablename AS table_full_name,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename) - 
                  pg_relation_size(schemaname || '.' || tablename)) AS index_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
LIMIT 10;

-- Index Sizes
\echo '\n=== INDEX SIZES ==='
\echo 'Top 10 largest indexes:'

SELECT 
    schemaname || '.' || tablename AS table_name,
    indexname AS index_name,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_relation_size(indexname::regclass) DESC
LIMIT 10;

-- Row Counts
\echo '\n=== TABLE ROW COUNTS ==='
\echo 'Estimated row count for each table:'

SELECT 
    schemaname || '.' || relname AS table_full_name,
    n_live_tup AS row_count,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || relname)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname || '.' || relname)) AS table_size
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Table Activity
\echo '\n=== TABLE ACTIVITY ==='
\echo 'Activity statistics for tables:'

SELECT 
    schemaname || '.' || relname AS table_full_name,
    seq_scan AS sequential_scans,
    idx_scan AS index_scans,
    n_tup_ins AS rows_inserted,
    n_tup_upd AS rows_updated,
    n_tup_del AS rows_deleted,
    n_live_tup AS live_rows,
    n_dead_tup AS dead_rows
FROM pg_stat_user_tables
ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
LIMIT 10;

-- Growth Trend (using pg_stat_statements extension if available)
\echo '\n=== QUERY EXECUTION STATISTICS ==='
\echo 'Top 10 most time-consuming queries (if pg_stat_statements is enabled):'

SELECT EXISTS (
    SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
) AS pg_stat_statements_enabled \gset

\if :pg_stat_statements_enabled
    SELECT 
        substring(query, 1, 80) AS query_preview,
        calls AS execution_count,
        round(total_exec_time::numeric, 2) AS total_time_ms,
        round(mean_exec_time::numeric, 2) AS avg_time_ms,
        round((100 * total_exec_time / sum(total_exec_time) OVER())::numeric, 2) AS percentage
    FROM pg_stat_statements
    ORDER BY total_exec_time DESC
    LIMIT 10;
\else
    \echo 'The pg_stat_statements extension is not enabled. Enable it for query statistics.';
\endif

\echo 'Database size report completed' 