#!/usr/bin/env python3
"""
Enhanced Screen Sensor
Captures screen data and sends it to the bridge server.
"""
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import websockets
from websockets.client import WebSocketClientProtocol
import subprocess
import hashlib

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BRIDGE_SERVER_URI = "ws://localhost:8765"  # Connect directly to WebSocket server
CLIENT_TYPE = "screen_sensor"
VERSION = "1.0.0"
CAPABILITIES = ["screen_capture", "image_hash"]

async def connect_to_bridge() -> Optional[WebSocketClientProtocol]:
    """Connect to the bridge server."""
    try:
        websocket = await websockets.connect(BRIDGE_SERVER_URI)
        logger.info("Connected to bridge server")
        return websocket
    except Exception as e:
        logger.error(f"Error connecting to bridge server: {e}")
        return None

async def register_with_bridge(websocket: WebSocketClientProtocol) -> bool:
    """Register with the bridge server."""
    try:
        # First, receive the welcome message
        welcome = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        welcome_data = json.loads(welcome)
        logger.info(f"Received welcome: {welcome_data.get('type')}")
        
        # Send registration message
        registration_msg = {
            "type": "register",
            "client_type": CLIENT_TYPE,
            "version": VERSION,
            "capabilities": CAPABILITIES,
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send(json.dumps(registration_msg))
        logger.info("Sent registration message")
        
        # Wait for registration confirmation
        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        data = json.loads(response)
        
        if data.get("type") == "registration_success":
            logger.info(f"Registration successful: {data.get('message')}")
            return True
        elif data.get("type") == "registration_confirmed":
            logger.info(f"Registration confirmed as {data.get('payload', {}).get('client_type')}")
            return True
        else:
            logger.error(f"Unexpected response to registration: {data}")
            return False
            
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for registration confirmation")
        return False
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return False

def get_active_window_info() -> Dict[str, str]:
    """Get information about the currently active window (macOS specific)."""
    try:
        logger.debug("Attempting to get active window info...")
        
        # Method 1: Try AppleScript for app and window info
        try:
            app_script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''
            
            window_script = '''
            tell application "System Events"
                try
                    set frontWindow to name of front window of first application process whose frontmost is true
                    return frontWindow
                on error
                    return "Main Window"
                end try
            end tell
            '''
            
            # Get app name
            app_result = subprocess.run(['osascript', '-e', app_script], 
                                      capture_output=True, text=True, timeout=3)
            app_name = app_result.stdout.strip() if app_result.returncode == 0 else 'Unknown'
            
            # Get window name
            window_result = subprocess.run(['osascript', '-e', window_script], 
                                         capture_output=True, text=True, timeout=3)
            window_name = window_result.stdout.strip() if window_result.returncode == 0 else 'Main Window'
            
            # Clean up app name (remove " (Renderer)" suffixes etc)
            if app_name != 'Unknown':
                app_name = app_name.split(' (')[0]  # Remove helper process names
                app_name = app_name.replace('Helper', '').strip()
                
            # Create window title in format "App - Window"
            if window_name and window_name != 'Main Window' and app_name != 'Unknown':
                window_title = f"{app_name} - {window_name}"
            else:
                window_title = app_name if app_name != 'Unknown' else 'Unknown Window'
            
            result = {
                'active_app': app_name,
                'active_window': window_title
            }
            
            logger.debug(f"Successfully got window info: {result}")
            return result
            
        except subprocess.TimeoutExpired:
            logger.warning("AppleScript timeout - using fallback method")
            
        # Method 2: Fallback - try to get just the frontmost app
        try:
            simple_script = 'tell application "System Events" to get name of first process whose frontmost is true'
            result = subprocess.run(['osascript', '-e', simple_script], 
                                  capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0 and result.stdout.strip():
                app_name = result.stdout.strip().split(' (')[0]  # Clean helper names
                return {
                    'active_app': app_name,
                    'active_window': f"{app_name} - Main Window"
                }
        except Exception as e:
            logger.warning(f"Fallback method failed: {e}")
            
        # Method 3: Use psutil as last resort
        try:
            import psutil
            # Find processes with highest CPU that aren't system processes
            processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                try:
                    if proc.info['name'] not in ['kernel_task', 'WindowServer', 'loginwindow']:
                        processes.append((proc.info['name'], proc.info['cpu_percent'] or 0))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if processes:
                # Sort by CPU and take the most active non-system process
                processes.sort(key=lambda x: x[1], reverse=True)
                app_name = processes[0][0]
                return {
                    'active_app': app_name,
                    'active_window': f"{app_name} - Active Window"
                }
        except Exception as e:
            logger.warning(f"psutil fallback failed: {e}")
            
    except Exception as e:
        logger.error(f"Error getting active window info: {e}")
    
    # Final fallback
    logger.debug("Using final fallback for window detection")
    return {'active_app': 'Unknown', 'active_window': 'Unknown Window'}

def capture_screen_text() -> Dict[str, Any]:
    """Capture actual screen content and application data."""
    try:
        # Get window and application info
        window_info = get_active_window_info()
        
        # Try to get actual screen content using various methods
        screen_content = ""
        confidence = 0.8
        
        # Method 1: Try to get clipboard content (if recently copied)
        try:
            clipboard_result = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=1)
            if clipboard_result.returncode == 0 and clipboard_result.stdout.strip():
                recent_clipboard = clipboard_result.stdout.strip()[:500]  # Limit size
                screen_content += f"Recent clipboard: {recent_clipboard}\n"
        except Exception:
            pass
            
        # Method 2: Get application-specific information
        app_name = window_info['active_app'].lower()
        
        # Enhanced content based on application
        if 'cursor' in app_name or 'code' in app_name:
            screen_content += f"Development Environment: {window_info['active_app']}\n"
            screen_content += f"Current Project Window: {window_info['active_window']}\n"
            screen_content += "Coding activity detected - text editor/IDE environment\n"
            
            # Try to detect file type from window title
            window_title = window_info['active_window'].lower()
            if '.py' in window_title:
                screen_content += "Python file editing detected\n"
            elif '.js' in window_title or '.ts' in window_title:
                screen_content += "JavaScript/TypeScript editing detected\n"
            elif '.md' in window_title:
                screen_content += "Markdown document editing detected\n"
            elif 'readme' in window_title:
                screen_content += "README file editing detected\n"
                
        elif 'chrome' in app_name or 'safari' in app_name or 'firefox' in app_name:
            screen_content += f"Web Browser: {window_info['active_app']}\n"
            screen_content += f"Current Tab/Page: {window_info['active_window']}\n"
            screen_content += "Web browsing activity detected\n"
            
            # Detect website context from window title
            window_title = window_info['active_window'].lower()
            if 'github' in window_title:
                screen_content += "GitHub repository or development platform\n"
            elif 'stackoverflow' in window_title:
                screen_content += "Programming Q&A platform\n"
            elif 'google' in window_title:
                screen_content += "Google search or services\n"
            elif 'claude' in window_title:
                screen_content += "Claude AI assistant interface\n"
                
        elif 'terminal' in app_name or 'iterm' in app_name:
            screen_content += f"Terminal Application: {window_info['active_app']}\n"
            screen_content += "Command line interface detected\n"
            screen_content += "Terminal/shell activity in progress\n"
            
        elif 'finder' in app_name:
            screen_content += f"File Manager: {window_info['active_app']}\n"
            screen_content += f"Current Location: {window_info['active_window']}\n"
            screen_content += "File system navigation detected\n"
            
        else:
            screen_content += f"Application: {window_info['active_app']}\n"
            screen_content += f"Window: {window_info['active_window']}\n"
            screen_content += "General application usage detected\n"
        
        # Add timestamp and system context
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        screen_content += f"Capture time: {current_time}\n"
        
        # Get screen resolution info
        try:
            resolution_result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                             capture_output=True, text=True, timeout=3)
            if 'Resolution:' in resolution_result.stdout:
                screen_content += "High-resolution display detected\n"
        except Exception:
            pass
            
        return {
            'screen_text': screen_content,
            'window_title': window_info['active_window'],
            'active_app': window_info['active_app'],
            'screen_size': [2940, 1912],  # Default MacBook resolution
            'has_images': True,  # Assume UI elements
            'has_videos': False,
            'confidence': confidence,
            'capture_method': 'application_context',
            'timestamp': current_time
        }
        
    except Exception as e:
        logger.error(f"Error capturing screen text: {e}")
        return {
            'screen_text': f'Error capturing screen content: {str(e)}',
            'window_title': 'Unknown',
            'active_app': 'Unknown',
            'screen_size': [0, 0],
            'has_images': False,
            'has_videos': False,
            'confidence': 0.0,
            'capture_method': 'error'
        }

