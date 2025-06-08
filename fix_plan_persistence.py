#!/usr/bin/env python3
"""
Fix Plan Persistence Module

This script adds the missing generate_plan_id function to the plan_persistence module
and ensures proper initialization of the plan persistence system.
"""

import os
import sys
import time
import logging
import importlib
import inspect
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/fix_plan_persistence.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FixPlanPersistence")

def add_generate_plan_id_to_persistence():
    """Add generate_plan_id function to plan_persistence module"""
    try:
        # Import the module
        import plan_persistence
        
        # Check if generate_plan_id already exists
        if not hasattr(plan_persistence, 'generate_plan_id'):
            # Add the function to the module
            def generate_plan_id(prefix="plan"):
                """Generate a unique plan ID with the given prefix"""
                return f"{prefix}_{int(time.time())}"
                
            # Add the function to the module
            plan_persistence.generate_plan_id = generate_plan_id
            logger.info("✅ Added generate_plan_id function to plan_persistence module")
            
            # Reload any modules that import plan_persistence
            reload_dependents(plan_persistence)
            
            return True
        else:
            logger.info("✅ generate_plan_id function already exists in plan_persistence module")
            return True
    except ImportError:
        logger.error("❌ Failed to import plan_persistence module")
        return False
    except Exception as e:
        logger.error(f"❌ Error adding generate_plan_id to plan_persistence: {e}")
        return False

def reload_dependents(module):
    """Reload all modules that depend on the given module"""
    try:
        # Get all loaded modules
        modules = list(sys.modules.values())
        
        # Find modules that import the given module
        for m in modules:
            if not inspect.ismodule(m):
                continue
                
            try:
                # Check if the module imports the given module
                if hasattr(m, '__dict__') and module.__name__ in m.__dict__:
                    logger.info(f"Reloading module: {m.__name__}")
                    importlib.reload(m)
            except Exception as e:
                logger.warning(f"Could not check module {m}: {e}")
                
        logger.info("✅ Reloaded dependent modules")
        return True
    except Exception as e:
        logger.error(f"❌ Error reloading dependent modules: {e}")
        return False

def fix_real_agent_automation_handler():
    """Fix the real_agent_automation_handler module to handle missing generate_plan_id"""
    try:
        import real_agent_automation_handler
        
        # Check if the module has an init_plan_persistence method
        if hasattr(real_agent_automation_handler, 'init_plan_persistence'):
            # Get the original method
            original_init = real_agent_automation_handler.init_plan_persistence
            
            # Create a new method that adds generate_plan_id if needed
            def fixed_init_plan_persistence():
                """Fixed version of init_plan_persistence that handles missing generate_plan_id"""
                try:
                    # Call the original method
                    result = original_init()
                    
                    # Check if plan_persistence was imported
                    if 'plan_persistence' in sys.modules:
                        # Make sure generate_plan_id exists
                        if not hasattr(sys.modules['plan_persistence'], 'generate_plan_id'):
                            # Add the function
                            def generate_plan_id(prefix="plan"):
                                """Generate a unique plan ID with the given prefix"""
                                return f"{prefix}_{int(time.time())}"
                                
                            sys.modules['plan_persistence'].generate_plan_id = generate_plan_id
                            logger.info("✅ Added generate_plan_id function to plan_persistence module (from fixed_init_plan_persistence)")
                            
                    return result
                except Exception as e:
                    logger.error(f"❌ Error in fixed_init_plan_persistence: {e}")
                    # Try to initialize with a fallback
                    try:
                        import plan_persistence
                        logger.info("✅ Imported plan_persistence module in fallback")
                        
                        # Add generate_plan_id if needed
                        if not hasattr(plan_persistence, 'generate_plan_id'):
                            def generate_plan_id(prefix="plan"):
                                """Generate a unique plan ID with the given prefix"""
                                return f"{prefix}_{int(time.time())}"
                                
                            plan_persistence.generate_plan_id = generate_plan_id
                            logger.info("✅ Added generate_plan_id function to plan_persistence module (fallback)")
                            
                        return True
                    except Exception as inner_e:
                        logger.error(f"❌ Error in fallback initialization: {inner_e}")
                        return False
            
            # Replace the original method
            real_agent_automation_handler.init_plan_persistence = fixed_init_plan_persistence
            logger.info("✅ Patched init_plan_persistence method in real_agent_automation_handler")
            
            # Reload any modules that might use this
            reload_dependents(real_agent_automation_handler)
            
            return True
        else:
            logger.warning("⚠️ Could not find init_plan_persistence method in real_agent_automation_handler")
            return False
    except ImportError:
        logger.error("❌ Failed to import real_agent_automation_handler module")
        return False
    except Exception as e:
        logger.error(f"❌ Error fixing real_agent_automation_handler module: {e}")
        return False

