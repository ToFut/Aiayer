"""
Overlay Sensor Module
Monitors overlay widget state.
"""
import os
import json
import subprocess
import logging
import platform
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

class OverlaySensor:
    """Sensor for monitoring overlay widget state."""
    
    def __init__(self, config: Dict):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.overlay_path = Path(config.get('overlay_path', 'overlay'))
        self._process = None
        self._last_restart = 0
        self._restart_attempts = 0
        self._max_restarts = 3
        self._restart_cooldown = 60  # seconds
        self.port = config.get('port', 8765)
        self.is_running = False

    async def get_data(self) -> Dict:
        """Get current overlay data with proper async handling."""
        try:
            # Check status with timeout
            status = await asyncio.get_event_loop().run_in_executor(
                None, self._check_status
            )
            
            # Try to restart if stopped
            if status["status"] == "stopped" and self._should_attempt_restart():
                success = await asyncio.get_event_loop().run_in_executor(
                    None, self._attempt_restart
                )
                if success:
                    status = await asyncio.get_event_loop().run_in_executor(
                        None, self._check_status
                    )
                
            return status
        except Exception as e:
            self.logger.error(f"Error getting overlay data: {e}")
            return {
                "status": "error",
                "error": str(e),
                "process_id": "None",
                "port": self.port
            }
            
    def _check_status(self) -> Dict:
        """Check the current status of the overlay."""
        try:
            # Check if process is running
            if self._process and self._process.poll() is None:
                return {
                    "status": "running",
                    "process_id": str(self._process.pid),
                    "port": self.port
                }
            else:
                return {
                    "status": "stopped",
                    "process_id": "None",
                    "port": self.port
                }
        except Exception as e:
            self.logger.error(f"Error checking overlay status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "port": self.port
            }
            
    def _should_attempt_restart(self) -> bool:
        """Determine if we should attempt a restart."""
        current_time = time.time()
        
        # Check if we've exceeded max restarts
        if self._restart_attempts >= self._max_restarts:
            # Reset counter if cooldown period has passed
            if current_time - self._last_restart > self._restart_cooldown:
                self._restart_attempts = 0
            else:
                return False
                
        # Don't restart too frequently
        if current_time - self._last_restart < 5:  # 5 second minimum between restarts
            return False
            
        return True
        
    def _attempt_restart(self) -> bool:
        """Attempt to restart the overlay process."""
        try:
            # Kill existing process if any
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=2.0)
                except:
                    pass
                    
            # Start new process
            cmd = [
                "python",
                "-m", "overlay.widget",
                "--port", str(self.port)
            ]
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Update restart tracking
            self._last_restart = time.time()
            self._restart_attempts += 1
            
            # Give it a moment to start
            time.sleep(0.5)
            
            # Check if process is running
            if self._process.poll() is None:
                self.logger.info("Successfully restarted overlay process")
                return True
            else:
                self.logger.error("Overlay process failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restarting overlay: {e}")
            return False
            
    async def start(self) -> bool:
        """Start the overlay process."""
        try:
            if self._process and self._process.poll() is None:
                self.logger.info("Overlay already running")
                return True
                
            return await asyncio.get_event_loop().run_in_executor(
                None, self._attempt_restart
            )
            
        except Exception as e:
            self.logger.error(f"Error starting overlay: {e}")
            return False
            
    async def stop(self) -> bool:
        """Stop the overlay process."""
        try:
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    
            self._process = None
            self.is_running = False
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping overlay: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the overlay widget."""
        return {
            "is_running": self.is_running,
            "process_id": self._process.pid if self._process else None
        }

    async def send_message(self, message: str) -> bool:
        """Send a message to the overlay widget."""
        try:
            # TODO: Implement actual message sending to Tauri app
            # This will require setting up a communication channel
            # between the Python backend and the Tauri frontend
            return True
        except Exception as e:
            print(f"Error sending message to overlay: {e}")
            return False 