import os
import json
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path

class OverlaySensor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.overlay_path = Path(config.get('overlay_path', 'overlay'))
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False

    def start(self) -> bool:
        """Start the overlay widget."""
        try:
            if not self.overlay_path.exists():
                print(f"Overlay path not found: {self.overlay_path}")
                return False

            # Change to the overlay directory and start the Tauri app
            os.chdir(self.overlay_path)
            self.process = subprocess.Popen(
                ['npm', 'run', 'tauri', 'dev'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.is_running = True
            return True
        except Exception as e:
            print(f"Error starting overlay: {e}")
            return False

    def stop(self) -> bool:
        """Stop the overlay widget."""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
            self.is_running = False
            return True
        except Exception as e:
            print(f"Error stopping overlay: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the overlay widget."""
        return {
            "is_running": self.is_running,
            "process_id": self.process.pid if self.process else None
        }

    def send_message(self, message: str) -> bool:
        """Send a message to the overlay widget."""
        try:
            # TODO: Implement actual message sending to Tauri app
            # This will require setting up a communication channel
            # between the Python backend and the Tauri frontend
            return True
        except Exception as e:
            print(f"Error sending message to overlay: {e}")
            return False 