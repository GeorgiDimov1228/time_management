-- PostgreSQL Bloat Check Maintenance Script
-- ------------------------------------------------
-- This script identifies tables and indexes that have bloat and may need maintenance

\echo 'Starting database bloat check'

-- Set client_min_messages to reduce verbosity
SET client_min_messages TO 'warning';

-- Table Bloat Check
\echo '=== TABLE BLOAT CHECK ==='
\echo 'Tables with potential bloat (estimating wasted space):'

SELECT
    schemaname || '.' || tablename AS table_full_name,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename) - 
                  pg_relation_size(schemaname || '.' || tablename)) AS index_size,
    round(100 * (pg_total_relation_size(schemaname || '.' || tablename) - 
                pg_relation_size(schemaname || '.' || tablename)) / 
          greatest(pg_total_relation_size(schemaname || '.' || tablename), 1), 2) AS index_ratio,
    pg_stat_get_live_tuples(schemaname || '.' || tablename) AS n_live_tup,
    pg_stat_get_dead_tuples(schemaname || '.' || tablename) AS n_dead_tup,
    CASE WHEN pg_stat_get_live_tuples(schemaname || '.' || tablename) = 0 THEN 0
         ELSE round(100 * pg_stat_get_dead_tuples(schemaname || '.' || tablename) / 
              greatest(pg_stat_get_live_tuples(schemaname || '.' || tablename), 1), 2)
    END AS dead_tup_ratio
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY dead_tup_ratio DESC, pg_total_relation_size(schemaname || '.' || tablename) DESC
LIMIT 10;

-- Index Bloat Check
\echo '\n=== INDEX BLOAT CHECK ==='
\echo 'Indexes with low usage that might be candidates for removal or rebuilding:'

SELECT
    schemaname || '.' || relname AS table_name,
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched,
    CASE WHEN idx_scan = 0 THEN 'Never Used!'
         WHEN (idx_tup_read = 0) THEN 'Never Used for Data!'
         ELSE 'OK'
    END AS usage_status
FROM pg_stat_user_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_relation_size(indexrelid) DESC, idx_scan ASC
LIMIT 10;

-- Unused Indexes
\echo '\n=== UNUSED INDEXES ==='
\echo 'Indexes that have never been used since last stats reset:'

SELECT
    schemaname || '.' || relname AS table_name,
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0 
  AND schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 10;

-- Bloated Indexes (using more generic approximation)
\echo '\n=== POTENTIALLY BLOATED INDEXES ==='
\echo 'Indexes that may need to be rebuilt due to bloat:'

SELECT
    schemaname || '.' || tablename AS table_name,
    indexname AS index_name,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size,
    indexdef AS index_definition
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  AND indexname IN (
    SELECT indexrelname 
    FROM pg_stat_user_indexes 
    WHERE idx_scan > 0 
      AND indexrelname NOT IN (
        SELECT indexrelname 
        FROM pg_stat_user_indexes 
        WHERE idx_scan = 0
      )
  )
ORDER BY pg_relation_size(indexname::regclass) DESC
LIMIT 10;

\echo 'Database bloat check completed' 