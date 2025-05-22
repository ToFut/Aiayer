#!/usr/bin/env python3
"""
UI Automation Engine
Real mouse and keyboard control for Agent mode
"""

import asyncio
import time
import logging
import subprocess
import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class UIAction:
    """UI automation action"""
    action_type: str  # 'click', 'type', 'key', 'move', 'scroll', 'drag'
    coordinates: Optional[Tuple[int, int]] = None
    text: Optional[str] = None
    key: Optional[str] = None
    duration: float = 0.1
    delay_after: float = 0.5

class MacOSUIController:
    """macOS UI automation using AppleScript and system tools"""
    
    def __init__(self):
        self.enabled = False
        self._check_permissions()
    
    def _check_permissions(self):
        """Check if we have accessibility permissions"""
        try:
            # Test AppleScript access
            script = '''
            tell application "System Events"
                get name of first process
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            self.enabled = result.returncode == 0
            
            if self.enabled:
                logger.info("✅ UI automation permissions granted")
            else:
                logger.warning("⚠️ UI automation requires accessibility permissions")
                logger.warning("   Go to: System Preferences > Security & Privacy > Privacy > Accessibility")
                
        except Exception as e:
            logger.warning(f"⚠️ Cannot check UI permissions: {e}")
            self.enabled = False
    
    async def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        try:
            script = '''
            tell application "System Events"
                set mouseLocation to location of mouse
                return item 1 of mouseLocation & "," & item 2 of mouseLocation
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                coords = result.stdout.strip().split(',')
                return (int(coords[0]), int(coords[1]))
        except Exception as e:
            logger.error(f"❌ Failed to get mouse position: {e}")
        
        return (0, 0)
    
    async def click(self, x: int, y: int, button: str = "left") -> bool:
        """Click at coordinates"""
        if not self.enabled:
            logger.warning("⚠️ UI automation not enabled")
            return False
        
        try:
            if button == "right":
                script = f'''
                tell application "System Events"
                    right click at {{{x}, {y}}}
                end tell
                '''
            else:
                script = f'''
                tell application "System Events"
                    click at {{{x}, {y}}}
                end tell
                '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=10)
            
            success = result.returncode == 0
            if success:
                logger.info(f"🖱️ Clicked at ({x}, {y}) - {button} button")
            else:
                logger.error(f"❌ Click failed: {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Click error: {e}")
            return False
    
    async def double_click(self, x: int, y: int) -> bool:
        """Double click at coordinates"""
        if not self.enabled:
            return False
        
        try:
            script = f'''
            tell application "System Events"
                double click at {{{x}, {y}}}
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=10)
            
            success = result.returncode == 0
            if success:
                logger.info(f"🖱️ Double-clicked at ({x}, {y})")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Double-click error: {e}")
            return False
    
    async def move_mouse(self, x: int, y: int) -> bool:
        """Move mouse to coordinates"""
        if not self.enabled:
            return False
        
        try:
            script = f'''
            tell application "System Events"
                set location of mouse to {{{x}, {y}}}
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            
            success = result.returncode == 0
            if success:
                logger.info(f"🖱️ Moved mouse to ({x}, {y})")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Mouse move error: {e}")
            return False
    
    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """Drag from start to end coordinates"""
        if not self.enabled:
            return False
        
        try:
            script = f'''
            tell application "System Events"
                set startPoint to {{{start_x}, {start_y}}}
                set endPoint to {{{end_x}, {end_y}}}
                
                -- Move to start position
                set location of mouse to startPoint
                delay 0.1
                
                -- Begin drag
                mouse down at startPoint
                delay 0.1
                
                -- Move to end position
                set location of mouse to endPoint
                delay 0.1
                
                -- Release
                mouse up at endPoint
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=15)
            
            success = result.returncode == 0
            if success:
                logger.info(f"🖱️ Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Drag error: {e}")
            return False
    
    async def type_text(self, text: str, delay: float = 0.05) -> bool:
        """Type text with optional delay between characters"""
        if not self.enabled:
            return False
        
        try:
            # Escape special characters for AppleScript
            escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
            
            script = f'''
            tell application "System Events"
                keystroke "{escaped_text}"
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=30)
            
            success = result.returncode == 0
            if success:
                logger.info(f"⌨️ Typed: {text[:50]}{'...' if len(text) > 50 else ''}")
            else:
                logger.error(f"❌ Type failed: {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Type error: {e}")
            return False
    
    async def press_key(self, key: str, modifiers: List[str] = None) -> bool:
        """Press key with optional modifiers"""
        if not self.enabled:
            return False
        
        try:
            # Convert key names to AppleScript format
            key_mapping = {
                'enter': 'return',
                'return': 'return',
                'space': 'space',
                'tab': 'tab',
                'escape': 'escape',
                'delete': 'delete',
                'backspace': 'delete',
                'up': 'up arrow',
                'down': 'down arrow',
                'left': 'left arrow',
                'right': 'right arrow',
                'cmd': 'command',
                'ctrl': 'control',
                'alt': 'option',
                'shift': 'shift'
            }
            
            apple_key = key_mapping.get(key.lower(), key.lower())
            
            if modifiers:
                modifier_list = [key_mapping.get(mod.lower(), mod.lower()) for mod in modifiers]
                modifier_str = " using {" + ", ".join(modifier_list) + " down}"
            else:
                modifier_str = ""
            
            script = f'''
            tell application "System Events"
                key code (ASCII number "{apple_key}"){modifier_str}
            end tell
            '''
            
            # For special keys, use direct keystroke
            if apple_key in ['return', 'space', 'tab', 'escape', 'delete', 'up arrow', 'down arrow', 'left arrow', 'right arrow']:
                script = f'''
                tell application "System Events"
                    keystroke {apple_key}{modifier_str}
                end tell
                '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=10)
            
            success = result.returncode == 0
            if success:
                mod_str = f" with {'+'.join(modifiers)}" if modifiers else ""
                logger.info(f"⌨️ Pressed key: {key}{mod_str}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Key press error: {e}")
            return False
    
    async def scroll(self, x: int, y: int, direction: str = "down", clicks: int = 3) -> bool:
        """Scroll at coordinates"""
        if not self.enabled:
            return False
        
        try:
            scroll_direction = "down" if direction.lower() in ["down", "d"] else "up"
            
            script = f'''
            tell application "System Events"
                repeat {clicks} times
                    scroll {scroll_direction} at {{{x}, {y}}}
                    delay 0.1
                end repeat
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=15)
            
            success = result.returncode == 0
            if success:
                logger.info(f"🖱️ Scrolled {direction} at ({x}, {y}) - {clicks} clicks")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Scroll error: {e}")
            return False
    
    async def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions"""
        try:
            script = '''
            tell application "Finder"
                set screenBounds to bounds of window of desktop
                return (item 3 of screenBounds) & "," & (item 4 of screenBounds)
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                dims = result.stdout.strip().split(',')
                return (int(dims[0]), int(dims[1]))
        except Exception as e:
            logger.error(f"❌ Failed to get screen size: {e}")
        
        return (1920, 1080)  # Default fallback
    
    async def take_screenshot(self, path: str = None) -> str:
        """Take screenshot and return path"""
        if not path:
            path = f"/tmp/screenshot_{int(time.time())}.png"
        
        try:
            result = subprocess.run(['screencapture', '-x', path], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(path):
                logger.info(f"📸 Screenshot saved: {path}")
                return path
            else:
                logger.error(f"❌ Screenshot failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Screenshot error: {e}")
            return None
    
    async def find_and_click_text(self, text: str, app: str = None) -> bool:
        """Find text on screen and click it (requires OCR or accessibility)"""
        # This is a placeholder - would require OCR integration
        logger.warning(f"🔍 Text finding not implemented: '{text}'")
        return False
    
    async def get_active_application(self) -> str:
        """Get name of currently active application"""
        try:
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                app_name = result.stdout.strip()
                logger.info(f"🖥️ Active app: {app_name}")
                return app_name
        except Exception as e:
            logger.error(f"❌ Failed to get active app: {e}")
        
        return "Unknown"
    
    async def switch_to_application(self, app_name: str) -> bool:
        """Switch to specific application"""
        try:
            script = f'''
            tell application "{app_name}"
                activate
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=10)
            
            success = result.returncode == 0
            if success:
                logger.info(f"🔄 Switched to: {app_name}")
                await asyncio.sleep(1)  # Wait for app to become active
            
            return success
            
        except Exception as e:
            logger.error(f"❌ App switch error: {e}")
            return False

class UIAutomationWorkflows:
    """Pre-built UI automation workflows for common tasks"""
    
    def __init__(self):
        self.ui_controller = MacOSUIController()
    
    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open an application"""
        try:
            logger.info(f"🚀 Opening application: {app_name}")
            
            # Use Spotlight to open app
            await self.ui_controller.press_key('space', ['cmd'])  # Cmd+Space for Spotlight
            await asyncio.sleep(0.5)
            
            await self.ui_controller.type_text(app_name)
            await asyncio.sleep(0.5)
            
            await self.ui_controller.press_key('return')
            await asyncio.sleep(2)  # Wait for app to launch
            
            # Verify app opened
            active_app = await self.ui_controller.get_active_application()
            success = app_name.lower() in active_app.lower()
            
            return {
                "success": success,
                "action": "open_application",
                "app_name": app_name,
                "active_app": active_app,
                "message": f"{'Successfully opened' if success else 'Failed to open'} {app_name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "action": "open_application",
                "error": str(e)
            }
    
    async def create_new_document(self) -> Dict[str, Any]:
        """Create new document (Cmd+N)"""
        try:
            logger.info("📄 Creating new document")
            success = await self.ui_controller.press_key('n', ['cmd'])
            await asyncio.sleep(1)
            
            return {
                "success": success,
                "action": "create_new_document",
                "message": "New document created" if success else "Failed to create document"
            }
        except Exception as e:
            return {"success": False, "action": "create_new_document", "error": str(e)}
    
    async def save_document(self, filename: str = None) -> Dict[str, Any]:
        """Save current document (Cmd+S)"""
        try:
            logger.info("💾 Saving document")
            
            # Press Cmd+S
            await self.ui_controller.press_key('s', ['cmd'])
            await asyncio.sleep(1)
            
            # If filename provided, type it
            if filename:
                await self.ui_controller.type_text(filename)
                await asyncio.sleep(0.5)
                await self.ui_controller.press_key('return')
                await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "save_document",
                "filename": filename,
                "message": f"Document saved{' as ' + filename if filename else ''}"
            }
        except Exception as e:
            return {"success": False, "action": "save_document", "error": str(e)}
    
    async def copy_paste_workflow(self, source_coords: Tuple[int, int], dest_coords: Tuple[int, int]) -> Dict[str, Any]:
        """Copy from source location and paste to destination"""
        try:
            logger.info(f"📋 Copy-paste from {source_coords} to {dest_coords}")
            
            # Click source and select all
            await self.ui_controller.click(*source_coords)
            await asyncio.sleep(0.2)
            await self.ui_controller.press_key('a', ['cmd'])  # Select all
            await asyncio.sleep(0.2)
            
            # Copy
            await self.ui_controller.press_key('c', ['cmd'])
            await asyncio.sleep(0.2)
            
            # Click destination
            await self.ui_controller.click(*dest_coords)
            await asyncio.sleep(0.2)
            
            # Paste
            await self.ui_controller.press_key('v', ['cmd'])
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "action": "copy_paste_workflow",
                "source": source_coords,
                "destination": dest_coords,
                "message": "Copy-paste completed successfully"
            }
        except Exception as e:
            return {"success": False, "action": "copy_paste_workflow", "error": str(e)}
    
    async def window_management(self, action: str) -> Dict[str, Any]:
        """Manage windows (minimize, maximize, close)"""
        try:
            key_mappings = {
                "minimize": ('m', ['cmd']),
                "close": ('w', ['cmd']),
                "maximize": ('f', ['cmd', 'ctrl']),  # Full screen
                "hide": ('h', ['cmd'])
            }
            
            if action.lower() not in key_mappings:
                return {"success": False, "error": f"Unknown window action: {action}"}
            
            key, modifiers = key_mappings[action.lower()]
            success = await self.ui_controller.press_key(key, modifiers)
            await asyncio.sleep(0.5)
            
            return {
                "success": success,
                "action": f"window_{action}",
                "message": f"Window {action} executed"
            }
        except Exception as e:
            return {"success": False, "action": f"window_{action}", "error": str(e)}
    
    async def text_editing_workflow(self, text: str, formatting: List[str] = None) -> Dict[str, Any]:
        """Type text with optional formatting"""
        try:
            logger.info(f"✏️ Text editing: {text[:50]}...")
            
            # Type the text
            await self.ui_controller.type_text(text)
            await asyncio.sleep(0.5)
            
            # Apply formatting if specified
            if formatting:
                # Select the text first
                await self.ui_controller.press_key('a', ['cmd'])
                await asyncio.sleep(0.2)
                
                for fmt in formatting:
                    if fmt.lower() == "bold":
                        await self.ui_controller.press_key('b', ['cmd'])
                    elif fmt.lower() == "italic":
                        await self.ui_controller.press_key('i', ['cmd'])
                    elif fmt.lower() == "underline":
                        await self.ui_controller.press_key('u', ['cmd'])
                    
                    await asyncio.sleep(0.2)
            
            return {
                "success": True,
                "action": "text_editing",
                "text_length": len(text),
                "formatting": formatting or [],
                "message": f"Text typed and formatted successfully"
            }
        except Exception as e:
            return {"success": False, "action": "text_editing", "error": str(e)}

# Global instance
_ui_automation = None

async def get_ui_automation() -> UIAutomationWorkflows:
    """Get or create global UI automation instance"""
    global _ui_automation
    if _ui_automation is None:
        _ui_automation = UIAutomationWorkflows()
    return _ui_automation

async def execute_ui_action(action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute UI automation action"""
    automation = await get_ui_automation()
    
    try:
        if action_type == "open_app":
            return await automation.open_application(parameters.get("app_name", ""))
        elif action_type == "click":
            coords = parameters.get("coordinates", (0, 0))
            controller = automation.ui_controller
            success = await controller.click(coords[0], coords[1])
            return {"success": success, "action": "click", "coordinates": coords}
        elif action_type == "type":
            text = parameters.get("text", "")
            controller = automation.ui_controller
            success = await controller.type_text(text)
            return {"success": success, "action": "type", "text": text}
        elif action_type == "key":
            key = parameters.get("key", "")
            modifiers = parameters.get("modifiers", [])
            controller = automation.ui_controller
            success = await controller.press_key(key, modifiers)
            return {"success": success, "action": "key", "key": key, "modifiers": modifiers}
        elif action_type == "window_action":
            return await automation.window_management(parameters.get("action", ""))
        elif action_type == "copy_paste":
            source = parameters.get("source", (0, 0))
            dest = parameters.get("destination", (0, 0))
            return await automation.copy_paste_workflow(source, dest)
        elif action_type == "new_document":
            return await automation.create_new_document()
        elif action_type == "save_document":
            return await automation.save_document(parameters.get("filename"))
        else:
            return {"success": False, "error": f"Unknown UI action: {action_type}"}
            
    except Exception as e:
        return {"success": False, "error": str(e), "action": action_type}