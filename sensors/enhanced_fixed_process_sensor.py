#!/usr/bin/env python3
"""
Enhanced Fixed Process Sensor

This module captures process information and sends it to the bridge server.
"""
import os
import json
import time
import asyncio
import logging
import websockets
import traceback
import psutil
from datetime import datetime

# Configure logging
os.makedirs('logs/sensors/process_sensor', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/process_sensor/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('process_sensor')

class ProcessSensor:
    """Captures process information and sends to bridge server"""
    
    def __init__(self, bridge_uri="ws://localhost:8766", capture_interval=5):  # Changed to backend port
        self.bridge_uri = bridge_uri
        self.capture_interval = capture_interval
        self.running = True
        self.cache_dir = "cache/process_sensor"
        self.last_process_list = set()
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"Process sensor initialized with interval {capture_interval}s")
    
    def _get_processes(self):
        """Get current running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    # Get process info
                    process_info = proc.info
                    
                    # Check if valid process
                    if process_info['pid'] > 0:
                        # Add to list
                        processes.append({
                            'pid': process_info['pid'],
                            'name': process_info['name'],
                            'user': process_info['username']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            return processes
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def _get_active_applications(self):
        """Get list of active applications (simplified implementation)"""
        try:
            # In a real implementation, this would detect actual applications,
            # not just processes. Here we'll use process data as a proxy.
            processes = self._get_processes()
            
            # Extract unique application names from processes, simplified approach
            apps = set()
            for proc in processes:
                name = proc.get('name', '')
                if name and len(name) > 3 and not name.startswith('python'):
                    apps.add(name)
            
            # Convert to list of application objects
            app_list = []
            for app_name in apps:
                app_list.append({
                    'name': app_name,
                    'type': self._guess_app_type(app_name)
                })
            
            return app_list
        except Exception as e:
            logger.error(f"Error getting active applications: {e}")
            return []
    
    def _guess_app_type(self, app_name):
        """Guess the type of application based on name"""
        app_name = app_name.lower()
        
        # Browser detection
        if any(browser in app_name for browser in ['chrome', 'firefox', 'safari', 'edge', 'opera']):
            return 'browser'
            
        # Development tools
        if any(dev in app_name for dev in ['code', 'studio', 'intellij', 'pycharm', 'terminal']):
            return 'development'
            
        # Communications
        if any(comm in app_name for comm in ['slack', 'teams', 'zoom', 'meet', 'discord', 'mail']):
            return 'communication'
            
        # Office/Productivity
        if any(office in app_name for office in ['office', 'word', 'excel', 'powerpoint', 'docs']):
            return 'productivity'
            
        # Media
        if any(media in app_name for media in ['vlc', 'player', 'spotify', 'itunes', 'music']):
            return 'media'
            
        # Default
        return 'application'
    
    def _get_active_window(self):
        """Get active window information (simplified implementation)"""
        try:
            # This is a placeholder - in a real implementation we would use
            # platform-specific libraries to get the actual active window
            return {
                'title': 'Unknown Window',
                'application': 'Unknown Application'
            }
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
            return {
                'title': 'Unknown Window',
                'application': 'Unknown Application'
            }
    
    def _cache_process_data(self, process_data):
        """Cache process data to file"""
        try:
            cache_file = os.path.join(self.cache_dir, "process_cache.json")
            
            # Create a backup before overwriting
            if os.path.exists(cache_file):
                backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{cache_file}.bak_{backup_timestamp}"
                os.rename(cache_file, backup_file)
            
            # Write new cache file
            with open(cache_file, 'w') as f:
                json.dump(process_data, f, indent=2)
            
            logger.debug(f"Cached process data to {cache_file}")
            
        except Exception as e:
            logger.error(f"Error caching process data: {e}")
    
    def _is_significant_change(self, processes, active_apps):
        """Determine if there's a significant change in processes"""
        try:
            # Get current process list
            current_process_set = set()
            for proc in processes:
                pid = proc.get('pid', 0)
                name = proc.get('name', '')
                if pid > 0 and name:
                    current_process_set.add(f"{name}:{pid}")
            
            # Compare with last process list
            diff = current_process_set.symmetric_difference(self.last_process_list)
            is_significant = len(diff) > 5  # Arbitrary threshold
            
            # Update last process list
            self.last_process_list = current_process_set
            
            return is_significant
        except Exception as e:
            logger.error(f"Error checking for significant change: {e}")
            return False
    
    async def _heartbeat_loop(self, websocket):
        """Send periodic heartbeats to keep the connection alive"""
        heartbeat_interval = 30  # seconds
        try:
            while self.running:
                try:
                    await websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": time.time()
                    }))
                    logger.debug("Sent heartbeat ping to bridge server")
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {e}")
                    break
                
                await asyncio.sleep(heartbeat_interval)
        except asyncio.CancelledError:
            logger.info("Heartbeat task cancelled")
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
            
    async def connect_to_bridge(self):
        """Connect to bridge server and send process data"""
        while self.running:
            heartbeat_task = None
            try:
                async with websockets.connect(self.bridge_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.bridge_uri}")
                    
                    # Identify as process sensor with proper registration format
                    await websocket.send(json.dumps({
                        "type": "register",
                        "client_type": "sensor",
                        "sensor_type": "process",  # Add specific sensor type
                        "version": "1.0.0",
                        "capabilities": ["process_monitoring", "application_detection"]
                    }))
                    logger.info("Sent registration message to bridge server")
                    
                    # Wait for registration confirmation
                    registered = False
                    registration_timeout = 10  # seconds
                    registration_start = time.time()
                    
                    while not registered and time.time() - registration_start < registration_timeout:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            data = json.loads(response)
                            
                            if data.get('type') == 'registration_confirmed':
                                logger.info("Registration confirmed by bridge server")
                                registered = True
                                break
                            elif data.get('type') == 'error':
                                logger.error(f"Registration error: {data.get('message', 'Unknown error')}")
                                await asyncio.sleep(2)
                                # Retry registration
                                await websocket.send(json.dumps({
                                    "type": "register",
                                    "client_type": "sensor",
                                    "sensor_type": "process",  # Add specific sensor type  
                                    "version": "1.0.0",
                                    "capabilities": ["process_monitoring", "application_detection"]
                                }))
                            else:
                                logger.warning(f"Unexpected message during registration: {data.get('type')}")
                        except asyncio.TimeoutError:
                            logger.warning("Waiting for registration confirmation...")
                        except Exception as e:
                            logger.error(f"Error during registration confirmation: {e}")
                            await asyncio.sleep(1)
                    
                    if not registered:
                        logger.error("Failed to confirm registration, retrying connection")
                        continue  # Retry the connection
                    
                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(websocket))
                    logger.debug("Started heartbeat task")
                    
                    # Main loop for sending process updates
                    while self.running:
                        try:
                            # Get process data
                            processes = self._get_processes()
                            active_apps = self._get_active_applications()
                            active_window = self._get_active_window()
                            
                            # Check if significant change
                            is_significant = self._is_significant_change(processes, active_apps)
                            
                            # Prepare process data
                            process_data = {
                                "timestamp": datetime.now().isoformat(),
                                "processes": processes[:50],  # Limit to 50 processes
                                "active_apps": active_apps,
                                "active_window": active_window.get('title', 'Unknown'),
                                "active_app": active_window.get('application', 'Unknown'),
                                "is_significant": is_significant
                            }
                            
                            # Cache process data
                            self._cache_process_data(process_data)
                            
                            # Send to bridge
                            await websocket.send(json.dumps({
                                "type": "sensor_data",
                                "sensor_type": "process",
                                "payload": process_data
                            }))
                            
                            logger.info(f"Sent process data to bridge server ({len(processes)} processes, {len(active_apps)} apps)")
                            
                            # Process incoming messages (pongs, etc.)
                            while True:
                                try:
                                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                                    data = json.loads(response)
                                    logger.debug(f"Received message: {data.get('type')}")
                                    
                                    # Handle pong responses
                                    if data.get('type') == 'pong':
                                        logger.debug("Received pong from bridge server")
                                except asyncio.TimeoutError:
                                    # No more messages to process
                                    break
                                except Exception as msg_e:
                                    logger.error(f"Error processing message: {msg_e}")
                                    break
                            
                            # Wait for next capture
                            await asyncio.sleep(self.capture_interval)
                            
                        except (websockets.exceptions.ConnectionClosed, ConnectionError) as conn_e:
                            logger.warning(f"Connection lost: {conn_e}")
                            break
                        except Exception as loop_e:
                            logger.error(f"Error in main processing loop: {loop_e}")
                            logger.error(traceback.format_exc())
                            await asyncio.sleep(1)  # Brief pause before retrying
            
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)  # Wait before reconnecting
            finally:
                # Clean up heartbeat task if it exists
                if heartbeat_task and not heartbeat_task.done():
                    heartbeat_task.cancel()
                    try:
                        await heartbeat_task
                    except asyncio.CancelledError:
                        pass
    
    async def run(self):
        """Run the process sensor"""
        logger.info("Starting process sensor")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/process_sensor.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Connect to bridge and start sending data
        await self.connect_to_bridge()

# Run the process sensor
async def run_process_sensor():
    sensor = ProcessSensor()
    await sensor.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_process_sensor())
    except KeyboardInterrupt:
        logger.info("Process sensor stopped by user")
    except Exception as e:
        logger.error(f"Error running process sensor: {e}")
        logger.error(traceback.format_exc())
