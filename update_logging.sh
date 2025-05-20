#!/bin/bash
# Update logging configuration and clean up existing logs

# Backup current logging configuration
echo "Backing up current logging configuration..."
timestamp=$(date +"%Y%m%d_%H%M%S")
cp config/logging.conf config/backups/logging_${timestamp}.conf

# Apply new optimized logging configuration
echo "Applying new optimized logging configuration..."
cp config/logging.conf.optimized config/logging.conf

# Create archive directory for logs
echo "Creating log archive directories..."
mkdir -p logs/archive
mkdir -p logs/memory/archive

# Clean up existing logs
echo "Cleaning up existing logs..."
python scripts/log_cleanup.py --log-dir logs --max-size 20 --max-age 3 --clear-empty

# Make memory logger use the optimized version
echo "Updating memory logger to use optimized version..."
# This will be done automatically on next system startup

echo "Log optimization complete!"
echo "The system will now use reduced logging levels and only log significant events."
echo "Empty log entries will be throttled to reduce disk usage."
echo ""
echo "To further reduce logs, you can run the cleanup script regularly:"
echo "  python scripts/log_cleanup.py --log-dir logs --clear-empty"