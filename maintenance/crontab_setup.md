# PostgreSQL Maintenance Cron Setup

This document outlines how to set up scheduled maintenance tasks for your PostgreSQL database using cron jobs.

## Making Scripts Executable

Before setting up cron jobs, make the maintenance script executable:

```bash
chmod +x /path/to/maintenance/run_maintenance.sh
```

## Recommended Maintenance Schedule

Below is a recommended maintenance schedule for different database sizes:

### Small to Medium Databases (< 50GB)

```
# Run VACUUM ANALYZE daily during off-peak hours (2:00 AM)
0 2 * * * /path/to/maintenance/run_maintenance.sh

# Detailed maintenance report weekly (Sunday at 3:00 AM)
0 3 * * 0 docker exec time_management-db-1 psql -U yourusername -d time_management_db -f /maintenance/db_size_report.sql > /var/log/postgres_maintenance/weekly_report_$(date +\%Y-\%m-\%d).log
```

### Large Databases (> 50GB)

```
# Run lightweight VACUUM daily (2:00 AM)
0 2 * * * docker exec time_management-db-1 psql -U yourusername -d time_management_db -c "VACUUM ANALYZE;"

# Run full maintenance weekly during weekends (Sunday at 1:00 AM)
0 1 * * 0 /path/to/maintenance/run_maintenance.sh

# Generate monthly database size report (1st of month at 4:00 AM)
0 4 1 * * docker exec time_management-db-1 psql -U yourusername -d time_management_db -f /maintenance/db_size_report.sql > /var/log/postgres_maintenance/monthly_report_$(date +\%Y-\%m-\%d).log
```

## Setting Up Cron Jobs

To set up these cron jobs, follow these steps:

1. Edit the crontab for the appropriate user:

```bash
sudo crontab -e
```

2. Add the desired cron job entries from above

3. Save and exit

## Adjusting the Schedule

Adjust the schedule according to your specific needs:

- **Database size**: Larger databases may require more frequent maintenance
- **Traffic patterns**: Schedule during low-traffic periods
- **Business hours**: Make sure maintenance doesn't impact users during working hours

## Monitoring Cron Job Execution

To monitor whether the cron jobs are running properly:

```bash
# Check the cron logs
sudo grep CRON /var/log/syslog

# View maintenance logs
ls -la /var/log/postgres_maintenance/
cat /var/log/postgres_maintenance/maintenance_YYYY-MM-DD_HH-MM-SS.log
```

## Docker Environment Configuration

Since our application runs in Docker, make sure the container names in the maintenance scripts match your actual Docker container names. Use `docker ps` to verify container names.

## Testing the Scripts Manually

Before setting up cron jobs, it's advisable to run the maintenance script manually to verify it works correctly:

```bash
# Make sure you're in the right directory
cd /path/to/time_management

# Run the script
./maintenance/run_maintenance.sh
```

## Common Issues

- **Permission problems**: Ensure the cron job runs as a user with appropriate permissions
- **Path issues**: Use absolute paths in cron jobs
- **Docker container names**: Verify container names with `docker ps`
- **Log rotation**: Set up log rotation for maintenance logs to prevent disk space issues 