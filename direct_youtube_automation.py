#!/usr/bin/env python3

import subprocess
import time
import pyautogui
import webbrowser
from urllib.parse import quote

def open_youtube_and_search_segev():
    """Directly automate opening YouTube and searching for SEGEV"""
    
    print("🎬 Starting direct YouTube automation...")
    print("🔍 Target: Search for 'SEGEV' on YouTube")
    print("=" * 50)
    
    try:
        # Step 1: Open YouTube in default browser
        print("📱 Step 1: Opening YouTube...")
        youtube_url = "https://www.youtube.com"
        webbrowser.open(youtube_url)
        
        # Wait for browser to load
        print("⏳ Waiting for browser to load...")
        time.sleep(3)
        
        # Step 2: Try to find and click search box
        print("🔍 Step 2: Looking for search box...")
        
        # Wait a bit more for page to fully load
        time.sleep(2)
        
        # Try to find the search box using keyboard shortcut (more reliable)
        print("⌨️ Using keyboard shortcut to access search...")
        
        # Press '/' to focus on search box (YouTube shortcut)
        pyautogui.press('/')
        time.sleep(0.5)
        
        # Step 3: Type the search term
        print("✍️ Step 3: Typing 'SEGEV'...")
        pyautogui.typewrite('SEGEV', interval=0.1)
        time.sleep(0.5)
        
        # Step 4: Press Enter to search
        print("🔄 Step 4: Executing search...")
        pyautogui.press('enter')
        
        print("✅ YouTube automation completed successfully!")
        print("🎯 Search for 'SEGEV' should now be running on YouTube")
        
        return True
        
    except Exception as e:
        print(f"❌ Automation failed: {e}")
        print("💡 Make sure:")
        print("   - You have pyautogui installed: pip install pyautogui")
        print("   - Your system allows automation (check accessibility settings)")
        return False

def alternative_youtube_search():
    """Alternative method: Direct URL search"""
    print("\n🔄 Trying alternative method: Direct URL search...")
    
    try:
        # Construct YouTube search URL
        search_term = "SEGEV"
        search_url = f"https://www.youtube.com/results?search_query={quote(search_term)}"
        
        print(f"🌐 Opening: {search_url}")
        webbrowser.open(search_url)
        
        print("✅ Alternative method completed!")
        print("🎯 YouTube search results for 'SEGEV' should now be open")
        return True
        
    except Exception as e:
        print(f"❌ Alternative method failed: {e}")
        return False

if __name__ == "__main__":
    # Try main automation method
    success = open_youtube_and_search_segev()
    
    # If main method fails, try alternative
    if not success:
        alternative_youtube_search()
    
    print("\n🏁 Automation script finished")