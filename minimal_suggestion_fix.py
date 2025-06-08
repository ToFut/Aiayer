#!/usr/bin/env python3
"""
Minimal fix for suggestion notifications in NextGenAppleChatWidget
"""

import os
import shutil
from datetime import datetime

# Path to component
COMPONENT_PATH = "/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/NextGenAppleChatWidget.svelte"

def backup_file(file_path):
    """Create a backup of the file"""
    timestamp = int(datetime.now().timestamp())
    backup_path = f"{file_path}.bak.{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    return backup_path

def apply_fix():
    """Apply minimal fix to make suggestion notifications work"""
    # Restore from the backup first
    backups = [f for f in os.listdir(os.path.dirname(COMPONENT_PATH)) 
               if f.startswith(os.path.basename(COMPONENT_PATH) + ".bak")]
    
    if backups:
        latest_backup = sorted(backups)[-1]
        backup_path = os.path.join(os.path.dirname(COMPONENT_PATH), latest_backup)
        shutil.copy2(backup_path, COMPONENT_PATH)
        print(f"Restored from backup {latest_backup}")
    
    # Create a fresh backup
    backup_file(COMPONENT_PATH)
    
    # Read the file content
    with open(COMPONENT_PATH, 'r') as f:
        lines = f.readlines()
    
    # Find the suggestion handler section
    suggestion_start_line = -1
    for i, line in enumerate(lines):
        if "// Handle suggestion messages" in line:
            suggestion_start_line = i
            break
    
    if suggestion_start_line == -1:
        print("Could not find suggestion handler section")
        return False
    
    # Find the end of the suggestion handler
    suggestion_end_line = -1
    for i in range(suggestion_start_line, len(lines)):
        if "return;" in lines[i]:
            suggestion_end_line = i
            break
    
    if suggestion_end_line == -1:
        print("Could not find end of suggestion handler")
        return False
    
    # Create the fixed suggestion handler
    fixed_handler = [
        "    // Handle suggestion messages\n",
        "    if (data.type === 'suggestion' || (data.mode === 'SUGGEST' && data.notification)) {\n",
        "      console.log('💡 Received suggestion:', data);\n",
        "      \n",
        "      // Play notification sound if enabled\n",
        "      if (data.play_sound && soundEnabled) {\n",
        "        playSound('notification');\n",
        "      }\n",
        "      \n",
        "      // Add the suggestion to messages\n",
        "      messages = [...messages, {\n",
        "        id: Date.now(),\n",
        "        type: 'suggestion',\n",
        "        content: data.response || '',\n",
        "        buttons: data.buttons || [],\n",
        "        timestamp: new Date().toISOString(),\n",
        "        importance: data.importance || 'high',\n",
        "        plan_id: data.plan_id || `suggestion_${Date.now()}`\n",
        "      }];\n",
        "      \n",
        "      // Scroll to bottom\n",
        "      setTimeout(() => {\n",
        "        if (chatContainer) {\n",
        "          chatContainer.scrollTop = chatContainer.scrollHeight;\n",
        "        }\n",
        "      }, 100);\n",
        "      \n",
        "      return;\n",
        "    }\n"
    ]
    
    # Replace the original handler with the fixed version
    new_lines = lines[:suggestion_start_line] + fixed_handler + lines[suggestion_end_line+1:]
    
    # Write the fixed content back to the file
    with open(COMPONENT_PATH, 'w') as f:
        f.writelines(new_lines)
    
    print("Successfully applied minimal fix to suggestion handler")
    return True

if __name__ == "__main__":
    print("\n=== MINIMAL SUGGESTION NOTIFICATION FIX ===\n")
    
    if not os.path.exists(COMPONENT_PATH):
        print(f"Error: Component file not found at {COMPONENT_PATH}")
        exit(1)
    
    success = apply_fix()
    
    if success:
        print("\nFix applied successfully!")
        print("Next steps:")
        print("1. Run 'cd /Users/segevbin/Desktop/SensAI/Aiayer/overlay && npm run build'")
        print("2. Restart the overlay application")
        print("3. Test with 'python3 fixed_nextgen_suggestion_handler.py'")
    else:
        print("\nFailed to apply the fix")
        print("Please check the component file manually")
    
    print("\n==============================================\n")