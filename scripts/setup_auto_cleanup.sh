#!/bin/bash
# Set up automatic cleaning for sensor logs and cache
# This script sets up a cron job to run the cleanup_manager.py script

# Ensure the script is executable
chmod +x scripts/log_manager.py
chmod +x scripts/cleanup_manager.py

# Create a crontab entry
CRON_SCHEDULE="0 */3 * * *"  # Run every 3 hours
CLEANUP_SCRIPT="$PWD/scripts/cleanup_manager.py"
LOG_FILE="$PWD/logs/cleanup_manager.log"

# Create a temporary file for the crontab
TEMP_CRONTAB=$(mktemp)

# Get existing crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || true

# Check if the entry already exists
if grep -q "$CLEANUP_SCRIPT" "$TEMP_CRONTAB"; then
    echo "Cron job for cleanup already exists"
else
    # Add our new cron job
    echo "# SensAI automatic cleanup - $(date)" >> "$TEMP_CRONTAB"
    echo "$CRON_SCHEDULE cd $PWD && python3 $CLEANUP_SCRIPT --max-cache-mb=500 --max-logs-mb=200 >> $LOG_FILE 2>&1" >> "$TEMP_CRONTAB"
    echo "Added cron job to run cleanup every 3 hours"
    
    # Install the new crontab
    crontab "$TEMP_CRONTAB"
    echo "Crontab updated successfully"
fi

# Clean up the temporary file
rm "$TEMP_CRONTAB"

# Run the cleanup script once now to set everything up
echo "Running initial cleanup..."
python3 "$CLEANUP_SCRIPT" --max-cache-mb=500 --max-logs-mb=200

echo "Auto-cleanup has been set up successfully"
echo "The script will run every 3 hours to keep your system optimized"
echo "Logs will be written to: $LOG_FILE"