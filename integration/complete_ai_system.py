#!/usr/bin/env python3
"""
Complete AI System - Universal UI Automation with Advanced Memory Integration

This system creates perfect synergy between:
1. UI Understanding (neural_ui_detector, sensai_ui2html, total_screen_analyzer)
2. Intelligent Action Suggestions (universal_smart_planner, brain_router)
3. Execution (advanced_input_controller, RPA_AVEN)
4. Memory Management (task_memory_manager, task_context_awareness, conscious_memory)

The system maintains comprehensive memory (long-term, short-term, contextual) 
and provides accurate UI understanding with intelligent action suggestions.
"""

import asyncio
import json
import time
import logging
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/complete_ai_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("complete_ai_system")

@dataclass
class UIState:
    """Current UI state with comprehensive understanding"""
    timestamp: float
    neural_detection: Optional[Dict[str, Any]] = None
    semantic_tree: Optional[Dict[str, Any]] = None
    screen_analysis: Optional[Dict[str, Any]] = None
    accessibility_info: Optional[Dict[str, Any]] = None
    visual_features: Optional[List[float]] = None
    text_content: Optional[str] = None
    ui_elements: List[Dict[str, Any]] = field(default_factory=list)
    active_applications: List[str] = field(default_factory=list)
    user_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionSuggestion:
    """Intelligent action suggestion with context"""
    action_id: str
    action_type: str  # 'click', 'type', 'navigate', 'wait', 'verify'
    target: str
    description: str
    confidence: float
    reasoning: str
    prerequisites: List[str] = field(default_factory=list)
    expected_outcome: str = ""
    context_hints: List[str] = field(default_factory=list)
    memory_references: List[str] = field(default_factory=list)

@dataclass
class ExecutionResult:
    """Result of action execution with verification"""
    success: bool
    action_id: str
    execution_time: float
    verification_passed: bool
    ui_changes_detected: bool
    memory_updated: bool
    errors: List[str] = field(default_factory=list)
    telemetry: Dict[str, Any] = field(default_factory=dict)

