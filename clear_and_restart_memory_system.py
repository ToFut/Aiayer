#!/usr/bin/env python3
"""
Clear All Memory Content and Restart with Continuous Real Data Collection
"""

import os
import shutil
import json
import sqlite3
from datetime import datetime
from pathlib import Path

def clear_all_memory_content():
    """Clear all existing memory content"""
    print("🧹 CLEARING ALL EXISTING MEMORY CONTENT")
    print("="*60)
    
    # Memory files to clear
    memory_files = [
        "memory/memory_state.json",
        "memory/memory/memory_state.json", 
        "memory/conscious.json",
        "memory/conversation_history.json",
        "memory/last_context.json"
    ]
    
    # Clear memory files
    for file_path in memory_files:
        if os.path.exists(file_path):
            try:
                # Create empty/default content
                if "memory_state.json" in file_path:
                    empty_state = {
                        "version": "1.0",
                        "last_update": datetime.now().isoformat(),
                        "short_term": [],
                        "long_term": [], 
                        "context": {},
                        "sensor_data": {}
                    }
                    with open(file_path, 'w') as f:
                        json.dump(empty_state, f, indent=2)
                    print(f"✅ Cleared: {file_path}")
                elif "conscious.json" in file_path:
                    empty_conscious = {
                        "timestamp": datetime.now().isoformat(),
                        "sensor_buffers": {"screen": [], "process": []},
                        "insights": [],
                        "status": "active"
                    }
                    with open(file_path, 'w') as f:
                        json.dump(empty_conscious, f, indent=2)
                    print(f"✅ Cleared: {file_path}")
                else:
                    with open(file_path, 'w') as f:
                        json.dump([], f)
                    print(f"✅ Cleared: {file_path}")
            except Exception as e:
                print(f"⚠️ Error clearing {file_path}: {e}")
        else:
            print(f"📝 File not found: {file_path}")
    
    # Clear vector database
    vector_db_path = "memory/vector_store.db"
    if os.path.exists(vector_db_path):
        try:
            os.remove(vector_db_path)
            print(f"✅ Cleared vector database: {vector_db_path}")
        except Exception as e:
            print(f"⚠️ Error clearing vector database: {e}")
    
    # Clear cache directories
    cache_dirs = [
        "cache/complete_ui_understanding",
        "cache/app_detection", 
        "cache/llava_processor",
        "cache/process_sensor",
        "cache/screen_sensor"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                # Remove all files but keep directory
                for file in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                print(f"✅ Cleared cache: {cache_dir}")
            except Exception as e:
                print(f"⚠️ Error clearing {cache_dir}: {e}")
    
    # Clear backup files in process sensor cache
    process_cache_dir = Path("cache/process_sensor")
    if process_cache_dir.exists():
        backup_files = list(process_cache_dir.glob("process_cache.json.bak_*"))
        for backup_file in backup_files:
            try:
                backup_file.unlink()
            except Exception as e:
                print(f"⚠️ Error removing {backup_file}: {e}")
        print(f"✅ Cleared {len(backup_files)} backup files from process sensor cache")
    
    print(f"\n🎯 MEMORY CLEARANCE COMPLETE")
    print(f"   • All memory files reset to empty state")
    print(f"   • Vector database removed")
    print(f"   • Cache directories cleared")
    print(f"   • System ready for fresh data collection")

if __name__ == "__main__":
    clear_all_memory_content()