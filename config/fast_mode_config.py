#!/usr/bin/env python3
"""
Fast Mode Configuration for Performance Optimization
"""

# Screen analysis settings
FAST_MODE_SETTINGS = {
    "capture_interval": 8,          # Increased from 4s to 8s  
    "skip_unchanged_screens": True,  # Skip analysis if screen unchanged
    "cache_duration": 5,            # Cache results for 5 seconds
    "max_analysis_time": 30,        # Timeout analysis after 30s
    "enable_progress_feedback": True, # Send progress updates
    "lightweight_mode": True,       # Use faster analysis methods
}

# LLaVA optimization settings
LLAVA_SETTINGS = {
    "max_retries": 1,               # Reduce retries from 3 to 1
    "timeout": 20,                  # Reduce timeout from 30s to 20s  
    "skip_redundant_calls": True,   # Skip if similar analysis recent
    "batch_processing": False,      # Disable batch processing for speed
}

# Workflow optimization
WORKFLOW_SETTINGS = {
    "max_concurrent_analyses": 1,   # Limit concurrent screen analyses
    "adaptive_intervals": True,     # Adjust intervals based on complexity
    "smart_caching": True,         # Cache workflow patterns
    "fast_simple_tasks": True,     # Bypass complex analysis for simple tasks
}
