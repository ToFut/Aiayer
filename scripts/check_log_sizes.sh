#!/bin/bash
# Script to check the sizes of all log files in the project

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Find all log files in the project
find_log_files() {
  find "$(dirname "$(dirname "$(realpath "$0")")")" -name "*.log" -o -name "*.out"
}

# Get size of file in MB
get_size_mb() {
  local file="$1"
  local size_bytes=$(stat -f "%z" "$file" 2>/dev/null || stat --format="%s" "$file" 2>/dev/null)
  
  if [ -z "$size_bytes" ]; then
    echo "0"
    return
  fi
  
  echo "scale=2; $size_bytes / 1024 / 1024" | bc
}

# Main function
main() {
  echo "Scanning for log files..."
  
  # Get all log files
  mapfile -t logs < <(find_log_files)
  
  # Print header
  printf "%-80s | %-10s | %s\n" "Log File" "Size (MB)" "Status"
  printf "%s\n" "---------------------------------------------------------------------------------------------------------------"
  
  # Track total size and large files
  total_size=0
  large_files=0
  
  # Check each log file
  for log in "${logs[@]}"; do
    size=$(get_size_mb "$log")
    
    # Determine status based on size
    if (( $(echo "$size > 500" | bc -l) )); then
      status="${RED}CRITICAL - Needs immediate rotation${NC}"
      large_files=$((large_files + 1))
    elif (( $(echo "$size > 200" | bc -l) )); then
      status="${YELLOW}WARNING - Getting large${NC}"
    else
      status="${GREEN}OK${NC}"
    fi
    
    # Add to total size
    total_size=$(echo "$total_size + $size" | bc)
    
    # Truncate path for display
    display_path=$(echo "$log" | sed "s|$(dirname "$(dirname "$(realpath "$0")")")/||")
    
    # Print information
    printf "%-80s | %-10s | %b\n" "$display_path" "$size" "$status"
  done
  
  # Print summary
  printf "\n%s\n" "---------------------------------------------------------------------------------------------------------------"
  printf "Total log files: %d\n" "${#logs[@]}"
  printf "Total size: %.2f MB\n" "$total_size"
  printf "Large files (>500MB): %d\n" "$large_files"
  
  if [ "$large_files" -gt 0 ]; then
    echo -e "\n${YELLOW}Recommendation:${NC} Some log files are very large. Consider running the log rotation manually:"
    echo "  python3 scripts/log_monitor.py"
  fi
}

# Run the script
main