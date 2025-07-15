#!/usr/bin/env python3
"""
Lightweight Backend Configuration
"""
import os
import json

# Lightweight settings
LIGHTWEIGHT_CONFIG = {
    "max_concurrent_requests": 2,
    "request_timeout": 10,
    "max_memory_mb": 200,
    "enable_throttling": True,
    "screen_capture_interval": 30,
    "process_monitor_interval": 15,
    "disable_heavy_features": True,
    "use_caching": True,
    "cache_duration": 300
}

# Save config
with open('config/lightweight_backend_config.json', 'w') as f:
    json.dump(LIGHTWEIGHT_CONFIG, f, indent=2)

print("✅ Lightweight backend configuration created")