def analyze_application_context(app_name: str, window_title: str) -> Dict[str, Any]:
    """Analyze application context to provide richer insights."""
    try:
        app_lower = app_name.lower()
        window_lower = window_title.lower()
        
        application_data = {
            'name': app_name,
            'category': 'other'
        }
        
        # Categorize application and extract workflow context
        if any(browser in app_lower for browser in ['chrome', 'safari', 'firefox', 'edge', 'opera']):
            application_data['category'] = 'browser'
            application_data['view'] = 'web_browsing'
            
            # Extract workflow stage from window title
            if any(keyword in window_lower for keyword in ['github', 'gitlab', 'bitbucket']):
                application_data['workflow_stage'] = 'code repository management'
            elif any(keyword in window_lower for keyword in ['stackoverflow', 'docs', 'documentation']):
                application_data['workflow_stage'] = 'research and documentation'
            elif any(keyword in window_lower for keyword in ['gmail', 'outlook', 'mail']):
                application_data['workflow_stage'] = 'email communication'
            elif any(keyword in window_lower for keyword in ['youtube', 'netflix', 'video']):
                application_data['workflow_stage'] = 'media consumption'
            else:
                application_data['workflow_stage'] = 'web browsing'
                
        elif any(dev in app_lower for dev in ['code', 'studio', 'intellij', 'pycharm', 'xcode']):
            application_data['category'] = 'development'
            application_data['view'] = 'code_editor'
            
            # Extract project context from window title
            if any(lang in window_lower for lang in ['python', '.py']):
                application_data['workflow_stage'] = 'Python development'
            elif any(lang in window_lower for lang in ['javascript', '.js', '.ts', 'typescript']):
                application_data['workflow_stage'] = 'JavaScript/TypeScript development'
            elif any(lang in window_lower for lang in ['java', '.java']):
                application_data['workflow_stage'] = 'Java development'
            else:
                application_data['workflow_stage'] = 'software development'
                
        elif any(comm in app_lower for comm in ['slack', 'teams', 'discord', 'zoom']):
            application_data['category'] = 'communication'
            application_data['view'] = 'messaging'
            application_data['workflow_stage'] = 'team communication'
            
        elif any(mail in app_lower for mail in ['mail', 'outlook']):
            application_data['category'] = 'communication'
            application_data['view'] = 'email'
            application_data['workflow_stage'] = 'email management'
            
        elif any(prod in app_lower for prod in ['office', 'word', 'excel', 'powerpoint', 'docs', 'sheets']):
            application_data['category'] = 'productivity'
            application_data['view'] = 'document_editing'
            application_data['workflow_stage'] = 'document creation/editing'
            
        return application_data
        
    except Exception as e:
        logger.error(f"Error analyzing application context: {e}")
        return {'name': app_name, 'category': 'other'}

