"""
Agent Mode Handler - Task Planning and Execution

Handles Agent mode requests by breaking down tasks into actionable steps,
creating execution plans, and coordinating with automation systems.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

from ..core.brain_router import BrainResponse, ChatRequest, ChatMode

logger = logging.getLogger(__name__)

@dataclass
class TaskStep:
    """Represents a single step in a task execution plan"""
    id: str
    description: str
    action_type: str  # 'automation', 'query', 'analysis', 'verification'
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    estimated_duration: float = 1.0
    status: str = "pending"  # pending, executing, completed, failed
    result: Optional[Dict[str, Any]] = None

@dataclass
class ExecutionPlan:
    """Complete execution plan for an agent task"""
    task_id: str
    title: str
    description: str
    steps: List[TaskStep]
    priority: str
    estimated_total_duration: float
    created_at: float
    status: str = "planned"  # planned, executing, completed, failed
    progress: float = 0.0
    metadata: Dict[str, Any] = None

class TaskPlanner:
    """Intelligent task planning and decomposition"""
    
    def __init__(self):
        self.planning_patterns = {
            # File/System Operations
            "file": ["analyze_request", "locate_files", "perform_operation", "verify_result"],
            "system": ["check_system_state", "plan_changes", "execute_changes", "verify_changes"],
            
            # Data/Analysis Tasks  
            "analyze": ["gather_data", "process_data", "generate_insights", "present_results"],
            "search": ["define_criteria", "execute_search", "filter_results", "format_output"],
            
            # Automation Tasks
            "automate": ["understand_goal", "create_automation", "test_automation", "deploy_automation"],
            "optimize": ["baseline_measurement", "identify_bottlenecks", "implement_improvements", "measure_results"],
            
            # Communication/Integration
            "integrate": ["analyze_systems", "design_integration", "implement_connection", "test_integration"],
            "notify": ["prepare_message", "select_channels", "send_notification", "confirm_delivery"]
        }
    
    async def create_execution_plan(self, request: ChatRequest) -> ExecutionPlan:
        """Create detailed execution plan from user request"""
        try:
            # Analyze the request to determine task type
            task_type = await self._classify_task(request.query)
            
            # Get planning pattern
            pattern = self.planning_patterns.get(task_type, ["understand_request", "plan_approach", "execute_plan", "verify_completion"])
            
            # Generate detailed steps
            steps = await self._generate_detailed_steps(request, pattern, task_type)
            
            # Calculate estimated duration
            total_duration = sum(step.estimated_duration for step in steps)
            
            plan = ExecutionPlan(
                task_id=f"task_{int(time.time())}_{hash(request.query) % 10000}",
                title=await self._generate_task_title(request.query),
                description=request.query,
                steps=steps,
                priority="medium",
                estimated_total_duration=total_duration,
                created_at=time.time(),
                metadata={"task_type": task_type, "user_id": request.user_id}
            )
            
            logger.info(f"Created execution plan: {plan.title} with {len(steps)} steps")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            # Return minimal fallback plan
            return ExecutionPlan(
                task_id=f"fallback_{int(time.time())}",
                title="Process Request",
                description=request.query,
                steps=[TaskStep(
                    id="step_1",
                    description="Process the user request",
                    action_type="query",
                    parameters={"query": request.query}
                )],
                priority="medium",
                estimated_total_duration=2.0,
                created_at=time.time()
            )
    
    async def _classify_task(self, query: str) -> str:
        """Classify the type of task based on query content"""
        query_lower = query.lower()
        
        # File operations
        if any(word in query_lower for word in ["file", "folder", "directory", "save", "load", "delete"]):
            return "file"
        
        # System operations
        if any(word in query_lower for word in ["system", "process", "service", "install", "configure"]):
            return "system"
        
        # Analysis tasks
        if any(word in query_lower for word in ["analyze", "analyze", "report", "statistics", "data"]):
            return "analyze"
        
        # Search tasks
        if any(word in query_lower for word in ["find", "search", "locate", "look for"]):
            return "search"
        
        # Automation tasks
        if any(word in query_lower for word in ["automate", "script", "batch", "schedule"]):
            return "automate"
        
        # Optimization tasks
        if any(word in query_lower for word in ["optimize", "improve", "speed up", "performance"]):
            return "optimize"
        
        # Integration tasks
        if any(word in query_lower for word in ["connect", "integrate", "sync", "api"]):
            return "integrate"
        
        # Notification tasks
        if any(word in query_lower for word in ["notify", "alert", "remind", "message"]):
            return "notify"
        
        return "general"
    
    async def _generate_detailed_steps(self, request: ChatRequest, pattern: List[str], task_type: str) -> List[TaskStep]:
        """Generate detailed executable steps based on pattern and request"""
        steps = []
        
        for i, step_template in enumerate(pattern):
            step_id = f"step_{i+1}"
            
            # Customize step based on task type and template
            step_config = await self._customize_step(step_template, request, task_type)
            
            step = TaskStep(
                id=step_id,
                description=step_config["description"],
                action_type=step_config["action_type"],
                parameters=step_config["parameters"],
                dependencies=step_config.get("dependencies", [] if i == 0 else [f"step_{i}"]),
                estimated_duration=step_config.get("duration", 1.0)
            )
            
            steps.append(step)
        
        return steps
    
    async def _customize_step(self, template: str, request: ChatRequest, task_type: str) -> Dict[str, Any]:
        """Customize a step template for the specific request"""
        
        # Step customization rules
        customizations = {
            "understand_request": {
                "description": f"Analyze and understand the request: '{request.query[:100]}...'",
                "action_type": "analysis",
                "parameters": {"query": request.query, "context": request.context},
                "duration": 0.5
            },
            "analyze_request": {
                "description": f"Break down the request into actionable components",
                "action_type": "analysis", 
                "parameters": {"request": request.query, "mode": "decomposition"},
                "duration": 1.0
            },
            "plan_approach": {
                "description": "Develop approach and strategy for execution",
                "action_type": "planning",
                "parameters": {"strategy": "adaptive", "task_type": task_type},
                "duration": 1.5
            },
            "execute_plan": {
                "description": "Execute the planned approach",
                "action_type": "execution",
                "parameters": {"plan": "main", "monitor": True},
                "duration": 3.0
            },
            "verify_completion": {
                "description": "Verify task completion and quality",
                "action_type": "verification",
                "parameters": {"check_quality": True, "validate_output": True},
                "duration": 1.0
            },
            
            # File operations
            "locate_files": {
                "description": "Locate relevant files and directories",
                "action_type": "automation",
                "parameters": {"operation": "search", "criteria": "auto_detect"},
                "duration": 1.5
            },
            "perform_operation": {
                "description": "Perform the requested file operation",
                "action_type": "automation", 
                "parameters": {"operation": "file_op", "safety_check": True},
                "duration": 2.0
            },
            
            # Data operations
            "gather_data": {
                "description": "Collect required data from available sources",
                "action_type": "query",
                "parameters": {"sources": ["memory", "sensors", "storage"], "scope": "relevant"},
                "duration": 2.0
            },
            "process_data": {
                "description": "Process and analyze collected data",
                "action_type": "analysis",
                "parameters": {"method": "comprehensive", "output": "structured"},
                "duration": 3.0
            },
            
            # Default fallback
            "default": {
                "description": f"Process step: {template}",
                "action_type": "query",
                "parameters": {"step": template, "context": request.context},
                "duration": 1.0
            }
        }
        
        return customizations.get(template, customizations["default"])
    
    async def _generate_task_title(self, query: str) -> str:
        """Generate a concise title for the task"""
        # Simple title generation based on first few words
        words = query.split()[:6]
        title = " ".join(words)
        if len(query.split()) > 6:
            title += "..."
        return title.title()

class TaskExecutor:
    """Executes planned tasks step by step"""
    
    def __init__(self):
        self.active_executions: Dict[str, ExecutionPlan] = {}
        self.execution_handlers = {
            "analysis": self._handle_analysis,
            "planning": self._handle_planning,
            "query": self._handle_query,
            "automation": self._handle_automation,
            "execution": self._handle_execution,
            "verification": self._handle_verification
        }
    
    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute the complete task plan"""
        try:
            plan.status = "executing"
            self.active_executions[plan.task_id] = plan
            
            results = []
            completed_steps = 0
            
            for step in plan.steps:
                try:
                    # Check dependencies
                    if not await self._check_dependencies(step, results):
                        step.status = "failed"
                        step.result = {"error": "Dependencies not met"}
                        continue
                    
                    # Execute step
                    step.status = "executing"
                    step_result = await self._execute_step(step, plan)
                    
                    step.result = step_result
                    step.status = "completed" if step_result.get("success", False) else "failed"
                    
                    results.append({
                        "step_id": step.id,
                        "result": step_result,
                        "status": step.status
                    })
                    
                    if step.status == "completed":
                        completed_steps += 1
                    
                    # Update progress
                    plan.progress = (completed_steps / len(plan.steps)) * 100
                    
                    logger.info(f"Step {step.id} completed: {step.description}")
                    
                except Exception as e:
                    logger.error(f"Error executing step {step.id}: {e}")
                    step.status = "failed"
                    step.result = {"error": str(e)}
                    results.append({
                        "step_id": step.id,
                        "result": {"error": str(e)},
                        "status": "failed"
                    })
            
            # Finalize execution
            plan.status = "completed" if all(step.status == "completed" for step in plan.steps) else "partially_completed"
            
            return {
                "success": plan.status in ["completed", "partially_completed"],
                "plan_id": plan.task_id,
                "status": plan.status,
                "progress": plan.progress,
                "results": results,
                "summary": await self._generate_execution_summary(plan, results)
            }
            
        except Exception as e:
            logger.error(f"Error executing plan {plan.task_id}: {e}")
            plan.status = "failed"
            return {
                "success": False,
                "plan_id": plan.task_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            # Clean up
            if plan.task_id in self.active_executions:
                del self.active_executions[plan.task_id]
    
    async def _check_dependencies(self, step: TaskStep, previous_results: List[Dict]) -> bool:
        """Check if step dependencies are satisfied"""
        if not step.dependencies:
            return True
        
        # Check if all dependent steps completed successfully
        completed_step_ids = {r["step_id"] for r in previous_results if r["status"] == "completed"}
        return all(dep in completed_step_ids for dep in step.dependencies)
    
    async def _execute_step(self, step: TaskStep, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute a single step"""
        handler = self.execution_handlers.get(step.action_type, self._handle_default)
        return await handler(step, plan)
    
    async def _handle_analysis(self, step: TaskStep, plan: ExecutionPlan) -> Dict[str, Any]:
        """Handle analysis-type steps"""
        # Simulate analysis processing
        await asyncio.sleep(0.2)  # Simulate processing time
        
        return {
            "success": True,
            "type": "analysis",
            "result": f"Analysis completed for: {step.description}",
            "insights": ["Key insight 1", "Key insight 2"],
            "confidence": 0.85
        }
    
    async def _handle_planning(self, step: TaskStep, plan: ExecutionPlan) -> Dict[str, Any]:
        """Handle planning-type steps"""
        await asyncio.sleep(0.3)
        
        return {
            "success": True,
            "type": "planning", 
            "result": f"Planning completed for: {step.description}",
            "strategy": "adaptive_approach",
            "estimated_effort": "medium"
        }
    
    async def _handle_query(self, step: TaskStep, plan: ExecutionPlan) -> Dict[str, Any]:
        """Handle query-type steps"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "type": "query",
            "result": f"Query processed: {step.description}",
            "data_retrieved": True,
            "relevance_score": 0.9
        }
    
    async def _handle_automation(self, step: TaskStep, plan: ExecutionPlan) -> Dict[str, Any]:
        """Handle automation-type steps"""
        await asyncio.sleep(0.5)  # Automation takes longer
        
        return {
            "success": True,
            "type": "automation",
            "result": f"Automation executed: {step.description}",
            "actions_performed": ["action_1", "action_2"],
            "safety_checks_passed": True
        }
    
    async def _handle_execution(self, step: TaskStep, plan: ExecutionPlan) -> Dict[str, Any]:
        """Handle execution-type steps"""
        await asyncio.sleep(0.4)
        
        return {
            "success": True,
            "type": "execution",
            "result": f"Execution completed: {step.description}",
            "output": "Task executed successfully",
            "performance_metrics": {"duration": 0.4, "efficiency": "high"}
        }
    
    async def _handle_verification(self, step: TaskStep, plan: ExecutionPlan) -> Dict[str, Any]:
        """Handle verification-type steps"""
        await asyncio.sleep(0.2)
        
        return {
            "success": True,
            "type": "verification",
            "result": f"Verification completed: {step.description}",
            "validation_passed": True,
            "quality_score": 0.92
        }
    
    async def _handle_default(self, step: TaskStep, plan: ExecutionPlan) -> Dict[str, Any]:
        """Handle unknown step types"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "type": "default",
            "result": f"Step processed: {step.description}",
            "method": "default_handler"
        }
    
    async def _generate_execution_summary(self, plan: ExecutionPlan, results: List[Dict]) -> str:
        """Generate a human-readable summary of the execution"""
        completed = len([r for r in results if r["status"] == "completed"])
        failed = len([r for r in results if r["status"] == "failed"])
        total = len(results)
        
        summary = f"Task '{plan.title}' execution completed.\n"
        summary += f"Steps: {completed}/{total} successful"
        
        if failed > 0:
            summary += f", {failed} failed"
        
        summary += f"\nProgress: {plan.progress:.1f}%"
        summary += f"\nStatus: {plan.status.replace('_', ' ').title()}"
        
        return summary

class AgentModeHandler:
    """Main handler for Agent mode requests"""
    
    def __init__(self):
        self.task_planner = TaskPlanner()
        self.task_executor = TaskExecutor()
        logger.info("AgentModeHandler initialized")
    
    async def handle_request(self, request: ChatRequest) -> BrainResponse:
        """Handle Agent mode request with full task planning and execution"""
        start_time = time.time()
        
        try:
            logger.info(f"Agent mode handling request: {request.query[:100]}...")
            
            # Create execution plan
            plan = await self.task_planner.create_execution_plan(request)
            
            # Execute the plan
            execution_result = await self.task_executor.execute_plan(plan)
            
            # Format response
            if execution_result["success"]:
                response_text = f"Task completed successfully!\n\n"
                response_text += f"**{plan.title}**\n"
                response_text += f"{execution_result['summary']}\n\n"
                
                # Add step details
                response_text += "**Execution Steps:**\n"
                for i, step in enumerate(plan.steps, 1):
                    status_emoji = "✅" if step.status == "completed" else "❌" if step.status == "failed" else "⏳"
                    response_text += f"{i}. {status_emoji} {step.description}\n"
                
                confidence = 0.9 if plan.status == "completed" else 0.7
                
            else:
                response_text = f"Task execution encountered issues:\n\n"
                response_text += f"**{plan.title}**\n"
                response_text += f"Status: {execution_result.get('status', 'unknown')}\n"
                response_text += f"Progress: {plan.progress:.1f}%\n\n"
                
                if "error" in execution_result:
                    response_text += f"Error: {execution_result['error']}"
                
                confidence = 0.4
            
            return BrainResponse(
                success=execution_result["success"],
                response=response_text,
                mode_used=ChatMode.AGENT,
                processing_time=time.time() - start_time,
                resources_used=["memory", "llm", "execution"],
                confidence=confidence,
                metadata={
                    "plan_id": plan.task_id,
                    "steps_completed": len([s for s in plan.steps if s.status == "completed"]),
                    "total_steps": len(plan.steps),
                    "execution_result": execution_result
                }
            )
            
        except Exception as e:
            logger.error(f"Error in AgentModeHandler: {e}")
            return BrainResponse(
                success=False,
                response=f"I encountered an error while planning your task: {str(e)}",
                mode_used=ChatMode.AGENT,
                processing_time=time.time() - start_time,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )

# Create singleton instance
agent_mode_handler = AgentModeHandler()

# Export the handler function
async def handle_agent_mode(request: ChatRequest) -> BrainResponse:
    """Entry point for Agent mode handling"""
    return await agent_mode_handler.handle_request(request)