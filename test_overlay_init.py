#!/usr/bin/env python3
import json
import os
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_overlay_config():
    """Check the overlay configuration to verify WebSocket URL"""
    config_path = os.path.expanduser("~/Desktop/SensAI/Aiayer/overlay/src/config.js")
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            logger.info(f"Overlay config file contents:\n{content}")
            
            # Check if WebSocket URL is correctly set
            if "ws://localhost:8765" in content:
                logger.info("✅ Overlay is configured to connect to the correct WebSocket URL (8765)")
                return True
            else:
                logger.error("❌ Overlay is NOT configured to connect to port 8765")
                return False
    except Exception as e:
        logger.error(f"Error reading config file: {str(e)}")
        return False

def restart_overlay():
    """Restart the overlay application"""
    try:
        # Stop current overlay
        logger.info("Stopping current overlay process...")
        subprocess.run("cd ~/Desktop/SensAI/Aiayer/overlay && npm run tauri dev -- --close", shell=True, text=True, capture_output=True)
        
        # Start new overlay
        logger.info("Starting overlay in development mode...")
        subprocess.Popen("cd ~/Desktop/SensAI/Aiayer/overlay && npm run tauri dev", shell=True, text=True)
        
        logger.info("Overlay restart initiated")
        return True
    except Exception as e:
        logger.error(f"Error restarting overlay: {str(e)}")
        return False

def check_running_processes():
    """Check what relevant processes are running"""
    try:
        logger.info("Checking running processes...")
        result = subprocess.run("ps aux | grep -i 'fix_do_button\\|ws_server\\|bridge\\|8765\\|8766\\|overlay'", 
                              shell=True, text=True, capture_output=True)
        
        logger.info(f"Running processes:\n{result.stdout}")
        return True
    except Exception as e:
        logger.error(f"Error checking processes: {str(e)}")
        return False

def main():
    logger.info("=== OVERLAY INITIALIZATION TEST ===")
    
    # Check running processes
    check_running_processes()
    
    # Check overlay config
    config_status = check_overlay_config()
    
    # Based on config, decide if we should restart overlay
    if not config_status:
        logger.warning("Overlay configuration might be incorrect")
        restart = input("Do you want to restart the overlay? (y/n): ")
        if restart.lower() == 'y':
            restart_overlay()
    
    logger.info("""
VISUAL VERIFICATION NEEDED:
1. Look at your screen - do you see the overlay app?
2. It should appear as a floating window or icon
3. Check if the overlay is in focus or if it needs to be clicked
4. The overlay should be listening for WebSocket messages on port 8765
5. If you don't see the overlay, try running: 
   cd ~/Desktop/SensAI/Aiayer/overlay && npm run tauri dev
""")

if __name__ == "__main__":
    main()