class CompleteAISystem:
    """
    Complete AI system that integrates all components for universal UI automation
    with comprehensive memory management and intelligent action suggestions.
    """
    
    def __init__(self, rpa_server_url: str = "http://localhost:16901"):
        self.rpa_server_url = rpa_server_url
        self.session_id = f"complete_session_{int(time.time())}"
        
        # Initialize all components
        self.ui_understanding = None
        self.action_planner = None
        self.execution_engine = None
        self.memory_system = None
        self.brain_router = None
        
        # State tracking
        self.current_ui_state: Optional[UIState] = None
        self.action_history: List[ExecutionResult] = []
        self.memory_updates: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.stats = {
            "ui_analyses": 0,
            "action_suggestions": 0,
            "executions": 0,
            "memory_updates": 0,
            "total_time": 0
        }
        
        logger.info("🤖 Complete AI System initializing...")
    
    async def initialize(self) -> bool:
        """Initialize all system components"""
        try:
            logger.info("📦 Initializing UI Understanding components...")
            
            # 1. Initialize UI Understanding
            await self._initialize_ui_understanding()
            
            # 2. Initialize Action Planning
            await self._initialize_action_planning()
            
            # 3. Initialize Execution Engine
            await self._initialize_execution_engine()
            
            # 4. Initialize Memory System
            await self._initialize_memory_system()
            
            # 5. Initialize Brain Router
            await self._initialize_brain_router()
            
            # 6. Test RPA server connection
            await self._test_rpa_connection()
            
            logger.info("✅ Complete AI System initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def _initialize_ui_understanding(self):
        """Initialize UI understanding components"""
        try:
            # Neural UI Detector
            from neural_ui_detector import NeuralUIDetector
            self.neural_detector = NeuralUIDetector()
            logger.info("✅ Neural UI Detector initialized")
            
            # Semantic UI Tree
            try:
                from sensai_ui2html import get_ui_tree, store_ui_snapshot
                self.semantic_ui = {
                    "get_ui_tree": get_ui_tree,
                    "store_ui_snapshot": store_ui_snapshot
                }
                logger.info("✅ Semantic UI Tree system initialized")
            except ImportError as e:
                logger.warning(f"⚠️ Semantic UI Tree not available: {e}")
                self.semantic_ui = None
            
            # Total Screen Analyzer
            try:
                from sensors.total_screen_analyzer import TotalScreenAnalyzer
                self.screen_analyzer = TotalScreenAnalyzer(fast_mode=True)
                logger.info("✅ Total Screen Analyzer initialized")
            except ImportError as e:
                logger.warning(f"⚠️ Total Screen Analyzer not available: {e}")
                self.screen_analyzer = None
            
            self.ui_understanding = True
            logger.info("✅ UI Understanding components initialized")
            
        except Exception as e:
            logger.error(f"❌ UI Understanding initialization failed: {e}")
            raise
    
    async def _initialize_action_planning(self):
        """Initialize action planning components"""
        try:
            # Universal Smart Planner
            from universal_smart_planner import UniversalSmartPlanner
            self.smart_planner = UniversalSmartPlanner()
            logger.info("✅ Universal Smart Planner initialized")
            
            # Universal Task Loop Controller
            from universal_task_loop_controller import UniversalTaskLoopController
            self.task_controller = UniversalTaskLoopController()
            await self.task_controller.initialize()
            logger.info("✅ Universal Task Loop Controller initialized")
            
            # Universal Intelligent Automation Handler
            from universal_intelligent_automation_handler import UniversalIntelligentAutomationHandler
            self.automation_handler = UniversalIntelligentAutomationHandler()
            logger.info("✅ Universal Intelligent Automation Handler initialized")
            
            self.action_planner = True
            logger.info("✅ Action Planning components initialized")
            
        except Exception as e:
            logger.error(f"❌ Action Planning initialization failed: {e}")
            raise
    
    async def _initialize_execution_engine(self):
        """Initialize execution engine components"""
        try:
            # Advanced Input Controller
            from agent_workflow.advanced_input_controller import AdvancedInputController
            self.input_controller = AdvancedInputController(safety_level="medium")
            logger.info("✅ Advanced Input Controller initialized")
            
            # RPA Bridge
            import requests
            self.rpa_client = requests.Session()
            logger.info("✅ RPA Client initialized")
            
            self.execution_engine = True
            logger.info("✅ Execution Engine components initialized")
            
        except Exception as e:
            logger.error(f"❌ Execution Engine initialization failed: {e}")
            raise
    
    async def _initialize_memory_system(self):
        """Initialize memory system components"""
        try:
            # Task Memory Manager
            from memory.task_memory_manager import initialize as init_task_memory
            self.task_memory = await init_task_memory()
            logger.info("✅ Task Memory Manager initialized")
            
            # Task Context Awareness
            from memory.task_context_awareness import initialize as init_task_context
            self.task_context = await init_task_context()
            logger.info("✅ Task Context Awareness initialized")
            
            # Conscious Memory
            try:
                from memory.conscious_memory import ConsciousMemory
                self.conscious_memory = ConsciousMemory()
                logger.info("✅ Conscious Memory initialized")
            except ImportError as e:
                logger.warning(f"⚠️ Conscious Memory not available: {e}")
                self.conscious_memory = None
            
            # Memory Integration Service
            try:
                from memory.memory_integration_service import MemoryIntegrationService
                self.memory_integration = MemoryIntegrationService()
                logger.info("✅ Memory Integration Service initialized")
            except ImportError as e:
                logger.warning(f"⚠️ Memory Integration Service not available: {e}")
                self.memory_integration = None
            
            self.memory_system = True
            logger.info("✅ Memory System components initialized")
            
        except Exception as e:
            logger.error(f"❌ Memory System initialization failed: {e}")
            raise
    
    async def _initialize_brain_router(self):
        """Initialize brain router"""
        try:
            from brain.core.brain_router import get_brain_router
            self.brain_router = await get_brain_router()
            logger.info("✅ Brain Router initialized")
            
        except Exception as e:
            logger.error(f"❌ Brain Router initialization failed: {e}")
            raise
    
    async def _test_rpa_connection(self):
        """Test connection to RPA server"""
        try:
            response = self.rpa_client.get(f"{self.rpa_server_url}/", timeout=5)
            if response.status_code == 200:
                logger.info("✅ RPA server is running and responsive")
            else:
                raise Exception(f"RPA server returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ RPA server connection failed: {e}")
            logger.info("💡 Make sure to start the RPA server first:")
            logger.info("   cd RPA_AVEN/helper && go run main.go")
            raise
    
    async def understand_ui(self) -> UIState:
        """Comprehensive UI understanding using all available methods"""
        start_time = time.time()
        
        try:
            logger.info("👁️ Performing comprehensive UI understanding...")
            
            ui_state = UIState(timestamp=time.time())
            
            # 1. Neural UI Detection
            if self.neural_detector:
                try:
                    neural_result = await self.neural_detector.detect_elements()
                    ui_state.neural_detection = neural_result.to_dict()
                    ui_state.ui_elements = [elem.to_dict() for elem in neural_result.elements]
                    logger.info(f"   🧠 Neural detection: {len(ui_state.ui_elements)} elements")
                except Exception as e:
                    logger.warning(f"   ⚠️ Neural detection failed: {e}")
            
            # 2. Semantic UI Tree
            if self.semantic_ui:
                try:
                    semantic_tree = self.semantic_ui["get_ui_tree"]()
                    ui_state.semantic_tree = semantic_tree
                    logger.info(f"   🌳 Semantic tree: {semantic_tree.get('name', 'unknown')}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Semantic tree failed: {e}")
            
            # 3. Total Screen Analysis
            if self.screen_analyzer:
                try:
                    screen_analysis = await self.screen_analyzer.analyze_full_screen()
                    ui_state.screen_analysis = screen_analysis
                    if screen_analysis:
                        ui_state.text_content = screen_analysis.get("text_content", "")
                        ui_state.active_applications = screen_analysis.get("active_applications", [])
                        logger.info(f"   📊 Screen analysis: {len(ui_state.active_applications)} apps")
                except Exception as e:
                    logger.warning(f"   ⚠️ Screen analysis failed: {e}")
            
            # 4. Extract text content
            if not ui_state.text_content and ui_state.neural_detection:
                ui_state.text_content = " ".join([
                    elem.get("text", "") for elem in ui_state.ui_elements 
                    if elem.get("text", "").strip()
                ])
            
            self.current_ui_state = ui_state
            self.stats["ui_analyses"] += 1
            
            analysis_time = time.time() - start_time
            logger.info(f"✅ UI understanding completed in {analysis_time:.2f}s")
            
            return ui_state
            
        except Exception as e:
            logger.error(f"❌ UI understanding failed: {e}")
            return UIState(timestamp=time.time())
    
    async def suggest_actions(self, user_request: str, ui_state: Optional[UIState] = None) -> List[ActionSuggestion]:
        """Generate intelligent action suggestions based on UI state and user request"""
        start_time = time.time()
        
        try:
            logger.info("🧠 Generating intelligent action suggestions...")
            
            if ui_state is None:
                ui_state = await self.understand_ui()
            
            suggestions = []
            
            # 1. Use Brain Router for intelligent processing
            if self.brain_router:
                try:
                    brain_response = await self.brain_router.process_request({
                        "mode": "Agent",
                        "query": user_request,
                        "user_id": "user",
                        "session_id": self.session_id,
                        "context": {
                            "ui_state": ui_state.__dict__,
                            "current_applications": ui_state.active_applications,
                            "text_content": ui_state.text_content
                        }
                    })
                    
                    if brain_response.success:
                        # Parse brain response for action suggestions
                        parsed_suggestions = self._parse_brain_response(brain_response, ui_state)
                        suggestions.extend(parsed_suggestions)
                        logger.info(f"   🧠 Brain router: {len(parsed_suggestions)} suggestions")
                except Exception as e:
                    logger.warning(f"   ⚠️ Brain router failed: {e}")
            
            # 2. Use Smart Planner for structured planning
            if self.smart_planner:
                try:
                    plan = await self.smart_planner.create_universal_plan(user_request, self.session_id)
                    plan_suggestions = self._convert_plan_to_suggestions(plan, ui_state)
                    suggestions.extend(plan_suggestions)
                    logger.info(f"   📋 Smart planner: {len(plan_suggestions)} suggestions")
                except Exception as e:
                    logger.warning(f"   ⚠️ Smart planner failed: {e}")
            
            # 3. Use Automation Handler for advanced automation
            if self.automation_handler:
                try:
                    automation_result = await self.automation_handler.create_universal_automation_plan(
                        user_request, self.session_id
                    )
                    if automation_result.get("success"):
                        auto_suggestions = self._parse_automation_plan(automation_result, ui_state)
                        suggestions.extend(auto_suggestions)
                        logger.info(f"   🤖 Automation handler: {len(auto_suggestions)} suggestions")
                except Exception as e:
                    logger.warning(f"   ⚠️ Automation handler failed: {e}")
            
            # 4. Add memory-based suggestions
            memory_suggestions = await self._generate_memory_based_suggestions(user_request, ui_state)
            suggestions.extend(memory_suggestions)
            logger.info(f"   💾 Memory-based: {len(memory_suggestions)} suggestions")
            
            # 5. Rank and filter suggestions
            ranked_suggestions = self._rank_suggestions(suggestions, ui_state)
            
            self.stats["action_suggestions"] += 1
            
            suggestion_time = time.time() - start_time
            logger.info(f"✅ Generated {len(ranked_suggestions)} action suggestions in {suggestion_time:.2f}s")
            
            return ranked_suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"❌ Action suggestion generation failed: {e}")
            return []
    
    def _parse_brain_response(self, brain_response, ui_state: UIState) -> List[ActionSuggestion]:
        """Parse brain router response into action suggestions"""
        suggestions = []
        
        try:
            response_text = brain_response.response
            execution_plan = brain_response.execution_plan
            
            if execution_plan:
                # Parse structured execution plan
                for step in execution_plan.get("steps", []):
                    suggestion = ActionSuggestion(
                        action_id=f"brain_{len(suggestions)}",
                        action_type=step.get("action_type", "unknown"),
                        target=step.get("target", ""),
                        description=step.get("description", ""),
                        confidence=brain_response.confidence,
                        reasoning=f"Brain router analysis: {step.get('reasoning', '')}",
                        expected_outcome=step.get("expected_outcome", "")
                    )
                    suggestions.append(suggestion)
            else:
                # Parse text response for action hints
                action_hints = self._extract_action_hints_from_text(response_text)
                for hint in action_hints:
                    suggestion = ActionSuggestion(
                        action_id=f"brain_text_{len(suggestions)}",
                        action_type=hint["type"],
                        target=hint["target"],
                        description=hint["description"],
                        confidence=0.7,
                        reasoning=f"Extracted from brain response: {hint['reasoning']}"
                    )
                    suggestions.append(suggestion)
                    
        except Exception as e:
            logger.warning(f"Failed to parse brain response: {e}")
        
        return suggestions
    
    def _convert_plan_to_suggestions(self, plan, ui_state: UIState) -> List[ActionSuggestion]:
        """Convert smart planner plan to action suggestions"""
        suggestions = []
        
        try:
            for step in plan.steps:
                suggestion = ActionSuggestion(
                    action_id=f"plan_{step.id}",
                    action_type=step.action_type,
                    target=step.target or "",
                    description=step.description,
                    confidence=step.confidence,
                    reasoning=f"Smart planner: {step.description}",
                    estimated_duration=step.estimated_duration
                )
                suggestions.append(suggestion)
        except Exception as e:
            logger.warning(f"Failed to convert plan to suggestions: {e}")
        
        return suggestions
    
    def _parse_automation_plan(self, automation_result, ui_state: UIState) -> List[ActionSuggestion]:
        """Parse automation handler result into action suggestions"""
        suggestions = []
        
        try:
            plan_id = automation_result.get("plan_id")
            if plan_id and self.automation_handler.active_plans.get(plan_id):
                plan = self.automation_handler.active_plans[plan_id]
                for step in plan.steps:
                    suggestion = ActionSuggestion(
                        action_id=f"auto_{step.id}",
                        action_type=step.action_type,
                        target=step.target or "",
                        description=step.description,
                        confidence=step.confidence,
                        reasoning=f"Automation handler: {step.description}",
                        fallback_action=step.fallback_action
                    )
                    suggestions.append(suggestion)
        except Exception as e:
            logger.warning(f"Failed to parse automation plan: {e}")
        
        return suggestions
    
    async def _generate_memory_based_suggestions(self, user_request: str, ui_state: UIState) -> List[ActionSuggestion]:
        """Generate suggestions based on memory and context"""
        suggestions = []
        
        try:
            # Search task memory for similar requests
            if self.task_memory:
                similar_tasks = await self.task_memory.search_task_records(user_request, limit=3)
                for task in similar_tasks:
                    suggestion = ActionSuggestion(
                        action_id=f"memory_{task.get('task_id', 'unknown')}",
                        action_type="memory_reference",
                        target="previous_task",
                        description=f"Similar to: {task.get('description', 'unknown task')}",
                        confidence=0.6,
                        reasoning=f"Based on memory of similar task: {task.get('description', '')}",
                        memory_references=[task.get('task_id', '')]
                    )
                    suggestions.append(suggestion)
            
            # Use conscious memory for context-aware suggestions
            if self.conscious_memory:
                conscious_context = self.conscious_memory.get_current_context()
                if conscious_context:
                    suggestion = ActionSuggestion(
                        action_id="conscious_context",
                        action_type="context_aware",
                        target="current_context",
                        description=f"Context: {conscious_context.get('current_activity', 'unknown')}",
                        confidence=0.5,
                        reasoning=f"Based on conscious memory context: {conscious_context.get('reasoning', '')}",
                        context_hints=[conscious_context.get('current_activity', '')]
                    )
                    suggestions.append(suggestion)
                    
        except Exception as e:
            logger.warning(f"Failed to generate memory-based suggestions: {e}")
        
        return suggestions
    
    def _extract_action_hints_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract action hints from text response"""
        hints = []
        
        # Simple pattern matching for common actions
        action_patterns = [
            (r"click\s+(?:on\s+)?([^\s]+)", "click"),
            (r"type\s+(?:the\s+)?([^\s]+)", "type"),
            (r"open\s+([^\s]+)", "open_app"),
            (r"navigate\s+to\s+([^\s]+)", "navigate"),
            (r"wait\s+(?:for\s+)?([^\s]+)", "wait")
        ]
        
        for pattern, action_type in action_patterns:
            import re
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                hints.append({
                    "type": action_type,
                    "target": match,
                    "description": f"{action_type} {match}",
                    "reasoning": f"Extracted from text: {text[:100]}..."
                })
        
        return hints
    
    def _rank_suggestions(self, suggestions: List[ActionSuggestion], ui_state: UIState) -> List[ActionSuggestion]:
        """Rank suggestions by relevance and confidence"""
        try:
            # Score each suggestion
            for suggestion in suggestions:
                score = 0.0
                
                # Base confidence score
                score += suggestion.confidence * 0.4
                
                # UI state relevance
                if ui_state.text_content and suggestion.target.lower() in ui_state.text_content.lower():
                    score += 0.3
                
                # Active application relevance
                if any(app.lower() in suggestion.target.lower() for app in ui_state.active_applications):
                    score += 0.2
                
                # Memory reference bonus
                if suggestion.memory_references:
                    score += 0.1
                
                # Context hint bonus
                if suggestion.context_hints:
                    score += 0.1
                
                suggestion.confidence = min(1.0, score)
            
            # Sort by confidence
            return sorted(suggestions, key=lambda s: s.confidence, reverse=True)
            
        except Exception as e:
            logger.warning(f"Failed to rank suggestions: {e}")
            return suggestions
    
    async def execute_action(self, suggestion: ActionSuggestion) -> ExecutionResult:
        """Execute a suggested action with verification"""
        start_time = time.time()
        
        try:
            logger.info(f"⚡ Executing action: {suggestion.description}")
            
            # Pre-execution UI state
            pre_ui_state = await self.understand_ui()
            
            # Execute action based on type
            success = False
            errors = []
            
            if suggestion.action_type == "click":
                success = await self._execute_click(suggestion)
            elif suggestion.action_type == "type":
                success = await self._execute_type(suggestion)
            elif suggestion.action_type == "open_app":
                success = await self._execute_open_app(suggestion)
            elif suggestion.action_type == "navigate":
                success = await self._execute_navigate(suggestion)
            elif suggestion.action_type == "wait":
                success = await self._execute_wait(suggestion)
            else:
                errors.append(f"Unknown action type: {suggestion.action_type}")
            
            # Post-execution UI state
            post_ui_state = await self.understand_ui()
            
            # Verify execution
            verification_passed = self._verify_execution(suggestion, pre_ui_state, post_ui_state)
            
            # Detect UI changes
            ui_changes_detected = self._detect_ui_changes(pre_ui_state, post_ui_state)
            
            # Update memory
            memory_updated = await self._update_memory(suggestion, success, pre_ui_state, post_ui_state)
            
            execution_time = time.time() - start_time
            
            result = ExecutionResult(
                success=success,
                action_id=suggestion.action_id,
                execution_time=execution_time,
                verification_passed=verification_passed,
                ui_changes_detected=ui_changes_detected,
                memory_updated=memory_updated,
                errors=errors,
                telemetry={
                    "pre_ui_elements": len(pre_ui_state.ui_elements),
                    "post_ui_elements": len(post_ui_state.ui_elements),
                    "confidence": suggestion.confidence
                }
            )
            
            self.action_history.append(result)
            self.stats["executions"] += 1
            
            logger.info(f"✅ Action execution completed: {success} ({execution_time:.2f}s)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Action execution failed: {e}")
            return ExecutionResult(
                success=False,
                action_id=suggestion.action_id,
                execution_time=time.time() - start_time,
                verification_passed=False,
                ui_changes_detected=False,
                memory_updated=False,
                errors=[str(e)]
            )
    
    async def _execute_click(self, suggestion: ActionSuggestion) -> bool:
        """Execute click action"""
        try:
            # Find target element
            target_element = self._find_element_by_description(suggestion.target)
            
            if target_element:
                # Use advanced input controller
                if self.input_controller:
                    result = await self.input_controller.click(
                        x=target_element["center"][0],
                        y=target_element["center"][1]
                    )
                    return result.success
                else:
                    # Fallback to RPA server
                    response = self.rpa_client.post(
                        f"{self.rpa_server_url}/click",
                        json={
                            "x": target_element["center"][0],
                            "y": target_element["center"][1]
                        },
                        timeout=10
                    )
                    return response.status_code == 200
            else:
                logger.warning(f"Target element not found: {suggestion.target}")
                return False
                
        except Exception as e:
            logger.error(f"Click execution failed: {e}")
            return False
    
    async def _execute_type(self, suggestion: ActionSuggestion) -> bool:
        """Execute type action"""
        try:
            if self.input_controller:
                result = await self.input_controller.type_text(suggestion.target)
                return result.success
            else:
                # Fallback to RPA server
                response = self.rpa_client.post(
                    f"{self.rpa_server_url}/type",
                    json={"text": suggestion.target},
                    timeout=10
                )
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Type execution failed: {e}")
            return False
    
    async def _execute_open_app(self, suggestion: ActionSuggestion) -> bool:
        """Execute open app action"""
        try:
            response = self.rpa_client.post(
                f"{self.rpa_server_url}/open_app",
                json={"app_name": suggestion.target},
                timeout=10
            )
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Open app execution failed: {e}")
            return False
    
    async def _execute_navigate(self, suggestion: ActionSuggestion) -> bool:
        """Execute navigate action"""
        try:
            # This would typically open a browser and navigate
            # For now, just log the action
            logger.info(f"Navigate to: {suggestion.target}")
            return True
            
        except Exception as e:
            logger.error(f"Navigate execution failed: {e}")
            return False
    
    async def _execute_wait(self, suggestion: ActionSuggestion) -> bool:
        """Execute wait action"""
        try:
            wait_time = float(suggestion.target) if suggestion.target.isdigit() else 1.0
            await asyncio.sleep(wait_time)
            return True
            
        except Exception as e:
            logger.error(f"Wait execution failed: {e}")
            return False
    
    def _find_element_by_description(self, description: str) -> Optional[Dict[str, Any]]:
        """Find UI element by description"""
        if not self.current_ui_state or not self.current_ui_state.ui_elements:
            return None
        
        # Simple text matching
        description_lower = description.lower()
        for element in self.current_ui_state.ui_elements:
            element_text = element.get("text", "").lower()
            if description_lower in element_text or element_text in description_lower:
                return element
        
        return None
    
    def _verify_execution(self, suggestion: ActionSuggestion, pre_state: UIState, post_state: UIState) -> bool:
        """Verify that execution had the expected effect"""
        try:
            # Check if UI changed
            if len(pre_state.ui_elements) != len(post_state.ui_elements):
                return True
            
            # Check if text content changed
            if pre_state.text_content != post_state.text_content:
                return True
            
            # Check if active applications changed
            if pre_state.active_applications != post_state.active_applications:
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Verification failed: {e}")
            return False
    
    def _detect_ui_changes(self, pre_state: UIState, post_state: UIState) -> bool:
        """Detect if UI changed between states"""
        try:
            # Compare UI elements
            if len(pre_state.ui_elements) != len(post_state.ui_elements):
                return True
            
            # Compare text content
            if pre_state.text_content != post_state.text_content:
                return True
            
            # Compare active applications
            if pre_state.active_applications != post_state.active_applications:
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"UI change detection failed: {e}")
            return False
    
    async def _update_memory(self, suggestion: ActionSuggestion, success: bool, 
                           pre_state: UIState, post_state: UIState) -> bool:
        """Update memory with execution results"""
        try:
            # Create memory record
            memory_record = {
                "timestamp": time.time(),
                "action_id": suggestion.action_id,
                "action_type": suggestion.action_type,
                "target": suggestion.target,
                "description": suggestion.description,
                "success": success,
                "confidence": suggestion.confidence,
                "reasoning": suggestion.reasoning,
                "pre_ui_state": pre_state.__dict__,
                "post_ui_state": post_state.__dict__,
                "ui_changes": self._detect_ui_changes(pre_state, post_state),
                "memory_type": "action_execution"
            }
            
            # Update task memory
            if self.task_memory:
                await self.task_memory.create_task_record(
                    suggestion.action_id,
                    memory_record
                )
            
            # Update conscious memory
            if self.conscious_memory:
                self.conscious_memory.add_memory(memory_record)
            
            # Update memory integration
            if self.memory_integration:
                await self.memory_integration.update_memory(memory_record)
            
            self.memory_updates.append(memory_record)
            self.stats["memory_updates"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Memory update failed: {e}")
            return False
    
    async def process_user_request(self, user_request: str) -> Dict[str, Any]:
        """Complete processing of user request with UI understanding, suggestions, and execution"""
        start_time = time.time()
        
        try:
            logger.info(f"🎯 Processing user request: {user_request}")
            
            # 1. Understand current UI state
            ui_state = await self.understand_ui()
            
            # 2. Generate action suggestions
            suggestions = await self.suggest_actions(user_request, ui_state)
            
            # 3. Execute top suggestion
            execution_result = None
            if suggestions:
                execution_result = await self.execute_action(suggestions[0])
            
            # 4. Prepare response
            response = {
                "success": True,
                "user_request": user_request,
                "ui_understanding": {
                    "elements_detected": len(ui_state.ui_elements),
                    "active_applications": ui_state.active_applications,
                    "text_content_length": len(ui_state.text_content or "")
                },
                "suggestions_generated": len(suggestions),
                "top_suggestion": suggestions[0].__dict__ if suggestions else None,
                "execution_result": execution_result.__dict__ if execution_result else None,
                "processing_time": time.time() - start_time,
                "session_id": self.session_id
            }
            
            self.stats["total_time"] += response["processing_time"]
            
            logger.info(f"✅ Request processing completed in {response['processing_time']:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Request processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        return {
            "ui_analyses": self.stats["ui_analyses"],
            "action_suggestions": self.stats["action_suggestions"],
            "executions": self.stats["executions"],
            "memory_updates": self.stats["memory_updates"],
            "total_time": self.stats["total_time"],
            "average_time": self.stats["total_time"] / max(1, self.stats["executions"]),
            "session_id": self.session_id,
            "components_available": {
                "ui_understanding": self.ui_understanding is not None,
                "action_planner": self.action_planner is not None,
                "execution_engine": self.execution_engine is not None,
                "memory_system": self.memory_system is not None,
                "brain_router": self.brain_router is not None
            }
        }

# Global instance
complete_system = None

async def initialize_complete_system(rpa_server_url: str = "http://localhost:16901") -> CompleteAISystem:
    """Initialize the complete AI system"""
    global complete_system
    
    if complete_system is None:
        complete_system = CompleteAISystem(rpa_server_url)
        await complete_system.initialize()
    
    return complete_system

async def process_request(user_request: str) -> Dict[str, Any]:
    """Process a user request with the complete AI system"""
    if complete_system is None:
        await initialize_complete_system()
    
    return await complete_system.process_user_request(user_request)

async def get_system_stats() -> Dict[str, Any]:
    """Get system statistics"""
    if complete_system is None:
        return {"error": "System not initialized"}
    
    return complete_system.get_system_stats()

async def test_system():
    """Test the complete AI system"""
    logger.info("🧪 Testing Complete AI System")
    
    try:
        # Initialize system
        system = await initialize_complete_system()
        
        # Test UI understanding
        logger.info("1. Testing UI Understanding...")
        ui_state = await system.understand_ui()
        logger.info(f"   ✅ Detected {len(ui_state.ui_elements)} UI elements")
        
        # Test action suggestions
        logger.info("2. Testing Action Suggestions...")
        suggestions = await system.suggest_actions("Open Calculator")
        logger.info(f"   ✅ Generated {len(suggestions)} suggestions")
        
        # Test execution
        logger.info("3. Testing Action Execution...")
        if suggestions:
            result = await system.execute_action(suggestions[0])
            logger.info(f"   ✅ Execution result: {result.success}")
        
        # Test complete request processing
        logger.info("4. Testing Complete Request Processing...")
        response = await system.process_user_request("Open Calculator")
        logger.info(f"   ✅ Processing result: {response['success']}")
        
        # Get stats
        stats = system.get_system_stats()
        logger.info(f"5. System Stats: {stats}")
        
        logger.info("✅ Complete AI System test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ System test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_system()) 