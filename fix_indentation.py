#!/usr/bin/env python3
"""
Quick fix for indentation issue in ultimate_do_button_server.py
"""
import os
import sys

def fix_indentation():
    file_path = '/Users/segevbin/Desktop/SensAI/Aiayer/ultimate_do_button_server.py'
    backup_path = '/Users/segevbin/Desktop/SensAI/Aiayer/ultimate_do_button_server.py.indentation_bak'
    
    # Create backup
    with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
        dst.write(src.read())
    print(f"Created backup at {backup_path}")
    
    # Read file line by line
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Restore from original backup
    original_backup = '/Users/segevbin/Desktop/SensAI/Aiayer/ultimate_do_button_server.py.bak'
    if os.path.exists(original_backup):
        print(f"Restoring from original backup at {original_backup}")
        with open(original_backup, 'r') as f:
            original_content = f.read()
        
        with open(file_path, 'w') as f:
            f.write(original_content)
        
        print(f"Original content restored to {file_path}")
        return True
    else:
        print("Original backup not found, cannot restore")
        return False

if __name__ == "__main__":
    success = fix_indentation()
    if success:
        print("✅ Fixed indentation issue by restoring from backup")
    else:
        print("❌ Failed to fix indentation issue")
    sys.exit(0 if success else 1)