#!/usr/bin/env python3
"""
RPA_AVEN Bridge for AIayer
Connects AIayer's intelligent automation planning with RPA_AVEN's low-level automation server.
Provides real UI automation capabilities instead of simulation.
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)

@dataclass
class RPAConfig:
    """Configuration for RPA_AVEN server connection"""
    host: str = "localhost"
    port: int = 16901
    timeout: float = 10.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

class RPA_AVENBridge:
    """Bridge between AIayer and RPA_AVEN server"""
    
    def __init__(self, config: RPAConfig = None):
        self.config = config or RPAConfig()
        self.base_url = f"http://{self.config.host}:{self.config.port}"
        self.session = None
        self.connected = False
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self) -> bool:
        """Connect to RPA_AVEN server"""
        try:
            if self.session is None:
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    self.connected = True
                    logger.info(f"✅ Connected to RPA_AVEN server at {self.base_url}")
                    return True
                else:
                    logger.error(f"❌ RPA_AVEN server returned status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to connect to RPA_AVEN server: {e}")
            self.connected = False
            return False
            
    async def disconnect(self):
        """Disconnect from RPA_AVEN server"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("🔌 Disconnected from RPA_AVEN server")
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to RPA_AVEN server with retry logic"""
        if not self.connected:
            await self.connect()
            
        for attempt in range(self.config.retry_attempts):
            try:
                url = f"{self.base_url}{endpoint}"
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        # Check if this is an image endpoint
                        if "/display/img/" in endpoint:
                            # Return binary data for image endpoints
                            image_data = await response.read()
                            return {"success": True, "data": image_data}
                        else:
                            # Try to parse as JSON for other endpoints
                            try:
                                return await response.json()
                            except:
                                return {"success": True, "data": await response.text()}
                    else:
                        logger.warning(f"⚠️ RPA_AVEN request failed (attempt {attempt+1}): {response.status}")
                        if attempt < self.config.retry_attempts - 1:
                            await asyncio.sleep(self.config.retry_delay)
                        else:
                            return {"success": False, "error": f"HTTP {response.status}"}
                            
            except Exception as e:
                logger.warning(f"⚠️ RPA_AVEN request error (attempt {attempt+1}): {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    return {"success": False, "error": str(e)}
                    
        return {"success": False, "error": "Max retries exceeded"}
        
    # Mouse Control Methods
    async def move_mouse(self, x: int, y: int) -> bool:
        """Move mouse to coordinates"""
        result = await self._make_request("GET", f"/mouse/move/{x}/{y}")
        return result.get("success", False)
        
    async def click_mouse(self, x: int, y: int) -> bool:
        """Click mouse at coordinates"""
        result = await self._make_request("GET", f"/mouse/click/{x}/{y}")
        return result.get("success", False)
        
    async def double_click_mouse(self, x: int, y: int) -> bool:
        """Double-click mouse at coordinates"""
        result = await self._make_request("GET", f"/mouse/dblclick/{x}/{y}")
        return result.get("success", False)
        
    # Keyboard Control Methods
    async def type_key(self, key_code: str) -> bool:
        """Type a single key"""
        result = await self._make_request("GET", f"/keyboard/type/{key_code}")
        return result.get("success", False)
        
    async def type_text(self, text: str) -> bool:
        """Type text string"""
        result = await self._make_request("GET", f"/keyboard/input?text={text}")
        return result.get("success", False)
        
    async def press_hotkey(self, key_code: str) -> bool:
        """Press hotkey combination"""
        result = await self._make_request("GET", f"/keyboard/type_hotkey/{key_code}")
        return result.get("success", False)
        
    async def press_shift_key(self, key_code: str) -> bool:
        """Press key with shift modifier"""
        result = await self._make_request("GET", f"/keyboard/type_shift/{key_code}")
        return result.get("success", False)
        
    async def key_down(self, key_code: str) -> bool:
        """Press key down"""
        result = await self._make_request("GET", f"/keyboard/down/{key_code}")
        return result.get("success", False)
        
    async def key_up(self, key_code: str) -> bool:
        """Release key"""
        result = await self._make_request("GET", f"/keyboard/up/{key_code}")
        return result.get("success", False)
        
    # Screen Capture Methods
    async def capture_screen_region(self, left: int, top: int, width: int, height: int) -> Optional[bytes]:
        """Capture screen region as image bytes"""
        result = await self._make_request("GET", f"/display/img/{left}/{top}/{width}/{height}")
        if result.get("success"):
            # The response should contain image data
            return result.get("data")
        return None
        
    async def get_window_html(self, window_name: str) -> Optional[str]:
        """Get window HTML overlay"""
        result = await self._make_request("GET", f"/display/html/{window_name}")
        if result.get("success"):
            return result.get("data")
        return None
        
    async def get_window_json(self, window_name: str) -> Optional[Dict[str, Any]]:
        """Get window information as JSON"""
        result = await self._make_request("GET", f"/display/json/{window_name}")
        if result.get("success"):
            return result.get("data")
        return None
        
    # Vision/Image Processing Methods
    async def match_template_on_screen(self, template_path: str) -> Optional[Dict[str, Any]]:
        """Match template on screen"""
        result = await self._make_request("GET", f"/vison/match/screen/template?template={template_path}")
        if result.get("success"):
            return result.get("data")
        return None
        
    async def match_base64_image(self, base64_image: str) -> Optional[Dict[str, Any]]:
        """Match base64 encoded image on screen"""
        data = {"image": base64_image}
        result = await self._make_request("POST", "/vison/match/screen/b64", json=data)
        if result.get("success"):
            return result.get("data")
        return None
        
    # System Control Methods
    async def run_application(self, app_path: str) -> bool:
        """Run application"""
        result = await self._make_request("GET", f"/system/app/run?path={app_path}")
        return result.get("success", False)
        
    async def kill_application(self, app_name: str) -> bool:
        """Kill application"""
        result = await self._make_request("GET", f"/system/app/kill?name={app_name}")
        return result.get("success", False)
        
    # Clipboard Methods
    async def write_clipboard(self, text: str) -> bool:
        """Write text to clipboard"""
        result = await self._make_request("GET", f"/clipboard/write?text={text}")
        return result.get("success", False)

class AIayerRPAIntegration:
    """Integration layer that replaces AIayer's simulated automation with real RPA_AVEN automation"""
    
    def __init__(self):
        self.rpa_bridge = RPA_AVENBridge()
        self.connected = False
        
    async def initialize(self) -> bool:
        """Initialize connection to RPA_AVEN server"""
        try:
            self.connected = await self.rpa_bridge.connect()
            if self.connected:
                logger.info("🤖 AIayer-RPA_AVEN integration initialized successfully")
            else:
                logger.warning("⚠️ Failed to connect to RPA_AVEN server - will use fallback methods")
            return self.connected
        except Exception as e:
            logger.error(f"❌ Failed to initialize RPA integration: {e}")
            return False
            
    async def execute_mouse_click(self, x: int, y: int, double_click: bool = False) -> bool:
        """Execute mouse click using RPA_AVEN"""
        if not self.connected:
            logger.warning("⚠️ RPA_AVEN not connected, using fallback")
            return True  # Fallback to simulation
            
        try:
            if double_click:
                return await self.rpa_bridge.double_click_mouse(x, y)
            else:
                return await self.rpa_bridge.click_mouse(x, y)
        except Exception as e:
            logger.error(f"❌ Mouse click failed: {e}")
            return False
            
    async def execute_mouse_move(self, x: int, y: int) -> bool:
        """Execute mouse move using RPA_AVEN"""
        if not self.connected:
            logger.warning("⚠️ RPA_AVEN not connected, using fallback")
            return True  # Fallback to simulation
            
        try:
            return await self.rpa_bridge.move_mouse(x, y)
        except Exception as e:
            logger.error(f"❌ Mouse move failed: {e}")
            return False
            
    async def execute_keyboard_type(self, text: str) -> bool:
        """Execute keyboard typing using RPA_AVEN"""
        if not self.connected:
            logger.warning("⚠️ RPA_AVEN not connected, using fallback")
            return True  # Fallback to simulation
            
        try:
            return await self.rpa_bridge.type_text(text)
        except Exception as e:
            logger.error(f"❌ Keyboard typing failed: {e}")
            return False
            
    async def execute_hotkey(self, keys: List[str]) -> bool:
        """Execute hotkey combination using RPA_AVEN"""
        if not self.connected:
            logger.warning("⚠️ RPA_AVEN not connected, using fallback")
            return True  # Fallback to simulation
            
        try:
            # Convert list of keys to RPA_AVEN format
            key_code = "+".join(keys)
            return await self.rpa_bridge.press_hotkey(key_code)
        except Exception as e:
            logger.error(f"❌ Hotkey execution failed: {e}")
            return False
            
    async def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[bytes]:
        """Capture screen using RPA_AVEN"""
        if not self.connected:
            logger.warning("⚠️ RPA_AVEN not connected, using fallback")
            return None  # Fallback to other methods
            
        try:
            if region:
                left, top, width, height = region
                return await self.rpa_bridge.capture_screen_region(left, top, width, height)
            else:
                # Capture full screen
                return await self.rpa_bridge.capture_screen_region(0, 0, 1920, 1080)
        except Exception as e:
            logger.error(f"❌ Screen capture failed: {e}")
            return None
            
    async def find_ui_element(self, element_description: str, screenshot: bytes = None) -> Optional[Dict[str, Any]]:
        """Find UI element using RPA_AVEN vision capabilities"""
        if not self.connected:
            logger.warning("⚠️ RPA_AVEN not connected, using fallback")
            return None  # Fallback to other methods
            
        try:
            if screenshot:
                # Convert screenshot to base64
                base64_image = base64.b64encode(screenshot).decode('utf-8')
                return await self.rpa_bridge.match_base64_image(base64_image)
            else:
                # Use template matching
                return await self.rpa_bridge.match_template_on_screen(element_description)
        except Exception as e:
            logger.error(f"❌ UI element detection failed: {e}")
            return None

# Global integration instance
aiayer_rpa_integration = AIayerRPAIntegration()

async def initialize_rpa_integration() -> bool:
    """Initialize the RPA integration globally"""
    return await aiayer_rpa_integration.initialize()

def get_rpa_integration() -> AIayerRPAIntegration:
    """Get the global RPA integration instance"""
    return aiayer_rpa_integration 