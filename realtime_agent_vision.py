#!/usr/bin/env python3
"""
Real-Time Agent Vision Client
Connects to screen TCP server and provides real-time vision like TeamViewer remote control
"""

import asyncio
import socket
import struct
import json
import base64
import time
import logging
import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime

# Import existing automation components
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_workflow.input_controller import InputController
    INPUT_CONTROL_AVAILABLE = True
except ImportError:
    INPUT_CONTROL_AVAILABLE = False
    print("Warning: Input controller not available")

try:
    from llm.llm_service import LLMService
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: LLM service not available")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentVisionState:
    """Current state of agent's vision"""
    current_frame: Optional[Dict[str, Any]]
    frame_timestamp: float
    ui_elements: List[Dict[str, Any]]
    cursor_position: Tuple[int, int]
    active_window: str
    screen_dimensions: Tuple[int, int]
    fps: float
    connection_active: bool

@dataclass
class ActionPlan:
    """Agent action plan based on live vision"""
    action_id: str
    action_type: str  # click, type, scroll, hotkey
    target_element: Optional[Dict[str, Any]]
    target_coordinates: Tuple[int, int]
    action_value: Optional[str]  # text to type, etc.
    confidence: float
    reasoning: str
    timestamp: float

class RealTimeAgentVision:
    """SECURE LOCAL Agent with real-time screen vision - localhost only"""
    
    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 9999):
        # SECURITY: Force localhost only
        if server_host not in ["127.0.0.1", "localhost"]:
            raise ValueError("SECURITY: Only localhost connections allowed")
        
        self.server_host = "127.0.0.1"  # Force localhost
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.running = False
        
        logger.info(f"🔒 SECURE AGENT: Connecting to {self.server_host}:{self.server_port} only")
        logger.info("🔒 SECURITY: Local-only agent, no external network access")
        
        # Vision state
        self.vision_state = AgentVisionState(
            current_frame=None,
            frame_timestamp=0,
            ui_elements=[],
            cursor_position=(0, 0),
            active_window="",
            screen_dimensions=(1920, 1080),
            fps=0,
            connection_active=False
        )
        
        # Performance metrics
        self.frames_received = 0
        self.actions_executed = 0
        self.start_time = time.time()
        
        # Initialize components
        self.input_controller = None
        self.llm_service = None
        self._init_components()
        
        # Action execution callbacks
        self.action_callbacks: Dict[str, Callable] = {}
        self._setup_action_callbacks()
        
        # Real-time decision making
        self.decision_threshold = 0.7  # Confidence threshold for actions
        self.max_actions_per_second = 5  # Rate limiting
        self.last_action_time = 0
        
    def _init_components(self):
        """Initialize automation components"""
        if INPUT_CONTROL_AVAILABLE:
            self.input_controller = InputController(safety_level="medium")
            logger.info("Input controller initialized")
        
        if LLM_AVAILABLE:
            self.llm_service = LLMService(model_name="llama3.2:1b")  # Fast model for real-time
            logger.info("LLM service initialized for real-time decisions")
    
    def _setup_action_callbacks(self):
        """Setup callbacks for different action types"""
        self.action_callbacks = {
            "click": self._execute_click,
            "type": self._execute_type,
            "scroll": self._execute_scroll,
            "hotkey": self._execute_hotkey,
            "wait": self._execute_wait
        }
    
    async def connect_to_screen_server(self) -> bool:
        """Connect to real-time screen TCP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setblocking(False)
            
            await asyncio.get_event_loop().sock_connect(
                self.socket, (self.server_host, self.server_port)
            )
            
            self.connected = True
            self.vision_state.connection_active = True
            logger.info(f"🔒 SECURE CONNECTION: Connected to local screen server at {self.server_host}:{self.server_port}")
            logger.info("🔒 SECURITY: Localhost-only connection established")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def start_real_time_vision(self):
        """Start real-time vision processing"""
        if not self.connected:
            logger.info("Not connected - attempting to connect...")
            if not await self.connect_to_screen_server():
                logger.error("Cannot start vision - connection failed")
                return
        else:
            logger.info("Already connected - starting vision processing...")
        
        self.running = True
        self.start_time = time.time()
        
        logger.info("Starting real-time agent vision...")
        
        # Start frame receiving loop
        receive_task = asyncio.create_task(self._receive_frames())
        # Start vision processing loop
        vision_task = asyncio.create_task(self._process_vision())
        
        try:
            await asyncio.gather(receive_task, vision_task)
        except Exception as e:
            logger.error(f"Vision processing error: {e}")
        finally:
            await self.stop_vision()
    
    async def stop_vision(self):
        """Stop real-time vision"""
        self.running = False
        self.connected = False
        self.vision_state.connection_active = False
        
        if self.socket:
            self.socket.close()
        
        logger.info("Real-time vision stopped")
    
    async def _receive_frames(self):
        """Receive frames from TCP server"""
        while self.running and self.connected:
            try:
                # Receive frame size (4 bytes)
                size_data = await self._recv_exact(4)
                if not size_data:
                    break
                
                frame_size = struct.unpack('!I', size_data)[0]
                
                # Receive frame data
                frame_data = await self._recv_exact(frame_size)
                if not frame_data:
                    break
                
                # Parse frame
                frame_json = frame_data.decode('utf-8')
                frame = json.loads(frame_json)
                
                # Decode image data
                if frame.get('data'):
                    frame['data'] = base64.b64decode(frame['data'])
                
                # Update vision state
                self._update_vision_state(frame)
                
                self.frames_received += 1
                
                # Log first few frames for debugging
                if self.frames_received <= 5:
                    logger.info(f"📥 Received frame {self.frames_received}: {frame.get('width', 0)}x{frame.get('height', 0)}")
                
                # Log performance every 100 frames
                if self.frames_received % 100 == 0:
                    elapsed = time.time() - self.start_time
                    fps = self.frames_received / elapsed
                    logger.info(f"Receiving: {fps:.1f} FPS, {self.frames_received} frames total")
                
            except Exception as e:
                if self.running:
                    logger.error(f"Frame receive error: {e}")
                break
            
            # Small delay to prevent CPU overload
            await asyncio.sleep(0.001)
    
    async def _recv_exact(self, size: int) -> bytes:
        """Receive exact number of bytes"""
        data = b''
        while len(data) < size and self.running:
            chunk = await asyncio.get_event_loop().sock_recv(self.socket, size - len(data))
            if not chunk:
                break
            data += chunk
        return data
    
    def _update_vision_state(self, frame: Dict[str, Any]):
        """Update agent's vision state with new frame"""
        self.vision_state.current_frame = frame
        self.vision_state.frame_timestamp = frame.get('timestamp', time.time())
        self.vision_state.ui_elements = frame.get('ui_elements', [])
        self.vision_state.cursor_position = tuple(frame.get('cursor_position', (0, 0)))
        self.vision_state.active_window = frame.get('active_window', '')
        self.vision_state.screen_dimensions = (frame.get('width', 1920), frame.get('height', 1080))
        self.vision_state.fps = frame.get('fps', 0)
    
    async def _process_vision(self):
        """Process vision data and make real-time decisions"""
        while self.running:
            try:
                if self.vision_state.current_frame:
                    # Analyze current screen state
                    analysis = await self._analyze_screen_state()
                    
                    # Make decisions based on analysis
                    if analysis.get('requires_action', False):
                        action_plan = await self._create_action_plan(analysis)
                        
                        if action_plan and action_plan.confidence >= self.decision_threshold:
                            # Rate limiting
                            current_time = time.time()
                            if current_time - self.last_action_time >= (1.0 / self.max_actions_per_second):
                                await self._execute_action(action_plan)
                                self.last_action_time = current_time
                
            except Exception as e:
                logger.error(f"Vision processing error: {e}")
            
            # Process at 10Hz for real-time decisions
            await asyncio.sleep(0.1)
    
    async def _analyze_screen_state(self) -> Dict[str, Any]:
        """Analyze current screen state for decision making"""
        if not self.vision_state.current_frame:
            return {}
        
        analysis = {
            'timestamp': time.time(),
            'active_window': self.vision_state.active_window,
            'ui_elements_count': len(self.vision_state.ui_elements),
            'cursor_position': self.vision_state.cursor_position,
            'requires_action': False,
            'suggested_actions': [],
            'screen_changes': self._detect_screen_changes(),
            'clickable_elements': []
        }
        
        # Find clickable elements
        for element in self.vision_state.ui_elements:
            if element.get('clickable', False) and element.get('visible', True):
                analysis['clickable_elements'].append(element)
        
        # Simple heuristics for when action might be needed
        # (In real system, this would be driven by user commands)
        if len(analysis['clickable_elements']) > 0:
            analysis['requires_action'] = False  # Don't auto-click
            analysis['suggested_actions'] = ['analyze_elements']
        
        return analysis
    
    def _detect_screen_changes(self) -> Dict[str, Any]:
        """Detect changes in screen (simplified version)"""
        # This is a placeholder - in real implementation, you'd compare
        # with previous frames to detect UI changes
        return {
            'has_changes': True,
            'change_regions': [],
            'change_confidence': 0.5
        }
    
    async def _create_action_plan(self, analysis: Dict[str, Any]) -> Optional[ActionPlan]:
        """Create action plan based on screen analysis"""
        try:
            # For now, create a simple observation action
            # In real system, this would be driven by user commands
            
            action_plan = ActionPlan(
                action_id=f"observe_{int(time.time() * 1000)}",
                action_type="wait",
                target_element=None,
                target_coordinates=(0, 0),
                action_value=None,
                confidence=0.9,
                reasoning=f"Observing screen with {len(analysis.get('clickable_elements', []))} clickable elements",
                timestamp=time.time()
            )
            
            return action_plan
            
        except Exception as e:
            logger.error(f"Action planning error: {e}")
            return None
    
    async def _execute_action(self, action_plan: ActionPlan):
        """Execute action plan on real screen"""
        try:
            logger.info(f"Executing: {action_plan.action_type} - {action_plan.reasoning}")
            
            # Get action callback
            callback = self.action_callbacks.get(action_plan.action_type)
            if callback:
                success = await callback(action_plan)
                if success:
                    self.actions_executed += 1
                    logger.info(f"Action executed successfully: {action_plan.action_id}")
                else:
                    logger.warning(f"Action failed: {action_plan.action_id}")
            else:
                logger.error(f"Unknown action type: {action_plan.action_type}")
                
        except Exception as e:
            logger.error(f"Action execution error: {e}")
    
    async def _execute_click(self, action_plan: ActionPlan) -> bool:
        """Execute click action"""
        if not self.input_controller:
            logger.error("Input controller not available")
            return False
        
        try:
            x, y = action_plan.target_coordinates
            self.input_controller.click(x, y)
            await asyncio.sleep(0.1)  # Brief delay after click
            return True
        except Exception as e:
            logger.error(f"Click execution error: {e}")
            return False
    
    async def _execute_type(self, action_plan: ActionPlan) -> bool:
        """Execute typing action"""
        if not self.input_controller or not action_plan.action_value:
            return False
        
        try:
            self.input_controller.type_text(action_plan.action_value)
            await asyncio.sleep(0.05 * len(action_plan.action_value))  # Typing delay
            return True
        except Exception as e:
            logger.error(f"Type execution error: {e}")
            return False
    
    async def _execute_scroll(self, action_plan: ActionPlan) -> bool:
        """Execute scroll action"""
        if not self.input_controller:
            return False
        
        try:
            x, y = action_plan.target_coordinates
            # Scroll direction based on action_value
            scroll_direction = action_plan.action_value or "down"
            scroll_amount = 3 if scroll_direction == "down" else -3
            
            self.input_controller.scroll(x, y, 0, scroll_amount)
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Scroll execution error: {e}")
            return False
    
    async def _execute_hotkey(self, action_plan: ActionPlan) -> bool:
        """Execute hotkey action"""
        if not self.input_controller or not action_plan.action_value:
            return False
        
        try:
            keys = action_plan.action_value.split('+')
            if len(keys) == 2:
                self.input_controller.hotkey(keys[0], keys[1])
            elif len(keys) == 1:
                self.input_controller.press_key(keys[0])
            
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Hotkey execution error: {e}")
            return False
    
    async def _execute_wait(self, action_plan: ActionPlan) -> bool:
        """Execute wait action (observation)"""
        # This is just observation - always succeeds
        return True
    
    # Public API for external control
    
    async def execute_user_command(self, command: str) -> Dict[str, Any]:
        """Execute user command with real-time vision context"""
        try:
            logger.info(f"Executing user command: {command}")
            
            # Analyze command with current vision state
            context = {
                'screen_state': {
                    'active_window': self.vision_state.active_window,
                    'ui_elements': self.vision_state.ui_elements,
                    'screen_size': self.vision_state.screen_dimensions
                },
                'command': command,
                'timestamp': time.time()
            }
            
            # Create action plan for user command
            action_plan = await self._plan_user_action(command, context)
            
            if action_plan:
                # Execute the action
                success = await self._execute_action(action_plan)
                
                return {
                    'success': success,
                    'action_plan': action_plan.__dict__,
                    'vision_state': self.get_vision_summary()
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not create action plan',
                    'vision_state': self.get_vision_summary()
                }
                
        except Exception as e:
            logger.error(f"User command execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'vision_state': self.get_vision_summary()
            }
    
    async def _plan_user_action(self, command: str, context: Dict[str, Any]) -> Optional[ActionPlan]:
        """Plan action based on user command and vision context"""
        # Simple command parsing - in real system, use LLM
        command_lower = command.lower()
        
        if "click" in command_lower:
            # Find best element to click
            clickable_elements = [e for e in self.vision_state.ui_elements if e.get('clickable')]
            if clickable_elements:
                target = clickable_elements[0]  # Take first for now
                x, y, w, h = target['bounds']
                center_x, center_y = x + w//2, y + h//2
                
                return ActionPlan(
                    action_id=f"user_click_{int(time.time() * 1000)}",
                    action_type="click",
                    target_element=target,
                    target_coordinates=(center_x, center_y),
                    action_value=None,
                    confidence=0.8,
                    reasoning=f"Clicking on {target.get('text', 'element')}",
                    timestamp=time.time()
                )
        
        elif "type" in command_lower:
            # Extract text to type
            words = command.split()
            if len(words) > 1:
                text_to_type = " ".join(words[1:])
                
                return ActionPlan(
                    action_id=f"user_type_{int(time.time() * 1000)}",
                    action_type="type",
                    target_element=None,
                    target_coordinates=(0, 0),
                    action_value=text_to_type,
                    confidence=0.9,
                    reasoning=f"Typing: {text_to_type}",
                    timestamp=time.time()
                )
        
        return None
    
    def get_vision_summary(self) -> Dict[str, Any]:
        """Get summary of current vision state"""
        return {
            'connected': self.vision_state.connection_active,
            'fps': self.vision_state.fps,
            'screen_size': self.vision_state.screen_dimensions,
            'active_window': self.vision_state.active_window,
            'ui_elements_count': len(self.vision_state.ui_elements),
            'cursor_position': self.vision_state.cursor_position,
            'frames_received': self.frames_received,
            'actions_executed': self.actions_executed,
            'uptime': time.time() - self.start_time
        }

async def main():
    """Main function for testing real-time agent vision"""
    agent = RealTimeAgentVision()
    
    try:
        print("Starting real-time agent vision...")
        await agent.start_real_time_vision()
    except KeyboardInterrupt:
        print("Stopping agent vision...")
    finally:
        await agent.stop_vision()

if __name__ == "__main__":
    asyncio.run(main())