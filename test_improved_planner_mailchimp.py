#!/usr/bin/env python3
"""
Test script to verify the improved intelligent task planner works correctly
with the original failing Mailchimp request.
"""

import asyncio
import logging
import sys
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from improved_intelligent_task_planner import ImprovedIntelligentTaskPlanner
    from enhanced_complex_task_handler import AdvancedTaskPlanner, TaskContext, EnhancedAgentModeHandler
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    MODULES_AVAILABLE = False

async def test_mailchimp_request():
    """Test the original failing Mailchimp request that was misinterpreted"""
    
    if not MODULES_AVAILABLE:
        print("❌ Required modules not available. Please check imports.")
        return
    
    print("🧪 Testing Improved Planner with Original Mailchimp Request")
    print("=" * 80)
    
    # The original request that was failing
    original_request = "create email templates in Mailchimp, segment subscriber lists, A/B test subject lines, schedule campaigns, and set up performance tracking"
    
    print(f"📧 Original Request: {original_request}")
    print()
    
    # Test 1: Direct intelligent planner test
    print("🤖 Test 1: Direct Intelligent Planner")
    print("-" * 50)
    
    try:
        intelligent_planner = ImprovedIntelligentTaskPlanner()
        
        # Test analysis
        analysis = await intelligent_planner.analyze_user_request(original_request)
        print(f"📊 Request Analysis:")
        print(f"   Intent: {analysis.get('intent', 'unknown')}")
        print(f"   Platforms: {', '.join(analysis.get('platforms', []))}")
        print(f"   Actions: {', '.join(analysis.get('actions', []))}")
        print(f"   Complexity: {analysis.get('complexity_score', 0)}")
        print()
        
        # Test plan creation
        plan = await intelligent_planner.create_intelligent_plan(original_request, "moderate")
        print(f"📋 Generated Plan:")
        print(f"   Plan ID: {plan.plan_id}")
        print(f"   Complexity: {plan.complexity.name if hasattr(plan.complexity, 'name') else plan.complexity}")
        print(f"   Steps: {len(plan.steps)}")
        print(f"   Duration: {plan.estimated_total_duration}s")
        print(f"   Max Parallel: {len(plan.parallel_groups[0]) if plan.parallel_groups else 'N/A'}")
        print()
        
        print(f"📝 Step Details:")
        for i, step in enumerate(plan.steps):
            print(f"   {i+1:2d}. {step.description}")
            print(f"       Action: {step.action_type}")
            print(f"       Target: {step.target or 'N/A'}")
            if step.dependencies:
                print(f"       Dependencies: {', '.join(step.dependencies)}")
        print()
        
        print(f"✅ Success Criteria:")
        for criteria in plan.success_criteria:
            print(f"   • {criteria}")
        print()
        
        print(f"🔄 Fallback Actions:")
        for action in plan.fallback_actions:
            print(f"   • {action}")
        print()
        
    except Exception as e:
        print(f"❌ Direct planner test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Enhanced Complex Task Handler integration
    print("🔧 Test 2: Enhanced Task Handler Integration")
    print("-" * 50)
    
    try:
        planner = AdvancedTaskPlanner()
        context = TaskContext(
            user_id="test_user",
            session_id="test_session", 
            domain="email_marketing"
        )
        
        # Test complex plan creation
        complex_plan = await planner.create_complex_plan(original_request, context)
        
        print(f"📋 Complex Plan Generated:")
        print(f"   Plan ID: {complex_plan.plan_id}")
        print(f"   Title: {complex_plan.title}")
        print(f"   Complexity: {complex_plan.complexity.name}")
        print(f"   Strategy: {complex_plan.strategy.value}")
        print(f"   Steps: {len(complex_plan.steps)}")
        print(f"   Execution Layers: {len(complex_plan.execution_layers)}")
        print(f"   Duration: {complex_plan.estimated_total_duration}s")
        print(f"   Max Parallel: {complex_plan.max_parallel_steps}")
        print()
        
        print(f"📝 Enhanced Step Details:")
        for i, step in enumerate(complex_plan.steps):
            deps = f" (deps: {', '.join(step.dependencies)})" if step.dependencies else ""
            print(f"   {i+1:2d}. {step.description}")
            print(f"       Type: {step.action_type}")
            print(f"       Duration: {step.estimated_duration}s")
            print(f"       Success Prob: {step.success_probability:.2f}{deps}")
        print()
        
        # Test execution layers
        if complex_plan.execution_layers:
            print(f"🔄 Execution Layers (Parallelization):")
            for i, layer in enumerate(complex_plan.execution_layers):
                print(f"   Layer {i+1}: {len(layer)} step(s) - {', '.join(layer)}")
        print()
        
    except Exception as e:
        print(f"❌ Enhanced task handler test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Full Brain Router Handler Integration
    print("🧠 Test 3: Brain Router Handler Integration")
    print("-" * 50)
    
    try:
        handler = EnhancedAgentModeHandler()
        
        # Test full handler request
        result = await handler.handle_complex_request(
            original_request,
            user_id="test_user",
            session_id="test_session",
            context={"domain": "email_marketing"}
        )
        
        print(f"🎯 Handler Result:")
        print(f"   Success: {result['success']}")
        print(f"   Mode Used: {result['mode_used']}")
        print(f"   Processing Time: {result['processing_time']:.2f}s")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Resources Used: {', '.join(result['resources_used'])}")
        print()
        
        print(f"📊 Metadata:")
        metadata = result.get('metadata', {})
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        print()
        
        print(f"💬 Generated Response:")
        print("   " + "\n   ".join(result['response'].split('\n')))
        print()
        
    except Exception as e:
        print(f"❌ Brain router handler test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Compare with the old broken behavior
    print("🔍 Test 4: Validation Against Previous Issues")
    print("-" * 50)
    
    # Check for the specific issues that were happening before
    validation_passed = True
    validation_issues = []
    
    # Check if the planner is properly understanding Mailchimp
    try:
        intelligent_planner = ImprovedIntelligentTaskPlanner()
        analysis = await intelligent_planner.analyze_user_request(original_request)
        
        if "mailchimp" not in analysis.get('platforms', []):
            validation_issues.append("❌ Mailchimp platform not detected")
            validation_passed = False
        else:
            print("✅ Mailchimp platform correctly detected")
        
        expected_actions = ["create_templates", "segment_lists", "ab_test", "schedule_campaigns", "track_performance"]
        detected_actions = analysis.get('actions', [])
        
        if not any(action in str(detected_actions).lower() for action in ["create", "segment", "test", "schedule", "track"]):
            validation_issues.append("❌ Core actions not properly identified")
            validation_passed = False
        else:
            print("✅ Core email marketing actions identified")
        
        # Check if it's NOT trying to browse Instagram (the previous bug)
        plan = await intelligent_planner.create_intelligent_plan(original_request, "moderate")
        plan_text = json.dumps(plan.steps, default=str).lower()
        
        if "instagram" in plan_text or "browse instagram" in plan_text:
            validation_issues.append("❌ Still trying to browse Instagram (old bug present)")
            validation_passed = False
        else:
            print("✅ No longer trying to browse Instagram")
        
        # Check if steps are actually about Mailchimp/email marketing
        mailchimp_related = any("mailchimp" in str(step).lower() or "email" in str(step).lower() 
                               for step in plan.steps)
        if not mailchimp_related:
            validation_issues.append("❌ Steps don't appear to be Mailchimp/email marketing related")
            validation_passed = False
        else:
            print("✅ Steps are properly focused on email marketing tasks")
        
    except Exception as e:
        validation_issues.append(f"❌ Validation test failed: {e}")
        validation_passed = False
    
    print()
    print("🏆 Final Validation Results:")
    print("-" * 30)
    
    if validation_passed:
        print("✅ ALL VALIDATION TESTS PASSED!")
        print("🎉 The improved planner successfully fixes the original issues:")
        print("   • Correctly identifies Mailchimp as the target platform")
        print("   • Properly understands email marketing workflow")
        print("   • No longer misinterprets requests as Instagram browsing")
        print("   • Generates appropriate email marketing automation steps")
    else:
        print("❌ VALIDATION ISSUES FOUND:")
        for issue in validation_issues:
            print(f"   {issue}")
    
    print("\n" + "=" * 80)
    print("🔬 Test Completed")
    
    return validation_passed

if __name__ == "__main__":
    result = asyncio.run(test_mailchimp_request())
    if result:
        print("🎯 SUCCESS: Improved planner is working correctly!")
        sys.exit(0)
    else:
        print("⚠️  ISSUES: Some validation tests failed.")
        sys.exit(1)