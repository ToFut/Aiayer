#!/usr/bin/env python3
"""
Quick fix to update memory with current running applications
"""

import json
import os
from datetime import datetime

def get_current_apps():
    """Get currently running applications"""
    import subprocess
    
    # Get running processes
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    
    apps = set()
    for line in lines:
        if '/Applications/' in line:
            if 'Cursor' in line:
                apps.add('Cursor')
            elif 'Chrome' in line:
                apps.add('Google Chrome')
            elif 'Safari' in line:
                apps.add('Safari')
            elif 'Spotify' in line:
                apps.add('Spotify')
            elif 'Discord' in line:
                apps.add('Discord')
            elif 'Slack' in line:
                apps.add('Slack')
    
    return list(apps)

def update_memory_with_current_apps():
    """Update memory state with current apps"""
    memory_file = "/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_state.json"
    
    current_apps = get_current_apps()
    print(f"Detected running apps: {current_apps}")
    
    # Create new memory entry
    new_memory = {
        "timestamp": datetime.now().isoformat(),
        "memory_type": "current_system_state", 
        "user_activity": {
            "primary_activity": "development",
            "application_used": "Cursor",
            "professional_context": "software_development",
            "activity_specifics": ["coding", "development", "using_cursor"],
            "productivity_score": 0.8,
            "confidence_level": 0.9,
            "current_applications": current_apps
        },
        "context_analysis": {
            "workflow_stage": "active_development",
            "user_intent": "software_development", 
            "productivity_context": "coding_session",
            "meaningful_interaction": True
        },
        "concurrent_activities": [
            {
                "app": app,
                "category": "development" if app == "Cursor" else "productivity",
                "context": "software_development"
            } for app in current_apps
        ],
        "memory_id": f"current_state_{int(datetime.now().timestamp())}",
        "insights": [
            f"User is actively using {len(current_apps)} applications",
            "Primary focus on software development with Cursor",
            "Multi-application workflow active"
        ],
        "productivity_category": "high_productivity"
    }
    
    try:
        # Read existing memory
        with open(memory_file, 'r') as f:
            memory_data = json.load(f)
        
        # Add new memory to short_term
        if 'short_term' not in memory_data:
            memory_data['short_term'] = []
        
        memory_data['short_term'].insert(0, new_memory)
        memory_data['last_update'] = datetime.now().isoformat()
        
        # Keep only last 10 short term memories
        memory_data['short_term'] = memory_data['short_term'][:10]
        
        # Write back
        with open(memory_file, 'w') as f:
            json.dump(memory_data, f, indent=2)
        
        print(f"✅ Updated memory with current apps: {current_apps}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update memory: {e}")
        return False

if __name__ == "__main__":
    update_memory_with_current_apps()