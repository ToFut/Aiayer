#!/usr/bin/env python3
"""
Start Memory Trigger System

This script starts the complete memory trigger system, including the WebSocket server
for displaying notifications and the memory trigger service for detecting patterns
in memory data.
"""

import asyncio
import logging
import os
import sys
import signal
import time
import subprocess
import threading
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_trigger_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory_trigger_system")

class MemoryTriggerSystem:
    """Class to manage the memory trigger system components"""
    
    def __init__(self):
        """Initialize memory trigger system"""
        self.processes = {}
        self.running = True
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Ensure required directories exist
        os.makedirs('logs/memory', exist_ok=True)
        os.makedirs('pids', exist_ok=True)
        
    def _run_process(self, name: str, cmd: List[str]) -> None:
        """Run a process in a separate thread"""
        try:
            logger.info(f"Starting {name}: {' '.join(cmd)}")
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                cwd=self.base_dir
            )
            
            # Store process
            self.processes[name] = process
            
            # Write PID to file
            with open(f"pids/memory_trigger_{name}.pid", 'w') as f:
                f.write(str(process.pid))
            
            logger.info(f"Started {name} (PID: {process.pid})")
            
            # Monitor process output
            while self.running:
                try:
                    stdout_line = process.stdout.readline()
                    if stdout_line:
                        logger.info(f"[{name}] {stdout_line.strip()}")
                    
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        logger.error(f"[{name}] {stderr_line.strip()}")
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        remaining_output, remaining_error = process.communicate()
                        if remaining_output:
                            logger.info(f"[{name}] {remaining_output.strip()}")
                        if remaining_error:
                            logger.error(f"[{name}] {remaining_error.strip()}")
                        
                        logger.warning(f"{name} process exited with code {process.returncode}")
                        
                        # If still running, restart the process
                        if self.running:
                            logger.info(f"Restarting {name}...")
                            process = subprocess.Popen(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                bufsize=1,
                                cwd=self.base_dir
                            )
                            self.processes[name] = process
                            logger.info(f"Restarted {name} (PID: {process.pid})")
                            
                            # Write PID to file
                            with open(f"pids/memory_trigger_{name}.pid", 'w') as f:
                                f.write(str(process.pid))
                        
                        # If not running anymore, break loop
                        else:
                            break
                    
                    # Small sleep to avoid high CPU usage
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error monitoring {name} process: {e}")
                    time.sleep(1)  # Sleep to avoid rapid error loops
            
            # Ensure process is terminated
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Terminated {name} process (PID: {process.pid})")
                
        except Exception as e:
            logger.error(f"Error running {name} process: {e}")
            
    def start(self) -> None:
        """Start all system components"""
        try:
            logger.info("Starting Memory Trigger System...")
            
            # Start WebSocket server
            ws_thread = threading.Thread(
                target=self._run_process,
                args=("websocket", ["python", "overlay/minimal_ws_server.py"]),
                daemon=True
            )
            ws_thread.start()
            
            # Wait for WebSocket server to start
            logger.info("Waiting for WebSocket server to start...")
            time.sleep(3)
            
            # Start memory trigger connector (using fixed version)
            connector_thread = threading.Thread(
                target=self._run_process,
                args=("connector", ["python", "fixed_connect_memory_trigger.py"]),
                daemon=True
            )
            connector_thread.start()
            
            logger.info("Memory Trigger System started")
            
            # Add test memories after startup
            test_memory_thread = threading.Thread(
                target=self._delayed_test_memory,
                daemon=True
            )
            test_memory_thread.start()
            
            # Wait for threads to finish (they shouldn't unless error occurs)
            ws_thread.join()
            connector_thread.join()
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            self.stop()
    
    def _delayed_test_memory(self) -> None:
        """Add test memories after a delay"""
        try:
            # Wait for system to start
            time.sleep(10)
            
            # Only add test memories if system is still running
            if self.running:
                logger.info("Adding test memory items...")
                
                # Add shopping memory
                subprocess.run(
                    ["python", "add_test_memory.py", "shopping"],
                    cwd=self.base_dir,
                    check=True
                )
                
                # Wait a bit then add form memory
                time.sleep(5)
                subprocess.run(
                    ["python", "add_test_memory.py", "form"],
                    cwd=self.base_dir,
                    check=True
                )
                
                logger.info("Test memory items added")
        except Exception as e:
            logger.error(f"Error adding test memory: {e}")
            
    def stop(self) -> None:
        """Stop all system components"""
        logger.info("Stopping Memory Trigger System...")
        self.running = False
        
        # Terminate all processes
        for name, process in self.processes.items():
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"Terminated {name} process (PID: {process.pid})")
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.warning(f"Killed {name} process (PID: {process.pid})")
                except Exception as e:
                    logger.error(f"Error terminating {name} process: {e}")
        
        logger.info("Memory Trigger System stopped")

def handle_signals(trigger_system):
    """Handle termination signals"""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {signal.Signals(sig).name}, shutting down...")
        trigger_system.stop()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main function"""
    logger.info("🚀 Starting Memory Trigger System")
    
    # Create system manager
    trigger_system = MemoryTriggerSystem()
    
    # Set up signal handlers
    handle_signals(trigger_system)
    
    # Start system
    try:
        trigger_system.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down...")
        trigger_system.stop()
    except Exception as e:
        logger.error(f"Error running system: {e}")
        trigger_system.stop()
        return False
        
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Memory Trigger System stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)