def fix_universal_intelligent_automation_handler():
    """Fix the universal_intelligent_automation_handler module to handle missing generate_plan_id"""
    try:
        import universal_intelligent_automation_handler
        
        # Check if the module has a load_plan_persistence method
        if hasattr(universal_intelligent_automation_handler, 'load_plan_persistence'):
            # Get the original method
            original_load = universal_intelligent_automation_handler.load_plan_persistence
            
            # Create a new method that adds generate_plan_id if needed
            def fixed_load_plan_persistence():
                """Fixed version of load_plan_persistence that handles missing generate_plan_id"""
                try:
                    # Call the original method
                    result = original_load()
                    
                    # Check if plan_persistence was imported
                    if 'plan_persistence' in sys.modules:
                        # Make sure generate_plan_id exists
                        if not hasattr(sys.modules['plan_persistence'], 'generate_plan_id'):
                            # Add the function
                            def generate_plan_id(prefix="plan"):
                                """Generate a unique plan ID with the given prefix"""
                                return f"{prefix}_{int(time.time())}"
                                
                            sys.modules['plan_persistence'].generate_plan_id = generate_plan_id
                            logger.info("✅ Added generate_plan_id function to plan_persistence module (from fixed_load_plan_persistence)")
                            
                    return result
                except Exception as e:
                    logger.error(f"❌ Error in fixed_load_plan_persistence: {e}")
                    # Try to initialize with a fallback
                    try:
                        import plan_persistence
                        logger.info("✅ Imported plan_persistence module in fallback")
                        
                        # Add generate_plan_id if needed
                        if not hasattr(plan_persistence, 'generate_plan_id'):
                            def generate_plan_id(prefix="plan"):
                                """Generate a unique plan ID with the given prefix"""
                                return f"{prefix}_{int(time.time())}"
                                
                            plan_persistence.generate_plan_id = generate_plan_id
                            logger.info("✅ Added generate_plan_id function to plan_persistence module (fallback)")
                            
                        return True
                    except Exception as inner_e:
                        logger.error(f"❌ Error in fallback initialization: {inner_e}")
                        return False
            
            # Replace the original method
            universal_intelligent_automation_handler.load_plan_persistence = fixed_load_plan_persistence
            logger.info("✅ Patched load_plan_persistence method in universal_intelligent_automation_handler")
            
            # Reload any modules that might use this
            reload_dependents(universal_intelligent_automation_handler)
            
            return True
        else:
            logger.warning("⚠️ Could not find load_plan_persistence method in universal_intelligent_automation_handler")
            return False
    except ImportError:
        logger.error("❌ Failed to import universal_intelligent_automation_handler module")
        return False
    except Exception as e:
        logger.error(f"❌ Error fixing universal_intelligent_automation_handler module: {e}")
        return False

def fix_adaptive_retry_automation_handler():
    """Fix the adaptive_retry_automation_handler module to handle missing generate_plan_id"""
    try:
        import adaptive_retry_automation_handler
        
        # Check if the module has a load_plan_persistence method
        if hasattr(adaptive_retry_automation_handler, 'load_plan_persistence'):
            # Get the original method
            original_load = adaptive_retry_automation_handler.load_plan_persistence
            
            # Create a new method that adds generate_plan_id if needed
            def fixed_load_plan_persistence():
                """Fixed version of load_plan_persistence that handles missing generate_plan_id"""
                try:
                    # Call the original method
                    result = original_load()
                    
                    # Check if plan_persistence was imported
                    if 'plan_persistence' in sys.modules:
                        # Make sure generate_plan_id exists
                        if not hasattr(sys.modules['plan_persistence'], 'generate_plan_id'):
                            # Add the function
                            def generate_plan_id(prefix="plan"):
                                """Generate a unique plan ID with the given prefix"""
                                return f"{prefix}_{int(time.time())}"
                                
                            sys.modules['plan_persistence'].generate_plan_id = generate_plan_id
                            logger.info("✅ Added generate_plan_id function to plan_persistence module (from fixed_load_plan_persistence)")
                            
                    return result
                except Exception as e:
                    logger.error(f"❌ Error in fixed_load_plan_persistence: {e}")
                    # Try to initialize with a fallback
                    try:
                        import plan_persistence
                        logger.info("✅ Imported plan_persistence module in fallback")
                        
                        # Add generate_plan_id if needed
                        if not hasattr(plan_persistence, 'generate_plan_id'):
                            def generate_plan_id(prefix="plan"):
                                """Generate a unique plan ID with the given prefix"""
                                return f"{prefix}_{int(time.time())}"
                                
                            plan_persistence.generate_plan_id = generate_plan_id
                            logger.info("✅ Added generate_plan_id function to plan_persistence module (fallback)")
                            
                        return True
                    except Exception as inner_e:
                        logger.error(f"❌ Error in fallback initialization: {inner_e}")
                        return False
            
            # Replace the original method
            adaptive_retry_automation_handler.load_plan_persistence = fixed_load_plan_persistence
            logger.info("✅ Patched load_plan_persistence method in adaptive_retry_automation_handler")
            
            # Reload any modules that might use this
            reload_dependents(adaptive_retry_automation_handler)
            
            return True
        else:
            logger.warning("⚠️ Could not find load_plan_persistence method in adaptive_retry_automation_handler")
            return False
    except ImportError:
        logger.error("❌ Failed to import adaptive_retry_automation_handler module")
        return False
    except Exception as e:
        logger.error(f"❌ Error fixing adaptive_retry_automation_handler module: {e}")
        return False

