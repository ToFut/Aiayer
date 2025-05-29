#!/usr/bin/env python3
"""
Simple script to check running applications on macOS
"""
import psutil
import os
from AppKit import NSWorkspace
import json

def get_running_applications():
    """Get list of running applications"""
    try:
        # Get running applications using NSWorkspace
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        
        apps_info = []
        for app in running_apps:
            app_info = {
                'name': app.localizedName() or 'Unknown',
                'bundle_id': app.bundleIdentifier() or 'Unknown',
                'pid': app.processIdentifier(),
                'active': app.isActive(),
                'hidden': app.isHidden()
            }
            apps_info.append(app_info)
        
        return apps_info
    except Exception as e:
        print(f"Error getting applications: {e}")
        return []

def get_processes():
    """Get running processes using psutil"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes

if __name__ == "__main__":
    print("🖥️  RUNNING APPLICATIONS ON YOUR PC:")
    print("=" * 50)
    
    # Get applications
    apps = get_running_applications()
    if apps:
        # Filter out system processes and focus on user applications
        user_apps = [app for app in apps if not app['name'].startswith('com.') and app['name'] != 'Unknown']
        
        print(f"\n📱 USER APPLICATIONS ({len(user_apps)} running):")
        for i, app in enumerate(user_apps, 1):
            status = "🟢 Active" if app['active'] else "⚪ Background"
            hidden = " (Hidden)" if app['hidden'] else ""
            print(f"{i:2d}. {app['name']:25} - PID: {app['pid']:6} - {status}{hidden}")
        
        print(f"\n🔧 ALL APPLICATIONS ({len(apps)} total):")
        for i, app in enumerate(apps, 1):
            status = "🟢" if app['active'] else "⚪"
            print(f"{i:2d}. {status} {app['name']}")
    else:
        print("❌ Could not retrieve application list")
    
    print("\n" + "=" * 50)
    print("✅ Done!")