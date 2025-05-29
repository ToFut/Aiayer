#!/usr/bin/env python3
"""
Real-Time Screen TCP Server
Like TeamViewer screen sharing - streams live screen data to agent via TCP
"""

import asyncio
import socket
import struct
import json
import time
import logging
import threading
import queue
import numpy as np
import cv2
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Platform-specific screen capture
import sys
if sys.platform == "darwin":
    import Quartz
    import Quartz.CoreGraphics as CG
    MACOS_AVAILABLE = True
else:
    MACOS_AVAILABLE = False

try:
    import PIL.Image
    import PIL.ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScreenFrame:
    """Real-time screen frame data"""
    timestamp: float
    frame_id: int
    width: int
    height: int
    format: str  # "rgb", "bgr", "compressed"
    data: bytes
    ui_elements: List[Dict[str, Any]]
    cursor_position: Tuple[int, int]
    active_window: Optional[str]
    fps: float

@dataclass
class UIElement:
    """Live UI element detected in real-time"""
    id: str
    type: str  # button, input, text, etc.
    text: str
    bounds: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    clickable: bool
    visible: bool
    timestamp: float

class RealTimeScreenCapture:
    """High-performance real-time screen capture like TeamViewer"""
    
    def __init__(self, fps: int = 30, compression_quality: int = 85):
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.compression_quality = compression_quality
        self.frame_id = 0
        self.running = False
        self.capture_thread = None
        self.frame_queue = queue.Queue(maxsize=5)  # Buffer 5 frames max
        
        # Performance metrics
        self.frames_captured = 0
        self.last_frame_time = 0
        
        # Screen sharing settings
        self.enable_compression = True
        self.jpeg_quality = compression_quality
        self.scale_factor = 0.75  # Scale down for faster transmission
        self.start_time = time.time()
        self.last_frame_time = 0
        
        # Screen info
        self.screen_width = 0
        self.screen_height = 0
        self._init_screen_info()
        
        logger.info(f"Screen capture initialized: {self.screen_width}x{self.screen_height} @ {fps}fps")
    
    def _init_screen_info(self):
        """Initialize screen dimensions"""
        if MACOS_AVAILABLE:
            # macOS screen info
            main_display = CG.CGMainDisplayID()
            self.screen_width = CG.CGDisplayPixelsWide(main_display)
            self.screen_height = CG.CGDisplayPixelsHigh(main_display)
        elif PIL_AVAILABLE:
            # Cross-platform fallback
            screenshot = PIL.ImageGrab.grab()
            self.screen_width, self.screen_height = screenshot.size
        else:
            # Default fallback
            self.screen_width, self.screen_height = 1920, 1080
    
    def start_capture(self):
        """Start real-time screen capture"""
        if self.running:
            return
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("Real-time screen capture started")
    
    def stop_capture(self):
        """Stop screen capture"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        logger.info("Screen capture stopped")
    
    def _capture_loop(self):
        """Main capture loop running at target FPS"""
        while self.running:
            loop_start = time.time()
            
            try:
                # Capture screen
                frame_data = self._capture_screen_fast()
                if frame_data:
                    # Try to put frame in queue (non-blocking)
                    try:
                        self.frame_queue.put_nowait(frame_data)
                    except queue.Full:
                        # Drop oldest frame if queue full
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame_data)
                        except queue.Empty:
                            pass
                
                self.frames_captured += 1
                
            except Exception as e:
                logger.error(f"Screen capture error: {e}")
            
            # Maintain target FPS
            elapsed = time.time() - loop_start
            sleep_time = max(0, self.frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _capture_screen_fast(self) -> Optional[ScreenFrame]:
        """Fast screen capture with UI element detection"""
        try:
            current_time = time.time()
            
            # Use PIL for more reliable cross-platform capture
            if PIL_AVAILABLE:
                # PIL capture (most reliable)
                screenshot = PIL.ImageGrab.grab()
                
                # Convert RGBA to RGB if needed (fix for JPEG compatibility)
                if screenshot.mode == 'RGBA':
                    screenshot = screenshot.convert('RGB')
                
                frame_rgb = np.array(screenshot)
                width, height = screenshot.size
                
            elif MACOS_AVAILABLE:
                # macOS native capture as fallback
                try:
                    image = CG.CGWindowListCreateImage(
                        CG.CGRectInfinite,
                        CG.kCGWindowListOptionOnScreenOnly,
                        CG.kCGNullWindowID,
                        CG.kCGWindowImageDefault
                    )
                    
                    if not image:
                        return None
                    
                    # Convert to numpy array safely
                    width = CG.CGImageGetWidth(image)
                    height = CG.CGImageGetHeight(image)
                    bytes_per_row = CG.CGImageGetBytesPerRow(image)
                    bits_per_pixel = CG.CGImageGetBitsPerPixel(image)
                    
                    # Get raw pixel data
                    try:
                        provider = CG.CGImageGetDataProvider(image)
                        data = CG.CGDataProviderCopyData(provider)
                        pixels = np.frombuffer(data, dtype=np.uint8)
                        
                        # Calculate expected array size safely
                        expected_size = height * bytes_per_row
                        actual_size = len(pixels)
                        
                        if actual_size != expected_size:
                            logger.debug(f"Pixel array size mismatch: got {actual_size}, expected {expected_size}")
                            # Fall back to PIL immediately for safety
                            raise ValueError("Pixel size mismatch - using PIL fallback")
                        
                        # Reshape safely based on actual data
                        if bits_per_pixel == 32 and bytes_per_row % 4 == 0:  # BGRA
                            try:
                                pixels_per_row = bytes_per_row // 4
                                frame_array = pixels.reshape((height, pixels_per_row, 4))
                                # Crop to actual width if needed
                                if pixels_per_row > width:
                                    frame_array = frame_array[:, :width, :]
                                frame_rgb = cv2.cvtColor(frame_array, cv2.COLOR_BGRA2RGB)
                            except ValueError as reshape_error:
                                logger.debug(f"Reshape error: {reshape_error} - using PIL fallback")
                                raise ValueError("Reshape failed - using PIL fallback")
                        else:
                            # Unsupported format - fallback to PIL
                            raise ValueError("Unsupported pixel format - using PIL fallback")
                    
                    except (ValueError, Exception) as capture_error:
                        logger.debug(f"macOS capture issue: {capture_error} - falling back to PIL")
                        # Always fall back to PIL for any issues
                        if PIL_AVAILABLE:
                            screenshot = PIL.ImageGrab.grab()
                            frame_rgb = np.array(screenshot)
                            width, height = screenshot.size
                        else:
                            return None
                                
                except Exception as e:
                    logger.warning(f"macOS capture failed, falling back to PIL: {e}")
                    if PIL_AVAILABLE:
                        screenshot = PIL.ImageGrab.grab()
                        frame_rgb = np.array(screenshot)
                        width, height = screenshot.size
                    else:
                        return None
            else:
                logger.error("No screen capture method available")
                return None
            
            # Compress frame for network transmission
            _, compressed_data = cv2.imencode(
                '.jpg', 
                cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, self.compression_quality]
            )
            
            # Get cursor position
            cursor_pos = self._get_cursor_position()
            
            # Detect UI elements in real-time
            ui_elements = self._detect_ui_elements_fast(frame_rgb)
            
            # Get active window
            active_window = self._get_active_window()
            
            # Calculate FPS
            fps = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0
            self.last_frame_time = current_time
            
            self.frame_id += 1
            
            return ScreenFrame(
                timestamp=current_time,
                frame_id=self.frame_id,
                width=width,
                height=height,
                format="compressed_jpeg",
                data=compressed_data.tobytes(),
                ui_elements=ui_elements,
                cursor_position=cursor_pos,
                active_window=active_window,
                fps=fps
            )
            
        except Exception as e:
            logger.error(f"Fast screen capture failed: {e}")
            return None
    
    def _get_cursor_position(self) -> Tuple[int, int]:
        """Get current cursor position"""
        try:
            if MACOS_AVAILABLE:
                # macOS cursor position
                event = CG.CGEventCreate(None)
                cursor_pos = CG.CGEventGetLocation(event)
                return (int(cursor_pos.x), int(cursor_pos.y))
            else:
                # Try other methods or return center
                return (self.screen_width // 2, self.screen_height // 2)
        except:
            return (0, 0)
    
    def _get_active_window(self) -> Optional[str]:
        """Get active window title"""
        try:
            if MACOS_AVAILABLE:
                from AppKit import NSWorkspace
                active_app = NSWorkspace.sharedWorkspace().activeApplication()
                return active_app.get('NSApplicationName', 'Unknown')
            else:
                return "Unknown"
        except:
            return None
    
    def _detect_ui_elements_fast(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Fast UI element detection on live frame"""
        ui_elements = []
        
        try:
            # Convert to grayscale for faster processing
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Quick button detection using edge detection
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            element_id = 0
            for contour in contours:
                # Filter by size - likely UI elements
                area = cv2.contourArea(contour)
                if 500 < area < 50000:  # Reasonable button/element size
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Basic shape analysis
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Classify element type
                    element_type = "button"
                    if aspect_ratio > 3:
                        element_type = "text_field"
                    elif aspect_ratio < 0.5:
                        element_type = "icon"
                    
                    # Extract text region (simplified)
                    text_region = gray[y:y+h, x:x+w]
                    text = f"Element_{element_id}"  # Placeholder - could use OCR
                    
                    ui_elements.append({
                        "id": f"ui_{element_id}",
                        "type": element_type,
                        "text": text,
                        "bounds": (x, y, w, h),
                        "confidence": 0.7,
                        "clickable": True,
                        "visible": True,
                        "timestamp": time.time()
                    })
                    
                    element_id += 1
                    
                    # Limit elements for performance
                    if element_id >= 20:
                        break
        
        except Exception as e:
            logger.error(f"UI element detection error: {e}")
        
        return ui_elements
    
    def get_latest_frame(self) -> Optional[ScreenFrame]:
        """Get latest screen frame (non-blocking)"""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_compressed_frame_data(self) -> Optional[Dict[str, Any]]:
        """Get compressed frame data for web streaming"""
        frame = self.get_latest_frame()
        if not frame:
            return None
        
        import base64
        
        # Convert frame data to base64 for web transmission
        frame_base64 = base64.b64encode(frame.data).decode('utf-8')
        
        return {
            "type": "screen_frame",
            "timestamp": frame.timestamp,
            "frame_id": frame.frame_id,
            "width": frame.width,
            "height": frame.height,
            "format": frame.format,
            "data": frame_base64,
            "ui_elements": frame.ui_elements,
            "cursor_position": frame.cursor_position,
            "active_window": frame.active_window,
            "fps": frame.fps,
            "compressed": True
        }

