#!/usr/bin/env python3
"""
Add Generate Plan ID Function

This script directly modifies the plan_persistence.py file to add the missing generate_plan_id function.
"""

import os
import re
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/add_generate_plan_id.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AddGeneratePlanId")

def add_generate_plan_id_function():
    """Add the generate_plan_id function to plan_persistence.py"""
    try:
        # Path to the plan_persistence.py file
        file_path = os.path.join(os.getcwd(), "plan_persistence.py")
        
        # Check if the file exists
        if not os.path.exists(file_path):
            logger.error(f"❌ File not found: {file_path}")
            return False
            
        # Read the file
        with open(file_path, "r") as f:
            content = f.read()
            
        # Check if generate_plan_id already exists
        if "def generate_plan_id" in content:
            logger.info("✅ generate_plan_id function already exists in plan_persistence.py")
            return True
            
        # Find the position to insert the function (after the imports but before the first class)
        import_section_end = max(
            content.rfind("import", 0, 200),
            content.rfind("from", 0, 200)
        )
        
        # Find the first real code after imports
        next_section_start = content.find("\n\n", import_section_end)
        if next_section_start == -1:
            next_section_start = content.find("\n", import_section_end)
            
        if next_section_start == -1:
            logger.error("❌ Could not find a good position to insert the function")
            return False
            
        # Create the function to insert
        function_code = """
# Plan ID generation
def generate_plan_id(prefix="plan"):
    '''Generate a unique plan ID with the given prefix'''
    import time
    import uuid
    return f"{prefix}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
"""
        
        # Insert the function
        new_content = content[:next_section_start] + function_code + content[next_section_start:]
        
        # Write the updated content back to the file
        with open(file_path, "w") as f:
            f.write(new_content)
            
        logger.info("✅ Added generate_plan_id function to plan_persistence.py")
        
        # Now restart the fix_do_button_pending_plans.py process
        restart_fix_script()
        
        return True
    except Exception as e:
        logger.error(f"❌ Error adding generate_plan_id function: {e}")
        return False

def restart_fix_script():
    """Restart the fix_do_button_pending_plans.py process"""
    try:
        import subprocess
        import signal
        import psutil
        
        # Find the process ID of fix_do_button_pending_plans.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'fix_do_button_pending_plans.py' in ' '.join(proc.info['cmdline']):
                    logger.info(f"Found fix_do_button_pending_plans.py process: PID {proc.info['pid']}")
                    
                    # Kill the process
                    os.kill(proc.info['pid'], signal.SIGTERM)
                    logger.info(f"Terminated fix_do_button_pending_plans.py process: PID {proc.info['pid']}")
                    
                    # Wait for the process to terminate
                    try:
                        psutil.Process(proc.info['pid']).wait(timeout=5)
                        logger.info(f"Process PID {proc.info['pid']} terminated successfully")
                    except psutil.TimeoutExpired:
                        logger.warning(f"Process PID {proc.info['pid']} did not terminate within timeout, forcing kill")
                        os.kill(proc.info['pid'], signal.SIGKILL)
                    except psutil.NoSuchProcess:
                        logger.info(f"Process PID {proc.info['pid']} already terminated")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Start the process again
        script_path = os.path.join(os.getcwd(), "fix_do_button_pending_plans.py")
        if os.path.exists(script_path):
            process = subprocess.Popen(["python", script_path], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, 
                                      start_new_session=True)
            logger.info(f"Started fix_do_button_pending_plans.py with PID {process.pid}")
            return True
        else:
            logger.error(f"❌ Could not find fix_do_button_pending_plans.py at {script_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Error restarting fix_do_button_pending_plans.py: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting Add Generate Plan ID")
    
    # Add the function to plan_persistence.py
    if add_generate_plan_id_function():
        logger.info("✅ Successfully added generate_plan_id function to plan_persistence.py")
        
        # Restart the fix_do_button_pending_plans.py process
        if restart_fix_script():
            logger.info("✅ Successfully restarted fix_do_button_pending_plans.py")
        else:
            logger.error("❌ Failed to restart fix_do_button_pending_plans.py")
    else:
        logger.error("❌ Failed to add generate_plan_id function to plan_persistence.py")
        
    logger.info("✅ Add Generate Plan ID completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Add Generate Plan ID stopped by user")
    except Exception as e:
        logger.error(f"Error in Add Generate Plan ID: {e}")
        import traceback
        logger.error(traceback.format_exc())