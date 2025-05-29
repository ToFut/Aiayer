#!/usr/bin/env python3
"""
Improved Intelligent Task Planner
Advanced task decomposition with context understanding and domain knowledge.
"""

import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    SIMPLE = 1      # 1-3 steps, direct actions
    MODERATE = 2    # 4-10 steps, multi-step workflows
    COMPLEX = 3     # 10-50 steps, cross-platform integrations
    ENTERPRISE = 4  # 50+ steps, enterprise workflows

class ActionType(Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    VERIFY = "verify"
    EXTRACT = "extract"
    PROCESS = "process"
    CONFIGURE = "configure"
    SCHEDULE = "schedule"
    MONITOR = "monitor"

@dataclass
class DomainKnowledge:
    """Domain-specific knowledge for common platforms and workflows"""
    
    # Web platforms and their typical workflows
    PLATFORM_WORKFLOWS = {
        'mailchimp': {
            'base_url': 'mailchimp.com',
            'login_path': '/login',
            'campaigns_path': '/campaigns',
            'common_tasks': {
                'create_campaign': [
                    'Navigate to campaigns section',
                    'Click create new campaign',
                    'Select email campaign type',
                    'Choose audience/list',
                    'Design email template',
                    'Configure campaign settings',
                    'Schedule or send'
                ],
                'segment_audience': [
                    'Go to audience section',
                    'Select target list',
                    'Create new segment',
                    'Define segment criteria',
                    'Save segment'
                ],
                'ab_test': [
                    'Enable A/B testing in campaign',
                    'Set test variables (subject, content, etc)',
                    'Define test percentage',
                    'Set winning criteria',
                    'Schedule test'
                ],
                'track_performance': [
                    'Access campaign reports',
                    'Enable tracking pixels',
                    'Configure analytics integration',
                    'Set up automated reports'
                ]
            }
        },
        'salesforce': {
            'base_url': 'salesforce.com',
            'common_tasks': {
                'export_contacts': [
                    'Navigate to contacts',
                    'Apply filters if needed',
                    'Select export option',
                    'Choose export format',
                    'Download file'
                ]
            }
        },
        'hubspot': {
            'base_url': 'hubspot.com',
            'common_tasks': {
                'import_contacts': [
                    'Go to contacts section',
                    'Click import',
                    'Upload CSV file',
                    'Map fields',
                    'Review and import'
                ]
            }
        },
        'shopify': {
            'base_url': 'shopify.com',
            'common_tasks': {
                'setup_store': [
                    'Configure store settings',
                    'Upload products',
                    'Set up payment gateways',
                    'Configure shipping',
                    'Launch store'
                ]
            }
        },
        'youtube': {
            'base_url': 'youtube.com',
            'common_tasks': {
                'search_content': [
                    'Navigate to YouTube',
                    'Click search box',
                    'Enter search terms',
                    'Execute search',
                    'Browse results'
                ],
                'watch_video': [
                    'Navigate to YouTube',
                    'Search for video',
                    'Click on video',
                    'Play video'
                ],
                'create_playlist': [
                    'Login to YouTube',
                    'Go to playlists section',
                    'Create new playlist',
                    'Add videos to playlist',
                    'Set playlist visibility'
                ]
            }
        }
    }
    
    # Common task patterns and their decomposition
    TASK_PATTERNS = {
        'email_campaign': {
            'keywords': ['email', 'campaign', 'newsletter', 'marketing', 'mailchimp'],
            'typical_steps': [
                'Login to email platform',
                'Create new campaign',
                'Select audience/segments',
                'Design email template',
                'Set up A/B testing (if mentioned)',
                'Schedule campaign',
                'Enable tracking'
            ]
        },
        'data_analysis': {
            'keywords': ['analyze', 'data', 'report', 'chart', 'excel', 'spreadsheet'],
            'typical_steps': [
                'Open data file/source',
                'Clean and prepare data',
                'Create analysis/calculations',
                'Generate visualizations',
                'Create summary report',
                'Export results'
            ]
        },
        'crm_integration': {
            'keywords': ['crm', 'contacts', 'leads', 'salesforce', 'hubspot', 'export', 'import'],
            'typical_steps': [
                'Login to source CRM',
                'Export data',
                'Clean/format data',
                'Login to target CRM',
                'Import data',
                'Configure mappings',
                'Verify import'
            ]
        },
        'web_search': {
            'keywords': ['open', 'search', 'browse', 'navigate', 'youtube', 'google', 'find'],
            'typical_steps': [
                'Open web browser',
                'Navigate to target website',
                'Locate search functionality',
                'Enter search terms',
                'Execute search',
                'Review results'
            ]
        },
        'ecommerce_setup': {
            'keywords': ['shopify', 'store', 'products', 'ecommerce', 'payment'],
            'typical_steps': [
                'Login to platform',
                'Configure store settings',
                'Upload product catalog',
                'Set up payment processing',
                'Configure shipping',
                'Test functionality',
                'Launch store'
            ]
        }
    }

@dataclass
class TaskStep:
    """Improved task step with better context understanding"""
    step_id: str
    description: str
    action_type: ActionType
    target: Optional[str] = None  # What to interact with (URL, element, etc.)
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: float = 5.0  # seconds
    success_criteria: List[str] = field(default_factory=list)
    fallback_actions: List[str] = field(default_factory=list)
    domain_context: Optional[str] = None  # Platform/domain context

@dataclass
class TaskPlan:
    """Improved task plan with better organization"""
    plan_id: str
    user_request: str
    complexity: TaskComplexity
    steps: List[TaskStep]
    estimated_total_duration: float
    domains_involved: List[str] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)  # Steps that can run in parallel
    critical_path: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)

