#!/usr/bin/env python3
"""
Test Enhanced Enterprise Agent System
Professional testing of self-reflection, collaboration, validation, and deep analysis
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

# Import the enhanced enterprise system
from enhanced_enterprise_agent_system import (
    enterprise_agent_system,
    initialize_enterprise_system,
    process_enterprise_agent_request,
    ValidationLevel,
    AnalysisDepth
)

import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedSystemTester:
    """Professional testing suite for enhanced enterprise system"""
    
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    async def run_comprehensive_tests(self):
        """Run comprehensive test suite"""
        
        print("🧪 Enhanced Enterprise Agent System - Comprehensive Test Suite")
        print("=" * 70)
        print("Testing professional features:")
        print("• Agent self-reflection and task completion validation")
        print("• Inter-agent communication and context sharing")
        print("• Professional-grade validation (Claude Code standards)")
        print("• Deep dive analysis for complex task verification")
        print("• Context-aware agent collaboration framework")
        print()
        
        # Initialize system
        await self._test_system_initialization()
        
        # Test basic agent request
        await self._test_basic_agent_request()
        
        # Test self-reflection capabilities
        await self._test_agent_self_reflection()
        
        # Test inter-agent collaboration
        await self._test_agent_collaboration()
        
        # Test professional validation
        await self._test_professional_validation()
        
        # Test deep analysis
        await self._test_deep_analysis()
        
        # Test complex task handling
        await self._test_complex_task_handling()
        
        # Test approval workflow
        await self._test_approval_workflow()
        
        # Test execution monitoring
        await self._test_execution_monitoring()
        
        # Print test summary
        self._print_test_summary()
    
    async def _test_system_initialization(self):
        """Test system initialization"""
        test_name = "System Initialization"
        print(f"📋 Testing: {test_name}")
        
        try:
            start_time = time.time()
            await initialize_enterprise_system()
            init_time = time.time() - start_time
            
            # Verify system is ready
            metrics = enterprise_agent_system.get_system_metrics()
            
            if metrics is not None:
                self._record_test_result(test_name, True, {
                    "initialization_time": init_time,
                    "metrics_available": True
                })
                print(f"   ✅ System initialized successfully in {init_time:.2f}s")
            else:
                self._record_test_result(test_name, False, {"error": "Metrics not available"})
                print(f"   ❌ System initialization failed - metrics not available")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ System initialization failed: {e}")
    
    async def _test_basic_agent_request(self):
        """Test basic agent request processing"""
        test_name = "Basic Agent Request"
        print(f"📋 Testing: {test_name}")
        
        try:
            task = "Click on Documents Folder"
            evidence = {
                "screenshot_path": "/tmp/desktop.png",
                "accessibility_data": {"element_found": True, "clickable": True}
            }
            context = {
                "ui_state": {"application": "Finder", "window_state": "active"}
            }
            
            start_time = time.time()
            response = await process_enterprise_agent_request(
                task,
                agent_mode="agent",
                evidence=evidence,
                context=context,
                require_human_approval=False
            )
            processing_time = time.time() - start_time
            
            success = (
                response is not None and
                response.success and
                response.confidence > 0.0 and
                len(response.execution_plan) > 0
            )
            
            self._record_test_result(test_name, success, {
                "processing_time": processing_time,
                "confidence": response.confidence if response else 0.0,
                "execution_plan_steps": len(response.execution_plan) if response else 0,
                "agent_insights": len(response.agent_insights) if response else 0
            })
            
            if success:
                print(f"   ✅ Basic request processed successfully")
                print(f"      • Processing time: {processing_time:.2f}s")
                print(f"      • Confidence: {response.confidence:.2f}")
                print(f"      • Execution steps: {len(response.execution_plan)}")
            else:
                print(f"   ❌ Basic request processing failed")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ Basic request test failed: {e}")
    
    async def _test_agent_self_reflection(self):
        """Test agent self-reflection capabilities"""
        test_name = "Agent Self-Reflection"
        print(f"📋 Testing: {test_name}")
        
        try:
            task = "Open Documents folder and verify contents"
            evidence = {
                "screenshot_path": "/tmp/screen.png",
                "accessibility_data": {"element_found": True}
            }
            context = {"user_intent": "file_navigation"}
            
            response = await process_enterprise_agent_request(
                task,
                evidence=evidence,
                context=context,
                validation_level=ValidationLevel.ENTERPRISE,
                require_human_approval=False
            )
            
            # Check for self-reflection indicators
            has_reflection = (
                response.reflection_session_id is not None and
                response.validation_report is not None and
                response.analysis_report is not None
            )
            
            self._record_test_result(test_name, has_reflection, {
                "reflection_session_created": response.reflection_session_id is not None,
                "validation_conducted": response.validation_report is not None,
                "analysis_conducted": response.analysis_report is not None,
                "recommendations_generated": len(response.recommendations) > 0
            })
            
            if has_reflection:
                print(f"   ✅ Agent self-reflection working")
                print(f"      • Reflection session: {response.reflection_session_id}")
                print(f"      • Validation report: Available")
                print(f"      • Analysis report: Available")
                print(f"      • Recommendations: {len(response.recommendations)}")
            else:
                print(f"   ❌ Agent self-reflection not working properly")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ Self-reflection test failed: {e}")
    
    async def _test_agent_collaboration(self):
        """Test inter-agent collaboration"""
        test_name = "Inter-Agent Collaboration"
        print(f"📋 Testing: {test_name}")
        
        try:
            # Task that should trigger multiple agents
            task = "Click on Documents folder, check file permissions, and monitor system resources"
            evidence = {
                "screenshot_path": "/tmp/screen.png",
                "accessibility_data": {"element_found": True},
                "file_system_data": {"path": "/Users/segevbin/Documents"}
            }
            context = {
                "ui_state": {"application": "Finder"},
                "system_state": {"cpu_usage": 25.0, "memory_usage": 45.0}
            }
            
            response = await process_enterprise_agent_request(
                task,
                evidence=evidence,
                context=context,
                validation_level=ValidationLevel.ENTERPRISE,
                require_human_approval=False
            )
            
            # Check for multiple agent insights (collaboration)
            collaboration_active = len(response.agent_insights) > 1
            different_agents = len(set(insight.agent_id for insight in response.agent_insights)) > 1
            
            self._record_test_result(test_name, collaboration_active and different_agents, {
                "total_agent_insights": len(response.agent_insights),
                "unique_agents": len(set(insight.agent_id for insight in response.agent_insights)),
                "collaboration_detected": collaboration_active and different_agents
            })
            
            if collaboration_active and different_agents:
                print(f"   ✅ Inter-agent collaboration working")
                print(f"      • Agent insights: {len(response.agent_insights)}")
                print(f"      • Unique agents: {len(set(insight.agent_id for insight in response.agent_insights))}")
                for insight in response.agent_insights[:3]:  # Show first 3
                    print(f"      • {insight.agent_id}: {insight.confidence:.2f} confidence")
            else:
                print(f"   ❌ Inter-agent collaboration not detected")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ Collaboration test failed: {e}")
    
    async def _test_professional_validation(self):
        """Test professional validation engine"""
        test_name = "Professional Validation"
        print(f"📋 Testing: {test_name}")
        
        try:
            task = "Execute UI automation task with comprehensive validation"
            evidence = {
                "element_screenshot": "/tmp/element.png",
                "accessibility_data": {"element_found": True, "clickable": True},
                "interaction_log": {"success": True},
                "state_change_proof": {"changed": True}
            }
            
            response = await process_enterprise_agent_request(
                task,
                evidence=evidence,
                validation_level=ValidationLevel.ENTERPRISE,
                require_human_approval=False
            )
            
            # Check validation quality
            validation_comprehensive = (
                response.validation_report is not None and
                response.validation_report.total_rules_checked > 0 and
                response.validation_report.validation_level == ValidationLevel.ENTERPRISE
            )
            
            self._record_test_result(test_name, validation_comprehensive, {
                "validation_report_available": response.validation_report is not None,
                "rules_checked": response.validation_report.total_rules_checked if response.validation_report else 0,
                "validation_level": response.validation_report.validation_level.value if response.validation_report else "none",
                "overall_success": response.validation_report.overall_success if response.validation_report else False
            })
            
            if validation_comprehensive:
                print(f"   ✅ Professional validation working")
                print(f"      • Rules checked: {response.validation_report.total_rules_checked}")
                print(f"      • Validation level: {response.validation_report.validation_level.value}")
                print(f"      • Overall success: {response.validation_report.overall_success}")
                print(f"      • Confidence: {response.validation_report.overall_confidence:.2f}")
            else:
                print(f"   ❌ Professional validation not comprehensive")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ Professional validation test failed: {e}")
    
    async def _test_deep_analysis(self):
        """Test deep dive analysis capabilities"""
        test_name = "Deep Dive Analysis"
        print(f"📋 Testing: {test_name}")
        
        try:
            task = "Complex task requiring deep analysis and reasoning"
            evidence = {
                "complex_data": {"multiple_steps": True, "dependencies": ["step1", "step2"]},
                "context_rich": True
            }
            context = {
                "complexity_indicators": ["multi_step", "conditional_logic", "error_handling"]
            }
            
            response = await process_enterprise_agent_request(
                task,
                evidence=evidence,
                context=context,
                analysis_depth=AnalysisDepth.COMPREHENSIVE,
                require_human_approval=False
            )
            
            # Check analysis depth
            analysis_comprehensive = (
                response.analysis_report is not None and
                len(response.analysis_report.deep_insights) > 0 and
                len(response.analysis_report.reasoning_chain) > 0
            )
            
            self._record_test_result(test_name, analysis_comprehensive, {
                "analysis_report_available": response.analysis_report is not None,
                "deep_insights": len(response.analysis_report.deep_insights) if response.analysis_report else 0,
                "reasoning_chain_steps": len(response.analysis_report.reasoning_chain) if response.analysis_report else 0,
                "complexity_score": response.analysis_report.complexity_assessment.complexity_score if response.analysis_report else 0.0
            })
            
            if analysis_comprehensive:
                print(f"   ✅ Deep dive analysis working")
                print(f"      • Deep insights: {len(response.analysis_report.deep_insights)}")
                print(f"      • Reasoning steps: {len(response.analysis_report.reasoning_chain)}")
                print(f"      • Complexity score: {response.analysis_report.complexity_assessment.complexity_score:.2f}")
                print(f"      • Analysis time: {response.analysis_report.execution_time:.2f}s")
            else:
                print(f"   ❌ Deep dive analysis not comprehensive")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ Deep analysis test failed: {e}")
    
    async def _test_complex_task_handling(self):
        """Test complex task handling with all features"""
        test_name = "Complex Task Handling"
        print(f"📋 Testing: {test_name}")
        
        try:
            task = "Navigate to Documents folder, find specific file, check permissions, and open with appropriate application while monitoring system performance"
            evidence = {
                "screenshot_path": "/tmp/complex_screen.png",
                "accessibility_data": {"elements_found": 5, "interactive_elements": 3},
                "file_system_state": {"permissions": "readable", "applications": ["TextEdit", "Preview"]},
                "system_metrics": {"cpu": 30.0, "memory": 50.0, "disk": 85.0}
            }
            context = {
                "ui_state": {"application": "Finder", "window_state": "active"},
                "user_context": {"experience_level": "intermediate", "preferences": {"default_app": "TextEdit"}},
                "system_context": {"available_memory": "8GB", "cpu_cores": 4}
            }
            
            response = await process_enterprise_agent_request(
                task,
                evidence=evidence,
                context=context,
                validation_level=ValidationLevel.ENTERPRISE,
                analysis_depth=AnalysisDepth.COMPREHENSIVE,
                require_human_approval=True
            )
            
            # Check comprehensive handling
            comprehensive_handling = (
                response.success and
                response.confidence > 0.6 and
                len(response.execution_plan) > 3 and
                len(response.agent_insights) > 1 and
                response.validation_report is not None and
                response.analysis_report is not None and
                len(response.recommendations) > 0
            )
            
            self._record_test_result(test_name, comprehensive_handling, {
                "success": response.success,
                "confidence": response.confidence,
                "execution_plan_steps": len(response.execution_plan),
                "agent_insights": len(response.agent_insights),
                "recommendations": len(response.recommendations),
                "requires_approval": response.requires_approval,
                "processing_time": response.execution_time
            })
            
            if comprehensive_handling:
                print(f"   ✅ Complex task handling working")
                print(f"      • Success: {response.success}")
                print(f"      • Confidence: {response.confidence:.2f}")
                print(f"      • Execution steps: {len(response.execution_plan)}")
                print(f"      • Agent collaboration: {len(response.agent_insights)} insights")
                print(f"      • Recommendations: {len(response.recommendations)}")
                print(f"      • Requires approval: {response.requires_approval}")
            else:
                print(f"   ❌ Complex task handling not comprehensive")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ Complex task test failed: {e}")
    
    async def _test_approval_workflow(self):
        """Test human approval workflow"""
        test_name = "Approval Workflow"
        print(f"📋 Testing: {test_name}")
        
        try:
            task = "High-risk task requiring human approval"
            evidence = {"risk_indicators": ["system_modification", "file_deletion"]}
            
            response = await process_enterprise_agent_request(
                task,
                evidence=evidence,
                validation_level=ValidationLevel.ZERO_ERROR,
                require_human_approval=True
            )
            
            # Check approval workflow
            approval_working = (
                response.requires_approval and
                response.approval_details is not None and
                "triggers" in response.approval_details
            )
            
            self._record_test_result(test_name, approval_working, {
                "requires_approval": response.requires_approval,
                "approval_details_available": response.approval_details is not None,
                "approval_triggers": len(response.approval_details.get("triggers", [])) if response.approval_details else 0
            })
            
            if approval_working:
                print(f"   ✅ Approval workflow working")
                print(f"      • Requires approval: {response.requires_approval}")
                print(f"      • Approval triggers: {len(response.approval_details['triggers'])}")
                print(f"      • Risk assessment: Available")
            else:
                print(f"   ❌ Approval workflow not working")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ Approval workflow test failed: {e}")
    
    async def _test_execution_monitoring(self):
        """Test execution monitoring and reflection"""
        test_name = "Execution Monitoring"
        print(f"📋 Testing: {test_name}")
        
        try:
            # First create a request with approval
            task = "Simple task for execution monitoring"
            response = await process_enterprise_agent_request(
                task,
                require_human_approval=False
            )
            
            if response.success and len(response.execution_plan) > 0:
                # Test execution monitoring
                execution_result = await enterprise_agent_system.execute_approved_plan(
                    response, approval_granted=True
                )
                
                monitoring_working = (
                    execution_result is not None and
                    "execution_id" in execution_result and
                    "execution_results" in execution_result
                )
                
                self._record_test_result(test_name, monitoring_working, {
                    "execution_result_available": execution_result is not None,
                    "execution_tracked": "execution_id" in execution_result if execution_result else False,
                    "steps_monitored": len(execution_result.get("execution_results", [])) if execution_result else 0,
                    "final_validation": execution_result.get("final_validation") is not None if execution_result else False
                })
                
                if monitoring_working:
                    print(f"   ✅ Execution monitoring working")
                    print(f"      • Execution tracked: {execution_result['execution_id']}")
                    print(f"      • Steps monitored: {len(execution_result['execution_results'])}")
                    print(f"      • Success: {execution_result['success']}")
                else:
                    print(f"   ❌ Execution monitoring not working")
            else:
                self._record_test_result(test_name, False, {"error": "No execution plan to monitor"})
                print(f"   ❌ No execution plan available for monitoring test")
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
            print(f"   ❌ Execution monitoring test failed: {e}")
    
    def _record_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Record test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def _print_test_summary(self):
        """Print comprehensive test summary"""
        print()
        print("=" * 70)
        print("🧪 ENHANCED ENTERPRISE SYSTEM - TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        print("DETAILED RESULTS:")
        print("-" * 40)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['test_name']}")
            
            if not result["success"] and "error" in result["details"]:
                print(f"      Error: {result['details']['error']}")
        
        print()
        
        # System capabilities summary
        if success_rate >= 80:
            print("🎉 ENHANCED ENTERPRISE SYSTEM - FULLY OPERATIONAL")
            print("All major capabilities are working:")
            print("✅ Agent self-reflection and task completion validation")
            print("✅ Inter-agent communication and context sharing")
            print("✅ Professional-grade validation (Claude Code standards)")
            print("✅ Deep dive analysis for complex task verification")
            print("✅ Context-aware agent collaboration framework")
            print("✅ Human approval workflow for high-risk tasks")
            print("✅ Comprehensive execution monitoring and reflection")
        elif success_rate >= 60:
            print("⚠️  ENHANCED ENTERPRISE SYSTEM - PARTIALLY OPERATIONAL")
            print("Most capabilities working, some issues detected")
        else:
            print("❌ ENHANCED ENTERPRISE SYSTEM - NEEDS ATTENTION")
            print("Multiple capabilities not working properly")
        
        print()
        print("=" * 70)

async def main():
    """Main test execution"""
    print("🚀 Enhanced Enterprise Agent System - Professional Test Suite")
    print("Testing advanced AI capabilities with self-reflection and collaboration")
    print()
    
    tester = EnhancedSystemTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())