#!/usr/bin/env python3
"""
Advanced AI-RPA Bridge
Connects Aiayer's existing advanced UI understanding and multi-task planning 
with RPA_AVEN's real execution capabilities.

This bridge leverages:
- neural_ui_detector.py for state-of-the-art UI understanding
- universal_smart_planner.py for intelligent task planning  
- universal_task_loop_controller.py for multi-task execution
- universal_intelligent_automation_handler.py for advanced automation
- RPA_AVEN server for real low-level execution
"""

import asyncio
import json
import time
import logging
import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import Aiayer's existing advanced components
try:
    from neural_ui_detector import NeuralUIDetector, DetectionResult
    from universal_smart_planner import UniversalSmartPlanner
    from universal_task_loop_controller import UniversalTaskLoopController
    from universal_intelligent_automation_handler import UniversalIntelligentAutomationHandler
    AIAYER_ADVANCED_AVAILABLE = True
    logger = logging.getLogger("advanced_ai_rpa_bridge")
    logger.info("✅ All Aiayer advanced components loaded successfully")
except ImportError as e:
    logger = logging.getLogger("advanced_ai_rpa_bridge")
    logger.error(f"❌ Failed to load Aiayer advanced components: {e}")
    AIAYER_ADVANCED_AVAILABLE = False

@dataclass
class AdvancedExecutionResult:
    """Result of advanced AI-RPA execution"""
    success: bool
    task_id: str
    steps_completed: int
    total_steps: int
    ui_elements_detected: int
    execution_time: float
    errors: List[str]
    ui_snapshots: List[str]
    final_state: Dict[str, Any]

