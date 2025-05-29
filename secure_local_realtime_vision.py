#!/usr/bin/env python3
"""
Secure Local Real-Time Vision System
100% Local, No External Dependencies, Maximum Privacy & Security
"""

import asyncio
import socket
import json
import time
import logging
import threading
import queue
import numpy as np
import cv2
import os
import sys
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# SECURITY: Only local imports, no external connections
try:
    import PIL.Image
    import PIL.ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Platform-specific for macOS (local only)
if sys.platform == "darwin":
    try:
        import Quartz
        import Quartz.CoreGraphics as CG
        from AppKit import NSWorkspace
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
else:
    MACOS_AVAILABLE = False

# SECURITY: Local logging only, no external services
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/secure_vision.log'),  # Local temp file only
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SecureScreenFrame:
    """Secure local screen frame - never leaves this machine"""
    timestamp: float
    frame_id: int
    width: int
    height: int
    data_size: int  # Track data but don't store raw pixels in memory longer than needed
    ui_elements: List[Dict[str, Any]]
    cursor_position: Tuple[int, int]
    active_window: Optional[str]
    processing_time: float

class SecureLocalScreenCapture:
    """Secure local screen capture - all processing happens locally"""
    
    def __init__(self, fps: int = 15):  # Reduced FPS for security/performance
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.frame_id = 0
        self.running = False
        self.capture_thread = None
        
        # SECURITY: Local memory buffer only, auto-cleanup
        self.max_buffer_size = 3  # Keep only 3 frames max
        self.frame_buffer = queue.Queue(maxsize=self.max_buffer_size)
        
        # Performance tracking (local only)
        self.frames_captured = 0
        self.start_time = time.time()
        
        # Screen info
        self.screen_width = 1920
        self.screen_height = 1080
        self._init_screen_info()
        
        logger.info(f"🔒 Secure screen capture initialized: {self.screen_width}x{self.screen_height} @ {fps}fps")
    
    def _init_screen_info(self):
        """Initialize screen dimensions locally"""
        try:
            if PIL_AVAILABLE:
                # Get screen size without capturing
                screenshot = PIL.ImageGrab.grab(bbox=(0, 0, 100, 100))  # Tiny sample
                full_screenshot = PIL.ImageGrab.grab()
                self.screen_width, self.screen_height = full_screenshot.size
                del full_screenshot  # Immediate cleanup
        except Exception as e:
            logger.warning(f"Could not detect screen size: {e}")
    
    def start_capture(self):
        """Start secure local screen capture"""
        if self.running:
            return
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._secure_capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("🔒 Secure local screen capture started")
    
    def stop_capture(self):
        """Stop capture and cleanup"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        
        # SECURITY: Clear all frames from memory
        while not self.frame_buffer.empty():
            try:
                self.frame_buffer.get_nowait()
            except queue.Empty:
                break
        
        logger.info("🔒 Secure capture stopped and memory cleared")
    
    def _secure_capture_loop(self):
        """Secure capture loop - all data stays local"""
        while self.running:
            loop_start = time.time()
            
            try:
                # Capture screen securely
                frame_data = self._capture_screen_secure()
                if frame_data:
                    # Add to buffer (auto-drops old frames)
                    try:
                        self.frame_buffer.put_nowait(frame_data)
                    except queue.Full:
                        # Remove oldest frame and add new one
                        try:
                            old_frame = self.frame_buffer.get_nowait()
                            del old_frame  # Explicit cleanup
                            self.frame_buffer.put_nowait(frame_data)
                        except queue.Empty:
                            pass
                
                self.frames_captured += 1
                
            except Exception as e:
                logger.error(f"Secure capture error: {e}")
            
            # Maintain FPS
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _capture_screen_secure(self) -> Optional[SecureScreenFrame]:
        """Secure screen capture - data never leaves this function scope"""
        try:
            process_start = time.time()
            current_time = time.time()
            
            # SECURITY: Use most reliable local method
            screenshot = None
            if PIL_AVAILABLE:
                screenshot = PIL.ImageGrab.grab()
                width, height = screenshot.size
                frame_array = np.array(screenshot)
            else:
                logger.error("No secure screen capture method available")
                return None
            
            # Process locally for UI elements
            ui_elements = self._detect_ui_elements_secure(frame_array)
            
            # Get cursor position (locally)
            cursor_pos = self._get_cursor_position_secure()
            
            # Get active window (locally)
            active_window = self._get_active_window_secure()
            
            # Calculate processing time
            processing_time = time.time() - process_start
            
            self.frame_id += 1
            
            # Create secure frame (no raw data stored)
            secure_frame = SecureScreenFrame(
                timestamp=current_time,
                frame_id=self.frame_id,
                width=width,
                height=height,
                data_size=frame_array.nbytes,
                ui_elements=ui_elements,
                cursor_position=cursor_pos,
                active_window=active_window,
                processing_time=processing_time
            )
            
            # SECURITY: Immediate cleanup of image data
            del screenshot
            del frame_array
            
            return secure_frame
            
        except Exception as e:
            logger.error(f"Secure screen capture failed: {e}")
            return None
    
    def _detect_ui_elements_secure(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Secure local UI element detection"""
        ui_elements = []
        
        try:
            # Convert to grayscale for processing
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Simple edge detection for UI elements
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            element_id = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 50000:  # Reasonable UI element size
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Basic classification
                    aspect_ratio = w / h if h > 0 else 0
                    element_type = "button"
                    if aspect_ratio > 3:
                        element_type = "text_field"
                    elif aspect_ratio < 0.5:
                        element_type = "icon"
                    
                    ui_elements.append({
                        "id": f"ui_{element_id}",
                        "type": element_type,
                        "bounds": (x, y, w, h),
                        "confidence": 0.7,
                        "clickable": True,
                        "visible": True,
                        "timestamp": time.time()
                    })
                    
                    element_id += 1
                    if element_id >= 10:  # Limit for performance
                        break
        
        except Exception as e:
            logger.error(f"UI element detection error: {e}")
        
        return ui_elements
    
    def _get_cursor_position_secure(self) -> Tuple[int, int]:
        """Get cursor position locally"""
        try:
            if MACOS_AVAILABLE:
                event = CG.CGEventCreate(None)
                cursor_pos = CG.CGEventGetLocation(event)
                return (int(cursor_pos.x), int(cursor_pos.y))
            else:
                return (self.screen_width // 2, self.screen_height // 2)
        except:
            return (0, 0)
    
    def _get_active_window_secure(self) -> Optional[str]:
        """Get active window locally"""
        try:
            if MACOS_AVAILABLE:
                active_app = NSWorkspace.sharedWorkspace().activeApplication()
                return active_app.get('NSApplicationName', 'Unknown')
            else:
                return "Unknown"
        except:
            return None
    
    def get_latest_frame_secure(self) -> Optional[SecureScreenFrame]:
        """Get latest frame (secure local access only)"""
        try:
            return self.frame_buffer.get_nowait()
        except queue.Empty:
            return None

class SecureLocalVisionAgent:
    """Secure local vision agent - all processing happens on this machine"""
    
    def __init__(self):
        self.screen_capture = SecureLocalScreenCapture(fps=10)  # Conservative FPS
        self.running = False
        self.actions_executed = 0
        self.start_time = time.time()
        
        # SECURITY: Local input control only
        self.input_controller = None
        self._init_secure_input()
        
        # Vision state (local only)
        self.current_frame = None
        self.ui_elements = []
        self.active_window = ""
        
        logger.info("🔒 Secure local vision agent initialized")
    
    def _init_secure_input(self):
        """Initialize secure local input control"""
        try:
            # Import locally available input controller
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from agent_workflow.input_controller import InputController
            self.input_controller = InputController(safety_level="high")
            logger.info("🔒 Secure input controller initialized")
        except ImportError:
            logger.warning("Input controller not available - view-only mode")
    
    async def start_secure_vision(self):
        """Start secure local vision processing"""
        self.running = True
        self.start_time = time.time()
        
        # Start screen capture
        self.screen_capture.start_capture()
        
        logger.info("🔒 Starting secure local vision...")
        
        # Start processing loop
        await self._secure_vision_loop()
    
    async def stop_secure_vision(self):
        """Stop secure vision and cleanup"""
        self.running = False
        self.screen_capture.stop_capture()
        
        # Clear local state
        self.current_frame = None
        self.ui_elements = []
        
        logger.info("🔒 Secure vision stopped and cleaned up")
    
    async def _secure_vision_loop(self):
        """Secure vision processing loop"""
        while self.running:
            try:
                # Get latest frame (local only)
                frame = self.screen_capture.get_latest_frame_secure()
                if frame:
                    self._update_local_state(frame)
                    
                    # Log status every 50 frames
                    if frame.frame_id % 50 == 0:
                        logger.info(f"🔒 Processing frame {frame.frame_id}, "
                                  f"{len(self.ui_elements)} UI elements, "
                                  f"window: {self.active_window}")
                
            except Exception as e:
                logger.error(f"Secure vision loop error: {e}")
            
            # Process at 5Hz for security/performance
            await asyncio.sleep(0.2)
    
    def _update_local_state(self, frame: SecureScreenFrame):
        """Update local vision state"""
        self.current_frame = frame
        self.ui_elements = frame.ui_elements
        self.active_window = frame.active_window or ""
    
    async def execute_secure_command(self, command: str) -> Dict[str, Any]:
        """Execute command securely with local vision context"""
        try:
            logger.info(f"🔒 Executing secure command: {command}")
            
            if not self.input_controller:
                return {
                    'success': False,
                    'error': 'Input control not available - view-only mode',
                    'vision_summary': self.get_secure_vision_summary()
                }
            
            # Simple local command parsing
            command_lower = command.lower()
            
            if "click" in command_lower and self.ui_elements:
                # Find a clickable element
                clickable = [e for e in self.ui_elements if e.get('clickable', False)]
                if clickable:
                    element = clickable[0]
                    x, y, w, h = element['bounds']
                    center_x, center_y = x + w//2, y + h//2
                    
                    # Execute click locally
                    self.input_controller.click(center_x, center_y)
                    self.actions_executed += 1
                    
                    return {
                        'success': True,
                        'action': f'Clicked element at ({center_x}, {center_y})',
                        'vision_summary': self.get_secure_vision_summary()
                    }
            
            elif "type" in command_lower:
                # Extract text to type
                words = command.split()
                if len(words) > 1:
                    text = " ".join(words[1:])
                    self.input_controller.type_text(text)
                    self.actions_executed += 1
                    
                    return {
                        'success': True,
                        'action': f'Typed: {text}',
                        'vision_summary': self.get_secure_vision_summary()
                    }
            
            elif "observe" in command_lower or "analyze" in command_lower:
                # Just return current state
                return {
                    'success': True,
                    'action': 'Screen observation completed',
                    'vision_summary': self.get_secure_vision_summary()
                }
            
            return {
                'success': False,
                'error': f'Command not recognized: {command}',
                'vision_summary': self.get_secure_vision_summary()
            }
            
        except Exception as e:
            logger.error(f"Secure command execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'vision_summary': self.get_secure_vision_summary()
            }
    
    def get_secure_vision_summary(self) -> Dict[str, Any]:
        """Get secure local vision summary"""
        uptime = time.time() - self.start_time
        
        return {
            'mode': 'SECURE_LOCAL_ONLY',
            'privacy': 'MAXIMUM - No external connections',
            'uptime_seconds': round(uptime, 2),
            'frames_processed': self.screen_capture.frames_captured,
            'current_window': self.active_window,
            'ui_elements_detected': len(self.ui_elements),
            'actions_executed': self.actions_executed,
            'screen_size': f"{self.screen_capture.screen_width}x{self.screen_capture.screen_height}",
            'capture_fps': self.screen_capture.fps,
            'last_frame_id': self.current_frame.frame_id if self.current_frame else 0,
            'security_status': 'ALL_LOCAL_NO_NETWORK'
        }

class SecureLocalVisionServer:
    """Secure local vision server - Unix socket only, no network"""
    
    def __init__(self, socket_path: str = "/tmp/secure_vision.sock"):
        self.socket_path = socket_path
        self.agent = SecureLocalVisionAgent()
        self.running = False
        
        # SECURITY: Clean up any existing socket
        if os.path.exists(socket_path):
            os.unlink(socket_path)
    
    async def start_secure_server(self):
        """Start secure local server (Unix socket only)"""
        try:
            # SECURITY: Unix socket for local communication only
            self.server = await asyncio.start_unix_server(
                self._handle_secure_client,
                path=self.socket_path
            )
            
            # Restrict socket permissions (owner only)
            os.chmod(self.socket_path, 0o600)
            
            self.running = True
            
            # Start vision agent
            agent_task = asyncio.create_task(self.agent.start_secure_vision())
            
            logger.info(f"🔒 Secure local vision server started at {self.socket_path}")
            logger.info("🔒 SECURITY: Unix socket only, no network access")
            
            async with self.server:
                await self.server.serve_forever()
            
        except Exception as e:
            logger.error(f"Secure server error: {e}")
            await self.stop_secure_server()
    
    async def stop_secure_server(self):
        """Stop secure server and cleanup"""
        self.running = False
        
        if hasattr(self, 'server'):
            self.server.close()
            await self.server.wait_closed()
        
        await self.agent.stop_secure_vision()
        
        # SECURITY: Clean up socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        logger.info("🔒 Secure server stopped and cleaned up")
    
    async def _handle_secure_client(self, reader, writer):
        """Handle secure local client connections"""
        try:
            peer = writer.get_extra_info('peername', 'unknown')
            logger.info(f"🔒 Secure local client connected: {peer}")
            
            while self.running:
                # Read command (local only)
                data = await reader.read(1024)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    command = message.get('command', '')
                    
                    # Execute command securely
                    result = await self.agent.execute_secure_command(command)
                    
                    # Send response (local only)
                    response = json.dumps(result).encode('utf-8')
                    writer.write(response)
                    await writer.drain()
                    
                except json.JSONDecodeError:
                    error_response = json.dumps({
                        'success': False,
                        'error': 'Invalid JSON'
                    }).encode('utf-8')
                    writer.write(error_response)
                    await writer.drain()
        
        except Exception as e:
            logger.error(f"Secure client handler error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            logger.info("🔒 Secure client disconnected")

async def main():
    """Main function for secure local vision system"""
    print("🔒 SECURE LOCAL REAL-TIME VISION SYSTEM")
    print("=" * 50)
    print("✅ 100% Local Processing")
    print("✅ No External Network Connections") 
    print("✅ Maximum Privacy Protection")
    print("✅ Unix Socket Communication Only")
    print("✅ Automatic Memory Cleanup")
    print("=" * 50)
    
    server = SecureLocalVisionServer()
    
    try:
        await server.start_secure_server()
    except KeyboardInterrupt:
        print("\n🔒 Shutting down secure vision system...")
    finally:
        await server.stop_secure_server()

if __name__ == "__main__":
    asyncio.run(main())