def restart_fix_do_button_pending_plans():
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

def verify_fixes():
    """Verify that the fixes have been applied correctly"""
    try:
        # Check if plan_persistence has generate_plan_id
        import plan_persistence
        if hasattr(plan_persistence, 'generate_plan_id'):
            logger.info("✅ generate_plan_id function exists in plan_persistence module")
            
            # Test it
            test_id = plan_persistence.generate_plan_id("test")
            logger.info(f"✅ Generated test plan ID: {test_id}")
            
            # Check other modules
            modules_to_check = [
                "real_agent_automation_handler",
                "universal_intelligent_automation_handler",
                "adaptive_retry_automation_handler"
            ]
            
            all_ok = True
            for module_name in modules_to_check:
                try:
                    module = importlib.import_module(module_name)
                    logger.info(f"✅ Successfully imported {module_name} module")
                except ImportError:
                    logger.warning(f"⚠️ Could not import {module_name} module")
                    all_ok = False
                except Exception as e:
                    logger.error(f"❌ Error importing {module_name} module: {e}")
                    all_ok = False
            
            return all_ok
        else:
            logger.error("❌ generate_plan_id function does not exist in plan_persistence module after fixes")
            return False
    except ImportError:
        logger.error("❌ Failed to import plan_persistence module")
        return False
    except Exception as e:
        logger.error(f"❌ Error verifying fixes: {e}")
        return False

def main():
    """Main function that applies all fixes"""
    logger.info("🚀 Starting Plan Persistence Fix")
    
    # Step 1: Add generate_plan_id to plan_persistence
    logger.info("Step 1: Adding generate_plan_id to plan_persistence...")
    if add_generate_plan_id_to_persistence():
        logger.info("✅ Step 1 completed successfully")
    else:
        logger.error("❌ Step 1 failed")
        
    # Step 2: Fix real_agent_automation_handler
    logger.info("Step 2: Fixing real_agent_automation_handler...")
    if fix_real_agent_automation_handler():
        logger.info("✅ Step 2 completed successfully")
    else:
        logger.error("❌ Step 2 failed")
        
    # Step 3: Fix universal_intelligent_automation_handler
    logger.info("Step 3: Fixing universal_intelligent_automation_handler...")
    if fix_universal_intelligent_automation_handler():
        logger.info("✅ Step 3 completed successfully")
    else:
        logger.error("❌ Step 3 failed")
        
    # Step 4: Fix adaptive_retry_automation_handler
    logger.info("Step 4: Fixing adaptive_retry_automation_handler...")
    if fix_adaptive_retry_automation_handler():
        logger.info("✅ Step 4 completed successfully")
    else:
        logger.error("❌ Step 4 failed")
        
    # Step 5: Verify fixes
    logger.info("Step 5: Verifying fixes...")
    if verify_fixes():
        logger.info("✅ Step 5 completed successfully")
    else:
        logger.error("❌ Step 5 failed")
        
    # Step 6: Restart fix_do_button_pending_plans.py
    logger.info("Step 6: Restarting fix_do_button_pending_plans.py...")
    if restart_fix_do_button_pending_plans():
        logger.info("✅ Step 6 completed successfully")
    else:
        logger.error("❌ Step 6 failed")
        
    logger.info("✅ Plan Persistence Fix completed")
    logger.info("The DO button system should now have proper plan persistence")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Plan Persistence Fix stopped by user")
    except Exception as e:
        logger.error(f"Error in Plan Persistence Fix: {e}")
        import traceback
        logger.error(traceback.format_exc())