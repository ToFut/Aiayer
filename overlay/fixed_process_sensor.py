#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import psutil
import sys
import traceback
from datetime import datetime

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('process_sensor')

class ProcessSensor:
    def __init__(self, server_uri="ws://localhost:8765", reconnect_delay=5):
        self.server_uri = server_uri
        self.reconnect_delay = reconnect_delay
        self.running = True
        self.websocket = None
        self.last_processes = []
        self.cache_file = "cache/process_sensor/process_cache.json"
        
    async def connect_to_server(self):
        """Connect to the bridge server with retry logic"""
        while self.running:
            try:
                async with websockets.connect(self.server_uri) as websocket:
                    self.websocket = websocket
                    logger.info(f"Connected to bridge server at {self.server_uri}")
                    
                    # Process initial welcome message
                    response = await websocket.recv()
                    data = json.loads(response)
                    logger.info(f"Received from server: {data.get('type')}")
                    
                    # Send identification
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "process_sensor",
                            "version": "1.0.0",
                            "capabilities": ["process_monitoring"]
                        }
                    }))
                    
                    # Run data collection loop
                    await self.collection_loop(websocket)
                    
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                self.websocket = None
                await asyncio.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                self.websocket = None
                await asyncio.sleep(self.reconnect_delay)
    
    async def collection_loop(self, websocket):
        """Main process data collection loop"""
        while self.running and websocket.open:
            try:
                # Collect process data
                processes = self.collect_process_data()
                
                # Skip sending if nothing has changed significantly
                if self.should_send_update(processes):
                    # Send to bridge server
                    await websocket.send(json.dumps({
                        "type": "process_data",
                        "payload": processes,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Update last sent processes
                    self.last_processes = processes
                    
                    # Save to cache
                    self.save_to_cache(processes)
                
                # Wait before next collection
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in process data collection: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
                break
    
    def collect_process_data(self):
        """Collect data about running processes"""
        processes = []
        
        try:
            # First pass to let psutil calculate CPU over time
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc.cpu_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Short delay for CPU calculations
            time.sleep(0.5)
            
            # Second pass to collect actual data
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'username']):
                try:
                    # Get process info
                    proc_info = proc.info
                    if proc_info['memory_info']:
                        memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                    else:
                        memory_mb = 0
                    
                    processes.append({
                        "pid": proc_info['pid'],
                        "name": proc_info['name'],
                        "cpu": proc_info['cpu_percent'],
                        "memory": round(memory_mb, 1),
                        "user": proc_info.get('username', 'unknown')
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by CPU usage (descending)
            processes.sort(key=lambda x: x['cpu'], reverse=True)
            # Take top 15 processes
            return processes[:15]
            
        except Exception as e:
            logger.error(f"Error collecting process data: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def should_send_update(self, current_processes, threshold=2.0):
        """Determine if we should send an update based on significant changes"""
        if not self.last_processes:
            return True
            
        # Check for new or terminated important processes
        current_pids = {p['pid'] for p in current_processes[:5]}
        last_pids = {p['pid'] for p in self.last_processes[:5]}
        
        if current_pids != last_pids:
            return True
            
        # Check for significant CPU changes
        for curr in current_processes[:5]:
            for last in self.last_processes:
                if curr['pid'] == last['pid']:
                    if abs(curr['cpu'] - last['cpu']) > threshold:
                        return True
        
        return False
    
    def convert_to_builtin(self, obj):
        # If it's a macOS NSDictionary, convert to dict
        if hasattr(obj, 'copy') and hasattr(obj, 'allKeys'):
            return {str(k): self.convert_to_builtin(obj[k]) for k in obj}
        elif isinstance(obj, dict):
            return {k: self.convert_to_builtin(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_builtin(i) for i in obj]
        else:
            return obj

    def save_to_cache(self, processes):
        """Save current processes to cache file"""
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "processes": processes
            }
            cache_data = self.convert_to_builtin(cache_data)
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    def load_from_cache(self):
        """Load processes from cache file"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                return cache_data.get("processes", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    async def run(self):
        """Run the process sensor"""
        logger.info("Starting process sensor")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/process_sensor.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        # Load cache if available
        self.last_processes = self.load_from_cache()
        
        # Connect to server
        await self.connect_to_server()

# Function to maintain compatibility with direct execution
async def run_sensor():
    sensor = ProcessSensor()
    await sensor.run()

if __name__ == "__main__":
    import time  # Import needed for collect_process_data
    
    try:
        asyncio.run(run_sensor())
    except KeyboardInterrupt:
        logger.info("Process sensor stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running process sensor: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