async def send_screen_data(websocket: WebSocketClientProtocol):
    """Send enhanced screen data to the bridge server."""
    try:
        # Capture screen content and context
        screen_info = capture_screen_text()
        
        # Analyze application context
        application_context = analyze_application_context(
            screen_info['active_app'], 
            screen_info['window_title']
        )
        
        # Create enhanced screen data
        screen_data = {
            "type": "sensor_data",
            "sensor_type": "screen",
            "data": {
                    "timestamp": datetime.now().isoformat(),
                    "window_title": screen_info['window_title'],
                    "active_app": screen_info['active_app'],
                    "screen_content": screen_info['screen_text'],
                    "text": screen_info['screen_text'],  # Alias for compatibility
                    "application": application_context,
                    "visual_context": f"User is working in {application_context.get('name', 'unknown app')} " +
                                    f"({application_context.get('category', 'unknown category')}) " +
                                    f"doing {application_context.get('workflow_stage', 'general tasks')}",
                    "screen_metadata": {
                        "has_images": screen_info['has_images'],
                        "has_videos": screen_info['has_videos'],
                        "ocr_confidence": screen_info['confidence'],
                        "content_hash": hashlib.md5(screen_info['screen_text'].encode()).hexdigest()[:16]
                    },
                    "is_significant_action": application_context.get('workflow_stage') is not None
                }
        }
        
        # Also save to cache for direct integration
        cache_dir = "cache/screen_sensor"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "last_screen.json")
        
        with open(cache_file, 'w') as f:
            json.dump(screen_data["data"], f, indent=2)
        
        await websocket.send(json.dumps(screen_data))
        logger.info(f"Sent enhanced screen data: {application_context.get('name', 'Unknown')} - {application_context.get('workflow_stage', 'Unknown task')}")
        
    except Exception as e:
        logger.error(f"Error sending screen data: {e}")
        raise

