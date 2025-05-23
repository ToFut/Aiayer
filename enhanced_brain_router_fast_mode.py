#!/usr/bin/env python3
"""
Enhanced Brain Router - Fast Mode
Fast version that skips heavy LLaVA analysis to prevent timeouts.
Optimized for quick response while maintaining intelligent workflow capabilities.
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple

# Add paths for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Core imports
from memory.semantic_search_agent import SemanticSearchAgent, get_context_for_query, add_memory
from agent_workflow.input_controller import InputController
from sensors.total_screen_analyzer import TotalScreenAnalyzer
from intelligent_workflow_planner import IntelligentWorkflowPlanner, WorkflowPlan, WorkflowStep, ActionType

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_brain_router_fast.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(Enum):
    AGENT = "Agent"
    ASK = "Ask"
    SUGGEST = "Suggest"
    GENERAL = "General"

class AutomationResult:
    """Result of an automation operation"""
    def __init__(self, success: bool, action: str, details: str, coordinates: Optional[Tuple[int, int]] = None):
        self.success = success
        self.action = action
        self.details = details
        self.coordinates = coordinates
        self.timestamp = datetime.now().isoformat()

class FastAutomationEngine:
    """Fast automation engine optimized for quick response"""
    
    def __init__(self, safety_level: str = "medium"):
        self.input_controller = InputController(safety_level=safety_level)
        # Initialize screen analyzer in fast mode (no LLaVA)
        self.screen_analyzer = TotalScreenAnalyzer(fast_mode=True)
        self.workflow_planner = IntelligentWorkflowPlanner()
        self.safety_level = safety_level
        self.automation_active = True
        logger.info(f"🚀 FastAutomationEngine initialized with {safety_level} safety (FAST MODE)")
        
    async def execute_intelligent_workflow(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute intelligent workflow with fast screen analysis"""
        try:
            logger.info(f"🧠 Starting FAST intelligent workflow for: '{message}'")
            
            # Get current screen context (fast mode - no LLaVA)
            current_context = await self.screen_analyzer.analyze_full_screen()
            
            # Create workflow plan
            workflow_plan = await self.workflow_planner.create_workflow_plan(message, current_context)
            
            logger.info(f"📋 Created workflow plan with {len(workflow_plan.steps)} steps, confidence: {workflow_plan.confidence:.2f}")
            
            # Store workflow plan in memory
            await add_memory(
                f"Fast workflow plan for '{workflow_plan.goal}' with {len(workflow_plan.steps)} steps",
                source="fast_workflow_planning",
                tags={"workflow", "automation", "planning", "fast_mode"}
            )
            
            # Execute workflow steps
            results = []
            successful_steps = 0
            
            for step in workflow_plan.steps:
                logger.info(f"📝 Executing step {step.step_number}: {step.description}")
                
                step_result = await self._execute_workflow_step(step, current_context)
                results.append(step_result)
                
                if step_result.get('success', False):
                    successful_steps += 1
                    logger.info(f"✅ Step {step.step_number} completed successfully")
                    
                    # Quick context update for important steps
                    if step.action_type in [ActionType.CLICK, ActionType.TYPE]:
                        await asyncio.sleep(0.5)  # Shorter wait in fast mode
                else:
                    logger.warning(f"❌ Step {step.step_number} failed: {step_result.get('error', 'Unknown error')}")
                    
                    # Try simple fallback
                    if step.fallback_strategies:
                        logger.info(f"🔄 Trying fast fallback for step {step.step_number}")
                        fallback_success = await self._try_simple_fallback(step)
                        if fallback_success:
                            successful_steps += 1
                            logger.info(f"✅ Step {step.step_number} completed via fallback")
            
            # Calculate workflow success
            success_rate = successful_steps / len(workflow_plan.steps) if workflow_plan.steps else 0
            overall_success = success_rate >= 0.7  # Lower threshold for fast mode
            
            # Store final results in memory
            result_summary = f"Fast workflow '{workflow_plan.goal}' completed with {successful_steps}/{len(workflow_plan.steps)} successful steps"
            await add_memory(
                result_summary,
                source="fast_workflow_execution",
                tags={"workflow", "automation", "execution", "fast_mode"}
            )
            
            logger.info(f"🎯 Fast workflow completed: {successful_steps}/{len(workflow_plan.steps)} steps successful")
            
            return {
                "success": overall_success,
                "workflow_plan": {
                    "goal": workflow_plan.goal,
                    "total_steps": len(workflow_plan.steps),
                    "successful_steps": successful_steps,
                    "success_rate": success_rate,
                    "confidence": workflow_plan.confidence,
                    "estimated_duration": workflow_plan.estimated_duration,
                    "mode": "fast"
                },
                "step_results": results,
                "summary": result_summary,
                "action": "fast_intelligent_workflow"
            }
            
        except Exception as e:
            logger.error(f"Error executing fast intelligent workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "fast_intelligent_workflow"
            }
    
    async def _execute_workflow_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step quickly"""
        try:
            if step.action_type == ActionType.CLICK:
                # Fast click execution
                if step.target:
                    # Use simple center-screen click for common targets
                    if "search" in step.target.lower():
                        # Google search box is typically in center-top
                        success = self.input_controller.click(735, 284)  # Common Google search location
                        return {
                            "success": success,
                            "action": "click",
                            "target": step.target,
                            "details": f"Fast click on {step.target}",
                            "coordinates": (735, 284)
                        }
                    else:
                        # Generic center click
                        success = self.input_controller.click(735, 400)
                        return {
                            "success": success,
                            "action": "click",
                            "target": step.target,
                            "details": f"Fast center click on {step.target}",
                            "coordinates": (735, 400)
                        }
            
            elif step.action_type == ActionType.TYPE:
                # Fast typing
                if step.value:
                    success = self.input_controller.type_text(step.value)
                    return {
                        "success": success,
                        "action": "type",
                        "value": step.value,
                        "details": f"Fast typed: {step.value}"
                    }
            
            elif step.action_type == ActionType.HOTKEY:
                # Fast hotkey execution
                if step.target:
                    keys = step.target.split('+')
                    if len(keys) > 1:
                        success = self.input_controller.hotkey(*keys)
                    else:
                        success = self.input_controller.press_key(keys[0])
                    
                    return {
                        "success": success,
                        "action": "hotkey",
                        "keys": step.target,
                        "details": f"Fast hotkey: {step.target}"
                    }
            
            elif step.action_type == ActionType.WAIT:
                # Fast wait (shorter times)
                wait_time = min(float(step.value) if step.value else 1.0, 2.0)  # Max 2 seconds
                await asyncio.sleep(wait_time)
                return {
                    "success": True,
                    "action": "wait",
                    "duration": wait_time,
                    "details": f"Fast wait {wait_time}s"
                }
            
            elif step.action_type == ActionType.ANALYZE:
                # Skip heavy analysis in fast mode
                return {
                    "success": True,
                    "action": "analyze",
                    "details": "Fast mode - analysis skipped",
                    "analysis_available": False
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported action type: {step.action_type}",
                    "action": str(step.action_type)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": str(step.action_type)
            }
    
    async def _try_simple_fallback(self, step: WorkflowStep) -> bool:
        """Simple fallback strategies for fast mode"""
        try:
            if step.action_type == ActionType.CLICK:
                # Try pressing Tab then Enter
                tab_success = self.input_controller.press_key("tab")
                await asyncio.sleep(0.2)
                enter_success = self.input_controller.press_key("enter")
                return tab_success or enter_success
            
            elif step.action_type == ActionType.TYPE:
                # Try pressing Enter after typing
                enter_success = self.input_controller.press_key("enter")
                return enter_success
                
        except Exception as e:
            logger.warning(f"Simple fallback failed: {e}")
        
        return False

class FastBrainRouter:
    """Fast Brain Router optimized for quick response"""
    
    def __init__(self):
        self.semantic_agent = SemanticSearchAgent()
        self.automation_engine = FastAutomationEngine()
        self.connected_clients = set()
        self.start_time = datetime.now()
        logger.info("🚀 Fast Brain Router initialized (FAST MODE)")
    
    async def process_request_with_automation(self, mode: ChatMode, message: str, session_id: str) -> Dict[str, Any]:
        """Process request with fast automation"""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Fast processing {mode.value} mode: {message}")
            
            # Quick memory lookup (limit results for speed)
            context = await get_context_for_query(message, max_results=3)
            
            if mode == ChatMode.AGENT:
                response = await self._handle_agent_mode_fast(message, context)
            elif mode == ChatMode.ASK:
                response = await self._handle_ask_mode_fast(message, context)
            else:
                response = f"🚀 Fast mode - {mode.value}: {message}"
            
            processing_time = time.time() - start_time
            logger.info(f"🎯 Fast processing completed in {processing_time:.2f}s")
            
            return {
                "response": response,
                "mode": mode.value,
                "processing_time": processing_time,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "fast_mode": True
            }
            
        except Exception as e:
            logger.error(f"Error in fast processing: {e}")
            return {
                "response": f"⚡ Fast mode error: {str(e)}",
                "mode": mode.value,
                "session_id": session_id,
                "error": str(e),
                "fast_mode": True
            }
    
    async def _handle_agent_mode_fast(self, message: str, context: Dict[str, Any]) -> str:
        """Handle Agent mode with fast automation"""
        logger.info(f"🤖 Fast Agent mode: {message}")
        
        # Fast complex task detection
        is_complex_task = self._is_complex_task_fast(message)
        
        if is_complex_task:
            # Use fast intelligent workflow
            logger.info(f"🧠 Fast complex task detected")
            automation_result = await self.automation_engine.execute_intelligent_workflow(message, context)
            
            if automation_result.get('success'):
                workflow_plan = automation_result.get('workflow_plan', {})
                response = f"🚀 Fast workflow completed!\n"
                response += f"📋 Goal: {workflow_plan.get('goal', 'Unknown')}\n"
                response += f"✅ {workflow_plan.get('successful_steps', 0)}/{workflow_plan.get('total_steps', 0)} steps\n"
                response += f"⚡ Fast mode execution"
            else:
                response = f"❌ Fast workflow failed: {automation_result.get('error', 'Unknown error')}"
        else:
            # Simple automation
            message_lower = message.lower()
            if "click" in message_lower:
                success = self.automation_engine.input_controller.click(735, 400)
                response = f"✅ Fast click executed" if success else "❌ Click failed"
            elif "type" in message_lower:
                # Extract text to type
                if "'" in message or '"' in message:
                    import re
                    match = re.search(r'["\']([^"\']+)["\']', message)
                    if match:
                        text = match.group(1)
                        success = self.automation_engine.input_controller.type_text(text)
                        response = f"✅ Fast typed: {text}" if success else "❌ Typing failed"
                    else:
                        response = "❌ No text found to type"
                else:
                    response = "❌ No text specified to type"
            else:
                response = f"🚀 Fast Agent processing: {message}"
        
        return response
    
    async def _handle_ask_mode_fast(self, message: str, context: Dict[str, Any]) -> str:
        """Handle Ask mode with fast processing"""
        relevant_memories = context.get('relevant_memories', [])
        confidence = context.get('confidence_score', 0.0)
        
        if relevant_memories and confidence > 0.3:
            primary_memory = relevant_memories[0]
            response = f"💭 Fast answer: {primary_memory['content'][:100]}..."
        else:
            response = f"🚀 Fast mode - processing: {message}"
        
        return response
    
    def _is_complex_task_fast(self, message: str) -> bool:
        """Fast complex task detection"""
        message_lower = message.lower()
        
        # Quick pattern matching
        complex_patterns = [
            "search" in message_lower and ("google" in message_lower or "'" in message or '"' in message),
            " and " in message_lower,
            "go to" in message_lower,
            "open" in message_lower and ("and" in message_lower or "then" in message_lower),
        ]
        
        return any(complex_patterns)

    async def handle_websocket_connection(self, websocket, path):
        """Handle WebSocket connections with fast processing"""
        client_id = f"client_{len(self.connected_clients)}"
        self.connected_clients.add(client_id)
        logger.info(f"🚀 Fast client connected: {client_id}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "🚀 Connected to Fast Brain Router",
                "fast_mode": True
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('type') == 'chat_request':
                        mode = ChatMode(data.get('mode', 'General'))
                        user_message = data.get('message', '')
                        session_id = data.get('session_id', 'default')
                        
                        # Fast processing
                        result = await self.process_request_with_automation(mode, user_message, session_id)
                        
                        # Send response
                        await websocket.send(json.dumps({
                            "type": "chat_response",
                            "data": result
                        }))
                
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Processing error: {str(e)}"
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🚀 Fast client disconnected: {client_id}")
        finally:
            self.connected_clients.discard(client_id)

async def main():
    """Main server function"""
    router = FastBrainRouter()
    
    # Start WebSocket server
    server = await websockets.serve(
        router.handle_websocket_connection,
        "localhost",
        8765,
        ping_interval=20,
        ping_timeout=10
    )
    
    logger.info("🚀 Fast Brain Router WebSocket server started on ws://localhost:8765")
    logger.info("⚡ FAST MODE - No LLaVA timeouts, quick responses!")
    
    # Keep server running
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🚀 Fast Brain Router stopped by user")
    except Exception as e:
        logger.error(f"Fast Brain Router error: {e}")