class RealTimeScreenTCPServer:
    """LOCAL SECURE TCP server - localhost only, no external access"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9999):  # SECURITY: localhost only
        # SECURITY: Force localhost only
        if host not in ["127.0.0.1", "localhost"]:
            raise ValueError("SECURITY: Only localhost connections allowed")
        
        self.host = "127.0.0.1"  # Force localhost
        self.port = port
        self.server_socket = None
        self.client_connections = []
        self.running = False
        self.screen_capture = RealTimeScreenCapture(fps=15)  # Reduced for security
        
        # Performance tracking (local only)
        self.frames_sent = 0
        self.bytes_sent = 0
        self.start_time = None
        
        logger.info(f"🔒 SECURE LOCAL SERVER: {self.host}:{self.port} - NO EXTERNAL ACCESS")
        
    async def start_server(self):
        """Start SECURE LOCAL TCP server - localhost only"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # SECURITY: Bind to localhost only
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)  # Only 1 connection for security
            self.server_socket.setblocking(False)
            
            self.running = True
            self.start_time = time.time()
            
            # Start screen capture
            self.screen_capture.start_capture()
            
            logger.info(f"🔒 SECURE local server started on {self.host}:{self.port}")
            logger.info("🔒 SECURITY: Localhost only, no external network access")
            
            # Start accepting connections
            await self._accept_connections()
            
        except Exception as e:
            logger.error(f"Server start error: {e}")
            await self.stop_server()
    
    async def stop_server(self):
        """Stop TCP server"""
        self.running = False
        
        # Close client connections
        for client_socket in self.client_connections[:]:
            try:
                client_socket.close()
            except:
                pass
        self.client_connections.clear()
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Stop screen capture
        self.screen_capture.stop_capture()
        
        logger.info("TCP server stopped")
    
    async def _accept_connections(self):
        """Accept SECURE LOCAL connections only"""
        while self.running:
            try:
                client_socket, address = await asyncio.get_event_loop().sock_accept(self.server_socket)
                
                # SECURITY: Verify localhost connection
                client_ip = address[0]
                if client_ip not in ["127.0.0.1", "::1"]:
                    logger.warning(f"🔒 SECURITY ALERT: Rejected non-localhost connection from {address}")
                    logger.warning(f"🔒 SECURITY: Only localhost (127.0.0.1) connections allowed")
                    client_socket.close()
                    continue
                
                # SECURITY: Additional validation
                logger.info(f"🔒 SECURITY: Validated localhost connection from {address}")
                
                logger.info(f"🔒 Secure agent connected from {address}")
                
                # SECURITY: Limit to 1 connection
                if len(self.client_connections) >= 1:
                    logger.warning("🔒 SECURITY: Connection limit reached, closing new connection")
                    client_socket.close()
                    continue
                
                self.client_connections.append(client_socket)
                
                # Start streaming to this client
                asyncio.create_task(self._stream_to_client(client_socket, address))
                
            except Exception as e:
                if self.running:
                    logger.error(f"Accept connection error: {e}")
                await asyncio.sleep(0.1)
    
    async def _stream_to_client(self, client_socket: socket.socket, address):
        """Stream screen frames to connected agent"""
        try:
            while self.running:
                # Get latest frame - try multiple times if needed
                frame = None
                for _ in range(3):  # Try 3 times
                    frame = self.screen_capture.get_latest_frame()
                    if frame:
                        break
                    await asyncio.sleep(0.01)  # Short wait
                
                if frame:
                    try:
                        # Serialize frame data
                        frame_json = json.dumps(asdict(frame), default=self._json_serializer)
                        frame_bytes = frame_json.encode('utf-8')
                        
                        # Send frame size first (4 bytes)
                        size_bytes = struct.pack('!I', len(frame_bytes))
                        await asyncio.get_event_loop().sock_sendall(client_socket, size_bytes)
                        
                        # Send frame data
                        await asyncio.get_event_loop().sock_sendall(client_socket, frame_bytes)
                        
                        self.frames_sent += 1
                        self.bytes_sent += len(frame_bytes)
                        
                        # Log first few frames for debugging
                        if self.frames_sent <= 5:
                            logger.info(f"📤 Sent frame {self.frames_sent}: {frame.width}x{frame.height}, {len(frame_bytes)} bytes")
                        
                        # Log performance periodically
                        if self.frames_sent % 100 == 0:
                            elapsed = time.time() - self.start_time
                            fps = self.frames_sent / elapsed
                            mbps = (self.bytes_sent / elapsed) / (1024 * 1024)
                            logger.info(f"Streaming: {fps:.1f} FPS, {mbps:.2f} MB/s to {address}")
                    
                    except Exception as send_error:
                        logger.error(f"Frame send error: {send_error}")
                        break
                else:
                    # Log when no frame available
                    if self.frames_sent % 50 == 0:  # Log occasionally
                        logger.debug("No frame available from capture")
                
                # Control streaming rate
                await asyncio.sleep(0.066)  # ~15 FPS to match capture rate
                
        except Exception as e:
            logger.error(f"Streaming error to {address}: {e}")
        finally:
            try:
                client_socket.close()
                if client_socket in self.client_connections:
                    self.client_connections.remove(client_socket)
                logger.info(f"Client {address} disconnected")
            except:
                pass
    
    def _json_serializer(self, obj):
        """JSON serializer for numpy arrays and bytes"""
        if isinstance(obj, bytes):
            import base64
            return base64.b64encode(obj).decode('utf-8')
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class RealtimeScreenTCPServer:
    """
    Simplified screen capture server for WebSocket integration.
    Provides compressed frame data for screen sharing.
    """
    
    def __init__(self):
        self.screen_capture = RealTimeScreenCapture(fps=30)
        self.started = False
        logger.info("RealtimeScreenTCPServer initialized for WebSocket integration")
    
    async def start(self):
        """Start screen capture"""
        if not self.started:
            self.screen_capture.start_capture()
            self.started = True
            logger.info("Screen capture started for WebSocket streaming")
    
    def get_compressed_frame_data(self) -> Optional[Dict[str, Any]]:
        """Get compressed frame data for web streaming"""
        try:
            # Start capture if not already started
            if not self.started:
                self.screen_capture.start_capture()
                self.started = True
            
            # Get latest frame
            frame = self.screen_capture.get_latest_frame()
            if not frame:
                logger.warning("No frame available from screen capture")
                return None
            
            # Convert frame data to base64 for web transmission
            import base64
            
            frame_base64 = base64.b64encode(frame.data).decode('utf-8')
            
            compressed_frame = {
                "type": "screen_frame",
                "timestamp": frame.timestamp,
                "frame_id": frame.frame_id,
                "width": frame.width,
                "height": frame.height,
                "format": "compressed_jpeg",
                "data": frame_base64,
                "ui_elements": frame.ui_elements or [],
                "cursor_position": frame.cursor_position or {"x": 0, "y": 0},
                "active_window": frame.active_window or "Unknown",
                "fps": frame.fps,
                "compressed": True
            }
            
            logger.info(f"Generated compressed frame: {frame.width}x{frame.height} @ {frame.fps:.1f}fps")
            return compressed_frame
            
        except Exception as e:
            logger.error(f"Error generating compressed frame data: {e}")
            return None
    
    def stop(self):
        """Stop screen capture"""
        if self.started:
            self.screen_capture.stop_capture()
            self.started = False
            logger.info("Screen capture stopped")

async def main():
    """Main function to start SECURE LOCAL real-time screen TCP server"""
    # SECURITY: Force localhost only - no external network access
    server = RealTimeScreenTCPServer(host="127.0.0.1", port=9999)
    
    try:
        logger.info("🔒 Starting SECURE LOCAL screen sharing server...")
        logger.info("🔒 SECURITY: Localhost only, no external network access")
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("🔒 Shutting down secure server...")
    finally:
        await server.stop_server()

if __name__ == "__main__":
    asyncio.run(main())