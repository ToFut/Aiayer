#!/usr/bin/env python3
"""
Fix for overlay notification rendering
This script modifies the NextGenAppleChatWidget.svelte component to properly handle suggestion messages
"""

import os
import re
import shutil
import sys
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fix_overlay_notification')

# Path to Svelte component
COMPONENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            "overlay/src/components/NextGenAppleChatWidget.svelte")

def backup_file(file_path):
    """Create a backup of the file"""
    backup_path = f"{file_path}.bak.{int(datetime.now().timestamp())}"
    shutil.copy2(file_path, backup_path)
    logger.info(f"Created backup of {file_path} at {backup_path}")
    return backup_path

def fix_suggestion_handling(file_path):
    """Fix the suggestion handling in the NextGenAppleChatWidget.svelte file"""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    # Create backup
    backup_file(file_path)
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Add debug logging for suggestion messages
    debug_log_pattern = r"console\.log\('\🎯 Smart Progressive message received:', data\);"
    debug_log_replacement = r"console.log('🎯 Smart Progressive message received:', data);\n    if (data.type === 'suggestion') console.log('💡 SUGGESTION MESSAGE RECEIVED:', JSON.stringify(data));"
    
    content = re.sub(debug_log_pattern, debug_log_replacement, content)
    
    # Fix 2: Enhance suggestion message detection to handle both formats
    suggestion_detection_pattern = r"if \(data\.type === 'suggestion' \|\| \(data\.mode === 'SUGGEST' && data\.notification\)\) \{"
    suggestion_detection_replacement = r"if (data.type === 'suggestion' || (data.mode === 'SUGGEST' && (data.notification || data.type === 'notification')) || (data.notification && data.buttons)) {"
    
    if suggestion_detection_pattern in content:
        content = content.replace(suggestion_detection_pattern, suggestion_detection_replacement)
    else:
        logger.warning("Could not find suggestion detection pattern, adding fix might be more complex")
        
        # Try to find the suggestion handler section by looking for "Received suggestion:"
        suggestion_section_pattern = r"// Handle suggestion messages(.*?)return;"
        suggestion_section_match = re.search(suggestion_section_pattern, content, re.DOTALL)
        
        if suggestion_section_match:
            old_section = suggestion_section_match.group(0)
            enhanced_section = """// Handle suggestion messages
      if (data.type === 'suggestion' || (data.mode === 'SUGGEST' && (data.notification || data.type === 'notification')) || (data.notification && data.buttons)) {
        console.log('💡 Received suggestion:', data);
        
        // Play notification sound if enabled
        if (data.play_sound && soundEnabled) {
          playSound('notification');
        }
        
        // Add the suggestion to messages
        messages = [...messages, {
          type: 'suggestion',
          content: data.response || data.data?.response || '',
          buttons: data.buttons || data.data?.buttons || [],
          timestamp: new Date().toISOString(),
          importance: data.importance || data.data?.importance || 'medium',
          plan_id: data.plan_id || data.sessionId || data.id || `suggestion_${Date.now()}`
        }];
        
        // Scroll to bottom
        setTimeout(() => {
          if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
          }
        }, 100);
        
        return;
      }"""
            content = content.replace(old_section, enhanced_section)
    
    # Fix 3: Enhance animation for suggestions
    suggestion_animation_pattern = r"animation: pulse 2s infinite;"
    suggestion_animation_replacement = r"animation: pulse 2s infinite; box-shadow: 0 0 15px rgba(48, 209, 88, 0.5);"
    
    if suggestion_animation_pattern in content:
        content = content.replace(suggestion_animation_pattern, suggestion_animation_replacement)
    
    # Fix 4: Ensure suggestion buttons are properly styled
    suggestion_buttons_pattern = r"\.suggestion-btn {\s*flex: 1;\s*display: flex;"
    suggestion_buttons_replacement = """
  .suggestion-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 12px 16px;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all var(--transition-fast);
    backdrop-filter: blur(5px);
    box-shadow: 0 2px 10px rgba(48, 209, 88, 0.3);
  """
    
    if suggestion_buttons_pattern in content:
        content = re.sub(suggestion_buttons_pattern, suggestion_buttons_replacement, content, flags=re.DOTALL)
    
    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Applied fixes to {file_path}")
    
    return True

def rebuild_overlay():
    """Rebuild the overlay application to apply changes"""
    logger.info("Rebuilding overlay application...")
    
    try:
        # Change to overlay directory
        os.chdir(os.path.dirname(COMPONENT_PATH))
        os.chdir("..")  # Go to overlay root directory
        
        # Run npm build
        logger.info("Running npm run build...")
        result = subprocess.run(["npm", "run", "build"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
        
        if result.returncode == 0:
            logger.info("Overlay built successfully!")
            return True
        else:
            logger.error(f"Build failed: {result.stderr}")
            return False
    
    except Exception as e:
        logger.error(f"Error rebuilding overlay: {e}")
        return False

def main():
    """Main entry point for the script"""
    print("\n=== OVERLAY NOTIFICATION RENDERING FIX ===\n")
    print("This script fixes suggestion notification rendering in the NextGen overlay.")
    print("It will modify the NextGenAppleChatWidget.svelte component and rebuild the overlay.\n")
    
    # Fix the component
    success = fix_suggestion_handling(COMPONENT_PATH)
    
    if not success:
        print("\n❌ Failed to fix suggestion handling. Check the logs for details.")
        return
    
    # Ask user if they want to rebuild the overlay
    rebuild = input("\nDo you want to rebuild the overlay now? (y/n): ").lower().strip() == 'y'
    
    if rebuild:
        rebuild_success = rebuild_overlay()
        
        if rebuild_success:
            print("\n✅ Overlay has been rebuilt successfully!")
            print("Please restart the overlay application to apply the changes.")
        else:
            print("\n❌ Failed to rebuild the overlay. Please rebuild it manually:")
            print("  cd overlay")
            print("  npm run build")
    else:
        print("\nYou chose not to rebuild. Please rebuild the overlay manually:")
        print("  cd overlay")
        print("  npm run build")
    
    print("\n=== FIX COMPLETE ===")
    print("After rebuilding, restart the overlay application and test notifications again.")

if __name__ == "__main__":
    main()