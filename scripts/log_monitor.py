#!/usr/bin/env python3
"""
Log Monitor Script

This script monitors log files in the logs/ directory and its subdirectories,
checks for oversized log files (>500MB), and cleans them up.
It also analyzes logs for inefficient logging patterns and reports them.

Run in background as part of start_optimized_system_with_llm.sh
"""

import os
import sys
import time
import logging
import re
import json
from datetime import datetime
import glob
# No daemon module needed as we're using & in shell script

# Configure logging for the monitor itself
# We need an absolute path for the log file
log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'log_monitor.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'
)

# Constants
SIZE_THRESHOLD_MB = 500  # Size threshold in MB
CHECK_INTERVAL = 10      # Check every 10 seconds
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
MAX_LOG_RETENTION = 7    # Days to keep backup logs


class LogMonitor:
    def __init__(self):
        self.oversize_logs = []
        self.log_stats = {}
        self.inefficient_patterns = [
            # Inefficient logging patterns to look for
            r'JSON\.stringify\(.+\)',           # Excessive JSON stringification
            r'console\.log\(.+\)',              # Browser console logs that might be excessive
            r'DEBUG.*object dump',              # Large object dumps
            r'Dumping (state|context|memory)',  # Large memory/state dumps
            r'^\s*print\(.*\)',                 # Python print statements (not using logging)
            r'screen_text.*(?=.{1000,})',       # Very long screen text captures
            r'\.log\(.*\.repeat\(',             # Repeated log messages
            r'data:image\/.*;base64,',          # Base64 encoded images in logs
        ]

    def find_log_files(self):
        """Find all log files in the logs directory and subdirectories."""
        all_log_files = []
        
        # Walk through the logs directory
        for root, _, files in os.walk(LOGS_DIR):
            for file in files:
                if file.endswith('.log') or file.endswith('.out'):
                    full_path = os.path.join(root, file)
                    all_log_files.append(full_path)
        
        return all_log_files

    def check_log_size(self, log_file):
        """Check if a log file exceeds the size threshold."""
        try:
            size_bytes = os.path.getsize(log_file)
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb > SIZE_THRESHOLD_MB:
                return True, size_mb
            return False, size_mb
        except Exception as e:
            logging.error(f"Error checking size of {log_file}: {e}")
            return False, 0

    def rotate_log(self, log_file):
        """Rotate oversized log file by creating a backup and emptying the original."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{log_file}.{timestamp}.bak"
            
            # Create a backup
            with open(log_file, 'rb') as src, open(backup_name, 'wb') as dst:
                dst.write(src.read())
            
            # Empty the original log file
            with open(log_file, 'w') as f:
                f.write(f"# Log rotated at {datetime.now().isoformat()} - Previous content in {backup_name}\n")
            
            logging.info(f"Rotated log file {log_file} -> {backup_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to rotate log file {log_file}: {e}")
            return False

    def analyze_log_content(self, log_file, max_lines=1000):
        """Analyze log file for inefficient patterns."""
        inefficiencies = []
        try:
            # Only read the last X lines to keep memory usage reasonable
            with open(log_file, 'r', errors='ignore') as f:
                # Read last max_lines of the file
                lines = f.readlines()[-max_lines:] if len(lines := f.readlines()) > max_lines else lines
            
            for i, line in enumerate(lines):
                for pattern in self.inefficient_patterns:
                    if re.search(pattern, line):
                        line_num = f"~{i}" if len(lines) >= max_lines else i
                        inefficiencies.append({
                            'pattern': pattern,
                            'line_num': line_num,
                            'sample': line[:100] + ('...' if len(line) > 100 else '')
                        })
            
            return inefficiencies
        except Exception as e:
            logging.error(f"Error analyzing log file {log_file}: {e}")
            return []

    def find_source_files_with_pattern(self, pattern):
        """Find source files that might be causing inefficient logging."""
        try:
            source_files = []
            # Search Python files for the pattern
            for extension in ['.py', '.js', '.svelte']:
                cmd = f"grep -r '{pattern}' --include='*{extension}' {PROJECT_ROOT}"
                import subprocess
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.stdout:
                    for line in result.stdout.splitlines():
                        if ':' in line:
                            file_path, _ = line.split(':', 1)
                            if file_path not in source_files and os.path.exists(file_path):
                                source_files.append(file_path)
            return source_files
        except Exception as e:
            logging.error(f"Error finding source files for pattern {pattern}: {e}")
            return []

    def clean_old_backups(self):
        """Clean up backup log files older than MAX_LOG_RETENTION days."""
        try:
            current_time = time.time()
            backup_files = glob.glob(f"{LOGS_DIR}/**/*.bak", recursive=True)
            
            for backup_file in backup_files:
                file_time = os.path.getmtime(backup_file)
                file_age_days = (current_time - file_time) / (24 * 3600)
                
                if file_age_days > MAX_LOG_RETENTION:
                    os.remove(backup_file)
                    logging.info(f"Removed old backup file: {backup_file} (age: {file_age_days:.1f} days)")
        except Exception as e:
            logging.error(f"Error cleaning old backups: {e}")

    def generate_report(self):
        """Generate a report of log file issues."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'oversized_logs': self.oversize_logs,
            'inefficient_logs': self.log_stats
        }
        
        report_path = os.path.join(LOGS_DIR, 'log_monitor_report.json')
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            logging.info(f"Generated log monitor report at {report_path}")
        except Exception as e:
            logging.error(f"Failed to write report: {e}")

    def run_scan(self):
        """Run a full scan of log files."""
        self.oversize_logs = []
        self.log_stats = {}
        
        logging.info("Starting log file scan...")
        log_files = self.find_log_files()
        logging.info(f"Found {len(log_files)} log files to check")
        
        for log_file in log_files:
            is_oversized, size_mb = self.check_log_size(log_file)
            
            if is_oversized:
                logging.warning(f"Oversized log file found: {log_file} ({size_mb:.2f} MB)")
                self.oversize_logs.append({
                    'file': log_file,
                    'size_mb': round(size_mb, 2)
                })
                
                # Rotate the log
                self.rotate_log(log_file)
                
                # Analyze inefficiencies
                inefficiencies = self.analyze_log_content(log_file)
                if inefficiencies:
                    self.log_stats[log_file] = {
                        'inefficiencies': inefficiencies,
                        'suggestions': []
                    }
                    
                    # Find potential sources of inefficient logging
                    for issue in inefficiencies:
                        pattern = issue['pattern']
                        sources = self.find_source_files_with_pattern(pattern)
                        if sources:
                            self.log_stats[log_file]['suggestions'].append({
                                'pattern': pattern,
                                'source_files': sources,
                                'recommendation': self.get_recommendation(pattern)
                            })
        
        # Clean old backups
        self.clean_old_backups()
        
        # Generate a report if we found issues
        if self.oversize_logs or self.log_stats:
            self.generate_report()
            
        logging.info(f"Log scan complete. Found {len(self.oversize_logs)} oversized logs.")

    def get_recommendation(self, pattern):
        """Get a recommendation for fixing an inefficient logging pattern."""
        recommendations = {
            r'JSON\.stringify\(.+\)': "Use selective fields instead of stringifying entire objects",
            r'console\.log\(.+\)': "Replace with structured logging and appropriate log levels",
            r'DEBUG.*object dump': "Use selective logging or log sampling for large objects",
            r'Dumping (state|context|memory)': "Implement selective state logging or sampling",
            r'^\s*print\(.*\)': "Replace with structured logging framework",
            r'screen_text.*(?=.{1000,})': "Truncate screen text in logs or use sampling",
            r'\.log\(.*\.repeat\(': "Avoid repeating log messages",
            r'data:image\/.*;base64,': "Don't log base64 encoded images, store references instead",
        }
        
        for key, value in recommendations.items():
            if re.search(key, pattern):
                return value
        
        return "Review this logging pattern for efficiency improvements"

    def monitor_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                self.run_scan()
                logging.info(f"Sleeping for {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                logging.info("Log monitor stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(CHECK_INTERVAL)  # Still sleep to avoid tight loops on errors


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # In our case, we're running the script as a background process 
    # directly from the shell script with output redirection,
    # so we don't need the daemon module
    
    logging.info("=== Log Monitor Starting ===")
    monitor = LogMonitor()
    
    # Run the monitor (no need for daemon context since the script 
    # is already executed with & in the shell script)
    monitor.monitor_loop()