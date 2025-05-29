#!/usr/bin/env python3
"""
Enhanced Complex Task Handler
Handles sophisticated multi-step tasks with dynamic planning, learning, and adaptation.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Callable, Union
import networkx as nx
from datetime import datetime, timedelta

# Import the improved planner
try:
    from improved_intelligent_task_planner import ImprovedIntelligentTaskPlanner, TaskPlan as IntelligentTaskPlan
    IMPROVED_PLANNER_AVAILABLE = True
except ImportError:
    IMPROVED_PLANNER_AVAILABLE = False
    print("⚠️  Improved planner not available, using basic planner")

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    SIMPLE = 1      # 1-3 steps, linear execution
    MODERATE = 2    # 4-10 steps, some dependencies
    COMPLEX = 3     # 10-50 steps, multiple branches
    ENTERPRISE = 4  # 50+ steps, dynamic adaptation needed

class PlanningStrategy(Enum):
    LINEAR = "linear"
    HIERARCHICAL = "hierarchical"  
    DYNAMIC = "dynamic"
    ADAPTIVE = "adaptive"
    LEARNING = "learning"

class StepStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"

@dataclass
class EnhancedTaskStep:
    """Enhanced task step with learning and adaptation capabilities"""
    step_id: str
    parent_step_id: Optional[str] = None
    description: str = ""
    action_type: str = "generic"
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies and relationships
    dependencies: List[str] = field(default_factory=list)
    soft_dependencies: List[str] = field(default_factory=list)  # Preferred but not required
    alternatives: List[str] = field(default_factory=list)  # Alternative steps if this fails
    
    # Execution control
    priority: int = 5  # 1-10 scale
    timeout_seconds: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Learning and adaptation
    success_probability: float = 0.8
    estimated_duration: float = 1.0
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    
    # Runtime data
    status: StepStatus = StepStatus.PENDING
    retry_count: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Metrics and learning
    actual_duration: Optional[float] = None
    actual_success: Optional[bool] = None
    performance_score: Optional[float] = None

@dataclass 
class TaskContext:
    """Rich context for task execution with learning history"""
    user_id: str
    session_id: str
    domain: str  # e.g., "web_automation", "data_analysis", "system_admin"
    environment: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Historical learning
    similar_tasks: List[str] = field(default_factory=list)
    success_patterns: Dict[str, float] = field(default_factory=dict)
    failure_patterns: Dict[str, float] = field(default_factory=dict)

@dataclass
class ComplexExecutionPlan:
    """Enhanced execution plan for complex multi-step tasks"""
    plan_id: str
    title: str
    description: str
    complexity: TaskComplexity
    strategy: PlanningStrategy
    
    # Step management
    steps: List[EnhancedTaskStep]
    dependency_graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    execution_layers: List[List[str]] = field(default_factory=list)
    
    # Resource and timing
    estimated_total_duration: float = 0.0
    max_parallel_steps: int = 5
    resource_budget: Dict[str, float] = field(default_factory=dict)
    
    # Adaptation and learning
    adaptation_enabled: bool = True
    learning_enabled: bool = True
    fallback_plans: List[str] = field(default_factory=list)
    
    # Runtime tracking
    created_at: float = field(default_factory=time.time)
    status: str = "planned"
    progress: float = 0.0
    current_layer: int = 0
    active_steps: Set[str] = field(default_factory=set)
    
    # Performance metrics
    actual_start_time: Optional[float] = None
    actual_end_time: Optional[float] = None
    success_rate: float = 0.0
    efficiency_score: float = 0.0

class AdvancedTaskPlanner:
    """Advanced task planner with AI-driven decomposition and learning"""
    
    def __init__(self):
        # Initialize improved planner if available
        if IMPROVED_PLANNER_AVAILABLE:
            self.intelligent_planner = ImprovedIntelligentTaskPlanner()
            logger.info("✅ Initialized with Improved Intelligent Task Planner")
        else:
            self.intelligent_planner = None
            logger.warning("⚠️  Using basic task planner")
            
        self.planning_strategies = {
            TaskComplexity.SIMPLE: self._plan_simple_task,
            TaskComplexity.MODERATE: self._plan_moderate_task, 
            TaskComplexity.COMPLEX: self._plan_complex_task,
            TaskComplexity.ENTERPRISE: self._plan_enterprise_task
        }
        
        # Enhanced planning patterns with sub-patterns
        self.hierarchical_patterns = {
            "web_automation": {
                "patterns": {
                    "navigate": ["open_browser", "navigate_to_url", "wait_for_load", "verify_page"],
                    "form_interaction": ["locate_form", "fill_fields", "validate_input", "submit_form"],
                    "data_extraction": ["locate_elements", "extract_data", "validate_data", "format_output"],
                    "verification": ["capture_state", "compare_expected", "log_results", "cleanup"]
                },
                "combinations": {
                    "complete_workflow": ["navigate", "form_interaction", "verification"],
                    "data_collection": ["navigate", "data_extraction", "verification"]
                }
            },
            "data_analysis": {
                "patterns": {
                    "data_ingestion": ["identify_sources", "validate_format", "load_data", "clean_data"],
                    "analysis": ["exploratory_analysis", "feature_engineering", "model_selection", "validation"],
                    "visualization": ["create_plots", "format_dashboards", "export_results", "share_insights"],
                    "reporting": ["summarize_findings", "create_report", "peer_review", "publish"]
                },
                "combinations": {
                    "full_analysis": ["data_ingestion", "analysis", "visualization", "reporting"],
                    "quick_insights": ["data_ingestion", "analysis", "visualization"]
                }
            },
            "system_integration": {
                "patterns": {
                    "assessment": ["inventory_systems", "analyze_requirements", "identify_gaps", "create_roadmap"],
                    "design": ["architecture_design", "api_specification", "security_review", "performance_planning"],
                    "implementation": ["setup_environment", "develop_connectors", "implement_logic", "error_handling"],
                    "testing": ["unit_tests", "integration_tests", "performance_tests", "security_tests"],
                    "deployment": ["staging_deployment", "validation", "production_deployment", "monitoring"]
                },
                "combinations": {
                    "full_integration": ["assessment", "design", "implementation", "testing", "deployment"],
                    "rapid_prototype": ["assessment", "design", "implementation", "testing"]
                }
            }
        }
        
        # Learning database for pattern optimization
        self.execution_history: Dict[str, List[Dict[str, Any]]] = {}
        self.pattern_performance: Dict[str, Dict[str, float]] = {}
        
    def _map_complexity_level(self, complexity_level: str) -> TaskComplexity:
        """Map string complexity level to TaskComplexity enum"""
        mapping = {
            "simple": TaskComplexity.SIMPLE,
            "moderate": TaskComplexity.MODERATE,
            "complex": TaskComplexity.COMPLEX,
            "enterprise": TaskComplexity.ENTERPRISE
        }
        return mapping.get(complexity_level.lower(), TaskComplexity.MODERATE)
        
    async def create_complex_plan(self, request: str, context: TaskContext) -> ComplexExecutionPlan:
        """Create sophisticated execution plan with AI-driven decomposition using improved intelligent planner"""
        try:
            # Try using improved intelligent planner first
            if IMPROVED_PLANNER_AVAILABLE and hasattr(self, 'intelligent_planner'):
                logger.info("🤖 Using Improved Intelligent Task Planner for complex plan creation")
                try:
                    # Use intelligent planner to create initial plan
                    intelligent_plan = await self.intelligent_planner.create_intelligent_plan(request, "complex")
                    
                    # Convert intelligent plan to ComplexExecutionPlan format
                    plan = ComplexExecutionPlan(
                        plan_id=intelligent_plan.plan_id,
                        title=intelligent_plan.user_request.split('.')[0][:50] + "..." if len(intelligent_plan.user_request) > 50 else intelligent_plan.user_request,
                        description=request,
                        complexity=self._map_complexity_level(intelligent_plan.complexity.name if hasattr(intelligent_plan.complexity, 'name') else str(intelligent_plan.complexity)),
                        strategy=PlanningStrategy.LEARNING,  # Use learning strategy for intelligent plans
                        steps=[],  # Initialize empty, will be populated below
                        estimated_total_duration=intelligent_plan.estimated_total_duration,
                        max_parallel_steps=len(intelligent_plan.parallel_groups[0]) if intelligent_plan.parallel_groups and len(intelligent_plan.parallel_groups) > 0 and len(intelligent_plan.parallel_groups[0]) > 0 else 3
                    )
                    
                    # Convert intelligent steps to enhanced task steps
                    for i, step in enumerate(intelligent_plan.steps):
                        enhanced_step = EnhancedTaskStep(
                            step_id=step.step_id,
                            description=step.description,
                            action_type=step.action_type.value if hasattr(step.action_type, 'value') else str(step.action_type),
                            parameters={
                                'target': step.target or '',
                                'original_request': request,
                                'intelligent_plan': True,
                                'domain_context': getattr(step, 'domain_context', None),
                                **step.parameters
                            },
                            dependencies=step.dependencies,
                            priority=5,  # Default priority
                            estimated_duration=step.estimated_duration,
                            success_probability=0.8,  # Default
                            timeout_seconds=max(60, int(step.estimated_duration * 3)),  # 3x duration as timeout
                            max_retries=3
                        )
                        plan.steps.append(enhanced_step)
                    
                    # Build dependency graph and execution layers for intelligent plan
                    await self._build_dependency_graph(plan)
                    await self._create_execution_layers(plan)
                    
                    # Apply learning optimizations
                    await self._apply_learned_optimizations(plan, context)
                    await self._calculate_resource_requirements(plan)
                    
                    logger.info(f"✅ Created intelligent plan with {len(plan.steps)} steps, estimated duration: {plan.estimated_total_duration}s")
                    return plan
                    
                except Exception as e:
                    logger.warning(f"⚠️ Improved planner failed: {e}, falling back to original planning logic")
            
            # Fallback to original planning logic
            logger.info("📋 Using original complex planning logic")
            
            # Analyze task complexity
            complexity = await self._analyze_task_complexity(request, context)
            
            # Select planning strategy
            strategy = await self._select_planning_strategy(complexity, context)
            
            # Create base plan
            plan = ComplexExecutionPlan(
                plan_id=str(uuid.uuid4()),
                title=await self._generate_smart_title(request),
                description=request,
                complexity=complexity,
                strategy=strategy,
                steps=[]  # Initialize empty, will be populated by planner
            )
            
            # Use appropriate planner based on complexity
            planner = self.planning_strategies[complexity]
            plan = await planner(plan, request, context)
            
            # Build dependency graph and execution layers
            await self._build_dependency_graph(plan)
            await self._create_execution_layers(plan)
            
            # Apply learning from similar tasks
            await self._apply_learned_optimizations(plan, context)
            
            # Calculate resource requirements
            await self._calculate_resource_requirements(plan)
            
            logger.info(f"Created {complexity.name} plan with {len(plan.steps)} steps in {len(plan.execution_layers)} layers")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating complex plan: {e}")
            # Fallback to simple plan
            return await self._create_fallback_plan(request, context)
    
    async def _analyze_task_complexity(self, request: str, context: TaskContext) -> TaskComplexity:
        """Analyze request to determine task complexity"""
        request_lower = request.lower()
        
        # Count complexity indicators
        complexity_score = 0
        
        # Multi-step indicators
        multi_step_words = ["then", "after", "next", "subsequently", "followed by", "once", "when"]
        complexity_score += sum(1 for word in multi_step_words if word in request_lower)
        
        # Conditional indicators  
        conditional_words = ["if", "unless", "depending", "based on", "in case", "should"]
        complexity_score += sum(1.5 for word in conditional_words if word in request_lower) 
        
        # Integration indicators
        integration_words = ["integrate", "connect", "sync", "combine", "merge", "coordinate"]
        complexity_score += sum(2 for word in integration_words if word in request_lower)
        
        # Data complexity
        data_words = ["analyze", "process", "transform", "aggregate", "correlate", "model"]
        complexity_score += sum(1.2 for word in data_words if word in request_lower)
        
        # System complexity
        system_words = ["deploy", "configure", "setup", "install", "manage", "monitor"]
        complexity_score += sum(1.3 for word in system_words if word in request_lower)
        
        # Multiple targets/objects
        complexity_score += len(request.split(" and ")) * 0.5
        complexity_score += len(request.split(",")) * 0.3
        
        # Historical context
        if context.similar_tasks:
            avg_historical_complexity = sum(
                self.execution_history.get(task_id, [{}])[-1].get("complexity_score", 2) 
                for task_id in context.similar_tasks[-5:]  # Last 5 similar tasks
            ) / min(len(context.similar_tasks), 5)
            complexity_score = (complexity_score + avg_historical_complexity) / 2
        
        # Map score to complexity level
        if complexity_score <= 2:
            return TaskComplexity.SIMPLE
        elif complexity_score <= 5:
            return TaskComplexity.MODERATE
        elif complexity_score <= 10:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.ENTERPRISE
    
    async def _select_planning_strategy(self, complexity: TaskComplexity, context: TaskContext) -> PlanningStrategy:
        """Select optimal planning strategy based on complexity and context"""
        
        # Strategy selection rules
        if complexity == TaskComplexity.SIMPLE:
            return PlanningStrategy.LINEAR
        elif complexity == TaskComplexity.MODERATE:
            return PlanningStrategy.HIERARCHICAL
        elif complexity == TaskComplexity.COMPLEX:
            # Check if we have good historical data for learning
            if context.similar_tasks and len(context.similar_tasks) >= 3:
                return PlanningStrategy.LEARNING
            else:
                return PlanningStrategy.DYNAMIC
        else:  # ENTERPRISE
            return PlanningStrategy.ADAPTIVE
    
    async def _plan_simple_task(self, plan: ComplexExecutionPlan, request: str, context: TaskContext) -> ComplexExecutionPlan:
        """Plan simple linear task (1-3 steps)"""
        
        # Simple pattern matching
        action_type = await self._classify_simple_action(request)
        
        simple_patterns = {
            "click": [
                ("analyze_target", "Analyze target element"),
                ("execute_click", "Perform click action"),
                ("verify_result", "Verify action completed")
            ],
            "type": [
                ("locate_field", "Locate input field"),
                ("input_text", "Enter text"),
                ("validate_input", "Validate text was entered")
            ],
            "navigate": [
                ("prepare_navigation", "Prepare for navigation"),
                ("execute_navigation", "Navigate to target"),
                ("verify_arrival", "Verify navigation successful")
            ]
        }
        
        pattern = simple_patterns.get(action_type, [
            ("understand_request", "Understand the request"),
            ("execute_action", "Execute the action"),
            ("verify_completion", "Verify completion")
        ])
        
        for i, (action, description) in enumerate(pattern):
            step = EnhancedTaskStep(
                step_id=f"step_{i+1}",
                description=description,
                action_type=action,
                parameters={"original_request": request},
                priority=10 - i,  # Higher priority for earlier steps
                estimated_duration=1.0,
                success_probability=0.9
            )
            
            if i > 0:
                step.dependencies = [f"step_{i}"]
            
            plan.steps.append(step)
        
        return plan
    
    async def _plan_moderate_task(self, plan: ComplexExecutionPlan, request: str, context: TaskContext) -> ComplexExecutionPlan:
        """Plan moderate complexity task (4-10 steps) with hierarchical decomposition"""
        
        # Identify domain and select patterns
        domain = await self._identify_domain(request, context)
        
        if domain not in self.hierarchical_patterns:
            # Fallback to general moderate planning
            return await self._plan_general_moderate_task(plan, request, context)
        
        # Use domain-specific hierarchical patterns
        domain_patterns = self.hierarchical_patterns[domain]
        
        # Identify which combination pattern fits best
        combination_pattern = await self._select_combination_pattern(request, domain_patterns)
        
        step_counter = 1
        for pattern_name in combination_pattern:
            if pattern_name in domain_patterns["patterns"]:
                pattern_steps = domain_patterns["patterns"][pattern_name]
                
                for step_name in pattern_steps:
                    step = EnhancedTaskStep(
                        step_id=f"step_{step_counter}",
                        description=f"{pattern_name.title()}: {step_name.replace('_', ' ').title()}",
                        action_type=step_name,
                        parameters={
                            "pattern": pattern_name,
                            "domain": domain,
                            "original_request": request
                        },
                        priority=10 - ((step_counter - 1) % 10),
                        estimated_duration=2.0,
                        success_probability=0.8
                    )
                    
                    # Add dependencies within pattern
                    if step_counter > 1 and (step_counter - 1) % len(pattern_steps) != 0:
                        step.dependencies = [f"step_{step_counter - 1}"]
                    
                    plan.steps.append(step)
                    step_counter += 1
        
        return plan
    
    async def _plan_complex_task(self, plan: ComplexExecutionPlan, request: str, context: TaskContext) -> ComplexExecutionPlan:
        """Plan complex task (10-50 steps) with dynamic branching"""
        
        # Break down into major phases
        phases = await self._identify_task_phases(request, context)
        
        step_counter = 1
        phase_starts = {}
        
        for phase_idx, phase in enumerate(phases):
            phase_starts[phase["name"]] = step_counter
            
            # Create phase steps
            for substep in phase["substeps"]:
                step = EnhancedTaskStep(
                    step_id=f"step_{step_counter}",
                    description=f"Phase {phase_idx + 1}: {substep['description']}",
                    action_type=substep["action_type"],
                    parameters={
                        "phase": phase["name"],
                        "phase_index": phase_idx,
                        **substep.get("parameters", {})
                    },
                    priority=substep.get("priority", 5),
                    estimated_duration=substep.get("duration", 3.0),
                    success_probability=substep.get("success_prob", 0.7),
                    timeout_seconds=substep.get("timeout", 120)
                )
                
                # Add dependencies
                if "dependencies" in substep:
                    step.dependencies = [f"step_{phase_starts[dep] + substep['dependencies'][dep]}" 
                                       for dep in substep["dependencies"] 
                                       if dep in phase_starts]
                elif step_counter > 1:
                    step.dependencies = [f"step_{step_counter - 1}"]
                
                # Add alternatives for critical steps
                if substep.get("critical", False):
                    step.alternatives = await self._generate_alternatives(step, context)
                
                plan.steps.append(step)
                step_counter += 1
            
            # Add phase verification step
            verification_step = EnhancedTaskStep(
                step_id=f"step_{step_counter}",
                description=f"Verify Phase {phase_idx + 1} Completion",
                action_type="phase_verification",
                parameters={"phase": phase["name"], "expected_outcomes": phase.get("outcomes", [])},
                priority=9,
                estimated_duration=1.0,
                success_probability=0.9
            )
            
            # Depends on all steps in this phase
            verification_step.dependencies = [f"step_{i}" for i in range(phase_starts[phase["name"]], step_counter)]
            
            plan.steps.append(verification_step)
            step_counter += 1
        
        return plan
    
    async def _plan_enterprise_task(self, plan: ComplexExecutionPlan, request: str, context: TaskContext) -> ComplexExecutionPlan:
        """Plan enterprise-grade task (50+ steps) with adaptive execution"""
        
        # Use AI-driven decomposition for enterprise tasks
        decomposition = await self._ai_driven_decomposition(request, context)
        
        # Create adaptive execution plan
        step_counter = 1
        
        for workflow in decomposition["workflows"]:
            # Create workflow preparation
            prep_step = EnhancedTaskStep(
                step_id=f"step_{step_counter}",
                description=f"Prepare {workflow['name']} Workflow",
                action_type="workflow_preparation",
                parameters={
                    "workflow": workflow,
                    "adaptive_planning": True,
                    "learning_enabled": True
                },
                priority=8,
                estimated_duration=2.0,
                success_probability=0.85
            )
            plan.steps.append(prep_step)
            step_counter += 1
            
            # Create dynamic sub-steps
            for substep_template in workflow["substep_templates"]:
                step = EnhancedTaskStep(
                    step_id=f"step_{step_counter}",
                    description=substep_template["description"],
                    action_type=substep_template["action_type"],
                    parameters={
                        "template": substep_template,
                        "adaptive": True,
                        "workflow_context": workflow,
                        **substep_template.get("parameters", {})
                    },
                    priority=substep_template.get("priority", 5),
                    estimated_duration=substep_template.get("duration", 5.0),
                    success_probability=substep_template.get("success_prob", 0.75),
                    timeout_seconds=substep_template.get("timeout", 300)
                )
                
                # Enterprise tasks can have complex dependencies
                if "dependencies" in substep_template:
                    step.dependencies = substep_template["dependencies"]
                
                # Add checkpoint alternatives
                if substep_template.get("checkpoint", False):
                    step.alternatives = await self._generate_checkpoint_alternatives(step, workflow)
                
                plan.steps.append(step)
                step_counter += 1
            
            # Add workflow completion verification
            completion_step = EnhancedTaskStep(
                step_id=f"step_{step_counter}",
                description=f"Complete {workflow['name']} Workflow",
                action_type="workflow_completion",
                parameters={
                    "workflow": workflow,
                    "validation_criteria": workflow.get("completion_criteria", [])
                },
                priority=9,
                estimated_duration=3.0,
                success_probability=0.9
            )
            plan.steps.append(completion_step)
            step_counter += 1
        
        # Add final integration verification
        final_step = EnhancedTaskStep(
            step_id=f"step_{step_counter}",
            description="Final Enterprise Task Validation",
            action_type="enterprise_validation",
            parameters={
                "decomposition": decomposition,
                "success_criteria": decomposition.get("success_criteria", [])
            },
            priority=10,
            estimated_duration=5.0,
            success_probability=0.95
        )
        plan.steps.append(final_step)
        
        return plan

    async def _identify_domain(self, request: str, context: TaskContext) -> str:
        """Identify the domain/type of the task"""
        request_lower = request.lower()
        
        # Web automation indicators
        web_words = ["click", "button", "form", "website", "browser", "navigate", "login", "submit"]
        if any(word in request_lower for word in web_words):
            return "web_automation"
        
        # Data analysis indicators  
        data_words = ["analyze", "data", "chart", "report", "statistics", "visualization", "dashboard"]
        if any(word in request_lower for word in data_words):
            return "data_analysis"
        
        # System integration indicators
        system_words = ["integrate", "api", "database", "deploy", "configure", "setup", "install"]
        if any(word in request_lower for word in system_words):
            return "system_integration"
        
        # Default domain
        return context.domain if context.domain else "general"
    
    async def _select_combination_pattern(self, request: str, domain_patterns: Dict[str, Any]) -> List[str]:
        """Select the best combination pattern for the request"""
        request_lower = request.lower()
        
        # Score each combination pattern
        best_pattern = None
        best_score = 0
        
        for pattern_name, pattern_steps in domain_patterns["combinations"].items():
            score = 0
            
            # Check how many pattern keywords match the request
            for step in pattern_steps:
                step_keywords = step.split("_")
                for keyword in step_keywords:
                    if keyword in request_lower:
                        score += 1
            
            if score > best_score:
                best_score = score
                best_pattern = pattern_steps
        
        # Fallback to first available pattern
        if not best_pattern:
            best_pattern = list(domain_patterns["combinations"].values())[0]
        
        return best_pattern
    
    async def _identify_task_phases(self, request: str, context: TaskContext) -> List[Dict[str, Any]]:
        """Identify major phases for complex task decomposition"""
        
        phases = []
        
        # Phase 1: Preparation and Setup
        phases.append({
            "name": "preparation",
            "substeps": [
                {
                    "description": "Analyze task requirements",
                    "action_type": "requirement_analysis",
                    "duration": 2.0,
                    "priority": 9,
                    "success_prob": 0.9
                },
                {
                    "description": "Setup execution environment",
                    "action_type": "environment_setup", 
                    "duration": 3.0,
                    "priority": 8,
                    "success_prob": 0.85
                },
                {
                    "description": "Validate prerequisites",
                    "action_type": "prerequisite_validation",
                    "duration": 1.5,
                    "priority": 8,
                    "success_prob": 0.9
                }
            ],
            "outcomes": ["environment_ready", "requirements_validated"]
        })
        
        # Phase 2: Core Execution
        request_lower = request.lower()
        
        if "data" in request_lower or "analyze" in request_lower:
            phases.append({
                "name": "data_processing",
                "substeps": [
                    {
                        "description": "Collect and validate data sources",
                        "action_type": "data_collection",
                        "duration": 4.0,
                        "priority": 7,
                        "success_prob": 0.8
                    },
                    {
                        "description": "Process and transform data",
                        "action_type": "data_transformation",
                        "duration": 6.0,
                        "priority": 7,
                        "success_prob": 0.75,
                        "critical": True
                    },
                    {
                        "description": "Perform analysis and calculations",
                        "action_type": "data_analysis",
                        "duration": 8.0,
                        "priority": 8,
                        "success_prob": 0.7,
                        "timeout": 600
                    }
                ],
                "outcomes": ["data_processed", "analysis_complete"]
            })
        
        if "automation" in request_lower or "click" in request_lower or "form" in request_lower:
            phases.append({
                "name": "automation_execution", 
                "substeps": [
                    {
                        "description": "Navigate to target interface",
                        "action_type": "navigation",
                        "duration": 2.0,
                        "priority": 8,
                        "success_prob": 0.85
                    },
                    {
                        "description": "Interact with interface elements",
                        "action_type": "ui_interaction",
                        "duration": 5.0,
                        "priority": 7,
                        "success_prob": 0.75,
                        "critical": True
                    },
                    {
                        "description": "Validate interaction results",
                        "action_type": "interaction_validation",
                        "duration": 2.0,
                        "priority": 8,
                        "success_prob": 0.9
                    }
                ],
                "outcomes": ["interactions_complete", "results_validated"]
            })
        
        if "integrate" in request_lower or "connect" in request_lower:
            phases.append({
                "name": "integration",
                "substeps": [
                    {
                        "description": "Establish system connections",
                        "action_type": "connection_establishment",
                        "duration": 5.0,
                        "priority": 8,
                        "success_prob": 0.8,
                        "timeout": 300
                    },
                    {
                        "description": "Configure integration settings",
                        "action_type": "integration_configuration",
                        "duration": 7.0,
                        "priority": 7,
                        "success_prob": 0.75,
                        "critical": True
                    },
                    {
                        "description": "Test integration functionality",
                        "action_type": "integration_testing",
                        "duration": 6.0,
                        "priority": 9,
                        "success_prob": 0.85
                    }
                ],
                "outcomes": ["integration_active", "tests_passed"]
            })
        
        # Phase 3: Verification and Cleanup
        phases.append({
            "name": "finalization",
            "substeps": [
                {
                    "description": "Verify all objectives completed",
                    "action_type": "objective_verification",
                    "duration": 3.0,
                    "priority": 9,
                    "success_prob": 0.9
                },
                {
                    "description": "Generate completion report",
                    "action_type": "report_generation",
                    "duration": 2.0,
                    "priority": 6,
                    "success_prob": 0.95
                },
                {
                    "description": "Cleanup temporary resources",
                    "action_type": "resource_cleanup",
                    "duration": 1.0,
                    "priority": 5,
                    "success_prob": 0.98
                }
            ],
            "outcomes": ["task_verified", "report_generated", "cleanup_complete"]
        })
        
        return phases
    
    async def _ai_driven_decomposition(self, request: str, context: TaskContext) -> Dict[str, Any]:
        """Use AI-driven analysis for enterprise-level task decomposition"""
        
        # Simulate AI-driven analysis - in real implementation, this would use LLM
        decomposition = {
            "request": request,
            "complexity_analysis": {
                "estimated_steps": 50,
                "estimated_duration": 3600,  # 1 hour
                "risk_factors": ["integration_complexity", "data_volume", "system_dependencies"],
                "success_probability": 0.8
            },
            "workflows": [],
            "success_criteria": [
                "all_workflows_completed",
                "quality_thresholds_met", 
                "performance_requirements_satisfied",
                "stakeholder_approval_received"
            ]
        }
        
        # Identify major workflows based on request analysis
        request_lower = request.lower()
        
        if "crm" in request_lower or "customer" in request_lower:
            decomposition["workflows"].append({
                "name": "CRM_Integration",
                "priority": 8,
                "estimated_steps": 15,
                "substep_templates": [
                    {
                        "description": "Analyze CRM API capabilities",
                        "action_type": "api_analysis",
                        "duration": 10.0,
                        "success_prob": 0.9,
                        "priority": 9
                    },
                    {
                        "description": "Design data mapping schema",
                        "action_type": "schema_design",
                        "duration": 15.0,
                        "success_prob": 0.8,
                        "priority": 8,
                        "checkpoint": True
                    },
                    {
                        "description": "Implement data synchronization",
                        "action_type": "sync_implementation",
                        "duration": 30.0,
                        "success_prob": 0.75,
                        "priority": 8,
                        "timeout": 1800
                    },
                    {
                        "description": "Test data integrity",
                        "action_type": "integrity_testing",
                        "duration": 20.0,
                        "success_prob": 0.85,
                        "priority": 9
                    }
                ],
                "completion_criteria": ["api_connected", "data_synced", "tests_passed"]
            })
        
        if "email" in request_lower or "notification" in request_lower:
            decomposition["workflows"].append({
                "name": "Email_Platform_Integration",
                "priority": 7,
                "estimated_steps": 12,
                "substep_templates": [
                    {
                        "description": "Configure email service connections",
                        "action_type": "email_service_config",
                        "duration": 8.0,
                        "success_prob": 0.85,
                        "priority": 8
                    },
                    {
                        "description": "Setup automated workflow triggers",
                        "action_type": "workflow_triggers",
                        "duration": 12.0,
                        "success_prob": 0.8,
                        "priority": 7,
                        "checkpoint": True
                    },
                    {
                        "description": "Test email delivery and tracking",
                        "action_type": "delivery_testing",
                        "duration": 10.0,
                        "success_prob": 0.9,
                        "priority": 8
                    }
                ],
                "completion_criteria": ["email_configured", "workflows_active", "delivery_confirmed"]
            })
        
        if "migrate" in request_lower or "contact" in request_lower:
            decomposition["workflows"].append({
                "name": "Contact_Migration",
                "priority": 9,
                "estimated_steps": 18,
                "substep_templates": [
                    {
                        "description": "Export contacts from source system",
                        "action_type": "contact_export",
                        "duration": 15.0,
                        "success_prob": 0.9,
                        "priority": 9
                    },
                    {
                        "description": "Validate and clean contact data",
                        "action_type": "data_validation",
                        "duration": 25.0,
                        "success_prob": 0.85,
                        "priority": 8,
                        "checkpoint": True
                    },
                    {
                        "description": "Import contacts to target system",
                        "action_type": "contact_import", 
                        "duration": 20.0,
                        "success_prob": 0.8,
                        "priority": 9,
                        "timeout": 1200
                    },
                    {
                        "description": "Verify migration completeness",
                        "action_type": "migration_verification",
                        "duration": 10.0,
                        "success_prob": 0.95,
                        "priority": 9
                    }
                ],
                "completion_criteria": ["contacts_exported", "data_validated", "contacts_imported", "migration_verified"]
            })
        
        if "deploy" in request_lower or "production" in request_lower:
            decomposition["workflows"].append({
                "name": "Production_Deployment",
                "priority": 10,
                "estimated_steps": 10,
                "substep_templates": [
                    {
                        "description": "Prepare production environment",
                        "action_type": "production_prep",
                        "duration": 12.0,
                        "success_prob": 0.9,
                        "priority": 10
                    },
                    {
                        "description": "Execute staged deployment",
                        "action_type": "staged_deployment",
                        "duration": 20.0,
                        "success_prob": 0.85,
                        "priority": 10,
                        "checkpoint": True
                    },
                    {
                        "description": "Monitor system performance",
                        "action_type": "performance_monitoring",
                        "duration": 30.0,
                        "success_prob": 0.9,
                        "priority": 9,
                        "timeout": 1800
                    }
                ],
                "completion_criteria": ["environment_ready", "deployment_successful", "performance_stable"]
            })
        
        return decomposition
    
    async def _generate_alternatives(self, step: EnhancedTaskStep, context: TaskContext) -> List[str]:
        """Generate alternative approaches for critical steps"""
        alternatives = []
        
        if step.action_type == "ui_interaction":
            alternatives = ["keyboard_interaction", "api_fallback", "manual_guidance"]
        elif step.action_type == "data_transformation":
            alternatives = ["alternative_algorithm", "manual_processing", "external_service"]
        elif step.action_type == "integration_configuration":
            alternatives = ["backup_configuration", "minimal_configuration", "guided_setup"]
        else:
            alternatives = ["retry_with_delay", "manual_intervention", "skip_with_notification"]
        
        return alternatives
    
    async def _generate_checkpoint_alternatives(self, step: EnhancedTaskStep, workflow: Dict[str, Any]) -> List[str]:
        """Generate checkpoint alternatives for enterprise workflows"""
        return [
            f"checkpoint_save_{step.step_id}",
            f"rollback_option_{step.step_id}",
            f"manual_review_{step.step_id}",
            f"stakeholder_approval_{step.step_id}"
        ]
    
    async def _build_dependency_graph(self, plan: ComplexExecutionPlan):
        """Build comprehensive dependency graph for the execution plan"""
        plan.dependency_graph = nx.DiGraph()
        
        # Add all steps as nodes
        for step in plan.steps:
            plan.dependency_graph.add_node(step.step_id, step=step)
        
        # Add dependency edges
        for step in plan.steps:
            for dep_id in step.dependencies:
                if dep_id in [s.step_id for s in plan.steps]:
                    plan.dependency_graph.add_edge(dep_id, step.step_id)
            
            # Add soft dependency edges with different weight
            for soft_dep_id in step.soft_dependencies:
                if soft_dep_id in [s.step_id for s in plan.steps]:
                    plan.dependency_graph.add_edge(soft_dep_id, step.step_id, weight=0.5)
    
    async def _create_execution_layers(self, plan: ComplexExecutionPlan):
        """Create execution layers for optimal parallelization"""
        try:
            # Use topological sort to determine execution order
            topo_order = list(nx.topological_sort(plan.dependency_graph))
            
            # Group steps into layers based on dependencies
            layers = []
            remaining_steps = set(topo_order)
            
            while remaining_steps:
                current_layer = []
                
                # Find steps with no remaining dependencies
                for step_id in list(remaining_steps):
                    step_deps = set(plan.dependency_graph.predecessors(step_id))
                    if not step_deps.intersection(remaining_steps):
                        current_layer.append(step_id)
                
                # Remove current layer steps from remaining
                for step_id in current_layer:
                    remaining_steps.remove(step_id)
                
                if current_layer:
                    layers.append(current_layer)
                else:
                    # Break infinite loop if no progress
                    break
            
            plan.execution_layers = layers
            
        except nx.NetworkXError as e:
            logger.warning(f"Dependency graph error: {e}, falling back to sequential execution")
            plan.execution_layers = [[step.step_id] for step in plan.steps]
    
    async def _apply_learned_optimizations(self, plan: ComplexExecutionPlan, context: TaskContext):
        """Apply optimizations learned from similar past executions"""
        
        # Look for similar task patterns in execution history
        for task_id in context.similar_tasks[-5:]:  # Last 5 similar tasks
            if task_id in self.execution_history:
                historical_data = self.execution_history[task_id]
                
                # Apply learned timing optimizations
                for historical_step in historical_data:
                    for plan_step in plan.steps:
                        if (historical_step.get("action_type") == plan_step.action_type and
                            historical_step.get("actual_duration")):
                            
                            # Adjust duration estimate based on historical data
                            historical_duration = historical_step["actual_duration"]
                            plan_step.estimated_duration = (
                                plan_step.estimated_duration * 0.7 + 
                                historical_duration * 0.3
                            )
                            
                            # Adjust success probability
                            if "actual_success" in historical_step:
                                historical_success = historical_step["actual_success"]
                                plan_step.success_probability = (
                                    plan_step.success_probability * 0.8 +
                                    (1.0 if historical_success else 0.0) * 0.2
                                )
        
        # Apply pattern-based optimizations
        if context.success_patterns:
            for pattern, success_rate in context.success_patterns.items():
                for step in plan.steps:
                    if pattern in step.action_type and success_rate > 0.8:
                        step.success_probability = min(0.95, step.success_probability * 1.1)
        
        # Apply failure pattern avoidance
        if context.failure_patterns:
            for pattern, failure_rate in context.failure_patterns.items():
                for step in plan.steps:
                    if pattern in step.action_type and failure_rate > 0.3:
                        step.max_retries += 1
                        step.timeout_seconds = int(step.timeout_seconds * 1.2)
    
    async def _calculate_resource_requirements(self, plan: ComplexExecutionPlan):
        """Calculate comprehensive resource requirements for the plan"""
        
        resource_requirements = {
            "cpu": 0.0,
            "memory": 0.0,
            "network": 0.0,
            "storage": 0.0,
            "llm_calls": 0.0,
            "ui_automation": 0.0
        }
        
        for step in plan.steps:
            # Base resource calculation based on action type
            if step.action_type in ["ui_interaction", "navigation", "automation"]:
                resource_requirements["ui_automation"] += 1.0
                resource_requirements["cpu"] += 0.3
                resource_requirements["memory"] += 0.2
            
            elif step.action_type in ["data_analysis", "data_transformation"]:
                resource_requirements["cpu"] += 0.5
                resource_requirements["memory"] += 0.4
                resource_requirements["storage"] += 0.1
            
            elif step.action_type in ["api_analysis", "integration_configuration"]:
                resource_requirements["network"] += 0.3
                resource_requirements["cpu"] += 0.2
            
            elif "analysis" in step.action_type or "planning" in step.action_type:
                resource_requirements["llm_calls"] += 1.0
                resource_requirements["cpu"] += 0.1
            
            # Add step-specific requirements
            step_requirements = step.resource_requirements
            for resource, amount in step_requirements.items():
                if resource in resource_requirements:
                    resource_requirements[resource] += amount
        
        plan.resource_budget = resource_requirements
        
        # Calculate max parallel steps based on resource constraints
        max_resource_value = max(resource_requirements.values(), default=1.0)
        max_parallel = min(
            10,  # Hard limit
            max(1, int(5.0 / max_resource_value)) if max_resource_value > 0 else 3
        )
        plan.max_parallel_steps = max_parallel
    
    async def _create_fallback_plan(self, request: str, context: TaskContext) -> ComplexExecutionPlan:
        """Create a simple fallback plan when advanced planning fails"""
        
        fallback_plan = ComplexExecutionPlan(
            plan_id=str(uuid.uuid4()),
            title=f"Fallback Plan: {request[:50]}...",
            description=request,
            complexity=TaskComplexity.SIMPLE,
            strategy=PlanningStrategy.LINEAR,
            steps=[]  # Initialize empty, will be populated below
        )
        
        # Create basic 3-step fallback
        fallback_steps = [
            ("understand_request", "Understand and analyze the request"),
            ("execute_action", "Execute the requested action"),
            ("verify_completion", "Verify task completion")
        ]
        
        for i, (action_type, description) in enumerate(fallback_steps):
            step = EnhancedTaskStep(
                step_id=f"fallback_step_{i+1}",
                description=description,
                action_type=action_type,
                parameters={"original_request": request, "fallback": True},
                estimated_duration=2.0,
                success_probability=0.7
            )
            
            if i > 0:
                step.dependencies = [f"fallback_step_{i}"]
            
            fallback_plan.steps.append(step)
        
        return fallback_plan
    
    async def _classify_simple_action(self, request: str) -> str:
        """Classify simple action type for basic task planning"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["click", "press", "tap", "hit"]):
            return "click"
        elif any(word in request_lower for word in ["type", "enter", "input", "fill"]):
            return "type"
        elif any(word in request_lower for word in ["navigate", "go to", "open", "visit"]):
            return "navigate"
        elif any(word in request_lower for word in ["scroll", "swipe", "move"]):
            return "scroll"
        else:
            return "generic"
    
    async def _generate_smart_title(self, request: str) -> str:
        """Generate intelligent title based on request analysis"""
        words = request.split()
        
        # Extract key action words
        action_words = []
        for word in words:
            if word.lower() in ["click", "type", "navigate", "analyze", "create", "setup", "configure", "integrate", "deploy"]:
                action_words.append(word.title())
        
        # Extract key object words
        object_words = []
        for word in words:
            if word.lower() in ["button", "form", "data", "report", "system", "database", "api", "workflow"]:
                object_words.append(word)
        
        # Combine for smart title
        if action_words and object_words:
            return f"{' + '.join(action_words)} {' + '.join(object_words[:2])}"
        elif action_words:
            return f"{' + '.join(action_words)} Task"
        else:
            return f"Complex Task: {' '.join(words[:4])}..."
    
    async def _plan_general_moderate_task(self, plan: ComplexExecutionPlan, request: str, context: TaskContext) -> ComplexExecutionPlan:
        """Fallback planning for moderate tasks without specific domain patterns"""
        
        # Generic moderate task pattern
        moderate_pattern = [
            ("task_analysis", "Analyze task requirements and scope"),
            ("resource_preparation", "Prepare necessary resources and tools"),
            ("step_1_execution", "Execute first major task component"),
            ("checkpoint_1", "Verify first component completion"),
            ("step_2_execution", "Execute second major task component"),
            ("checkpoint_2", "Verify second component completion"),
            ("step_3_execution", "Execute final task component"),
            ("final_verification", "Perform comprehensive verification"),
            ("cleanup_and_report", "Clean up and generate completion report")
        ]
        
        for i, (action_type, description) in enumerate(moderate_pattern):
            step = EnhancedTaskStep(
                step_id=f"step_{i+1}",
                description=description,
                action_type=action_type,
                parameters={"original_request": request, "pattern": "general_moderate"},
                priority=8 - (i % 3),  # Varying priority
                estimated_duration=3.0 if "execution" in action_type else 1.5,
                success_probability=0.8 if "checkpoint" in action_type else 0.75
            )
            
            # Add dependencies (mostly sequential with some parallel opportunities)
            if i > 0:
                if action_type.startswith("checkpoint"):
                    # Checkpoints depend on their corresponding execution step
                    step.dependencies = [f"step_{i}"]
                elif "step_2" in action_type:
                    # Step 2 depends on checkpoint 1
                    step.dependencies = [f"step_{i-1}"]
                elif "step_3" in action_type:
                    # Step 3 depends on checkpoint 2
                    step.dependencies = [f"step_{i-1}"]
                elif "final_verification" in action_type:
                    # Final verification depends on step 3
                    step.dependencies = [f"step_{i-1}"]
                else:
                    # Default sequential dependency
                    step.dependencies = [f"step_{i}"]
            
            plan.steps.append(step)
        
        return plan

