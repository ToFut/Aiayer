#!/usr/bin/env python3
"""
System-Integrated Monitor - Live in the OS, don't capture it
Replaces inefficient screen capture with direct system integration
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import platform

# Platform-specific imports
if sys.platform == "darwin":
    try:
        import Quartz
        import AppKit
        from Foundation import NSObject
        from PyObjCTools import AppHelper
        MACOS_AVAILABLE = True
    except ImportError:
        MACOS_AVAILABLE = False
        print("Warning: macOS APIs not available")
elif sys.platform == "win32":
    try:
        import win32gui
        import win32con
        import win32api
        import win32process
        import psutil
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        print("Warning: Windows APIs not available")
else:
    try:
        import Xlib
        import Xlib.display
        import Xlib.X
        LINUX_AVAILABLE = True
    except ImportError:
        LINUX_AVAILABLE = False
        print("Warning: Linux X11 APIs not available")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventType(Enum):
    WINDOW_CREATED = "window_created"
    WINDOW_DESTROYED = "window_destroyed"
    WINDOW_FOCUSED = "window_focused"
    WINDOW_MOVED = "window_moved"
    WINDOW_RESIZED = "window_resized"
    UI_ELEMENT_APPEARED = "ui_element_appeared"
    UI_ELEMENT_DISAPPEARED = "ui_element_disappeared"
    UI_ELEMENT_CHANGED = "ui_element_changed"
    TEXT_CHANGED = "text_changed"
    MENU_OPENED = "menu_opened"
    MENU_CLOSED = "menu_closed"
    APPLICATION_LAUNCHED = "application_launched"
    APPLICATION_TERMINATED = "application_terminated"
    USER_INPUT = "user_input"

@dataclass
class SystemEvent:
    """Real-time system event - no screenshots needed"""
    event_type: EventType
    timestamp: float
    source_app: str
    window_title: str
    element_info: Dict[str, Any]
    coordinates: Optional[Dict[str, int]] = None
    text_content: Optional[str] = None
    accessibility_info: Optional[Dict[str, Any]] = None
    
class MacOSSystemMonitor:
    """macOS-specific system integration using native APIs"""
    
    def __init__(self, event_callback: Callable):
        self.event_callback = event_callback
        self.accessibility_enabled = False
        self.running = False
        
    async def start_monitoring(self):
        """Start monitoring macOS system events"""
        if not MACOS_AVAILABLE:
            raise RuntimeError("macOS APIs not available")
        
        logger.info("🍎 Starting macOS system integration...")
        
        # Check accessibility permissions
        if not self._check_accessibility_permissions():
            logger.error("❌ Accessibility permissions required for macOS integration")
            return False
        
        self.running = True
        
        # Start event monitoring tasks
        await asyncio.gather(
            self._monitor_window_events(),
            self._monitor_accessibility_events(),
            self._monitor_application_events(),
            self._monitor_ui_element_changes()
        )
        
        return True
    
    def _check_accessibility_permissions(self) -> bool:
        """Check if accessibility permissions are granted"""
        try:
            # Try to access accessibility API
            app = AppKit.NSWorkspace.sharedWorkspace().activeApplication()
            return app is not None
        except Exception as e:
            logger.error(f"Accessibility check failed: {e}")
            return False
    
    async def _monitor_window_events(self):
        """Monitor window creation, destruction, focus changes"""
        try:
            while self.running:
                # Get current window list
                window_list = Quartz.CGWindowListCopyWindowInfo(
                    Quartz.kCGWindowListOptionOnScreenOnly,
                    Quartz.kCGNullWindowID
                )
                
                for window in window_list:
                    if window.get('kCGWindowLayer', 0) == 0:  # Normal windows only
                        event = SystemEvent(
                            event_type=EventType.WINDOW_FOCUSED,
                            timestamp=time.time(),
                            source_app=window.get('kCGWindowOwnerName', 'Unknown'),
                            window_title=window.get('kCGWindowName', ''),
                            element_info={
                                'window_id': window.get('kCGWindowNumber'),
                                'bounds': window.get('kCGWindowBounds', {}),
                                'layer': window.get('kCGWindowLayer', 0),
                                'alpha': window.get('kCGWindowAlpha', 1.0)
                            },
                            coordinates={
                                'x': window.get('kCGWindowBounds', {}).get('X', 0),
                                'y': window.get('kCGWindowBounds', {}).get('Y', 0),
                                'width': window.get('kCGWindowBounds', {}).get('Width', 0),
                                'height': window.get('kCGWindowBounds', {}).get('Height', 0)
                            }
                        )
                        
                        await self.event_callback(event)
                
                await asyncio.sleep(0.1)  # 10Hz monitoring
                
        except Exception as e:
            logger.error(f"Window monitoring error: {e}")
    
    async def _monitor_accessibility_events(self):
        """Monitor accessibility events for UI changes"""
        try:
            while self.running:
                # Monitor active application's accessibility tree
                active_app = AppKit.NSWorkspace.sharedWorkspace().activeApplication()
                if active_app:
                    # Get UI elements through accessibility API
                    # This gives us structured data, not screenshots
                    app_name = active_app.get('NSApplicationName', 'Unknown')
                    
                    event = SystemEvent(
                        event_type=EventType.UI_ELEMENT_APPEARED,
                        timestamp=time.time(),
                        source_app=app_name,
                        window_title="",
                        element_info={'active_app': app_name},
                        accessibility_info={
                            'app_bundle_id': active_app.get('NSApplicationBundleIdentifier'),
                            'app_pid': active_app.get('NSApplicationProcessIdentifier')
                        }
                    )
                    
                    await self.event_callback(event)
                
                await asyncio.sleep(0.2)  # 5Hz accessibility monitoring
                
        except Exception as e:
            logger.error(f"Accessibility monitoring error: {e}")
    
    async def _monitor_application_events(self):
        """Monitor application launch/termination"""
        try:
            known_apps = set()
            
            while self.running:
                current_apps = set()
                
                # Get running applications
                running_apps = AppKit.NSWorkspace.sharedWorkspace().runningApplications()
                for app in running_apps:
                    app_name = app.localizedName()
                    app_bundle = app.bundleIdentifier()
                    current_apps.add(app_bundle or app_name)
                
                # Detect new applications
                new_apps = current_apps - known_apps
                for app in new_apps:
                    event = SystemEvent(
                        event_type=EventType.APPLICATION_LAUNCHED,
                        timestamp=time.time(),
                        source_app=app,
                        window_title="",
                        element_info={'bundle_id': app}
                    )
                    await self.event_callback(event)
                
                # Detect terminated applications
                terminated_apps = known_apps - current_apps
                for app in terminated_apps:
                    event = SystemEvent(
                        event_type=EventType.APPLICATION_TERMINATED,
                        timestamp=time.time(),
                        source_app=app,
                        window_title="",
                        element_info={'bundle_id': app}
                    )
                    await self.event_callback(event)
                
                known_apps = current_apps
                await asyncio.sleep(1.0)  # 1Hz app monitoring
                
        except Exception as e:
            logger.error(f"Application monitoring error: {e}")
    
    async def _monitor_ui_element_changes(self):
        """Monitor UI element changes without screenshots"""
        try:
            while self.running:
                # Monitor for UI changes using accessibility notifications
                # This is much more efficient than screen capture
                
                # Placeholder for accessibility event notifications
                # In real implementation, we'd use NSAccessibility notifications
                
                await asyncio.sleep(0.05)  # 20Hz UI monitoring
                
        except Exception as e:
            logger.error(f"UI element monitoring error: {e}")

class WindowsSystemMonitor:
    """Windows-specific system integration using Win32 APIs"""
    
    def __init__(self, event_callback: Callable):
        self.event_callback = event_callback
        self.running = False
        
    async def start_monitoring(self):
        """Start monitoring Windows system events"""
        if not WINDOWS_AVAILABLE:
            raise RuntimeError("Windows APIs not available")
        
        logger.info("🪟 Starting Windows system integration...")
        self.running = True
        
        await asyncio.gather(
            self._monitor_window_events(),
            self._monitor_process_events(),
            self._monitor_ui_automation_events()
        )
        
        return True
    
    async def _monitor_window_events(self):
        """Monitor Windows window events"""
        try:
            def enum_window_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if window_title:
                        rect = win32gui.GetWindowRect(hwnd)
                        
                        event = SystemEvent(
                            event_type=EventType.WINDOW_FOCUSED,
                            timestamp=time.time(),
                            source_app=self._get_window_process_name(hwnd),
                            window_title=window_title,
                            element_info={'hwnd': hwnd},
                            coordinates={
                                'x': rect[0], 'y': rect[1],
                                'width': rect[2] - rect[0],
                                'height': rect[3] - rect[1]
                            }
                        )
                        
                        asyncio.create_task(self.event_callback(event))
                
                return True
            
            while self.running:
                windows = []
                win32gui.EnumWindows(enum_window_callback, windows)
                await asyncio.sleep(0.1)  # 10Hz monitoring
                
        except Exception as e:
            logger.error(f"Windows window monitoring error: {e}")
    
    def _get_window_process_name(self, hwnd):
        """Get process name for window handle"""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name()
        except Exception:
            return "Unknown"
    
    async def _monitor_process_events(self):
        """Monitor process creation/termination"""
        try:
            known_processes = set()
            
            while self.running:
                current_processes = set()
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        current_processes.add(proc.info['name'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Detect new processes
                new_processes = current_processes - known_processes
                for proc_name in new_processes:
                    event = SystemEvent(
                        event_type=EventType.APPLICATION_LAUNCHED,
                        timestamp=time.time(),
                        source_app=proc_name,
                        window_title="",
                        element_info={'process_name': proc_name}
                    )
                    await self.event_callback(event)
                
                known_processes = current_processes
                await asyncio.sleep(1.0)  # 1Hz process monitoring
                
        except Exception as e:
            logger.error(f"Process monitoring error: {e}")
    
    async def _monitor_ui_automation_events(self):
        """Monitor UI Automation events (Windows equivalent of accessibility)"""
        try:
            # Placeholder for Windows UI Automation
            # Would use COM interfaces to UIAutomation
            while self.running:
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"UI Automation monitoring error: {e}")

class LinuxSystemMonitor:
    """Linux-specific system integration using X11/Wayland"""
    
    def __init__(self, event_callback: Callable):
        self.event_callback = event_callback
        self.running = False
        self.display = None
        
    async def start_monitoring(self):
        """Start monitoring Linux system events"""
        if not LINUX_AVAILABLE:
            raise RuntimeError("Linux X11 APIs not available")
        
        logger.info("🐧 Starting Linux system integration...")
        
        try:
            self.display = Xlib.display.Display()
            self.running = True
            
            await asyncio.gather(
                self._monitor_x11_events(),
                self._monitor_process_events()
            )
            
            return True
        except Exception as e:
            logger.error(f"Linux monitoring startup failed: {e}")
            return False
    
    async def _monitor_x11_events(self):
        """Monitor X11 window events"""
        try:
            root = self.display.screen().root
            root.change_attributes(event_mask=Xlib.X.SubstructureNotifyMask)
            
            while self.running:
                if self.display.pending_events():
                    event = self.display.next_event()
                    
                    if event.type == Xlib.X.CreateNotify:
                        sys_event = SystemEvent(
                            event_type=EventType.WINDOW_CREATED,
                            timestamp=time.time(),
                            source_app="Unknown",
                            window_title="",
                            element_info={'window_id': event.window.id}
                        )
                        await self.event_callback(sys_event)
                
                await asyncio.sleep(0.01)  # 100Hz event processing
                
        except Exception as e:
            logger.error(f"X11 monitoring error: {e}")
    
    async def _monitor_process_events(self):
        """Monitor Linux process events"""
        try:
            known_processes = set()
            
            while self.running:
                current_processes = set()
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        current_processes.add(proc.info['name'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Detect new processes
                new_processes = current_processes - known_processes
                for proc_name in new_processes:
                    event = SystemEvent(
                        event_type=EventType.APPLICATION_LAUNCHED,
                        timestamp=time.time(),
                        source_app=proc_name,
                        window_title="",
                        element_info={'process_name': proc_name}
                    )
                    await self.event_callback(event)
                
                known_processes = current_processes
                await asyncio.sleep(1.0)  # 1Hz process monitoring
                
        except Exception as e:
            logger.error(f"Linux process monitoring error: {e}")

class SystemIntegratedMonitor:
    """Cross-platform system integration - replaces screen capture"""
    
    def __init__(self):
        self.platform_monitor = None
        self.event_handlers: List[Callable] = []
        self.event_history: List[SystemEvent] = []
        self.running = False
        
        # Initialize platform-specific monitor
        if sys.platform == "darwin":
            self.platform_monitor = MacOSSystemMonitor(self._handle_system_event)
        elif sys.platform == "win32":
            self.platform_monitor = WindowsSystemMonitor(self._handle_system_event)
        else:
            self.platform_monitor = LinuxSystemMonitor(self._handle_system_event)
    
    def add_event_handler(self, handler: Callable):
        """Add event handler for system events"""
        self.event_handlers.append(handler)
    
    async def start_monitoring(self):
        """Start system-integrated monitoring"""
        logger.info("🚀 Starting system-integrated monitoring (no screen capture)")
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        
        if not self.platform_monitor:
            raise RuntimeError("No platform monitor available")
        
        self.running = True
        
        # Start platform-specific monitoring
        success = await self.platform_monitor.start_monitoring()
        
        if success:
            logger.info("✅ System integration active - living in the OS")
            logger.info("📡 Monitoring: Windows, Apps, UI Elements, Events")
            logger.info("🚫 No screen capture needed - direct system access")
        else:
            logger.error("❌ System integration failed")
        
        return success
    
    async def _handle_system_event(self, event: SystemEvent):
        """Handle incoming system events"""
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > 1000:  # Keep last 1000 events
            self.event_history.pop(0)
        
        # Forward to all handlers
        for handler in self.event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def get_current_system_state(self) -> Dict[str, Any]:
        """Get current system state without screen capture"""
        recent_events = self.event_history[-10:] if self.event_history else []
        
        return {
            'platform': platform.system(),
            'monitoring_active': self.running,
            'recent_events': [asdict(event) for event in recent_events],
            'event_count': len(self.event_history),
            'active_handlers': len(self.event_handlers),
            'timestamp': time.time()
        }
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.running = False
        logger.info("🛑 System monitoring stopped")

# Example usage and testing
async def main():
    """Test system integration monitoring"""
    monitor = SystemIntegratedMonitor()
    
    # Add event handler
    async def log_events(event: SystemEvent):
        logger.info(f"📡 {event.event_type.value}: {event.source_app} - {event.window_title}")
    
    monitor.add_event_handler(log_events)
    
    try:
        # Start monitoring
        success = await monitor.start_monitoring()
        
        if success:
            logger.info("🔄 Monitoring system events for 30 seconds...")
            await asyncio.sleep(30)
            
            # Show system state
            state = monitor.get_current_system_state()
            logger.info(f"📊 Captured {state['event_count']} events")
        else:
            logger.error("❌ Failed to start system monitoring")
            
    except KeyboardInterrupt:
        logger.info("👋 Stopping system monitoring...")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())