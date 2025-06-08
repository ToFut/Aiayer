#\!/usr/bin/env python3
"""
Test Emergency Notification System

This script uses the sendEmergencyNotification JavaScript function in the overlay
to display a notification directly in the DOM.
"""

import subprocess
import argparse
import os
import time
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Test emergency notification system')
    parser.add_argument('--message', type=str, default=None, 
                        help='Notification message (default: auto-generated)')
    parser.add_argument('--importance', type=str, default='high', 
                        choices=['high', 'medium', 'low'], 
                        help='Notification importance level')
    
    args = parser.parse_args()
    
    # Generate default message if none provided
    if not args.message:
        timestamp = datetime.now().strftime('%H:%M:%S')
        args.message = f"EMERGENCY NOTIFICATION TEST at {timestamp}. If you can see this, the notification system is working!"
    
    # Escape the message for JavaScript
    message = args.message.replace("'", r"\'").replace('"', r'\"')
    
    # Open Google Chrome DevTools and execute JavaScript
    cmd = [
        'osascript', '-e', 
        f'''
        tell application "Google Chrome"
            activate
            delay 1
            tell application "System Events"
                keystroke "j" using {{command down, option down}}
                delay 0.5
                keystroke "window.sendEmergencyNotification('{message}', null, '{args.importance}');"
                delay 0.2
                key code 36 -- Return/Enter key
            end tell
        end tell
        '''
    ]
    
    print(f"Attempting to inject emergency notification with importance: {args.importance}")
    print(f"Message: {args.message}")
    print("Make sure Chrome is open with the overlay page loaded")
    print("Script will activate Chrome and open DevTools console...")
    
    try:
        subprocess.run(cmd)
        print("\nCommand executed. Check Chrome for the notification.")
        print("If you don't see the notification, make sure Chrome is focused on the overlay page.")
    except Exception as e:
        print(f"Error running AppleScript: {e}")
        print("\nAlternative: Open Chrome DevTools console (Option+Command+J) and paste this JavaScript:")
        print(f"window.sendEmergencyNotification('{message}', null, '{args.importance}');")

if __name__ == "__main__":
    main()
