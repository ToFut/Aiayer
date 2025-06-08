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

def update_overlay_config():
    """Update the overlay configuration to connect to the proxy directly"""
    config_path = os.path.expanduser("~/Desktop/SensAI/Aiayer/overlay/src/config.js")
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at {config_path}")
        return False
    
    try:
        # Backup the current config
        backup_path = f"{config_path}.bak"
        with open(config_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
            logger.info(f"Created backup at {backup_path}")
        
        # Read the current config
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Replace the backend URL with the proxy URL
        updated_content = content.replace(
            "url: 'ws://localhost:8767'", 
            "url: 'ws://localhost:8766'"  # Connect to proxy instead
        )
        
        # Write the updated config
        with open(config_path, 'w') as f:
            f.write(updated_content)
        
        logger.info("✅ Updated overlay config to connect to proxy server on port 8766")
        
        # Also create a dedicated direct connection to the DO button server
        do_button_connection = """
        // DO button server for direct automation and notifications
        doButton: {
            url: 'ws://localhost:8765',
            reconnectAttempts: 10,
            reconnectDelay: 1000,
            debug: true
        },"""
        
        # Insert the DO button connection into the websockets section
        with open(config_path, 'r') as f:
            content = f.read()
        
        if "doButton: {" not in content:
            insertion_point = "websockets: {"
            updated_content = content.replace(
                insertion_point,
                f"{insertion_point}\n{do_button_connection}"
            )
            
            with open(config_path, 'w') as f:
                f.write(updated_content)
            
            logger.info("✅ Added direct DO button connection to config")
        
        return True
    except Exception as e:
        logger.error(f"Error updating config file: {str(e)}")
        return False

def update_nextgen_component():
    """Update the NextGenAppleChatWidget to connect to the DO button server directly"""
    component_path = os.path.expanduser("~/Desktop/SensAI/Aiayer/overlay/src/components/NextGenAppleChatWidget.svelte")
    
    if not os.path.exists(component_path):
        logger.error(f"Component file not found at {component_path}")
        return False
    
    try:
        # Look for the WebSocket connection section
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Find the onMount function and add a direct connection to DO button server
        if "onMount(async () => {" in content and "// Connect to DO button server" not in content:
            # Add direct connection to DO button server
            direct_connection = """
    // Connect to DO button server directly for notifications
    let doButtonSocket;
    
    const connectToDoButton = async () => {
      try {
        doButtonSocket = new WebSocket('ws://localhost:8765');
        
        doButtonSocket.onopen = () => {
          console.log('✅ Connected to DO button server');
        };
        
        doButtonSocket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log('📩 Received message from DO button server:', data);
          
          // Handle suggestion messages
          if (data.type === 'suggestion') {
            console.log('💡 Received suggestion from DO button server:', data);
            
            // Play notification sound if enabled
            if (data.play_sound && soundEnabled) {
              playSound('notification');
            }
            
            // Add the suggestion to messages
            const suggestionMessage = {
              id: Date.now(),
              type: 'suggestion',
              content: data.response || '',
              buttons: data.buttons || [],
              timestamp: new Date(),
              importance: data.importance || 'high',
              plan_id: data.plan_id || `suggestion_${Date.now()}`
            };
            
            messages = [...messages, suggestionMessage];
            
            // Scroll to bottom
            setTimeout(() => {
              if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
              }
            }, 100);
          }
        };
        
        doButtonSocket.onclose = () => {
          console.log('⚠️ DO button server connection closed');
          setTimeout(connectToDoButton, 2000);
        };
        
        doButtonSocket.onerror = (error) => {
          console.error('❌ DO button server connection error:', error);
        };
      } catch (error) {
        console.error('❌ Failed to connect to DO button server:', error);
        setTimeout(connectToDoButton, 2000);
      }
    };
    
    // Connect to both servers
    connectToDoButton();"""
            
            # Insert the direct connection after onMount
            insertion_point = "onMount(async () => {"
            updated_content = content.replace(
                insertion_point,
                f"{insertion_point}\n{direct_connection}"
            )
            
            # Backup the component
            backup_path = f"{component_path}.bak.direct"
            with open(backup_path, 'w') as f:
                f.write(content)
                logger.info(f"Created backup at {backup_path}")
            
            # Write the updated component
            with open(component_path, 'w') as f:
                f.write(updated_content)
            
            logger.info("✅ Updated NextGenAppleChatWidget with direct DO button connection")
            return True
        else:
            logger.warning("Could not find insertion point in component or modification already exists")
            return False
    except Exception as e:
        logger.error(f"Error updating component: {str(e)}")
        return False

def rebuild_overlay():
    """Rebuild the overlay with updated config"""
    try:
        logger.info("Building overlay with updated config...")
        result = subprocess.run("cd ~/Desktop/SensAI/Aiayer/overlay && npm run build", 
                              shell=True, text=True, capture_output=True)
        
        if result.returncode == 0:
            logger.info("✅ Overlay built successfully")
            logger.info(result.stdout)
            return True
        else:
            logger.error("❌ Overlay build failed")
            logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Error building overlay: {str(e)}")
        return False

def restart_overlay():
    """Restart the overlay application"""
    try:
        # Find and kill the current overlay process
        logger.info("Stopping current overlay processes...")
        subprocess.run("pkill -f 'ai-assistant-overlay'", shell=True, text=True)
        
        # Start the overlay application
        logger.info("Starting overlay application...")
        subprocess.Popen("cd ~/Desktop/SensAI/Aiayer/overlay && npm run tauri dev", 
                      shell=True, text=True)
        
        logger.info("✅ Overlay restart initiated")
        return True
    except Exception as e:
        logger.error(f"Error restarting overlay: {str(e)}")
        return False

def main():
    logger.info("=== FIXING OVERLAY CONNECTION ===")
    
    # Update the config
    config_updated = update_overlay_config()
    
    # Update the component for direct notification handling
    component_updated = update_nextgen_component()
    
    # Rebuild the overlay
    if config_updated or component_updated:
        rebuild_success = rebuild_overlay()
        
        if rebuild_success:
            restart_success = restart_overlay()
            
            if restart_success:
                logger.info("""
✅ OVERLAY CONNECTION FIX COMPLETE!
- Overlay now connects to proxy on port 8766
- Added direct connection to DO button server on port 8765
- Rebuilt and restarted the overlay

You should now receive notifications properly. Try sending a test notification:
python3 test_proxy_notification.py
""")
            else:
                logger.error("Failed to restart overlay. Try manually: cd ~/Desktop/SensAI/Aiayer/overlay && npm run tauri dev")
        else:
            logger.error("Failed to rebuild overlay. Check the logs for details.")
    else:
        logger.warning("No changes were made to the overlay config or component.")

if __name__ == "__main__":
    main()