#!/usr/bin/env python3
"""
Integrate Real-Time Vision with Enhanced Backend
Connects the TeamViewer-style real-time vision to the existing backend system
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional

# Import existing backend
from enhanced_enterprise_backend_with_context import EnhancedEnterpriseBackend

# Import real-time vision components
from realtime_agent_vision import RealTimeAgentVision
from realtime_screen_tcp_server import RealTimeScreenTCPServer

logger = logging.getLogger(__name__)

class RealTimeVisionBackend(EnhancedEnterpriseBackend):
    """Enhanced backend with real-time TeamViewer-style vision"""
    
    def __init__(self, port=8767):
        super().__init__(port)
        
        # Real-time vision components
        self.screen_server = None
        self.agent_vision = None
        self.vision_enabled = False
        self.realtime_mode = False
        
        # Performance tracking
        self.vision_requests = 0
        self.realtime_actions = 0
        
        logger.info("Real-Time Vision Backend initialized")
    
    async def start_realtime_vision(self):
        """Start real-time vision system"""
        try:
            logger.info("🚀 Starting real-time vision system...")
            
            # Start screen server
            self.screen_server = RealTimeScreenTCPServer(host="localhost", port=9999)
            server_task = asyncio.create_task(self.screen_server.start_server())
            
            # Give server time to start
            await asyncio.sleep(2)
            
            # Start agent vision
            self.agent_vision = RealTimeAgentVision(server_host="localhost", server_port=9999)
            
            # Connect to screen server
            connected = await self.agent_vision.connect_to_screen_server()
            if not connected:
                raise Exception("Failed to connect agent to screen server")
            
            # Start vision processing
            vision_task = asyncio.create_task(self.agent_vision.start_real_time_vision())
            
            self.vision_enabled = True
            self.realtime_mode = True
            
            logger.info("✅ Real-time vision system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start real-time vision: {e}")
            return False
    
    async def stop_realtime_vision(self):
        """Stop real-time vision system"""
        try:
            self.vision_enabled = False
            self.realtime_mode = False
            
            if self.agent_vision:
                await self.agent_vision.stop_vision()
            
            if self.screen_server:
                await self.screen_server.stop_server()
            
            logger.info("✅ Real-time vision system stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping real-time vision: {e}")
    
    async def handle_agent_request_with_realtime_vision(self, message: str, session_id: str, websocket=None) -> Dict[str, Any]:
        """Handle agent request with real-time vision context"""
        try:
            self.vision_requests += 1
            
            # Get real-time vision context
            vision_context = await self._get_realtime_vision_context()
            
            # Enhanced prompt with real-time screen awareness
            enhanced_prompt = f"""You are an AI agent with REAL-TIME SCREEN VISION like TeamViewer.

LIVE SCREEN STATE:
- Active Window: {vision_context.get('active_window', 'Unknown')}
- Screen Size: {vision_context.get('screen_size', 'Unknown')}
- UI Elements Detected: {vision_context.get('ui_elements_count', 0)}
- Clickable Elements: {vision_context.get('clickable_elements', 0)}
- Cursor Position: {vision_context.get('cursor_position', (0, 0))}
- Real-time FPS: {vision_context.get('fps', 0):.1f}

LIVE UI ELEMENTS:
{self._format_ui_elements_for_prompt(vision_context.get('ui_elements', []))}

You can see the screen in REAL-TIME and act on it immediately.
User Request: {message}

