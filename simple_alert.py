#\!/usr/bin/env python3
"""
Ultra-simple notification test using applescript to show an alert dialog
"""

import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Simple alert test")
    parser.add_argument("--message", default="This is a test alert. Can you see this?", 
                        help="Alert message")
    args = parser.parse_args()
    
    # Escape message for AppleScript
    message = args.message.replace('"', '\\"')
    
    # AppleScript to show alert
    applescript = f'''
    display dialog "{message}" with title "Notification Test" buttons {{"Yes, I see this", "No"}} default button 1 with icon caution
    '''
    
    # Run the script
    try:
        result = subprocess.run(['osascript', '-e', applescript], 
                               capture_output=True, text=True)
        print(f"Alert shown. Result: {result.stdout}")
    except Exception as e:
        print(f"Error showing alert: {e}")

if __name__ == "__main__":
    main()
