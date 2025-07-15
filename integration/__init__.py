"""
AIayer Integration Module
Provides integration between AIayer and RPA_AVEN for universal UI automation.
"""

from .rpa_aven_bridge import RPA_AVENBridge, AIayerRPAIntegration, get_rpa_integration, initialize_rpa_integration
from .enhanced_automation_handler import EnhancedAutomationHandler, RealAutomationStep, get_enhanced_automation_handler, initialize_enhanced_automation

__all__ = [
    'RPA_AVENBridge',
    'AIayerRPAIntegration', 
    'get_rpa_integration',
    'initialize_rpa_integration',
    'EnhancedAutomationHandler',
    'RealAutomationStep',
    'get_enhanced_automation_handler',
    'initialize_enhanced_automation'
] 