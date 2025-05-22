#!/usr/bin/env python3
"""
System-Level UI State Monitor
- Monitors OS accessibility events instead of screen captures
- Tracks window focus changes and UI updates
- Intelligent caching of UI hierarchies
- Real-time element state tracking
"""

import asyncio
import json
import time
import subprocess
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class UIState:
    """Complete UI state representation"""
    app_name: str
    window_title: str
    elements: List[Dict]
    timestamp: float
    state_hash: str

@dataclass 
class UIChangeEvent:
    """UI change event"""
    event_type: str  # focus_change, element_added, element_removed, etc.
    app_name: str
    element_info: Dict
    timestamp: float

class SystemUIMonitor:
    """Monitor system-level UI changes without screen capture"""
    
    def __init__(self):
        self.ui_cache = {}
        self.current_state = None
        self.change_callbacks = []
        self.monitoring = False
        self.monitor_thread = None
        
        # Track application states
        self.app_states = {}
        self.last_focused_app = None
        
        # Performance optimizations
        self.cache_timeout = 5.0  # Cache UI state for 5 seconds
        self.monitor_interval = 0.5  # Check for changes every 500ms
        
    async def start_monitoring(self):
        """Start monitoring system UI changes"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("System UI monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("System UI monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._check_ui_changes()
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(1.0)
    
    def _check_ui_changes(self):
        """Check for UI changes efficiently"""
        try:
            # Get current focused application
            current_app = self._get_focused_app()
            
            # Check if app focus changed
            if current_app != self.last_focused_app:
                self._handle_app_focus_change(current_app)
                self.last_focused_app = current_app
            
            # Check for UI changes in current app
            if current_app:
                self._check_app_ui_changes(current_app)
                
        except Exception as e:
            logger.error(f"UI change detection error: {e}")
    
    def _get_focused_app(self) -> Optional[str]:
        """Get currently focused application name"""
        try:
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                return name of frontApp
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                 capture_output=True, text=True, timeout=0.5)
            
            if result.returncode == 0:
                return result.stdout.strip().strip('"')
        except:
            pass
        return None
    
    def _handle_app_focus_change(self, app_name: str):
        """Handle application focus change"""
        event = UIChangeEvent(
            event_type='app_focus_change',
            app_name=app_name,
            element_info={'new_app': app_name, 'previous_app': self.last_focused_app},
            timestamp=time.time()
        )
        self._notify_change_callbacks(event)
        
        # Load cached UI state for this app if available
        if app_name in self.app_states:
            self.current_state = self.app_states[app_name]
            logger.info(f"Loaded cached UI state for {app_name}")
    
    def _check_app_ui_changes(self, app_name: str):
        """Check for UI changes in specific app"""
        try:
            # Get quick UI snapshot
            ui_snapshot = self._get_quick_ui_snapshot(app_name)
            
            if ui_snapshot:
                snapshot_hash = self._hash_ui_snapshot(ui_snapshot)
                
                # Check if UI changed
                if app_name in self.app_states:
                    if self.app_states[app_name].state_hash != snapshot_hash:
                        self._handle_ui_state_change(app_name, ui_snapshot, snapshot_hash)
                else:
                    # First time seeing this app
                    self._handle_ui_state_change(app_name, ui_snapshot, snapshot_hash)
                    
        except Exception as e:
            logger.error(f"App UI change detection error: {e}")
    
    def _get_quick_ui_snapshot(self, app_name: str) -> Optional[Dict]:
        """Get quick UI snapshot using accessibility API"""
        try:
            script = f'''
            tell application "System Events"
                set appProcess to application process "{app_name}"
                
                set elementCount to 0
                set buttonCount to 0
                set textFieldCount to 0
                set windowTitle to ""
                
                try
                    set frontWindow to front window of appProcess
                    set windowTitle to title of frontWindow
                    
                    set allElements to every UI element of frontWindow
                    set elementCount to count of allElements
                    
                    repeat with elem in allElements
                        try
                            set elemRole to role of elem
                            if elemRole contains "button" then set buttonCount to buttonCount + 1
                            if elemRole contains "text field" then set textFieldCount to textFieldCount + 1
                        end try
                    end repeat
                end try
                
                return {{windowTitle, elementCount, buttonCount, textFieldCount}}
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                 capture_output=True, text=True, timeout=1.0)
            
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                return self._parse_ui_snapshot_output(output)
                
        except subprocess.TimeoutExpired:
            logger.warning(f"UI snapshot timeout for {app_name}")
        except Exception as e:
            logger.error(f"UI snapshot error for {app_name}: {e}")
        
        return None
    
    def _parse_ui_snapshot_output(self, output: str) -> Dict:
        """Parse AppleScript output into UI snapshot"""
        try:
            # Remove brackets and split
            cleaned = output.strip('{}').split(', ')
            if len(cleaned) >= 4:
                return {
                    'window_title': cleaned[0].strip('"'),
                    'element_count': int(cleaned[1]) if cleaned[1].isdigit() else 0,
                    'button_count': int(cleaned[2]) if cleaned[2].isdigit() else 0,
                    'text_field_count': int(cleaned[3]) if cleaned[3].isdigit() else 0
                }
        except:
            pass
        return {'window_title': '', 'element_count': 0, 'button_count': 0, 'text_field_count': 0}
    
    def _hash_ui_snapshot(self, snapshot: Dict) -> str:
        """Create hash of UI snapshot for change detection"""
        snapshot_str = json.dumps(snapshot, sort_keys=True)
        return hashlib.md5(snapshot_str.encode()).hexdigest()
    
    def _handle_ui_state_change(self, app_name: str, snapshot: Dict, snapshot_hash: str):
        """Handle UI state change"""
        ui_state = UIState(
            app_name=app_name,
            window_title=snapshot.get('window_title', ''),
            elements=[snapshot],  # Simplified - would contain full element list
            timestamp=time.time(),
            state_hash=snapshot_hash
        )
        
        self.app_states[app_name] = ui_state
        self.current_state = ui_state
        
        event = UIChangeEvent(
            event_type='ui_state_change',
            app_name=app_name,
            element_info=snapshot,
            timestamp=time.time()
        )
        self._notify_change_callbacks(event)
        
        logger.info(f"UI state changed for {app_name}: {snapshot}")
    
    def _notify_change_callbacks(self, event: UIChangeEvent):
        """Notify registered callbacks of UI changes"""
        for callback in self.change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def register_change_callback(self, callback: Callable[[UIChangeEvent], None]):
        """Register callback for UI changes"""
        self.change_callbacks.append(callback)
    
    async def get_current_ui_state(self) -> Optional[UIState]:
        """Get current UI state (from cache if available)"""
        if self.current_state:
            # Check if cache is still valid
            age = time.time() - self.current_state.timestamp
            if age < self.cache_timeout:
                return self.current_state
        
        # Refresh current state
        current_app = self._get_focused_app()
        if current_app:
            snapshot = self._get_quick_ui_snapshot(current_app)
            if snapshot:
                snapshot_hash = self._hash_ui_snapshot(snapshot)
                self.current_state = UIState(
                    app_name=current_app,
                    window_title=snapshot.get('window_title', ''),
                    elements=[snapshot],
                    timestamp=time.time(),
                    state_hash=snapshot_hash
                )
        
        return self.current_state
    
    async def get_app_ui_elements(self, app_name: str = None) -> List[Dict]:
        """Get detailed UI elements for specific app"""
        if not app_name:
            app_name = self._get_focused_app()
        
        if not app_name:
            return []
        
        # Check cache first
        if app_name in self.app_states:
            state = self.app_states[app_name]
            age = time.time() - state.timestamp
            if age < self.cache_timeout:
                return state.elements
        
        # Get fresh elements
        elements = await self._get_detailed_elements(app_name)
        
        # Update cache
        if elements:
            snapshot_hash = self._hash_ui_snapshot({'elements': len(elements)})
            self.app_states[app_name] = UIState(
                app_name=app_name,
                window_title='',
                elements=elements,
                timestamp=time.time(),
                state_hash=snapshot_hash
            )
        
        return elements
    
    async def _get_detailed_elements(self, app_name: str) -> List[Dict]:
        """Get detailed UI elements using accessibility API"""
        elements = []
        
        try:
            script = f'''
            tell application "System Events"
                set appProcess to application process "{app_name}"
                set elementList to {{}}
                
                try
                    set frontWindow to front window of appProcess
                    set allElements to every UI element of frontWindow
                    
                    repeat with elem in allElements
                        try
                            set elemRole to role of elem
                            set elemTitle to title of elem
                            set elemValue to value of elem
                            set elemPos to position of elem
                            set elemSize to size of elem
                            
                            if elemRole is not missing value then
                                set end of elementList to {{elemRole, elemTitle, elemValue, elemPos, elemSize}}
                            end if
                        end try
                    end repeat
                end try
                
                return elementList
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                 capture_output=True, text=True, timeout=2.0)
            
            if result.returncode == 0 and result.stdout.strip():
                elements = self._parse_detailed_elements(result.stdout.strip())
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Detailed elements timeout for {app_name}")
        except Exception as e:
            logger.error(f"Detailed elements error for {app_name}: {e}")
        
        return elements
    
    def _parse_detailed_elements(self, output: str) -> List[Dict]:
        """Parse detailed elements from AppleScript output"""
        elements = []
        # This would parse the AppleScript output into structured element data
        # For now, return mock data
        return [
            {'type': 'button', 'text': 'Sample Button', 'bounds': (100, 100, 80, 30)},
            {'type': 'text', 'text': 'Sample Text', 'bounds': (200, 100, 120, 20)}
        ]

# Integration with fast UI detector
class IntelligentUISystem:
    """Combines fast detection with system monitoring"""
    
    def __init__(self):
        from fast_ui_detector import FastUIDetector
        
        self.fast_detector = FastUIDetector()
        self.system_monitor = SystemUIMonitor()
        self.last_elements = []
        
        # Register for UI changes
        self.system_monitor.register_change_callback(self._on_ui_change)
    
    async def start(self):
        """Start the intelligent UI system"""
        await self.system_monitor.start_monitoring()
        logger.info("Intelligent UI system started")
    
    def stop(self):
        """Stop the intelligent UI system"""
        self.system_monitor.stop_monitoring()
    
    def _on_ui_change(self, event: UIChangeEvent):
        """Handle UI change events"""
        logger.info(f"UI changed: {event.event_type} in {event.app_name}")
        # Clear cache when UI changes
        self.last_elements = []
    
    async def get_elements(self) -> List[Dict]:
        """Get UI elements using the best available method"""
        # First try cached system state
        ui_state = await self.system_monitor.get_current_ui_state()
        
        if ui_state and ui_state.elements:
            system_elements = ui_state.elements
            if system_elements:
                logger.info(f"Using system-cached elements: {len(system_elements)}")
                return system_elements
        
        # Fall back to fast detection
        fast_elements = await self.fast_detector.get_ui_elements(fast_mode=True)
        self.last_elements = [asdict(elem) for elem in fast_elements]
        
        logger.info(f"Using fast detection: {len(fast_elements)} elements")
        return self.last_elements
    
    async def find_element(self, text: str) -> Optional[Dict]:
        """Find element by text using intelligent caching"""
        # Try system monitor first (fastest)
        current_app = self.system_monitor._get_focused_app()
        if current_app:
            app_elements = await self.system_monitor.get_app_ui_elements(current_app)
            for element in app_elements:
                if text.lower() in element.get('text', '').lower():
                    return element
        
        # Fall back to fast detector
        element = await self.fast_detector.find_element_by_text(text)
        return asdict(element) if element else None

# Example usage
async def test_intelligent_ui():
    """Test the intelligent UI system"""
    ui_system = IntelligentUISystem()
    
    print("Starting intelligent UI monitoring...")
    await ui_system.start()
    
    try:
        # Wait a bit for monitoring to start
        await asyncio.sleep(1)
        
        print("Getting UI elements...")
        elements = await ui_system.get_elements()
        print(f"Found {len(elements)} elements")
        
        for elem in elements[:5]:  # Show first 5
            print(f"  {elem}")
        
        # Test element finding
        button = await ui_system.find_element("button")
        if button:
            print(f"Found button: {button}")
        
    finally:
        ui_system.stop()

if __name__ == "__main__":
    asyncio.run(test_intelligent_ui())