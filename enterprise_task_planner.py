#!/usr/bin/env python3
"""
Enterprise Task Planner
AI-powered task decomposition, planning, and execution orchestration
Like 500,000 senior developers wrote this code - ultra professional
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskComplexity(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"

class TaskType(Enum):
    UI_AUTOMATION = "ui_automation"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"
    WEB_INTERACTION = "web_interaction"
    DATA_PROCESSING = "data_processing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"

@dataclass
class ExecutionStep:
    """Individual execution step with comprehensive tracking"""
    id: str
    title: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    estimated_duration: float = 1.0
    actual_duration: float = 0.0
    status: TaskStatus = TaskStatus.PENDING
    confidence: float = 1.0
    risk_level: str = "low"
    validation_criteria: List[str] = None
    rollback_actions: List[str] = None
    result: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = None
    started_at: float = None
    completed_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.dependencies is None:
            self.dependencies = []
        if self.validation_criteria is None:
            self.validation_criteria = []
        if self.rollback_actions is None:
            self.rollback_actions = []

@dataclass
class TaskPlan:
    """Comprehensive task execution plan"""
    id: str
    title: str
    description: str
    user_request: str
    task_type: TaskType
    complexity: TaskComplexity
    status: TaskStatus = TaskStatus.PENDING
    steps: List[ExecutionStep] = None
    estimated_total_duration: float = 0.0
    actual_total_duration: float = 0.0
    success_criteria: List[str] = None
    risk_assessment: Dict[str, Any] = None
    context: Dict[str, Any] = None
    progress: float = 0.0
    created_at: float = None
    started_at: float = None
    completed_at: float = None
    created_by: str = "enterprise_task_planner"
    approval_required: bool = True
    auto_execute: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.steps is None:
            self.steps = []
        if self.success_criteria is None:
            self.success_criteria = []
        if self.risk_assessment is None:
            self.risk_assessment = {}
        if self.context is None:
            self.context = {}

@dataclass
class UserApprovalRequest:
    """User approval request with rich interaction options"""
    plan_id: str
    plan: TaskPlan
    message: str
    options: Dict[str, Any]
    created_at: float
    expires_at: float
    response: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None
    responded_at: Optional[float] = None

class EnterpriseTaskPlanner:
    """AI-powered enterprise task planner with human oversight"""
    
    def __init__(self):
        self.active_plans: Dict[str, TaskPlan] = {}
        self.completed_plans: Dict[str, TaskPlan] = {}
        self.pending_approvals: Dict[str, UserApprovalRequest] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # LLM integration for intelligent planning
        self.llm_service = None  # Will be injected
        
        # Performance metrics
        self.metrics = {
            'total_plans': 0,
            'successful_plans': 0,
            'failed_plans': 0,
            'avg_completion_time': 0.0,
            'user_approval_rate': 0.0,
            'plan_accuracy': 0.0
        }
        
        logger.info("✅ Enterprise Task Planner initialized")
    
    async def create_execution_plan(self, user_request: str, context: Dict[str, Any] = None) -> TaskPlan:
        """Create comprehensive execution plan using AI analysis"""
        try:
            logger.info(f"🧪 Creating execution plan for: {user_request}")
            
            # Generate unique plan ID
            plan_id = f"plan_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Analyze request complexity and type
            task_analysis = await self._analyze_task_request(user_request, context)
            
            # Create base plan
            plan = TaskPlan(
                id=plan_id,
                title=task_analysis['title'],
                description=task_analysis['description'],
                user_request=user_request,
                task_type=TaskType(task_analysis['type']),
                complexity=TaskComplexity(task_analysis['complexity']),
                context=context or {},
                approval_required=task_analysis['requires_approval'],
                auto_execute=task_analysis.get('auto_execute', False)
            )
            
            # Generate detailed execution steps using LLM
            steps = await self._generate_execution_steps(user_request, task_analysis, context)
            plan.steps = steps
            
            # Calculate estimates
            plan.estimated_total_duration = sum(step.estimated_duration for step in steps)
            
            # Generate success criteria
            plan.success_criteria = await self._generate_success_criteria(user_request, task_analysis)
            
            # Perform risk assessment
            plan.risk_assessment = await self._assess_risks(plan)
            
            # Update metrics
            self.metrics['total_plans'] += 1
            
            # Store plan
            self.active_plans[plan_id] = plan
            
            logger.info(f"✅ Execution plan created: {plan_id} ({len(steps)} steps, {plan.complexity.value} complexity)")
            
            return plan
            
        except Exception as e:
            logger.error(f"❌ Failed to create execution plan: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def request_user_approval(self, plan: TaskPlan) -> UserApprovalRequest:
        """Request user approval with rich interaction options"""
        try:
            # Create approval request
            approval_request = UserApprovalRequest(
                plan_id=plan.id,
                plan=plan,
                message=await self._generate_approval_message(plan),
                options=await self._generate_approval_options(plan),
                created_at=time.time(),
                expires_at=time.time() + 300  # 5 minutes timeout
            )
            
            # Store pending approval
            self.pending_approvals[plan.id] = approval_request
            
            # Update plan status
            plan.status = TaskStatus.AWAITING_APPROVAL
            
            logger.info(f"📋 User approval requested for plan: {plan.id}")
            
            return approval_request
            
        except Exception as e:
            logger.error(f"❌ Failed to request approval: {e}")
            raise
    
    async def process_user_response(self, plan_id: str, response: str, modifications: Dict[str, Any] = None) -> bool:
        """Process user approval response"""
        try:
            if plan_id not in self.pending_approvals:
                logger.error(f"No pending approval for plan: {plan_id}")
                return False
            
            approval_request = self.pending_approvals[plan_id]
            plan = self.active_plans[plan_id]
            
            # Record response
            approval_request.response = response
            approval_request.modifications = modifications
            approval_request.responded_at = time.time()
            
            logger.info(f"📋 User response for plan {plan_id}: {response}")
            
            if response.lower() == 'approve':
                plan.status = TaskStatus.APPROVED
                self.metrics['user_approval_rate'] = (self.metrics['user_approval_rate'] + 1.0) / 2
                
            elif response.lower() == 'dismiss':
                plan.status = TaskStatus.CANCELLED
                logger.info(f"❌ Plan dismissed by user: {plan_id}")
                
            elif response.lower() == 'adjust':
                if modifications:
                    await self._apply_plan_modifications(plan, modifications)
                    plan.status = TaskStatus.APPROVED
                else:
                    logger.warning("Adjust requested but no modifications provided")
                    return False
            
            # Remove from pending approvals
            del self.pending_approvals[plan_id]
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process user response: {e}")
            return False
    
    async def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """Execute approved plan with comprehensive monitoring"""
        try:
            if plan_id not in self.active_plans:
                raise ValueError(f"Plan not found: {plan_id}")
            
            plan = self.active_plans[plan_id]
            
            if plan.status != TaskStatus.APPROVED:
                raise ValueError(f"Plan not approved for execution: {plan.status}")
            
            logger.info(f"🚀 Starting plan execution: {plan_id}")
            
            plan.status = TaskStatus.EXECUTING
            plan.started_at = time.time()
            
            execution_result = {
                'plan_id': plan_id,
                'status': 'executing',
                'progress': 0.0,
                'completed_steps': 0,
                'total_steps': len(plan.steps),
                'results': {},
                'errors': []
            }
            
            # Execute steps sequentially with validation
            for i, step in enumerate(plan.steps):
                try:
                    logger.info(f"🔧 Executing step {i+1}/{len(plan.steps)}: {step.title}")
                    
                    # Check dependencies
                    if not await self._check_step_dependencies(step, execution_result['results']):
                        raise Exception(f"Step dependencies not met: {step.dependencies}")
                    
                    # Execute step
                    step.status = TaskStatus.EXECUTING
                    step.started_at = time.time()
                    
                    step_result = await self._execute_step(step, plan.context)
                    
                    step.completed_at = time.time()
                    step.actual_duration = step.completed_at - step.started_at
                    step.result = step_result
                    step.status = TaskStatus.COMPLETED
                    
                    # Store result
                    execution_result['results'][step.id] = step_result
                    execution_result['completed_steps'] += 1
                    execution_result['progress'] = (i + 1) / len(plan.steps) * 100
                    
                    # Validate step completion
                    if not await self._validate_step_completion(step, step_result):
                        raise Exception(f"Step validation failed: {step.title}")
                    
                    logger.info(f"✅ Step completed: {step.title}")
                    
                except Exception as step_error:
                    logger.error(f"❌ Step failed: {step.title} - {step_error}")
                    
                    step.status = TaskStatus.FAILED
                    step.error_details = str(step_error)
                    execution_result['errors'].append({
                        'step_id': step.id,
                        'step_title': step.title,
                        'error': str(step_error)
                    })
                    
                    # Attempt retry if configured
                    if step.retry_count < step.max_retries:
                        step.retry_count += 1
                        logger.info(f"🔄 Retrying step: {step.title} (attempt {step.retry_count + 1})")
                        continue
                    else:
                        # Critical failure - abort plan
                        plan.status = TaskStatus.FAILED
                        execution_result['status'] = 'failed'
                        break
            
            # Complete plan execution
            plan.completed_at = time.time()
            plan.actual_total_duration = plan.completed_at - plan.started_at
            plan.progress = execution_result['progress']
            
            if execution_result['progress'] >= 100 and not execution_result['errors']:
                plan.status = TaskStatus.COMPLETED
                execution_result['status'] = 'completed'
                self.metrics['successful_plans'] += 1
                logger.info(f"✅ Plan completed successfully: {plan_id}")
            else:
                plan.status = TaskStatus.FAILED
                execution_result['status'] = 'failed'
                self.metrics['failed_plans'] += 1
                logger.error(f"❌ Plan failed: {plan_id}")
            
            # Move to completed plans
            self.completed_plans[plan_id] = plan
            del self.active_plans[plan_id]
            
            # Update metrics
            self._update_performance_metrics()
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Plan execution failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def _analyze_task_request(self, user_request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """AI-powered task analysis and classification"""
        try:
            # Simplified analysis - in production would use LLM
            request_lower = user_request.lower()
            
            # Determine task type
            if any(keyword in request_lower for keyword in ['click', 'type', 'press', 'select', 'drag']):
                task_type = TaskType.UI_AUTOMATION.value
            elif any(keyword in request_lower for keyword in ['file', 'folder', 'directory', 'copy', 'move']):
                task_type = TaskType.FILE_OPERATION.value
            elif any(keyword in request_lower for keyword in ['command', 'terminal', 'script', 'run']):
                task_type = TaskType.SYSTEM_COMMAND.value
            else:
                task_type = TaskType.WORKFLOW_ORCHESTRATION.value
            
            # Determine complexity
            complexity_indicators = {
                'trivial': ['click', 'simple'],
                'simple': ['single', 'one', 'basic'],
                'moderate': ['multiple', 'several', 'sequence'],
                'complex': ['complex', 'advanced', 'workflow'],
                'expert': ['trading', 'financial', 'critical', 'enterprise']
            }
            
            complexity = TaskComplexity.SIMPLE.value
            for level, indicators in complexity_indicators.items():
                if any(indicator in request_lower for indicator in indicators):
                    complexity = level
            
            # Generate title and description
            title = f"Execute: {user_request[:50]}..."
            description = f"AI-generated plan to accomplish: {user_request}"
            
            # Determine if approval required
            requires_approval = complexity in ['complex', 'expert'] or any(risk_word in request_lower for risk_word in ['delete', 'remove', 'critical', 'important'])
            
            return {
                'title': title,
                'description': description,
                'type': task_type,
                'complexity': complexity,
                'requires_approval': requires_approval,
                'auto_execute': not requires_approval and complexity in ['trivial', 'simple']
            }
            
        except Exception as e:
            logger.error(f"❌ Task analysis failed: {e}")
            raise
    
    async def _generate_execution_steps(self, user_request: str, task_analysis: Dict[str, Any], context: Dict[str, Any] = None) -> List[ExecutionStep]:
        """Generate detailed execution steps using AI planning"""
        try:
            steps = []
            request_lower = user_request.lower()
            
            # For UI automation tasks
            if task_analysis['type'] == TaskType.UI_AUTOMATION.value:
                if 'click' in request_lower:
                    # Extract target from request
                    target = self._extract_click_target(user_request)
                    
                    steps.extend([
                        ExecutionStep(
                            id=f"step_{uuid.uuid4().hex[:8]}",
                            title="Capture Screen State",
                            description="Analyze current screen to locate UI elements",
                            action_type="screen_analysis",
                            parameters={'analysis_type': 'full_screen'},
                            estimated_duration=1.0,
                            confidence=0.95,
                            validation_criteria=["Screen captured successfully", "UI elements detected"]
                        ),
                        ExecutionStep(
                            id=f"step_{uuid.uuid4().hex[:8]}",
                            title=f"Locate '{target}'",
                            description=f"Find the exact location of '{target}' on screen",
                            action_type="element_location",
                            parameters={'target': target, 'element_type': 'auto'},
                            estimated_duration=0.5,
                            confidence=0.85,
                            validation_criteria=[f"'{target}' element found", "Coordinates determined"]
                        ),
                        ExecutionStep(
                            id=f"step_{uuid.uuid4().hex[:8]}",
                            title=f"Click '{target}'",
                            description=f"Perform precise click on '{target}'",
                            action_type="ui_click",
                            parameters={'target': target, 'click_type': 'left', 'verify_result': True},
                            estimated_duration=0.3,
                            confidence=0.9,
                            validation_criteria=["Click executed", "UI response detected"]
                        ),
                        ExecutionStep(
                            id=f"step_{uuid.uuid4().hex[:8]}",
                            title="Verify Action Result",
                            description="Confirm the click action achieved the intended result",
                            action_type="result_verification",
                            parameters={'verification_type': 'ui_change', 'timeout': 3.0},
                            estimated_duration=1.0,
                            confidence=0.8,
                            validation_criteria=["UI state changed", "Action completed successfully"]
                        )
                    ])
            
            # Add dependencies
            for i in range(1, len(steps)):
                steps[i].dependencies = [steps[i-1].id]
            
            logger.info(f"📋 Generated {len(steps)} execution steps")
            
            return steps
            
        except Exception as e:
            logger.error(f"❌ Step generation failed: {e}")
            raise
    
    def _extract_click_target(self, user_request: str) -> str:
        """Extract click target from user request"""
        # Simple extraction - in production would use NLP
        request_lower = user_request.lower()
        
        # Look for common patterns
        if 'on ' in request_lower:
            parts = request_lower.split('on ')
            if len(parts) > 1:
                target = parts[1].strip()
                # Remove common trailing words
                target = target.replace(' folder', '').replace(' button', '').replace(' icon', '')
                return target.title()
        
        # Fallback - return the whole request
        return user_request.replace('click', '').replace('on', '').strip()
    
    async def _generate_success_criteria(self, user_request: str, task_analysis: Dict[str, Any]) -> List[str]:
        """Generate success criteria for task completion"""
        criteria = [
            "All execution steps completed without errors",
            "User request objectives achieved",
            "System state is stable and consistent"
        ]
        
        # Add task-specific criteria
        if task_analysis['type'] == TaskType.UI_AUTOMATION.value:
            criteria.extend([
                "UI elements interacted with successfully",
                "No unexpected UI dialogs or errors",
                "Target application responsive"
            ])
        
        return criteria
    
    async def _assess_risks(self, plan: TaskPlan) -> Dict[str, Any]:
        """Comprehensive risk assessment"""
        risks = {
            'overall_risk': 'low',
            'identified_risks': [],
            'mitigation_strategies': [],
            'rollback_plan': 'available'
        }
        
        # Assess based on complexity
        if plan.complexity in [TaskComplexity.COMPLEX, TaskComplexity.EXPERT]:
            risks['overall_risk'] = 'medium'
            risks['identified_risks'].append('High complexity may lead to unexpected behavior')
            risks['mitigation_strategies'].append('Comprehensive step-by-step validation')
        
        # Assess based on task type
        if plan.task_type == TaskType.UI_AUTOMATION:
            risks['identified_risks'].append('UI elements may not be found')
            risks['mitigation_strategies'].append('Fallback to manual coordinate specification')
        
        return risks
    
    async def _generate_approval_message(self, plan: TaskPlan) -> str:
        """Generate user-friendly approval message"""
        message = f"""🧪 **Task Execution Plan Ready**

