#!/bin/bash
#
# PostgreSQL Maintenance Script
# ----------------------------
# This script automates regular maintenance tasks for PostgreSQL databases
# including VACUUM, REINDEX, and statistics updates.
#

# Configuration variables
DB_NAME="time_management_db"
DB_USER="${POSTGRES_USER}"
DB_CONTAINER="time_management-db-1"  # Use 'docker ps' to get the correct container name

# Log file setup
MAINTENANCE_LOG_DIR="/var/log/postgres_maintenance"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$MAINTENANCE_LOG_DIR/maintenance_$DATE.log"

# Create log directory if it doesn't exist
mkdir -p $MAINTENANCE_LOG_DIR

# Log function
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a $LOG_FILE
}

# Start maintenance log
log "Starting PostgreSQL maintenance operations"
log "=================================================="

# Run VACUUM ANALYZE on all tables
log "Running VACUUM ANALYZE on all tables"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -f /maintenance/vacuum_analyze.sql >> $LOG_FILE 2>&1
log "VACUUM ANALYZE completed"

# Run REINDEX to rebuild indexes
log "Running REINDEX on all tables"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -f /maintenance/reindex.sql >> $LOG_FILE 2>&1
log "REINDEX completed"

# Update database statistics
log "Updating database statistics"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -f /maintenance/update_statistics.sql >> $LOG_FILE 2>&1
log "Statistics update completed"

# Check for table bloat
log "Checking for table bloat"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -f /maintenance/check_bloat.sql >> $LOG_FILE 2>&1
log "Table bloat check completed"

# Generate database size report
log "Generating database size report"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -f /maintenance/db_size_report.sql >> $LOG_FILE 2>&1
log "Database size report generated"

# Run custom maintenance tasks if needed
if [ -f /maintenance/custom_maintenance.sql ]; then
    log "Running custom maintenance tasks"
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -f /maintenance/custom_maintenance.sql >> $LOG_FILE 2>&1
    log "Custom maintenance tasks completed"
fi

# Maintenance complete
log "=================================================="
log "PostgreSQL maintenance operations completed successfully"

# Optional: Cleanup old log files (keeping the last 30 days)
find $MAINTENANCE_LOG_DIR -name "maintenance_*.log" -type f -mtime +30 -delete

exit 0 