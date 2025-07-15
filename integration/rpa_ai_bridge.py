#!/usr/bin/env python3
"""
RPA AI Bridge - Connects AIAYER to RPA_AVEN for automation execution
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ApplicationInfo:
    """Information about an application"""
    name: str
    pid: int
    title: str
    is_active: bool
    window_rect: Optional[Dict[str, int]] = None

@dataclass
class WindowInfo:
    """Information about a window"""
    title: str
    pid: int
    handle: int
    rect: Dict[str, int]
    is_active: bool

class RPAAIBridge:
    """Bridge between AIAYER and RPA_AVEN for automation execution"""
    
    def __init__(self, rpa_server_url: str = "http://localhost:16901"):
        self.rpa_server_url = rpa_server_url
        self.session = None
        self.initialized = False
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize the RPA bridge"""
        try:
            # Create aiohttp session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            # Test connection to RPA server
            async with self.session.get(f"{self.rpa_server_url}/") as response:
                if response.status == 200:
                    self.initialized = True
                    self.logger.info(f"✅ RPA Bridge connected to {self.rpa_server_url}")
                else:
                    raise Exception(f"RPA server returned status {response.status}")
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize RPA bridge: {e}")
            self.initialized = False
            raise
    
    async def close(self):
        """Close the RPA bridge"""
        if self.session:
            await self.session.close()
            self.session = None
        self.initialized = False
    
    async def get_active_applications(self) -> List[ApplicationInfo]:
        """Get list of active applications"""
        try:
            if not self.initialized:
                return []
                
            # Use RPA server to get active applications
            # This is a simplified implementation - in practice, you'd use
            # the RPA server's process management capabilities
            
            apps = []
            
            # Common applications to check
            common_apps = [
                "Safari", "Chrome", "Firefox", "Calculator", "Notes", 
                "TextEdit", "Terminal", "Finder", "System Preferences"
            ]
            
            for app_name in common_apps:
                try:
                    # Check if app is running (simplified)
                    app = ApplicationInfo(
                        name=app_name,
                        pid=0,  # Would get actual PID from RPA server
                        title=app_name,
                        is_active=True
                    )
                    apps.append(app)
                except Exception as e:
                    self.logger.debug(f"Could not get info for {app_name}: {e}")
            
            return apps
            
        except Exception as e:
            self.logger.error(f"Error getting active applications: {e}")
            return []
    
    async def get_current_window(self) -> WindowInfo:
        """Get current window information"""
        try:
            if not self.initialized:
                return WindowInfo(
                    title="Unknown",
                    pid=0,
                    handle=0,
                    rect={"left": 0, "top": 0, "right": 1920, "bottom": 1080},
                    is_active=False
                )
            
            # Get current window info from RPA server
            # This would use the RPA server's window management capabilities
            
            return WindowInfo(
                title="Active Window",
                pid=0,
                handle=0,
                rect={"left": 0, "top": 0, "right": 1920, "bottom": 1080},
                is_active=True
            )
            
        except Exception as e:
            self.logger.error(f"Error getting current window: {e}")
            return WindowInfo(
                title="Error",
                pid=0,
                handle=0,
                rect={"left": 0, "top": 0, "right": 1920, "bottom": 1080},
                is_active=False
            )
    
    async def click_element(self, x: int, y: int, button: str = "left") -> bool:
        """Click at specific coordinates"""
        try:
            if not self.initialized:
                return False
                
            url = f"{self.rpa_server_url}/mouse/click/{x}/{y}"
            async with self.session.get(url) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Error clicking at ({x}, {y}): {e}")
            return False
    
    async def type_text(self, text: str) -> bool:
        """Type text using keyboard"""
        try:
            if not self.initialized:
                return False
                
            url = f"{self.rpa_server_url}/keyboard/input"
            params = {"text": text}
            
            async with self.session.get(url, params=params) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return False
    
    async def press_hotkey(self, *keys: str) -> bool:
        """Press a hotkey combination"""
        try:
            if not self.initialized:
                return False
                
            # Convert keys to the format expected by RPA server
            key_combination = "+".join(keys)
            url = f"{self.rpa_server_url}/keyboard/type_hotkey/{key_combination}"
            
            async with self.session.get(url) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Error pressing hotkey {keys}: {e}")
            return False
    
    async def capture_screen_region(self, x: int, y: int, width: int, height: int) -> Optional[bytes]:
        """Capture a region of the screen"""
        try:
            if not self.initialized:
                return None
                
            url = f"{self.rpa_server_url}/display/img/{x}/{y}/{width}/{height}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error capturing screen region: {e}")
            return None
    
    async def execute_automation_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complete automation plan"""
        try:
            if not self.initialized:
                return {"success": False, "error": "RPA bridge not initialized"}
            
            steps = plan.get("steps", [])
            results = []
            
            for step in steps:
                step_result = await self._execute_step(step)
                results.append(step_result)
                
                # Check if step failed
                if not step_result.get("success", False):
                    return {
                        "success": False,
                        "error": f"Step failed: {step_result.get('error', 'Unknown error')}",
                        "results": results
                    }
                
                # Wait between steps
                await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "results": results,
                "total_steps": len(steps)
            }
            
        except Exception as e:
            self.logger.error(f"Error executing automation plan: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single automation step"""
        try:
            action_type = step.get("action_type")
            
            if action_type == "click":
                x = step.get("x", 0)
                y = step.get("y", 0)
                success = await self.click_element(x, y)
                return {"success": success, "action": "click", "coordinates": (x, y)}
                
            elif action_type == "type":
                text = step.get("text", "")
                success = await self.type_text(text)
                return {"success": success, "action": "type", "text": text}
                
            elif action_type == "hotkey":
                keys = step.get("keys", [])
                success = await self.press_hotkey(*keys)
                return {"success": success, "action": "hotkey", "keys": keys}
                
            elif action_type == "wait":
                duration = step.get("duration", 1.0)
                await asyncio.sleep(duration)
                return {"success": True, "action": "wait", "duration": duration}
                
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global instance
_rpa_bridge = None

async def get_rpa_bridge() -> RPAAIBridge:
    """Get or create global RPA bridge instance"""
    global _rpa_bridge
    if _rpa_bridge is None:
        _rpa_bridge = RPAAIBridge()
        await _rpa_bridge.initialize()
    return _rpa_bridge

async def close_rpa_bridge():
    """Close global RPA bridge instance"""
    global _rpa_bridge
    if _rpa_bridge:
        await _rpa_bridge.close()
        _rpa_bridge = None 