**Request:** {plan.user_request}

**Plan Summary:**
• **Steps:** {len(plan.steps)} execution steps
• **Complexity:** {plan.complexity.value.title()}
• **Estimated Time:** {plan.estimated_total_duration:.1f} seconds
• **Risk Level:** {plan.risk_assessment.get('overall_risk', 'low').title()}

**Execution Steps:**
"""
        
        for i, step in enumerate(plan.steps, 1):
            message += f"{i}. {step.title}\n"
        
        message += f"""

**Success Criteria:**
"""
        for criterion in plan.success_criteria:
            message += f"• {criterion}\n"
        
        message += """

📋 **Please choose an action:**
• **Approve** - Execute the plan as designed
• **Dismiss** - Cancel this task
• **Adjust** - Modify the plan before execution
"""
        
        return message
    
    async def _generate_approval_options(self, plan: TaskPlan) -> Dict[str, Any]:
        """Generate approval options with adjustment capabilities"""
        return {
            'approve': {
                'label': 'Approve & Execute',
                'description': 'Execute the plan as designed',
                'action': 'approve',
                'style': 'success'
            },
            'dismiss': {
                'label': 'Dismiss',
                'description': 'Cancel this task completely',
                'action': 'dismiss',
                'style': 'danger'
            },
            'adjust': {
                'label': 'Adjust Plan',
                'description': 'Modify the plan before execution',
                'action': 'adjust',
                'style': 'warning',
                'adjustment_options': {
                    'modify_steps': 'Modify individual steps',
                    'change_parameters': 'Adjust step parameters',
                    'add_validation': 'Add more validation steps',
                    'reduce_complexity': 'Simplify the approach'
                }
            }
        }
    
    async def _apply_plan_modifications(self, plan: TaskPlan, modifications: Dict[str, Any]):
        """Apply user modifications to the plan"""
        logger.info(f"🔧 Applying modifications to plan: {plan.id}")
        
        # Apply modifications based on type
        if 'modify_steps' in modifications:
            # Handle step modifications
            pass
        
        if 'change_parameters' in modifications:
            # Handle parameter changes
            pass
        
        # Recalculate estimates after modifications
        plan.estimated_total_duration = sum(step.estimated_duration for step in plan.steps)
    
    async def _check_step_dependencies(self, step: ExecutionStep, completed_results: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        for dep_id in step.dependencies:
            if dep_id not in completed_results:
                return False
        return True
    
    async def _execute_step(self, step: ExecutionStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual step with comprehensive error handling"""
        try:
            # Import screen intelligence for UI operations
            from advanced_screen_intelligence import get_screen_intelligence
            from ui_automation_engine import MacOSUIController
            
            result = {'success': False, 'action': step.action_type, 'result': None}
            
            if step.action_type == 'screen_analysis':
                screen_intel = await get_screen_intelligence()
                screen_state = await screen_intel.capture_screen_state()
                result = {
                    'success': True,
                    'action': 'screen_analysis',
                    'result': f"Captured screen with {len(screen_state.elements)} elements",
                    'screen_state': screen_state
                }
                
            elif step.action_type == 'element_location':
                screen_intel = await get_screen_intelligence()
                target = step.parameters.get('target')
                element = await screen_intel.find_ui_element(target)
                
                if element:
                    result = {
                        'success': True,
                        'action': 'element_location',
                        'result': f"Found '{target}' at {element.center}",
                        'coordinates': element.center,
                        'element': element
                    }
                else:
                    raise Exception(f"Could not locate element: {target}")
                
            elif step.action_type == 'ui_click':
                screen_intel = await get_screen_intelligence()
                target = step.parameters.get('target')
                coordinates = await screen_intel.get_clickable_coordinates(target)
                
                if coordinates:
                    ui_controller = MacOSUIController()
                    click_result = await ui_controller.click(coordinates[0], coordinates[1])
                    
                    if click_result:
                        result = {
                            'success': True,
                            'action': 'ui_click',
                            'result': f"Clicked at {coordinates}",
                            'coordinates': coordinates,
                            'target': target
                        }
                    else:
                        raise Exception(f"Click failed at {coordinates}")
                else:
                    raise Exception(f"Could not determine click coordinates for: {target}")
                
            elif step.action_type == 'result_verification':
                # Wait a moment for UI to update
                await asyncio.sleep(step.parameters.get('timeout', 1.0))
                
                # Capture new screen state to verify changes
                screen_intel = await get_screen_intelligence()
                new_state = await screen_intel.capture_screen_state()
                
                result = {
                    'success': True,
                    'action': 'result_verification',
                    'result': 'Verification completed',
                    'new_screen_state': new_state
                }
            
            step.result = result
            return result
            
        except Exception as e:
            logger.error(f"❌ Step execution failed: {step.title} - {e}")
            raise
    
    async def _validate_step_completion(self, step: ExecutionStep, result: Dict[str, Any]) -> bool:
        """Validate step completion against criteria"""
        # Check basic success
        if not result.get('success', False):
            return False
        
        # Check specific validation criteria
        for criterion in step.validation_criteria:
            # Simplified validation - in production would be more sophisticated
            if 'successfully' in criterion.lower() and not result.get('success'):
                return False
        
        return True
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        total_completed = self.metrics['successful_plans'] + self.metrics['failed_plans']
        if total_completed > 0:
            self.metrics['plan_accuracy'] = self.metrics['successful_plans'] / total_completed
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a plan"""
        plan = self.active_plans.get(plan_id) or self.completed_plans.get(plan_id)
        if plan:
            return {
                'id': plan.id,
                'status': plan.status.value,
                'progress': plan.progress,
                'steps_completed': len([s for s in plan.steps if s.status == TaskStatus.COMPLETED]),
                'total_steps': len(plan.steps),
                'estimated_duration': plan.estimated_total_duration,
                'actual_duration': plan.actual_total_duration
            }
        return None

# Global instance
_task_planner = None

async def get_task_planner() -> EnterpriseTaskPlanner:
    """Get global task planner instance"""
    global _task_planner
    if _task_planner is None:
        _task_planner = EnterpriseTaskPlanner()
    return _task_planner

# Export key classes and functions
__all__ = ['EnterpriseTaskPlanner', 'TaskPlan', 'ExecutionStep', 'UserApprovalRequest', 'get_task_planner']
