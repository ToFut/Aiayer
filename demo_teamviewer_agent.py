#!/usr/bin/env python3
"""
Demo: TeamViewer-Style Agent Execution
Shows enhanced agent mode with visual verification in action
"""

import asyncio
import logging
import sys
import os
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TeamViewerAgentDemo:
    """Demo of TeamViewer-style agent capabilities"""
    
    def __init__(self):
        self.backend = None
        
    async def initialize(self):
        """Initialize the enhanced backend"""
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from enhanced_enterprise_backend_with_context import ContextualAIBackend
            
            self.backend = ContextualAIBackend()
            logger.info("🎯 Enhanced Agent Backend initialized with TeamViewer capabilities")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False
    
    async def demo_enhanced_agent_execution(self):
        """Demo enhanced agent execution with visual verification"""
        
        logger.info("\n🤖 DEMO: Enhanced Agent Mode with TeamViewer-Style Verification")
        logger.info("=" * 70)
        
        # Mock WebSocket for demo
        class DemoWebSocket:
            def __init__(self):
                self.messages = []
                
            async def send(self, message):
                data = json.loads(message)
                self.messages.append(data)
                
                # Log important messages
                msg_type = data.get('type', 'unknown')
                if msg_type == 'agent_plan_ready':
                    logger.info(f"📋 Plan created and ready for execution")
                elif msg_type == 'execution_start':
                    logger.info(f"🚀 Executing: {data.get('action', 'Unknown action')}")
                elif msg_type == 'execution_verification':
                    success = data.get('success', False)
                    changes = data.get('changes', {})
                    change_pct = changes.get('change_percentage', 0) * 100
                    logger.info(f"✅ Verification: {'SUCCESS' if success else 'FAILED'} ({change_pct:.1f}% screen changed)")
        
        demo_ws = DemoWebSocket()
        
        # Test scenarios
        test_scenarios = [
            {
                'name': 'Simple Web Search',
                'message': 'search for python tutorials on google',
                'execution_mode': 'verified'
            },
            {
                'name': 'File Management',
                'message': 'open finder and create a new folder',
                'execution_mode': 'monitored'
            },
            {
                'name': 'Application Control',
                'message': 'open calculator app and perform basic calculation',
                'execution_mode': 'verified'
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"\n📝 Scenario {i}: {scenario['name']}")
            logger.info(f"   Task: {scenario['message']}")
            logger.info(f"   Mode: {scenario['execution_mode']}")
            
            # Create enhanced agent request
            request_data = {
                'message': scenario['message'],
                'session_id': f'demo_session_{i}',
                'execution_mode': scenario['execution_mode']
            }
            
            try:
                # Create automation plan with verification
                result = await self.backend.handle_agent_execution_with_verification(
                    request_data, f'demo_client_{i}', demo_ws
                )
                
                if result.get('success', False):
                    plan_id = result.get('plan_id')
                    logger.info(f"   ✅ Plan created: {plan_id}")
                    
                    # Simulate plan execution (in real use, this would be triggered by user confirmation)
                    if hasattr(self.backend, 'pending_verified_plans') and plan_id in self.backend.pending_verified_plans:
                        logger.info(f"   🎬 Simulating execution with visual verification...")
                        
                        # Get the plan details
                        plan_data = self.backend.pending_verified_plans[plan_id]
                        plan = plan_data['plan']
                        
                        # Show plan details
                        logger.info(f"   📋 Plan type: {plan.get('request_type', 'Unknown')}")
                        logger.info(f"   📊 Estimated duration: {plan.get('estimated_duration', 0):.1f}s")
                        logger.info(f"   🎯 Success probability: {plan.get('success_probability', 0):.1%}")
                        
                        # Simulate execution with verification
                        steps = plan.get('steps', [])
                        logger.info(f"   📝 Steps to execute: {len(steps)}")
                        
                        for step_num, step in enumerate(steps[:3], 1):  # Limit to first 3 steps for demo
                            logger.info(f"      Step {step_num}: {step.get('description', 'Unknown step')}")
                            
                            # Simulate action execution with verification
                            step_result = await self.backend.execute_action_with_verification(step, demo_ws)
                            
                            if step_result.get('success'):
                                changes = step_result.get('verification', {})
                                change_pct = changes.get('change_percentage', 0) * 100
                                logger.info(f"      ✅ Step completed ({change_pct:.2f}% screen changed)")
                            else:
                                logger.info(f"      ❌ Step failed - would retry or use fallback")
                            
                            await asyncio.sleep(0.5)  # Brief pause between steps
                        
                        # Clean up
                        if len(steps) > 3:
                            logger.info(f"   ... (remaining {len(steps) - 3} steps would continue)")
                        
                        logger.info(f"   🎉 Scenario {i} demonstration completed")
                    else:
                        logger.warning(f"   ⚠️ Plan not found for execution demo")
                else:
                    logger.error(f"   ❌ Plan creation failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"   ❌ Scenario {i} failed: {e}")
                
            # Brief pause between scenarios
            await asyncio.sleep(1)
        
        # Show summary
        logger.info(f"\n📊 DEMO SUMMARY:")
        logger.info(f"   Total WebSocket messages: {len(demo_ws.messages)}")
        logger.info(f"   Message types: {set(msg.get('type') for msg in demo_ws.messages)}")
        
        # Show execution analytics
        analytics = await self.backend.get_execution_analytics()
        logger.info(f"   Executions performed: {analytics.get('total_executions', 0)}")
        logger.info(f"   Success rate: {analytics.get('success_rate', 0):.1%}")
        
    async def demo_visual_verification(self):
        """Demo visual verification capabilities"""
        
        logger.info("\n🔍 DEMO: Visual Verification System")
        logger.info("=" * 50)
        
        # Capture current screen
        logger.info("📸 Capturing current screen state...")
        screenshot1 = await self.backend.capture_screen_fast()
        
        if screenshot1 is not None:
            logger.info(f"✅ Screen captured: {screenshot1.shape}")
            
            # Wait a moment and capture again
            await asyncio.sleep(2)
            logger.info("📸 Capturing screen after 2 seconds...")
            screenshot2 = await self.backend.capture_screen_fast()
            
            if screenshot2 is not None:
                # Detect changes
                changes = await self.backend.detect_visual_changes(screenshot1, screenshot2, threshold=0.01)
                
                if changes.get('changes_detected', False):
                    logger.info(f"✅ Changes detected between captures:")
                    logger.info(f"   Change percentage: {changes.get('change_percentage', 0):.3%}")
                    logger.info(f"   Changed regions: {len(changes.get('changed_regions', []))}")
                    logger.info(f"   Confidence: {changes.get('confidence', 0):.2f}")
                else:
                    logger.info("ℹ️ No significant changes detected (screen was stable)")
                    
            else:
                logger.error("❌ Second screen capture failed")
        else:
            logger.error("❌ Initial screen capture failed")
    
    async def run_full_demo(self):
        """Run the complete demo"""
        
        logger.info("🎭 TEAMVIEWER-STYLE AGENT CAPABILITIES DEMO")
        logger.info("=" * 80)
        
        if not await self.initialize():
            logger.error("❌ Failed to initialize demo")
            return
        
        # Demo 1: Visual verification
        await self.demo_visual_verification()
        
        # Demo 2: Enhanced agent execution
        await self.demo_enhanced_agent_execution()
        
        logger.info("\n🎉 DEMO COMPLETED!")
        logger.info("=" * 80)
        logger.info("✨ TeamViewer-style capabilities successfully demonstrated!")
        logger.info("🔥 Your agent can now:")
        logger.info("   • Capture and monitor screen in real-time")
        logger.info("   • Verify task execution with visual evidence") 
        logger.info("   • Provide step-by-step execution feedback")
        logger.info("   • Detect and analyze screen changes")
        logger.info("   • Execute tasks with TeamViewer-level precision")

async def main():
    """Main demo execution"""
    demo = TeamViewerAgentDemo()
    await demo.run_full_demo()

if __name__ == "__main__":
    asyncio.run(main())