#!/bin/bash
# Test the log monitor functionality

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create log directory if it doesn't exist
mkdir -p ../logs

# Function to print colored output
echo_color() {
  color=$1
  text=$2
  echo -e "${color}${text}${NC}"
}

echo_color $YELLOW "=== Testing Log Monitor ==="

# Step 1: Create a test log file that exceeds the threshold (500MB)
echo_color $YELLOW "Step 1: Creating a test log file (550MB)..."
python3 create_test_log.py --size 550 --output ../logs/test_large_log.log
if [ $? -ne 0 ]; then
  echo_color $RED "Failed to create test log file"
  exit 1
fi

# Step 2: Run the log monitor once manually (not as daemon)
echo_color $YELLOW "Step 2: Running log monitor once to process large files..."
python3 log_monitor.py 
if [ $? -ne 0 ]; then
  echo_color $RED "Log monitor failed"
  exit 1
fi

# Step 3: Check if the log was rotated
echo_color $YELLOW "Step 3: Checking if log was rotated..."
backup_count=$(find ../logs -name "test_large_log.log.*.bak" | wc -l)

if [ $backup_count -gt 0 ]; then
  echo_color $GREEN "Success! Log file was rotated and backed up. Found $backup_count backup files."
  
  # Check if the original file was emptied
  original_size=$(du -k ../logs/test_large_log.log | cut -f1)
  
  if [ $original_size -lt 100 ]; then
    echo_color $GREEN "Original log file was properly emptied (size: ${original_size}KB)."
  else
    echo_color $RED "Original log file wasn't emptied properly (size: ${original_size}KB)."
  fi
  
  # Show the backup files
  echo_color $YELLOW "Backup files created:"
  ls -lh ../logs/test_large_log.log.*.bak
else
  echo_color $RED "Failed! Log file was not rotated. Check logs/log_monitor.log for errors."
fi

# Step 4: Test the check_log_sizes.sh utility
echo_color $YELLOW "Step 4: Testing check_log_sizes.sh utility..."
./check_log_sizes.sh

echo_color $YELLOW "=== Test Complete ==="