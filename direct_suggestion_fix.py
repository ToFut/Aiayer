#!/usr/bin/env python3
"""
Direct fix for NextGenAppleChatWidget to ensure suggestions work
"""

import os
import shutil
from datetime import datetime

# Component path
COMPONENT_PATH = "/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/NextGenAppleChatWidget.svelte"

def backup_file():
    """Create a backup of the file"""
    timestamp = int(datetime.now().timestamp())
    backup_path = f"{COMPONENT_PATH}.bak.{timestamp}"
    shutil.copy2(COMPONENT_PATH, backup_path)
    print(f"Created backup at {backup_path}")
    return backup_path

def restore_from_original():
    """Restore from the original file"""
    # Find all backups
    backups = [f for f in os.listdir(os.path.dirname(COMPONENT_PATH)) 
               if os.path.basename(COMPONENT_PATH) + ".bak" in f]
    
    # Get the earliest backup
    if backups:
        earliest_backup = sorted(backups)[0]
        backup_path = os.path.join(os.path.dirname(COMPONENT_PATH), earliest_backup)
        shutil.copy2(backup_path, COMPONENT_PATH)
        print(f"Restored from original backup {earliest_backup}")
        return True
    
    print("No backups found")
    return False

def fix_component():
    """Apply direct fix to the component file"""
    # Restore from original first
    restore_from_original()
    
    # Create new backup
    backup_file()
    
    # Read the original file
    with open(COMPONENT_PATH, 'r') as f:
        content = f.read()
    
    # Find the handle_client function
    suggestion_handler_pattern = "// Handle suggestion messages"
    suggestion_start = content.find(suggestion_handler_pattern)
    
    if suggestion_start == -1:
        print("Could not find suggestion handler section")
        return False
    
    # Find the end of the handler (next return statement)
    return_statement = content.find("return;", suggestion_start)
    if return_statement == -1:
        print("Could not find end of suggestion handler")
        return False
    
    # Find the ending closing brace after the return
    end_bracket = content.find("}", return_statement)
    if end_bracket == -1:
        print("Could not find end bracket after return")
        return False
    
    # Replace the suggestion handler with a fixed version
    new_handler = """// Handle suggestion messages
    if (data.type === 'suggestion' || (data.mode === 'SUGGEST' && data.notification)) {
      console.log('💡 Received suggestion:', data);
      
      // Play notification sound if enabled
      if (data.play_sound && soundEnabled) {
        playSound('notification');
      }
      
      // Add the suggestion to messages
      const suggestionMessage = {
        id: Date.now(),
        type: 'suggestion',
        content: data.response || '',
        buttons: data.buttons || [],
        timestamp: new Date(),
        importance: data.importance || 'high',
        plan_id: data.plan_id || `suggestion_${Date.now()}`
      };
      
      messages = [...messages, suggestionMessage];
      
      // Scroll to bottom
      setTimeout(() => {
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      }, 100);
      
      return;
    }"""
    
    # Replace the original handler
    new_content = content[:suggestion_start] + new_handler + content[end_bracket+1:]
    
    # Write the new content back to the file
    with open(COMPONENT_PATH, 'w') as f:
        f.write(new_content)
    
    print("Successfully applied suggestion handler fix")
    return True

if __name__ == "__main__":
    print("\n=== DIRECT SUGGESTION FIX ===\n")
    
    success = fix_component()
    
    if success:
        print("\nFix applied successfully!")
        print("Next steps:")
        print("1. Run 'cd /Users/segevbin/Desktop/SensAI/Aiayer/overlay && npm run build'")
        print("2. Restart the overlay application")
        print("3. Test with 'python3 fixed_nextgen_suggestion_handler.py'")
    else:
        print("\nFailed to apply the fix")
    
    print("\n=============================\n")