class ImprovedIntelligentTaskPlanner:
    """Advanced task planner with domain knowledge and context understanding"""
    
    def __init__(self):
        self.domain_knowledge = DomainKnowledge()
        self.learning_history = {}  # Store successful task patterns
        
    async def analyze_user_request(self, request: str) -> Dict[str, Any]:
        """Analyze user request to understand intent and extract key information"""
        analysis = {
            'intent': None,
            'platforms': [],
            'actions': [],
            'data_objects': [],
            'constraints': [],
            'keywords': []
        }
        
        # Convert to lowercase for analysis
        request_lower = request.lower()
        words = request_lower.split()
        
        # Extract platforms mentioned
        for platform in self.domain_knowledge.PLATFORM_WORKFLOWS.keys():
            if platform in request_lower:
                analysis['platforms'].append(platform)
        
        # Identify task patterns
        for pattern_name, pattern_info in self.domain_knowledge.TASK_PATTERNS.items():
            keyword_matches = sum(1 for keyword in pattern_info['keywords'] if keyword in request_lower)
            if keyword_matches >= 2:  # At least 2 keywords match
                analysis['intent'] = pattern_name
                analysis['keywords'].extend(pattern_info['keywords'])
                break
        
        # Extract specific actions mentioned
        action_verbs = [
            'create', 'setup', 'configure', 'login', 'navigate', 'click', 'type',
            'send', 'schedule', 'export', 'import', 'analyze', 'generate',
            'segment', 'test', 'track', 'monitor', 'integrate'
        ]
        
        for verb in action_verbs:
            if verb in words:
                analysis['actions'].append(verb)
        
        # Extract data objects
        data_objects = [
            'email', 'campaign', 'template', 'list', 'contacts', 'data',
            'report', 'chart', 'segment', 'audience', 'products', 'store'
        ]
        
        for obj in data_objects:
            if obj in words:
                analysis['data_objects'].append(obj)
        
        # Extract constraints and specific requirements
        if 'a/b test' in request_lower or 'ab test' in request_lower:
            analysis['constraints'].append('ab_testing_required')
        
        if 'schedule' in request_lower:
            analysis['constraints'].append('scheduling_required')
        
        if 'track' in request_lower or 'monitor' in request_lower:
            analysis['constraints'].append('tracking_required')
        
        return analysis
    
    async def determine_complexity(self, analysis: Dict[str, Any], request: str) -> TaskComplexity:
        """Determine task complexity based on analysis"""
        
        # Count complexity indicators
        complexity_score = 0
        
        # Platform count
        platform_count = len(analysis['platforms'])
        complexity_score += platform_count * 10
        
        # Action count
        action_count = len(analysis['actions'])
        complexity_score += action_count * 5
        
        # Data object count
        data_object_count = len(analysis['data_objects'])
        complexity_score += data_object_count * 3
        
        # Constraint count
        constraint_count = len(analysis['constraints'])
        complexity_score += constraint_count * 7
        
        # Special complexity indicators
        if 'integrate' in request.lower():
            complexity_score += 20
        
        if 'deploy' in request.lower() or 'migration' in request.lower():
            complexity_score += 30
        
        if len(request.split()) > 20:  # Long, detailed requests
            complexity_score += 10
        
        # Determine complexity level
        if complexity_score <= 15:
            return TaskComplexity.SIMPLE
        elif complexity_score <= 40:
            return TaskComplexity.MODERATE
        elif complexity_score <= 80:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.ENTERPRISE
    
    async def decompose_task_by_domain(self, analysis: Dict[str, Any], request: str) -> List[TaskStep]:
        """Decompose task based on domain knowledge and detected intent"""
        steps = []
        step_counter = 1
        
        # If we identified the intent pattern, use domain-specific decomposition
        if analysis['intent'] and analysis['intent'] in self.domain_knowledge.TASK_PATTERNS:
            pattern = self.domain_knowledge.TASK_PATTERNS[analysis['intent']]
            
            # Use typical steps as a base
            for step_desc in pattern['typical_steps']:
                step = TaskStep(
                    step_id=f"step_{step_counter}",
                    description=step_desc,
                    action_type=self._determine_action_type(step_desc),
                    estimated_duration=self._estimate_step_duration(step_desc),
                    domain_context=analysis.get('platforms', [None])[0] if analysis.get('platforms') else None
                )
                
                # Add specific parameters based on the original request
                step.parameters = self._extract_step_parameters(step_desc, request, analysis)
                
                steps.append(step)
                step_counter += 1
        
        # If platform is identified, add platform-specific steps
        for platform in analysis['platforms']:
            if platform in self.domain_knowledge.PLATFORM_WORKFLOWS:
                platform_info = self.domain_knowledge.PLATFORM_WORKFLOWS[platform]
                
                # Add login step if not already present
                if not any('login' in step.description.lower() for step in steps):
                    login_step = TaskStep(
                        step_id=f"step_{step_counter}",
                        description=f"Navigate to {platform} and login",
                        action_type=ActionType.NAVIGATE,
                        target=f"https://{platform_info['base_url']}{platform_info.get('login_path', '')}",
                        estimated_duration=10.0,
                        domain_context=platform
                    )
                    steps.insert(0, login_step)  # Login should be first
                    step_counter += 1
        
        # If no domain knowledge available, fall back to generic decomposition
        if not steps:
            steps = await self._generic_task_decomposition(request, analysis)
        
        # Add dependencies between steps
        self._add_step_dependencies(steps)
        
        # Add success criteria and fallback actions
        self._enhance_steps_with_validation(steps, analysis)
        
        return steps
    
    def _determine_action_type(self, description: str) -> ActionType:
        """Determine action type from step description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['navigate', 'go to', 'open', 'visit']):
            return ActionType.NAVIGATE
        elif any(word in desc_lower for word in ['click', 'select', 'choose', 'press']):
            return ActionType.CLICK
        elif any(word in desc_lower for word in ['type', 'enter', 'input', 'fill']):
            return ActionType.TYPE
        elif any(word in desc_lower for word in ['wait', 'pause', 'delay']):
            return ActionType.WAIT
        elif any(word in desc_lower for word in ['verify', 'check', 'confirm', 'validate']):
            return ActionType.VERIFY
        elif any(word in desc_lower for word in ['extract', 'get', 'download', 'export']):
            return ActionType.EXTRACT
        elif any(word in desc_lower for word in ['process', 'analyze', 'calculate']):
            return ActionType.PROCESS
        elif any(word in desc_lower for word in ['configure', 'setup', 'set up', 'enable']):
            return ActionType.CONFIGURE
        elif any(word in desc_lower for word in ['schedule', 'plan', 'time']):
            return ActionType.SCHEDULE
        elif any(word in desc_lower for word in ['monitor', 'track', 'watch']):
            return ActionType.MONITOR
        else:
            return ActionType.CLICK  # Default fallback
    
    def _estimate_step_duration(self, description: str) -> float:
        """Estimate duration based on step complexity"""
        desc_lower = description.lower()
        
        # Quick actions
        if any(word in desc_lower for word in ['click', 'select', 'press']):
            return 3.0
        
        # Navigation actions
        elif any(word in desc_lower for word in ['navigate', 'go to', 'open']):
            return 8.0
        
        # Data entry actions
        elif any(word in desc_lower for word in ['type', 'enter', 'fill', 'input']):
            return 6.0
        
        # Configuration actions
        elif any(word in desc_lower for word in ['configure', 'setup', 'enable']):
            return 15.0
        
        # Complex processing
        elif any(word in desc_lower for word in ['analyze', 'process', 'generate']):
            return 25.0
        
        # Default
        else:
            return 10.0
    
    def _extract_step_parameters(self, step_desc: str, original_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific parameters for a step based on the original request"""
        parameters = {}
        
        # Extract specific values mentioned in the request
        request_lower = original_request.lower()
        
        # Email-specific parameters
        if 'email' in step_desc.lower() or 'campaign' in step_desc.lower():
            # Extract subject lines for A/B testing
            subject_pattern = r'["\']([^"\']*subject[^"\']*)["\']'
            subjects = re.findall(subject_pattern, original_request, re.IGNORECASE)
            if subjects:
                parameters['subject_lines'] = subjects
            
            # Extract campaign type
            if 'newsletter' in request_lower:
                parameters['campaign_type'] = 'newsletter'
            elif 'product' in request_lower:
                parameters['campaign_type'] = 'product_announcement'
            
        # Segmentation parameters
        if 'segment' in step_desc.lower():
            if 'customer' in request_lower and 'prospect' in request_lower:
                parameters['segment_types'] = ['customers', 'prospects']
            elif 'recent' in request_lower:
                parameters['segment_criteria'] = 'recent_activity'
        
        # Scheduling parameters
        if 'schedule' in step_desc.lower():
            # Look for time indicators
            time_patterns = [
                r'tomorrow (\d+)\s*(am|pm)',
                r'(\d+)\s*(am|pm)',
                r'at (\d+:\d+)'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, request_lower)
                if match:
                    parameters['schedule_time'] = match.group(0)
                    break
        
        return parameters
    
    def _add_step_dependencies(self, steps: List[TaskStep]):
        """Add logical dependencies between steps"""
        for i, step in enumerate(steps):
            if i > 0:
                # Most steps depend on the previous step
                step.dependencies.append(steps[i-1].step_id)
                
                # Special dependency rules
                if step.action_type == ActionType.CONFIGURE and i > 1:
                    # Configuration might depend on navigation being complete
                    for j in range(i):
                        if steps[j].action_type == ActionType.NAVIGATE:
                            step.dependencies.append(steps[j].step_id)
                            break
    
    def _enhance_steps_with_validation(self, steps: List[TaskStep], analysis: Dict[str, Any]):
        """Add success criteria and fallback actions to steps"""
        for step in steps:
            # Add success criteria based on action type
            if step.action_type == ActionType.NAVIGATE:
                step.success_criteria.append("Page loads successfully")
                step.success_criteria.append("Correct URL is displayed")
                step.fallback_actions.append("Retry navigation")
                step.fallback_actions.append("Check internet connection")
                
            elif step.action_type == ActionType.CLICK:
                step.success_criteria.append("Element clicked successfully")
                step.success_criteria.append("Expected page/dialog appears")
                step.fallback_actions.append("Wait and retry click")
                step.fallback_actions.append("Look for alternative element")
                
            elif step.action_type == ActionType.TYPE:
                step.success_criteria.append("Text entered correctly")
                step.success_criteria.append("Field accepts input")
                step.fallback_actions.append("Clear field and retry")
                step.fallback_actions.append("Use alternative input method")
                
            elif step.action_type == ActionType.CONFIGURE:
                step.success_criteria.append("Configuration saved")
                step.success_criteria.append("Settings applied correctly")
                step.fallback_actions.append("Reset and reconfigure")
                step.fallback_actions.append("Use default settings")
    
    async def _generic_task_decomposition(self, request: str, analysis: Dict[str, Any]) -> List[TaskStep]:
        """Generic task decomposition when no domain knowledge is available"""
        steps = []
        step_counter = 1
        
        # Basic decomposition based on common patterns
        actions = analysis['actions']
        
        if 'navigate' in actions or 'login' in actions:
            step = TaskStep(
                step_id=f"step_{step_counter}",
                description="Navigate to target website/application",
                action_type=ActionType.NAVIGATE,
                estimated_duration=8.0
            )
            steps.append(step)
            step_counter += 1
        
        if 'create' in actions:
            step = TaskStep(
                step_id=f"step_{step_counter}",
                description="Create new item/campaign/project",
                action_type=ActionType.CLICK,
                estimated_duration=5.0
            )
            steps.append(step)
            step_counter += 1
        
        if 'configure' in actions or 'setup' in actions:
            step = TaskStep(
                step_id=f"step_{step_counter}",
                description="Configure settings and options",
                action_type=ActionType.CONFIGURE,
                estimated_duration=15.0
            )
            steps.append(step)
            step_counter += 1
        
        if 'schedule' in actions:
            step = TaskStep(
                step_id=f"step_{step_counter}",
                description="Schedule execution/delivery",
                action_type=ActionType.SCHEDULE,
                estimated_duration=8.0
            )
            steps.append(step)
            step_counter += 1
        
        if 'track' in actions or 'monitor' in actions:
            step = TaskStep(
                step_id=f"step_{step_counter}",
                description="Enable tracking and monitoring",
                action_type=ActionType.CONFIGURE,
                estimated_duration=10.0
            )
            steps.append(step)
            step_counter += 1
        
        return steps
    
    async def create_intelligent_plan(self, user_request: str, context: Dict[str, Any] = None) -> TaskPlan:
        """Create an intelligent task plan with improved understanding"""
        
        # Analyze the user request
        analysis = await self.analyze_user_request(user_request)
        
        # Determine task complexity
        complexity = await self.determine_complexity(analysis, user_request)
        
        # Decompose into steps using domain knowledge
        steps = await self.decompose_task_by_domain(analysis, user_request)
        
        # Calculate total estimated duration
        total_duration = sum(step.estimated_duration for step in steps)
        
        # Identify parallel execution opportunities
        parallel_groups = self._identify_parallel_groups(steps)
        
        # Create the task plan
        plan = TaskPlan(
            plan_id=f"intelligent_plan_{int(datetime.now().timestamp())}",
            user_request=user_request,
            complexity=complexity,
            steps=steps,
            estimated_total_duration=total_duration,
            domains_involved=analysis['platforms'],
            parallel_groups=parallel_groups,
            critical_path=[step.step_id for step in steps],  # Simplified for now
            success_metrics=[
                "All steps completed successfully",
                "No critical errors encountered",
                "User objectives achieved"
            ]
        )
        
        logger.info(f"Created intelligent plan: {plan.plan_id} with {len(steps)} steps")
        logger.info(f"Complexity: {complexity.name}, Duration: {total_duration:.1f}s")
        logger.info(f"Domains: {analysis['platforms']}, Intent: {analysis.get('intent', 'unknown')}")
        
        return plan
    
    def _identify_parallel_groups(self, steps: List[TaskStep]) -> List[List[str]]:
        """Identify steps that can be executed in parallel"""
        parallel_groups = []
        
        # Simple heuristic: steps with no dependencies on each other can run in parallel
        independent_steps = []
        
        for step in steps:
            # If step has minimal dependencies, it might be parallelizable
            if len(step.dependencies) <= 1:
                independent_steps.append(step.step_id)
        
        # Group independent steps that are of similar types
        if len(independent_steps) > 1:
            parallel_groups.append(independent_steps)
        
        return parallel_groups

