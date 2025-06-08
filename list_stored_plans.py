#!/usr/bin/env python3
"""
List stored automation plans

This utility script lists all stored automation plans from the persistent storage,
allowing operators to see what plans are available and their current status.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the plan persistence module
try:
    from plan_persistence import plan_manager
except ImportError:
    print("❌ Error: plan_persistence module not available")
    sys.exit(1)

async def list_stored_plans():
    """List all stored plans with details"""
    try:
        # Start the persistence service
        await plan_manager.start_auto_save()
        
        # Get all plan metadata
        plans = await plan_manager.get_all_plan_metadata()
        
        if not plans:
            print("📂 No stored plans found")
            return
        
        print(f"📂 Found {len(plans)} stored plans\n")
        print("{:<20} {:<30} {:<15} {:<20} {:<10}".format(
            "Plan ID", "Title", "Status", "Created", "Steps"
        ))
        print("-" * 100)
        
        for plan in plans:
            # Format the timestamp
            created = datetime.fromtimestamp(plan.get("created", 0)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Truncate long plan IDs
            plan_id = plan.get("plan_id", "unknown")
            if len(plan_id) > 18:
                plan_id = plan_id[:15] + "..."
            
            # Truncate long titles
            title = plan.get("title", "Untitled")
            if len(title) > 28:
                title = title[:25] + "..."
            
            print("{:<20} {:<30} {:<15} {:<20} {:<10}".format(
                plan_id,
                title,
                plan.get("status", "unknown"),
                created,
                plan.get("steps_count", 0)
            ))
        
        # Additional stats
        print("\n📊 Statistics:")
        statuses = {}
        for plan in plans:
            status = plan.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1
        
        for status, count in statuses.items():
            print(f"  • {status}: {count} plans")
        
    except Exception as e:
        print(f"❌ Error listing plans: {e}")
    finally:
        # Stop the auto-save task
        await plan_manager.stop_auto_save()

async def cleanup_old_plans():
    """Clean up old plans"""
    try:
        # Ask for confirmation
        days = input("Enter maximum age in days for plans to keep (or press Enter to skip cleanup): ")
        if not days:
            return
        
        days = int(days)
        if days <= 0:
            print("❌ Invalid number of days")
            return
        
        # Start the persistence service
        await plan_manager.start_auto_save()
        
        # Clean up old plans
        deleted = await plan_manager.cleanup_old_plans(days)
        
        print(f"🧹 Cleaned up {deleted} plans older than {days} days")
        
    except Exception as e:
        print(f"❌ Error cleaning up plans: {e}")
    finally:
        # Stop the auto-save task
        await plan_manager.stop_auto_save()

async def main():
    """Main function"""
    print("📋 Automation Plan Storage Utility\n")
    
    while True:
        print("\nOptions:")
        print("1. List all stored plans")
        print("2. Clean up old plans")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ")
        
        if choice == "1":
            await list_stored_plans()
        elif choice == "2":
            await cleanup_old_plans()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)