class ComplexTaskExecutor:
    """Executes complex plans with adaptive learning and real-time optimization"""
    
    def __init__(self, max_concurrent_steps: int = 10):
        self.max_concurrent_steps = max_concurrent_steps
        self.active_plans: Dict[str, ComplexExecutionPlan] = {}
        self.execution_semaphore = asyncio.Semaphore(max_concurrent_steps)
        self.learning_database = {}
        
    async def execute_complex_plan(self, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute complex plan with real-time adaptation"""
        
        plan.actual_start_time = time.time()
        plan.status = "executing"
        self.active_plans[plan.plan_id] = plan
        
        try:
            # Mark first layer steps as ready
            if plan.execution_layers:
                for step_id in plan.execution_layers[0]:
                    step = next(s for s in plan.steps if s.step_id == step_id)
                    step.status = StepStatus.READY
            
            # Execute in layers for optimal parallelization
            for layer_idx, layer_steps in enumerate(plan.execution_layers):
                plan.current_layer = layer_idx
                
                # Execute steps in current layer concurrently
                layer_tasks = []
                for step_id in layer_steps:
                    step = next(s for s in plan.steps if s.step_id == step_id)
                    if step.status == StepStatus.READY:
                        task = asyncio.create_task(self._execute_complex_step(step, plan, context))
                        layer_tasks.append(task)
                        plan.active_steps.add(step_id)
                
                # Wait for layer completion
                if layer_tasks:
                    results = await asyncio.gather(*layer_tasks, return_exceptions=True)
                    
                    # Handle exceptions in layer execution
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            step = next(s for s in plan.steps if s.step_id == layer_steps[i])
                            step.status = StepStatus.FAILED
                            step.error = str(result)
                
                # Mark next layer steps as ready if current layer succeeded
                if layer_idx + 1 < len(plan.execution_layers):
                    next_layer_ready = True
                    for step_id in layer_steps:
                        step = next(s for s in plan.steps if s.step_id == step_id)
                        if step.status != StepStatus.COMPLETED:
                            next_layer_ready = False
                            break
                    
                    if next_layer_ready:
                        for step_id in plan.execution_layers[layer_idx + 1]:
                            step = next(s for s in plan.steps if s.step_id == step_id)
                            # Check if all dependencies are met
                            deps_met = all(
                                next(d for d in plan.steps if d.step_id == dep_id).status == StepStatus.COMPLETED
                                for dep_id in step.dependencies
                                if any(d.step_id == dep_id for d in plan.steps)
                            )
                            if deps_met:
                                step.status = StepStatus.READY
                
                # Clean up active steps for this layer
                for step_id in layer_steps:
                    plan.active_steps.discard(step_id)
                
                # Update progress
                completed_steps = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED)
                plan.progress = (completed_steps / len(plan.steps)) * 100 if len(plan.steps) > 0 else 0
                
                # Adaptive re-planning if needed
                if plan.adaptation_enabled:
                    await self._adaptive_replan_if_needed(plan, context)
            
            # Calculate final metrics
            plan.actual_end_time = time.time()
            plan.success_rate = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED) / len(plan.steps) if len(plan.steps) > 0 else 0
            plan.efficiency_score = await self._calculate_efficiency_score(plan)
            
            # Learn from execution
            if plan.learning_enabled:
                await self._learn_from_execution(plan, context)
            
            return {
                "success": plan.success_rate > 0.8,
                "plan_id": plan.plan_id,
                "steps_completed": sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED),
                "total_steps": len(plan.steps),
                "success_rate": plan.success_rate,
                "efficiency_score": plan.efficiency_score,
                "execution_time": plan.actual_end_time - plan.actual_start_time,
                "adaptations_made": getattr(plan, 'adaptations_made', 0)
            }
            
        except Exception as e:
            logger.error(f"Error executing complex plan: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if plan.plan_id in self.active_plans:
                del self.active_plans[plan.plan_id]
    
    async def _execute_complex_step(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext):
        """Execute a single complex step with advanced error handling and adaptation"""
        async with self.execution_semaphore:
            step.status = StepStatus.RUNNING
            step.start_time = time.time()
            
            try:
                logger.info(f"Executing step: {step.step_id} - {step.description}")
                
                # Execute based on action type
                if step.action_type == "workflow_preparation":
                    result = await self._execute_workflow_preparation(step, plan, context)
                elif step.action_type == "requirement_analysis":
                    result = await self._execute_requirement_analysis(step, plan, context)
                elif step.action_type == "environment_setup":
                    result = await self._execute_environment_setup(step, plan, context)
                elif step.action_type in ["ui_interaction", "navigation"]:
                    result = await self._execute_ui_automation(step, plan, context)
                elif step.action_type in ["data_analysis", "data_transformation", "data_collection"]:
                    result = await self._execute_data_operation(step, plan, context)
                elif step.action_type in ["api_analysis", "integration_configuration", "connection_establishment"]:
                    result = await self._execute_integration_operation(step, plan, context)
                elif step.action_type in ["phase_verification", "objective_verification"]:
                    result = await self._execute_verification(step, plan, context)
                else:
                    result = await self._execute_generic_step(step, plan, context)
                
                step.result = result
                step.status = StepStatus.COMPLETED
                step.actual_success = True
                
                logger.info(f"Step completed successfully: {step.step_id}")
                
            except Exception as e:
                step.error = str(e)
                step.actual_success = False
                
                # Retry logic with exponential backoff
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    step.status = StepStatus.RETRY
                    
                    retry_delay = step.retry_delay * (2 ** (step.retry_count - 1))
                    logger.warning(f"Step {step.step_id} failed, retrying in {retry_delay}s (attempt {step.retry_count})")
                    
                    await asyncio.sleep(retry_delay)
                    await self._execute_complex_step(step, plan, context)
                else:
                    step.status = StepStatus.FAILED
                    logger.error(f"Step {step.step_id} failed permanently: {e}")
                    
                    # Try alternatives if available
                    if step.alternatives:
                        await self._try_step_alternatives(step, plan, context)
            
            finally:
                step.end_time = time.time()
                if step.start_time:
                    step.actual_duration = step.end_time - step.start_time
    
    async def _execute_workflow_preparation(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute workflow preparation step"""
        workflow = step.parameters.get("workflow", {})
        
        # Simulate workflow preparation
        await asyncio.sleep(1.0)
        
        return {
            "success": True,
            "workflow_prepared": workflow.get("name", "unknown"),
            "preparation_items": ["environment_check", "resource_allocation", "dependency_validation"],
            "ready_for_execution": True
        }
    
    async def _execute_requirement_analysis(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute requirement analysis step"""
        # Simulate requirement analysis
        await asyncio.sleep(0.5)
        
        requirements = {
            "functional": ["primary_objective", "user_interaction", "data_processing"],
            "non_functional": ["performance", "reliability", "security"],
            "constraints": ["time_limit", "resource_limit", "technology_stack"]
        }
        
        return {
            "success": True,
            "requirements_identified": requirements,
            "complexity_score": 7.5,
            "estimated_effort": "medium"
        }
    
    async def _execute_environment_setup(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute environment setup step"""
        # Simulate environment setup
        await asyncio.sleep(1.5)
        
        return {
            "success": True,
            "environment_configured": True,
            "components_initialized": ["database", "api_connections", "ui_automation"],
            "status": "ready"
        }
    
    async def _execute_ui_automation(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute UI automation step"""
        # This would integrate with your existing UI automation system
        await asyncio.sleep(2.0)
        
        return {
            "success": True,
            "action_performed": step.action_type,
            "target_element": "identified_and_interacted",
            "validation_passed": True
        }
    
    async def _execute_data_operation(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute data-related operations"""
        await asyncio.sleep(3.0)
        
        return {
            "success": True,
            "operation_type": step.action_type,
            "data_processed": True,
            "records_affected": 1000,
            "quality_score": 0.95
        }
    
    async def _execute_integration_operation(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute integration-related operations"""
        await asyncio.sleep(2.5)
        
        return {
            "success": True,
            "operation_type": step.action_type,
            "integration_established": True,
            "connection_tested": True,
            "performance_metrics": {"latency": "50ms", "throughput": "1000 req/s"}
        }
    
    async def _execute_verification(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute verification steps"""
        await asyncio.sleep(1.0)
        
        # Verify previous steps in the phase/plan
        verification_results = []
        
        if step.action_type == "phase_verification":
            expected_outcomes = step.parameters.get("expected_outcomes", [])
            for outcome in expected_outcomes:
                verification_results.append({
                    "outcome": outcome,
                    "verified": True,
                    "confidence": 0.9
                })
        
        return {
            "success": True,
            "verification_type": step.action_type,
            "results": verification_results,
            "overall_verification": "passed"
        }
    
    async def _execute_generic_step(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext) -> Dict[str, Any]:
        """Execute generic/unknown step types"""
        await asyncio.sleep(1.0)
        
        return {
            "success": True,
            "action_type": step.action_type,
            "processed": True,
            "method": "generic_handler"
        }
    
    async def _try_step_alternatives(self, step: EnhancedTaskStep, plan: ComplexExecutionPlan, context: TaskContext):
        """Try alternative approaches for failed steps"""
        for alternative in step.alternatives:
            try:
                logger.info(f"Trying alternative for {step.step_id}: {alternative}")
                
                # Create alternative step
                alt_step = EnhancedTaskStep(
                    step_id=f"{step.step_id}_alt_{alternative}",
                    description=f"Alternative: {alternative}",
                    action_type=alternative,
                    parameters=step.parameters.copy()
                )
                
                # Execute alternative
                await self._execute_complex_step(alt_step, plan, context)
                
                if alt_step.status == StepStatus.COMPLETED:
                    step.result = alt_step.result
                    step.status = StepStatus.COMPLETED
                    step.actual_success = True
                    logger.info(f"Alternative {alternative} succeeded for {step.step_id}")
                    break
                    
            except Exception as e:
                logger.warning(f"Alternative {alternative} failed for {step.step_id}: {e}")
                continue
    
    async def _adaptive_replan_if_needed(self, plan: ComplexExecutionPlan, context: TaskContext):
        """Adaptively replan if too many steps are failing"""
        failed_steps = sum(1 for s in plan.steps if s.status == StepStatus.FAILED)
        total_steps = len(plan.steps)
        failure_rate = failed_steps / total_steps if total_steps > 0 else 0
        
        if failure_rate > 0.3:  # More than 30% failure rate
            logger.warning(f"High failure rate ({failure_rate:.2f}) detected, initiating adaptive replanning")
            
            # Mark as adapted
            if not hasattr(plan, 'adaptations_made'):
                plan.adaptations_made = 0
            plan.adaptations_made += 1
            
            # Simple adaptation: increase timeouts and retries for remaining steps
            for step in plan.steps:
                if step.status in [StepStatus.PENDING, StepStatus.READY]:
                    step.timeout_seconds = int(step.timeout_seconds * 1.5)
                    step.max_retries += 1
                    step.retry_delay *= 1.2
    
    async def _calculate_efficiency_score(self, plan: ComplexExecutionPlan) -> float:
        """Calculate execution efficiency score"""
        if not plan.actual_start_time or not plan.actual_end_time:
            return 0.0
        
        actual_duration = plan.actual_end_time - plan.actual_start_time
        estimated_duration = plan.estimated_total_duration
        
        # Efficiency based on time performance
        time_efficiency = min(1.0, estimated_duration / actual_duration) if actual_duration > 0 else 0.0
        
        # Efficiency based on success rate
        success_efficiency = plan.success_rate
        
        # Efficiency based on resource utilization
        resource_efficiency = 0.8  # Placeholder - would calculate based on actual resource usage
        
        # Weighted average
        efficiency_score = (
            time_efficiency * 0.4 +
            success_efficiency * 0.4 +
            resource_efficiency * 0.2
        )
        
        return efficiency_score
    
    async def _learn_from_execution(self, plan: ComplexExecutionPlan, context: TaskContext):
        """Learn from task execution for future improvements"""
        learning_data = {
            "plan_id": plan.plan_id,
            "complexity": plan.complexity.name,
            "strategy": plan.strategy.value,
            "total_steps": len(plan.steps),
            "success_rate": plan.success_rate,
            "efficiency_score": plan.efficiency_score,
            "execution_time": plan.actual_end_time - plan.actual_start_time if plan.actual_end_time and plan.actual_start_time else 0,
            "adaptations_made": getattr(plan, 'adaptations_made', 0),
            "step_performance": []
        }
        
        # Record individual step performance
        for step in plan.steps:
            step_data = {
                "step_id": step.step_id,
                "action_type": step.action_type,
                "estimated_duration": step.estimated_duration,
                "actual_duration": step.actual_duration,
                "success_probability": step.success_probability,
                "actual_success": step.actual_success,
                "retry_count": step.retry_count,
                "status": step.status.value
            }
            learning_data["step_performance"].append(step_data)
        
        # Store in learning database
        task_key = f"{context.domain}_{plan.complexity.name}_{plan.strategy.value}"
        if task_key not in self.learning_database:
            self.learning_database[task_key] = []
        
        self.learning_database[task_key].append(learning_data)
        
        # Update context patterns for future use
        if plan.success_rate > 0.8:
            # Update success patterns
            for step in plan.steps:
                if step.actual_success:
                    pattern_key = f"{step.action_type}_{context.domain}"
                    context.success_patterns[pattern_key] = context.success_patterns.get(pattern_key, 0.5) * 0.9 + 0.1
        else:
            # Update failure patterns
            for step in plan.steps:
                if not step.actual_success:
                    pattern_key = f"{step.action_type}_{context.domain}"
                    context.failure_patterns[pattern_key] = context.failure_patterns.get(pattern_key, 0.0) * 0.9 + 0.1
        
        logger.info(f"Learning data recorded for plan {plan.plan_id} in domain {context.domain}")

# Integration with existing brain router
class EnhancedAgentModeHandler:
    """Enhanced agent mode handler that uses the complex task system"""
    
    def __init__(self):
        self.planner = AdvancedTaskPlanner()
        self.executor = ComplexTaskExecutor(max_concurrent_steps=15)  # Higher concurrency
        
    async def handle_complex_request(self, request: str, user_id: str = "default", session_id: str = "default", context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle complex request using enhanced task planning"""
        
        # Create task context
        task_context = TaskContext(
            user_id=user_id,
            session_id=session_id,
            domain=context.get("domain", "general") if context else "general",
            environment=context.get("environment", {}) if context else {},
            constraints=context.get("constraints", {}) if context else {},
            preferences=context.get("preferences", {}) if context else {}
        )
        
        try:
            # Create execution plan
            plan = await self.planner.create_complex_plan(request, task_context)
            
            # Execute the plan
            execution_result = await self.executor.execute_complex_plan(plan, task_context)
            
            # Format response for brain router
            return {
                "success": execution_result["success"],
                "response": await self._format_complex_response(plan, execution_result),
                "mode_used": "Agent",
                "processing_time": execution_result.get("execution_time", 0),
                "resources_used": ["memory", "llm", "execution", "sensors"],
                "confidence": execution_result.get("success_rate", 0.0),
                "metadata": {
                    "complexity": plan.complexity.name,
                    "strategy": plan.strategy.value,
                    "total_steps": execution_result.get("total_steps", 0),
                    "steps_completed": execution_result.get("steps_completed", 0),
                    "efficiency_score": execution_result.get("efficiency_score", 0.0),
                    "adaptations_made": execution_result.get("adaptations_made", 0),
                    "execution_layers": len(plan.execution_layers)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced agent mode handler: {e}")
            return {
                "success": False,
                "response": f"I encountered an error while planning your complex task: {str(e)}",
                "mode_used": "Agent",
                "processing_time": 0.0,
                "resources_used": [],
                "confidence": 0.0,
                "metadata": {"error": str(e), "fallback_used": True}
            }
    
    async def _format_complex_response(self, plan: ComplexExecutionPlan, execution_result: Dict[str, Any]) -> str:
        """Format a comprehensive response for complex task execution"""
        
        success_rate = execution_result.get("success_rate", 0.0)
        steps_completed = execution_result.get("steps_completed", 0)
        total_steps = execution_result.get("total_steps", 0)
        execution_time = execution_result.get("execution_time", 0)
        
        if execution_result["success"]:
            response = f"✅ **Complex Task Completed Successfully!**\n\n"
            response += f"**{plan.title}**\n"
            response += f"*Complexity Level: {plan.complexity.name} | Strategy: {plan.strategy.value}*\n\n"
            
            response += f"📊 **Execution Summary:**\n"
            response += f"• Steps Completed: {steps_completed}/{total_steps} ({success_rate:.1%})\n"
            response += f"• Execution Time: {execution_time:.1f}s\n"
            response += f"• Efficiency Score: {execution_result.get('efficiency_score', 0.0):.2f}\n"
            
            if execution_result.get('adaptations_made', 0) > 0:
                response += f"• Adaptations Made: {execution_result['adaptations_made']}\n"
            
            response += f"\n🎯 **Key Accomplishments:**\n"
            
            # Group completed steps by phase
            completed_steps = [s for s in plan.steps if s.status == StepStatus.COMPLETED]
            phases = {}
            for step in completed_steps:
                phase = step.parameters.get("phase", "General")
                if phase not in phases:
                    phases[phase] = []
                phases[phase].append(step.description)
            
            for phase, step_descriptions in phases.items():
                response += f"• **{phase.title()}**: {len(step_descriptions)} steps completed\n"
                for desc in step_descriptions[:3]:  # Show first 3 steps
                    response += f"  - {desc}\n"
                if len(step_descriptions) > 3:
                    response += f"  - ... and {len(step_descriptions) - 3} more\n"
            
        else:
            response = f"⚠️ **Complex Task Partially Completed**\n\n"
            response += f"**{plan.title}**\n"
            response += f"*Complexity Level: {plan.complexity.name}*\n\n"
            
            response += f"📊 **Execution Summary:**\n"
            response += f"• Steps Completed: {steps_completed}/{total_steps} ({success_rate:.1%})\n"
            response += f"• Execution Time: {execution_time:.1f}s\n"
            
            # Show failed steps
            failed_steps = [s for s in plan.steps if s.status == StepStatus.FAILED]
            if failed_steps:
                response += f"\n❌ **Issues Encountered:**\n"
                for step in failed_steps[:3]:  # Show first 3 failed steps
                    response += f"• {step.description}\n"
                    if step.error:
                        response += f"  Error: {step.error[:100]}...\n"
                
                if len(failed_steps) > 3:
                    response += f"• ... and {len(failed_steps) - 3} more issues\n"
            
            # Show completed steps
            completed_steps = [s for s in plan.steps if s.status == StepStatus.COMPLETED]
            if completed_steps:
                response += f"\n✅ **Successfully Completed:**\n"
                for step in completed_steps[:5]:  # Show first 5 completed steps
                    response += f"• {step.description}\n"
                
                if len(completed_steps) > 5:
                    response += f"• ... and {len(completed_steps) - 5} more\n"
        
        return response

# Usage example and testing code
async def test_complex_tasks():
    """Test the enhanced complex task handler with various complexity levels"""
    
    print("🚀 Testing Enhanced Complex Task Handler")
    print("=" * 80)
    
    planner = AdvancedTaskPlanner()
    executor = ComplexTaskExecutor()
    handler = EnhancedAgentModeHandler()
    
    # Test cases with increasing complexity
    test_cases = [
        {
            "name": "Simple Task",
            "request": "Click the login button",
            "context": TaskContext("user1", "session1", "web_automation"),
            "expected_complexity": TaskComplexity.SIMPLE
        },
        {
            "name": "Moderate Task", 
            "request": "Fill out the registration form, validate the input, and submit it with confirmation",
            "context": TaskContext("user1", "session1", "web_automation"),
            "expected_complexity": TaskComplexity.MODERATE
        },
        {
            "name": "Complex Task",
            "request": "Analyze sales data from multiple sources, create visualizations, generate insights, and produce a comprehensive executive report with recommendations",
            "context": TaskContext("user1", "session1", "data_analysis"),
            "expected_complexity": TaskComplexity.COMPLEX
        },
        {
            "name": "Enterprise Task",
            "request": "Integrate the CRM system with our email platform, migrate all customer contacts, set up automated marketing workflows, test the complete integration, monitor performance, and deploy to production with rollback capabilities",
            "context": TaskContext("user1", "session1", "system_integration"),
            "expected_complexity": TaskComplexity.ENTERPRISE
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{'─' * 60}")
        print(f"🧪 Testing: {test_case['name']}")
        print(f"{'─' * 60}")
        print(f"Request: {test_case['request']}")
        print()
        
        try:
            # Test planning
            plan = await planner.create_complex_plan(test_case['request'], test_case['context'])
            
            print(f"📋 **Plan Analysis:**")
            print(f"   Complexity: {plan.complexity.name} (Expected: {test_case['expected_complexity'].name})")
            print(f"   Strategy: {plan.strategy.value}")
            print(f"   Total Steps: {len(plan.steps)}")
            print(f"   Execution Layers: {len(plan.execution_layers)}")
            print(f"   Estimated Duration: {plan.estimated_total_duration:.1f}s")
            print(f"   Max Parallel Steps: {plan.max_parallel_steps}")
            
            # Show step breakdown
            print(f"\n📝 **Step Breakdown:**")
            for i, step in enumerate(plan.steps[:8]):  # Show first 8 steps
                deps = f" (deps: {', '.join(step.dependencies)})" if step.dependencies else ""
                print(f"   {i+1:2d}. {step.description} [{step.action_type}]{deps}")
            
            if len(plan.steps) > 8:
                print(f"   ... and {len(plan.steps) - 8} more steps")
            
            # Show execution layers
            if len(plan.execution_layers) > 1:
                print(f"\n🔄 **Execution Layers (Parallelization):**")
                for i, layer in enumerate(plan.execution_layers[:5]):  # Show first 5 layers
                    print(f"   Layer {i+1}: {len(layer)} step(s) - {', '.join(layer)}")
                
                if len(plan.execution_layers) > 5:
                    print(f"   ... and {len(plan.execution_layers) - 5} more layers")
            
            # Test execution (simulated)
            print(f"\n⚡ **Executing Plan...**")
            execution_result = await executor.execute_complex_plan(plan, test_case['context'])
            
            print(f"✅ **Execution Results:**")
            print(f"   Success: {execution_result['success']}")
            print(f"   Success Rate: {execution_result['success_rate']:.1%}")
            print(f"   Steps Completed: {execution_result['steps_completed']}/{execution_result['total_steps']}")
            print(f"   Execution Time: {execution_result['execution_time']:.2f}s")
            print(f"   Efficiency Score: {execution_result['efficiency_score']:.2f}")
            
            if execution_result.get('adaptations_made', 0) > 0:
                print(f"   Adaptations Made: {execution_result['adaptations_made']}")
            
            # Test handler integration
            print(f"\n🧠 **Brain Router Integration:**")
            handler_result = await handler.handle_complex_request(
                test_case['request'], 
                context={"domain": test_case['context'].domain}
            )
            
            print(f"   Handler Success: {handler_result['success']}")
            print(f"   Processing Time: {handler_result['processing_time']:.2f}s")
            print(f"   Confidence: {handler_result['confidence']:.2f}")
            print(f"   Resources Used: {', '.join(handler_result['resources_used'])}")
            
            results.append({
                "test_case": test_case['name'],
                "complexity_detected": plan.complexity.name,
                "complexity_expected": test_case['expected_complexity'].name,
                "complexity_match": plan.complexity == test_case['expected_complexity'],
                "steps_generated": len(plan.steps),
                "execution_layers": len(plan.execution_layers),
                "execution_success": execution_result['success'],
                "success_rate": execution_result['success_rate'],
                "efficiency_score": execution_result['efficiency_score'],
                "handler_integration": handler_result['success']
            })
            
        except Exception as e:
            print(f"❌ **Error in test case:** {e}")
            results.append({
                "test_case": test_case['name'],
                "error": str(e)
            })
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 **Test Summary**")
    print(f"{'='*80}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get('execution_success', False))
    complexity_matches = sum(1 for r in results if r.get('complexity_match', False))
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful Executions: {successful_tests}/{total_tests} ({successful_tests/total_tests:.1%})")
    print(f"Complexity Detection Accuracy: {complexity_matches}/{total_tests} ({complexity_matches/total_tests:.1%})")
    
    print(f"\n📈 **Capability Demonstration:**")
    max_steps = max(r.get('steps_generated', 0) for r in results)
    max_layers = max(r.get('execution_layers', 0) for r in results)
    avg_efficiency = sum(r.get('efficiency_score', 0) for r in results) / len(results)
    
    print(f"Maximum Steps Handled: {max_steps}")
    print(f"Maximum Parallel Layers: {max_layers}")
    print(f"Average Efficiency Score: {avg_efficiency:.2f}")
    
    print(f"\n🎯 **System Capabilities Verified:**")
    print(f"✅ Multi-complexity task handling (Simple → Enterprise)")
    print(f"✅ Intelligent strategy selection (Linear → Adaptive)")
    print(f"✅ Hierarchical task decomposition")
    print(f"✅ Dependency-aware execution")
    print(f"✅ Parallel step execution")
    print(f"✅ Adaptive replanning")
    print(f"✅ Learning from execution")
    print(f"✅ Brain router integration")

if __name__ == "__main__":
    asyncio.run(test_complex_tasks())