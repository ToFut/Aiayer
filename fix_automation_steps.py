#!/usr/bin/env python3
"""
Quick script to fix all AutomationStep calls to include estimated_duration
"""
import re

# Read the file
with open('real_agent_automation_handler.py', 'r') as f:
    content = f.read()

# Pattern to match AutomationStep constructor calls that don't have estimated_duration
pattern = r'(AutomationStep\([^)]*confidence=[\d.]+)(\s*\))'

def add_estimated_duration(match):
    """Add estimated_duration parameter to AutomationStep calls"""
    before_closing = match.group(1)
    closing = match.group(2)
    
    # Check if estimated_duration is already present
    if 'estimated_duration' in before_closing:
        return match.group(0)  # Return unchanged
    
    # Add estimated_duration before closing
    # Default values based on action type
    if 'action_type="wait"' in before_closing:
        duration = "3.0"  # Wait steps
    elif 'action_type="open"' in before_closing:
        duration = "3.0"  # App opening
    elif 'action_type="click"' in before_closing:
        duration = "1.0"  # Click actions
    elif 'action_type="type"' in before_closing:
        duration = "2.0"  # Typing
    elif 'action_type="hotkey"' in before_closing:
        duration = "0.5"  # Hotkeys
    elif 'action_type="navigate"' in before_closing:
        duration = "2.0"  # Navigation
    else:
        duration = "2.0"  # Default
    
    return f"{before_closing},\n                estimated_duration={duration}{closing}"

# Apply the fix
fixed_content = re.sub(pattern, add_estimated_duration, content, flags=re.DOTALL)

# Write back to file
with open('real_agent_automation_handler.py', 'w') as f:
    f.write(fixed_content)

print("Fixed AutomationStep calls to include estimated_duration")