Create a precise action plan based on the LIVE screen state."""

            # Use existing fast automation but with real-time context
            if hasattr(self, 'fast_universal_automation_handler') and self.fast_universal_automation_handler:
                # Override the request with real-time context
                result = await self.fast_universal_automation_handler.create_universal_automation_plan(
                    enhanced_prompt, session_id
                )
                
                # Add real-time vision data to response
                if result.get('success'):
                    result['realtime_vision'] = True
                    result['vision_context'] = vision_context
                    result['live_screen_analysis'] = await self._analyze_live_screen()
                
                return result
            else:
                # Fallback to direct real-time action
                return await self._execute_realtime_action(message, vision_context, session_id)
                
        except Exception as e:
            logger.error(f"Real-time vision agent request error: {e}")
            return {
                "success": False,
                "response": f"❌ Real-time vision error: {str(e)}",
                "realtime_vision": False
            }
    
    async def _get_realtime_vision_context(self) -> Dict[str, Any]:
        """Get current real-time vision context"""
        if not self.agent_vision or not self.vision_enabled:
            return {
                'available': False,
                'error': 'Real-time vision not enabled'
            }
        
        try:
            # Get live vision summary
            vision_summary = self.agent_vision.get_vision_summary()
            
            # Get current UI elements from live stream
            current_elements = self.agent_vision.vision_state.ui_elements
            
            # Filter clickable elements
            clickable_elements = [e for e in current_elements if e.get('clickable', False)]
            
            return {
                'available': True,
                'connected': vision_summary.get('connected', False),
                'fps': vision_summary.get('fps', 0),
                'screen_size': vision_summary.get('screen_size', (0, 0)),
                'active_window': vision_summary.get('active_window', ''),
                'cursor_position': vision_summary.get('cursor_position', (0, 0)),
                'ui_elements_count': len(current_elements),
                'clickable_elements': len(clickable_elements),
                'ui_elements': current_elements[:10],  # Top 10 elements
                'uptime': vision_summary.get('uptime', 0),
                'frames_received': vision_summary.get('frames_received', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting vision context: {e}")
            return {
                'available': False,
                'error': str(e)
            }
    
    def _format_ui_elements_for_prompt(self, elements: list) -> str:
        """Format UI elements for LLM prompt"""
        if not elements:
            return "No UI elements detected"
        
        formatted = []
        for i, element in enumerate(elements[:5]):  # Top 5 elements
            bounds = element.get('bounds', (0, 0, 0, 0))
            x, y, w, h = bounds
            center_x, center_y = x + w//2, y + h//2
            
            formatted.append(
                f"  {i+1}. {element.get('type', 'unknown')} "
                f"'{element.get('text', 'no_text')}' "
                f"at ({center_x}, {center_y}) "
                f"{'[CLICKABLE]' if element.get('clickable') else '[READ-only]'}"
            )
        
        return "\n".join(formatted)
    
    async def _analyze_live_screen(self) -> Dict[str, Any]:
        """Analyze live screen for additional context"""
        if not self.agent_vision or not self.vision_enabled:
            return {}
        
        try:
            vision_state = self.agent_vision.vision_state
            
            # Analyze UI element distribution
            element_types = {}
            for element in vision_state.ui_elements:
                elem_type = element.get('type', 'unknown')
                element_types[elem_type] = element_types.get(elem_type, 0) + 1
            
            # Screen activity analysis
            activity_level = "low"
            if len(vision_state.ui_elements) > 10:
                activity_level = "high"
            elif len(vision_state.ui_elements) > 5:
                activity_level = "medium"
            
            return {
                'element_distribution': element_types,
                'activity_level': activity_level,
                'screen_complexity': len(vision_state.ui_elements),
                'last_update': vision_state.frame_timestamp,
                'analysis_timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Live screen analysis error: {e}")
            return {}
    
    async def _execute_realtime_action(self, command: str, vision_context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute action using real-time vision"""
        try:
            if not self.agent_vision:
                raise Exception("Real-time vision not available")
            
            # Execute command with real-time vision
            result = await self.agent_vision.execute_user_command(command)
            
            self.realtime_actions += 1
            
            # Format response
            if result.get('success'):
                action_plan = result.get('action_plan', {})
                
                response_text = f"🎯 **REAL-TIME ACTION EXECUTED**\n\n"
                response_text += f"**🚀 Action:** {action_plan.get('action_type', 'unknown')}\n"
                response_text += f"**📋 Command:** {command}\n"
                response_text += f"**🎯 Target:** {action_plan.get('reasoning', 'N/A')}\n"
                response_text += f"**📊 Confidence:** {action_plan.get('confidence', 0):.1%}\n"
                response_text += f"**⏱️ Executed:** {time.strftime('%H:%M:%S')}\n\n"
                response_text += f"**👁️ Live Vision:** {vision_context.get('fps', 0):.1f} FPS, "
                response_text += f"{vision_context.get('ui_elements_count', 0)} UI elements detected\n"
                response_text += f"**🪟 Active Window:** {vision_context.get('active_window', 'Unknown')}"
                
                return {
                    "success": True,
                    "response": response_text,
                    "realtime_vision": True,
                    "action_executed": True,
                    "vision_context": vision_context,
                    "action_plan": action_plan
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                
                response_text = f"❌ **REAL-TIME ACTION FAILED**\n\n"
                response_text += f"**📋 Command:** {command}\n"
                response_text += f"**❌ Error:** {error_msg}\n"
                response_text += f"**👁️ Vision Status:** {vision_context.get('fps', 0):.1f} FPS\n"
                response_text += f"**🔍 Available Elements:** {vision_context.get('ui_elements_count', 0)}"
                
                return {
                    "success": False,
                    "response": response_text,
                    "realtime_vision": True,
                    "action_executed": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"Real-time action execution error: {e}")
            return {
                "success": False,
                "response": f"❌ Real-time action failed: {str(e)}",
                "realtime_vision": False,
                "error": str(e)
            }
    
    async def handle_websocket_message(self, websocket, message_data: Dict[str, Any]):
        """Override websocket handler to support real-time vision"""
        try:
            mode = message_data.get("mode", "").lower()
            
            # Check if this is an agent request and real-time vision is enabled
            if mode == "agent" and self.realtime_mode and self.vision_enabled:
                logger.info(f"🎯 Handling REAL-TIME AGENT request: {message_data.get('message', '')}")
                
                # Use real-time vision for agent requests
                result = await self.handle_agent_request_with_realtime_vision(
                    message_data.get("message", ""),
                    message_data.get("session_id", "default"),
                    websocket
                )
                
                # Send response
                await websocket.send(json.dumps({
                    "type": "response",
                    "success": result.get("success", False),
                    "response": result.get("response", ""),
                    "realtime_vision": True,
                    "vision_context": result.get("vision_context", {}),
                    "buttons": result.get("buttons", []),
                    "interactive": result.get("interactive", False)
                }))
                
                return
            
            # For other modes, use parent handler
            await super().handle_websocket_message(websocket, message_data)
            
        except Exception as e:
            logger.error(f"Real-time websocket handler error: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "error": str(e),
                "realtime_vision": False
            }))
    
    def get_realtime_status(self) -> Dict[str, Any]:
        """Get real-time vision system status"""
        if not self.vision_enabled:
            return {
                "enabled": False,
                "status": "disabled"
            }
        
        try:
            vision_summary = self.agent_vision.get_vision_summary() if self.agent_vision else {}
            
            return {
                "enabled": True,
                "status": "active" if vision_summary.get('connected', False) else "disconnected",
                "fps": vision_summary.get('fps', 0),
                "uptime": vision_summary.get('uptime', 0),
                "frames_received": vision_summary.get('frames_received', 0),
                "vision_requests": self.vision_requests,
                "realtime_actions": self.realtime_actions,
                "screen_size": vision_summary.get('screen_size', (0, 0)),
                "active_window": vision_summary.get('active_window', ''),
                "ui_elements_count": vision_summary.get('ui_elements_count', 0)
            }
            
        except Exception as e:
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }

async def main():
    """Main function to start real-time vision backend"""
    backend = RealTimeVisionBackend(port=8767)
    
    try:
        # Start real-time vision
        logger.info("🚀 Starting Real-Time Vision Backend...")
        vision_started = await backend.start_realtime_vision()
        
        if vision_started:
            logger.info("✅ Real-time vision system ready!")
            logger.info("🎯 Agent mode now has live screen vision like TeamViewer")
            
            # Start the backend server
            await backend.start_server()
        else:
            logger.error("❌ Failed to start real-time vision")
            
    except KeyboardInterrupt:
        logger.info("Shutting down real-time vision backend...")
    finally:
        await backend.stop_realtime_vision()

if __name__ == "__main__":
    asyncio.run(main())