class AdvancedAIRPABridge:
    """Advanced bridge connecting Aiayer's AI capabilities with RPA_AVEN execution"""
    
    def __init__(self, rpa_server_url: str = "http://localhost:8080"):
        self.rpa_server_url = rpa_server_url
        self.session_id = f"advanced_session_{int(time.time())}"
        
        # Initialize Aiayer's advanced components
        if AIAYER_ADVANCED_AVAILABLE:
            self.ui_detector = NeuralUIDetector()
            self.smart_planner = UniversalSmartPlanner()
            self.task_controller = UniversalTaskLoopController()
            self.automation_handler = UniversalIntelligentAutomationHandler()
            logger.info("🤖 Advanced AI components initialized")
        else:
            logger.error("❌ Cannot initialize - Aiayer advanced components not available")
            raise ImportError("Aiayer advanced components required")
    
    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize task controller
            await self.task_controller.initialize()
            logger.info("✅ Task controller initialized")
            
            # Test RPA server connection
            await self._test_rpa_connection()
            logger.info("✅ RPA server connection verified")
            
            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def _test_rpa_connection(self):
        """Test connection to RPA server"""
        try:
            response = requests.get(f"{self.rpa_server_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ RPA server is running and responsive")
            else:
                raise Exception(f"RPA server returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ RPA server connection failed: {e}")
            raise
    
    async def execute_advanced_task(self, user_request: str) -> AdvancedExecutionResult:
        """Execute a task using Aiayer's advanced AI with RPA_AVEN execution"""
        start_time = time.time()
        task_id = f"advanced_task_{int(time.time())}"
        
        try:
            logger.info(f"🚀 Starting advanced task execution: {user_request}")
            
            # Step 1: Create intelligent automation plan using Aiayer's planner
            logger.info("🧠 Creating intelligent automation plan...")
            plan = await self.automation_handler.create_universal_automation_plan(
                user_request, self.session_id
            )
            
            if not plan.get("success"):
                raise Exception(f"Failed to create plan: {plan.get('response')}")
            
            # Step 2: Detect current UI state using neural detector
            logger.info("👁️ Detecting current UI state...")
            ui_result = await self.ui_detector.detect_elements()
            ui_elements_detected = len(ui_result.elements)
            logger.info(f"📊 Detected {ui_elements_detected} UI elements")
            
            # Step 3: Submit task to advanced task controller
            logger.info("🎯 Submitting to advanced task controller...")
            task_result = await self.task_controller.submit_task(
                user_request, 
                task_type="universal",
                context={
                    "ui_state": ui_result.to_dict(),
                    "plan": plan,
                    "rpa_server_url": self.rpa_server_url
                }
            )
            
            # Step 4: Execute using RPA_AVEN with AI guidance
            logger.info("⚡ Executing with RPA_AVEN...")
            execution_result = await self._execute_with_rpa_guidance(
                task_result, ui_result, plan
            )
            
            execution_time = time.time() - start_time
            
            return AdvancedExecutionResult(
                success=True,
                task_id=task_id,
                steps_completed=execution_result.get("steps_completed", 0),
                total_steps=execution_result.get("total_steps", 0),
                ui_elements_detected=ui_elements_detected,
                execution_time=execution_time,
                errors=execution_result.get("errors", []),
                ui_snapshots=execution_result.get("ui_snapshots", []),
                final_state=execution_result.get("final_state", {})
            )
            
        except Exception as e:
            logger.error(f"❌ Advanced task execution failed: {e}")
            return AdvancedExecutionResult(
                success=False,
                task_id=task_id,
                steps_completed=0,
                total_steps=0,
                ui_elements_detected=0,
                execution_time=time.time() - start_time,
                errors=[str(e)],
                ui_snapshots=[],
                final_state={}
            )
    
    async def _execute_with_rpa_guidance(self, task_result: Dict, ui_result: DetectionResult, plan: Dict) -> Dict[str, Any]:
        """Execute task using RPA_AVEN with AI guidance from UI detection"""
        steps_completed = 0
        total_steps = 0
        errors = []
        ui_snapshots = []
        final_state = {}
        
        try:
            # Get task status and steps
            task_id = task_result.get("task_id")
            task_status = await self.task_controller.get_task_status(task_id)
            steps = task_status.get("current_plan", {}).get("steps", [])
            total_steps = len(steps)
            
            logger.info(f"📋 Executing {total_steps} steps with AI guidance")
            
            for i, step in enumerate(steps):
                try:
                    logger.info(f"⚡ Executing step {i+1}/{total_steps}: {step.get('description', 'Unknown')}")
                    
                    # Take UI snapshot before execution
                    ui_snapshot = await self.ui_detector.detect_elements()
                    ui_snapshots.append(ui_snapshot.to_dict())
                    
                    # Execute step using RPA_AVEN
                    step_result = await self._execute_rpa_step(step, ui_snapshot)
                    
                    if step_result.get("success"):
                        steps_completed += 1
                        logger.info(f"✅ Step {i+1} completed successfully")
                    else:
                        errors.append(f"Step {i+1} failed: {step_result.get('error')}")
                        logger.warning(f"⚠️ Step {i+1} failed: {step_result.get('error')}")
                    
                    # Wait between steps
                    await asyncio.sleep(1)
                    
                except Exception as step_error:
                    errors.append(f"Step {i+1} exception: {str(step_error)}")
                    logger.error(f"❌ Step {i+1} exception: {step_error}")
            
            # Get final state
            final_ui_state = await self.ui_detector.detect_elements()
            final_state = {
                "ui_elements": len(final_ui_state.elements),
                "task_status": await self.task_controller.get_task_status(task_id),
                "final_ui_snapshot": final_ui_state.to_dict()
            }
            
        except Exception as e:
            errors.append(f"Execution exception: {str(e)}")
            logger.error(f"❌ Execution exception: {e}")
        
        return {
            "steps_completed": steps_completed,
            "total_steps": total_steps,
            "errors": errors,
            "ui_snapshots": ui_snapshots,
            "final_state": final_state
        }
    
    async def _execute_rpa_step(self, step: Dict, ui_snapshot: DetectionResult) -> Dict[str, Any]:
        """Execute a single step using RPA_AVEN server"""
        try:
            action_type = step.get("action_type", "")
            
            if action_type == "open_app":
                return await self._rpa_open_app(step.get("target", ""))
            elif action_type == "click_element":
                return await self._rpa_click_element(step, ui_snapshot)
            elif action_type == "type_text":
                return await self._rpa_type_text(step, ui_snapshot)
            elif action_type == "hotkey":
                return await self._rpa_hotkey(step.get("value", ""))
            elif action_type == "wait":
                await asyncio.sleep(float(step.get("value", 1)))
                return {"success": True}
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _rpa_open_app(self, app_name: str) -> Dict[str, Any]:
        """Open app using RPA_AVEN"""
        try:
            response = requests.post(
                f"{self.rpa_server_url}/open_app",
                json={"app_name": app_name},
                timeout=10
            )
            return {"success": response.status_code == 200}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _rpa_click_element(self, step: Dict, ui_snapshot: DetectionResult) -> Dict[str, Any]:
        """Click element using AI guidance and RPA_AVEN"""
        try:
            # Use AI to find the best element to click
            target_description = step.get("target", "")
            element = await self.ui_detector.find_element(target_description)
            
            if element:
                # Click using coordinates
                response = requests.post(
                    f"{self.rpa_server_url}/click",
                    json={
                        "x": element.center[0],
                        "y": element.center[1]
                    },
                    timeout=10
                )
                return {"success": response.status_code == 200}
            else:
                return {"success": False, "error": f"Could not find element: {target_description}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _rpa_type_text(self, step: Dict, ui_snapshot: DetectionResult) -> Dict[str, Any]:
        """Type text using AI guidance and RPA_AVEN"""
        try:
            text = step.get("value", "")
            
            # Use RPA_AVEN to type text
            response = requests.post(
                f"{self.rpa_server_url}/type",
                json={"text": text},
                timeout=10
            )
            return {"success": response.status_code == 200}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _rpa_hotkey(self, hotkey: str) -> Dict[str, Any]:
        """Execute hotkey using RPA_AVEN"""
        try:
            response = requests.post(
                f"{self.rpa_server_url}/hotkey",
                json={"keys": hotkey.split("+")},
                timeout=10
            )
            return {"success": response.status_code == 200}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_ui_understanding(self) -> Dict[str, Any]:
        """Get current UI understanding using neural detector"""
        try:
            result = await self.ui_detector.detect_elements()
            return {
                "success": True,
                "elements": len(result.elements),
                "screen_size": f"{result.screen_width}x{result.screen_height}",
                "detection_methods": result.detection_methods,
                "execution_time": result.execution_time,
                "elements_by_type": {
                    elem_type: len(result.get_elements_by_type(elem_type))
                    for elem_type in set(e.element_type for e in result.elements)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_task_status(self) -> Dict[str, Any]:
        """Get status of all active tasks"""
        try:
            active_tasks = self.task_controller.get_active_tasks()
            return {
                "success": True,
                "active_tasks": len(active_tasks.get("tasks", [])),
                "tasks": active_tasks
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global instance
advanced_bridge = None

async def initialize_advanced_bridge(rpa_server_url: str = "http://localhost:8080") -> AdvancedAIRPABridge:
    """Initialize the advanced AI-RPA bridge"""
    global advanced_bridge
    
    if advanced_bridge is None:
        advanced_bridge = AdvancedAIRPABridge(rpa_server_url)
        await advanced_bridge.initialize()
    
    return advanced_bridge

async def execute_advanced_task(user_request: str) -> AdvancedExecutionResult:
    """Execute a task using the advanced AI-RPA bridge"""
    if advanced_bridge is None:
        await initialize_advanced_bridge()
    
    return await advanced_bridge.execute_advanced_task(user_request)

async def get_ui_understanding() -> Dict[str, Any]:
    """Get current UI understanding"""
    if advanced_bridge is None:
        await initialize_advanced_bridge()
    
    return await advanced_bridge.get_ui_understanding()

async def get_task_status() -> Dict[str, Any]:
    """Get task status"""
    if advanced_bridge is None:
        await initialize_advanced_bridge()
    
    return await advanced_bridge.get_task_status() 