# Test function
async def test_improved_planner():
    """Test the improved planner with various complex requests"""
    planner = ImprovedIntelligentTaskPlanner()
    
    test_requests = [
        "Create email templates in Mailchimp, segment subscriber lists, A/B test subject lines, schedule campaigns, and set up performance tracking",
        "Export contacts from Salesforce, clean duplicate entries, import to HubSpot, and set up automated workflows",
        "Analyze quarterly sales data from Excel, create pivot tables, generate trend charts, and compile into PowerPoint presentation",
        "Set up Shopify store, upload product catalog, configure payment gateways, and launch marketing campaigns"
    ]
    
    for request in test_requests:
        print(f"\n{'='*80}")
        print(f"Request: {request}")
        print(f"{'='*80}")
        
        plan = await planner.create_intelligent_plan(request)
        
        print(f"Plan ID: {plan.plan_id}")
        print(f"Complexity: {plan.complexity.name}")
        print(f"Total Duration: {plan.estimated_total_duration:.1f} seconds")
        print(f"Domains: {plan.domains_involved}")
        print(f"Steps ({len(plan.steps)}):")
        
        for i, step in enumerate(plan.steps, 1):
            print(f"  {i}. {step.description}")
            print(f"     Action: {step.action_type.value}, Duration: {step.estimated_duration:.1f}s")
            if step.parameters:
                print(f"     Parameters: {step.parameters}")
            if step.success_criteria:
                print(f"     Success: {step.success_criteria[0]}")

if __name__ == "__main__":
    asyncio.run(test_improved_planner())