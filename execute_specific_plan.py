#!/usr/bin/env python3
"""
Execute Specific Plan Test Script
Loads and executes a plan directly from the cache/plans directory
"""

import asyncio
import json
import os
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/execute_specific_plan.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('execute_specific_plan')

# Try to import the required modules
try:
    from plan_persistence import load_plan, save_plan
    from universal_intelligent_automation_handler import universal_automation_handler
    UNIVERSAL_AVAILABLE = True
    logger.info("✅ Universal automation handler loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Universal automation handler not available: {e}")
    UNIVERSAL_AVAILABLE = False
    universal_automation_handler = None

async def load_and_execute_plan(plan_id):
    """Load a plan from the cache/plans directory and execute it"""
    logger.info(f"🔍 Loading plan: {plan_id}")
    
    # Check if plan_id is a full path or just an ID
    if os.path.exists(plan_id):
        plan_path = plan_id
    else:
        # Check if it's a filename or just an ID
        if not plan_id.endswith('.json'):
            plan_path = os.path.join('cache', 'plans', f"{plan_id}.json")
        else:
            plan_path = os.path.join('cache', 'plans', plan_id)
    
    # Check if plan exists
    if not os.path.exists(plan_path):
        logger.error(f"❌ Plan file not found: {plan_path}")
        return False
    
    # Load plan data
    try:
        with open(plan_path, 'r') as f:
            plan_data = json.load(f)
        
        logger.info(f"✅ Successfully loaded plan: {plan_id}")
        logger.info(f"📄 Plan title: {plan_data.get('title', 'Untitled')}")
        logger.info(f"📋 Plan steps: {len(plan_data.get('steps', []))}")
        
        # Get plan ID from filename if not provided
        if plan_id.endswith('.json'):
            plan_id = os.path.basename(plan_id).replace('.json', '')
        
        # Try to execute the plan
        if UNIVERSAL_AVAILABLE and universal_automation_handler:
            # Log the plan data to understand its structure
            logger.info(f"Plan data type: {type(plan_data)}")
            logger.info(f"Plan data keys: {plan_data.keys() if isinstance(plan_data, dict) else 'Not a dict'}")
            
            # Adapt to the plan structure expected by universal_automation_handler
            # First ensure the plan is loaded into memory
            logger.info(f"🔄 Adding plan to active plans in the handler")
            universal_automation_handler.active_plans[plan_id] = plan_data
            
            # Then execute the plan
            logger.info(f"🚀 Executing plan: {plan_id}")
            result = await universal_automation_handler.handle_button_action('execute_plan', plan_id, plan_id)
            
            logger.info(f"📝 Execution result: {result}")
            return result.get('success', False)
        else:
            logger.error("❌ Universal automation handler not available")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error loading or executing plan: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    # Check if plan ID was provided as command line argument
    if len(sys.argv) > 1:
        plan_id = sys.argv[1]
    else:
        # Use the most recent plan
        plans_dir = os.path.join('cache', 'plans')
        plan_files = [f for f in os.listdir(plans_dir) if f.startswith('plan_') and f.endswith('.json')]
        plan_files.sort(key=lambda f: os.path.getmtime(os.path.join(plans_dir, f)), reverse=True)
        
        if not plan_files:
            logger.error("❌ No plan files found in cache/plans directory")
            return
        
        plan_id = plan_files[0]
        logger.info(f"🔍 Using most recent plan: {plan_id}")
    
    # Load and execute the plan
    success = await load_and_execute_plan(plan_id)
    
    if success:
        logger.info(f"✅ Plan execution successful!")
    else:
        logger.error(f"❌ Plan execution failed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Execution stopped by user")
    except Exception as e:
        logger.error(f"Execution error: {e}")
        import traceback
        logger.error(traceback.format_exc())