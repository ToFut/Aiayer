"""
Execution Package
Enterprise-grade agent execution system for SensAI.

This package provides a comprehensive agent execution framework inspired by:
- Google Project Mariner's contextual automation
- Claude Code's reasoning capabilities
- Enterprise-grade scalability and reliability

Architecture:
- Core: Base classes and interfaces
- Agents: Specialized agent implementations  
- Memory: Task and context memory management
- Services: External service integrations
- Interfaces: Communication protocols
- Config: Configuration management
- Utils: Utility functions and helpers
"""

__version__ = "1.0.0"
__author__ = "SensAI Development Team"

# Core exports
from .core.agent_base import AgentBase
from .core.task_orchestrator import TaskOrchestrator

# Agent exports
from .agents.automation_agent import AutomationAgent
from .agents.suggestion_agent import SuggestionAgent

# Memory exports
from .memory.agent_memory import AgentMemory
from .memory.task_tracker import TaskTracker

__all__ = [
    'AgentBase',
    'TaskOrchestrator',
    'AutomationAgent',
    'SuggestionAgent',
    'AgentMemory'
]