async def send_heartbeat(websocket: WebSocketClientProtocol):
    """Send heartbeat to keep connection alive."""
    try:
        heartbeat_msg = {
            "type": "heartbeat",
            "payload": {
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await websocket.send(json.dumps(heartbeat_msg))
        logger.debug("Sent heartbeat")
        
    except Exception as e:
        logger.error(f"Error sending heartbeat: {e}")
        raise

async def handle_messages(websocket: WebSocketClientProtocol):
    """Handle incoming messages from the bridge server."""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "heartbeat_ack":
                    logger.debug("Received heartbeat acknowledgment")
                elif msg_type == "error":
                    logger.error(f"Received error: {data.get('payload', {}).get('message')}")
                else:
                    logger.warning(f"Received unexpected message type: {msg_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message: {message[:100]}...")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
        raise
    except Exception as e:
        logger.error(f"Error handling messages: {e}")
        raise

async def main():
    """Main function to run the screen sensor."""
    while True:
        try:
            # Connect to bridge server
            websocket = await connect_to_bridge()
            if not websocket:
                logger.error("Failed to connect to bridge server")
                await asyncio.sleep(5)
                continue
            
            # Register with bridge server
            if not await register_with_bridge(websocket):
                logger.error("Failed to register with bridge server")
                await websocket.close()
                await asyncio.sleep(5)
                continue
            
            # Start message handler
            message_handler = asyncio.create_task(handle_messages(websocket))
            
            # Main loop
            while True:
                try:
                    # Send screen data
                    await send_screen_data(websocket)
                    
                    # Send heartbeat
                    await send_heartbeat(websocket)
                    
                    # Wait before next update (5 seconds for less frequent updates)
                    await asyncio.sleep(5)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed during main loop")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    break
            
            # Clean up
            message_handler.cancel()
            try:
                await message_handler
            except asyncio.CancelledError:
                pass
            
            await websocket.close()
            logger.info("Disconnected from bridge server")
            
        except Exception as e:
            logger.error(f"Error in main: {e}")
        
        # Wait before reconnecting
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error running screen sensor: {e}")
        sys.exit(1)
