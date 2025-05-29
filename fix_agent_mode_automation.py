#!/usr/bin/env python3
"""
Fix Agent Mode Automation
Diagnose and fix why agent mode is not performing real automation
"""

import logging
import asyncio
import websockets
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_mode_automation():
    """Test if agent mode is performing real automation"""
    logger.info("🔧 Testing Agent Mode Automation...")
    
    try:
        # Test the automation handlers directly
        logger.info("1. Testing Fast Universal Automation Handler...")
        
        try:
            from fast_universal_automation_handler import FastUniversalAutomationHandler
            handler = FastUniversalAutomationHandler()
            
            # Test planning
            start_time = time.time()
            plan = await handler.create_universal_automation_plan(
                "search for flights from nyc to miami", 
                "test_session"
            )
            planning_time = time.time() - start_time
            
            logger.info(f"✅ Fast handler planning: {planning_time:.2f}s")
            logger.info(f"Plan type: {type(plan)}")
            
            if hasattr(plan, 'steps') and plan.steps:
                logger.info(f"✅ Plan has {len(plan.steps)} steps")
                for i, step in enumerate(plan.steps[:3]):
                    logger.info(f"  Step {i+1}: {step.description}")
            else:
                logger.warning("⚠️ Plan has no steps")
                
        except Exception as e:
            logger.error(f"❌ Fast automation handler test failed: {e}")
        
        # Test backend automation integration
        logger.info("\n2. Testing Backend Automation Integration...")
        
        try:
            from enhanced_enterprise_backend_with_context import ContextualAIBackend
            backend = ContextualAIBackend()
            
            if hasattr(backend, 'automation_handler') and backend.automation_handler:
                logger.info(f"✅ Backend has automation handler: {type(backend.automation_handler)}")
                
                # Test if it can create plans
                if hasattr(backend.automation_handler, 'create_universal_automation_plan'):
                    logger.info("✅ Automation handler has create_universal_automation_plan method")
                else:
                    logger.warning("⚠️ Automation handler missing create_universal_automation_plan method")
                    
            else:
                logger.error("❌ Backend has no automation handler!")
                logger.info("Available attributes:", [attr for attr in dir(backend) if 'automation' in attr.lower()])
                
        except Exception as e:
            logger.error(f"❌ Backend automation test failed: {e}")
            
        # Test via WebSocket
        logger.info("\n3. Testing Agent Mode via WebSocket...")
        
        try:
            async with websockets.connect('ws://localhost:8767/ws', ping_timeout=10) as ws:
                # Get connection message
                await ws.recv()
                
                # Send agent mode request
                test_request = {
                    'type': 'chat_request',
                    'mode': 'agent',
                    'message': 'open google and search for python',
                    'client_id': 'automation_test'
                }
                
                logger.info("📤 Sending agent mode request...")
                await ws.send(json.dumps(test_request))
                
                # Collect responses
                responses = []
                start_time = time.time()
                timeout = 30  # 30 second timeout
                
                while time.time() - start_time < timeout:
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=2)
                        data = json.loads(response)
                        
                        if data.get('type') == 'chat_response':
                            responses.append(data.get('content', ''))
                        elif data.get('type') == 'chat_complete':
                            break
                        elif data.get('type') == 'automation_plan':
                            logger.info("✅ Received automation plan!")
                            logger.info(f"Plan details: {data}")
                        elif data.get('type') == 'automation_execution':
                            logger.info("✅ Automation execution detected!")
                            logger.info(f"Execution: {data}")
                            
                    except asyncio.TimeoutError:
                        continue
                        
                full_response = ''.join(responses)
                logger.info(f"📥 Agent mode response: {full_response[:200]}...")
                
                # Analyze the response
                if any(keyword in full_response.lower() for keyword in ['click', 'open', 'automation', 'executing', 'steps']):
                    logger.info("✅ Response indicates automation is working")
                elif any(keyword in full_response.lower() for keyword in ['visit', 'suggest', 'recommend', 'unable', 'cannot']):
                    logger.warning("⚠️ Response is giving suggestions instead of automation")
                    logger.warning("This indicates agent mode is not performing real automation")
                else:
                    logger.info("ℹ️ Response analysis inconclusive")
                    
        except Exception as e:
            logger.error(f"❌ WebSocket agent test failed: {e}")
            
    except Exception as e:
        logger.error(f"❌ Overall test failed: {e}")

async def fix_automation_handler_connection():
    """Fix the automation handler connection in the backend"""
    logger.info("\n🔧 Attempting to fix automation handler connection...")
    
    try:
        # Check what automation handlers are available
        automation_handlers = []
        
        try:
            from fast_universal_automation_handler import FastUniversalAutomationHandler
            automation_handlers.append(("FastUniversalAutomationHandler", FastUniversalAutomationHandler))
            logger.info("✅ FastUniversalAutomationHandler available")
        except ImportError:
            logger.warning("⚠️ FastUniversalAutomationHandler not available")
            
        try:
            from real_agent_automation_handler import RealAgentAutomationHandler
            automation_handlers.append(("RealAgentAutomationHandler", RealAgentAutomationHandler))
            logger.info("✅ RealAgentAutomationHandler available")
        except ImportError:
            logger.warning("⚠️ RealAgentAutomationHandler not available")
            
        if not automation_handlers:
            logger.error("❌ No automation handlers available!")
            return False
            
        # Try to manually connect the handler
        logger.info("Attempting to manually connect automation handler...")
        
        # Import and modify the backend
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        
        # Create a new backend instance with forced automation handler
        backend = ContextualAIBackend()
        
        # Manually set the automation handler
        handler_name, handler_class = automation_handlers[0]
        backend.automation_handler = handler_class()
        
        logger.info(f"✅ Manually connected {handler_name}")
        
        # Test it
        if hasattr(backend.automation_handler, 'create_universal_automation_plan'):
            test_plan = await backend.automation_handler.create_universal_automation_plan(
                "test automation", "test_session"
            )
            logger.info("✅ Manual automation handler test successful")
            return True
        else:
            logger.error("❌ Manual handler missing required methods")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fix attempt failed: {e}")
        return False

async def main():
    """Main diagnostic and fix routine"""
    logger.info("🚀 AGENT MODE AUTOMATION DIAGNOSTIC")
    logger.info("="*50)
    
    await test_agent_mode_automation()
    
    logger.info("\n" + "="*50)
    logger.info("🔧 ATTEMPTING FIXES...")
    
    fix_success = await fix_automation_handler_connection()
    
    logger.info("\n" + "="*50)
    logger.info("📊 DIAGNOSTIC SUMMARY")
    
    if fix_success:
        logger.info("✅ Automation handler connection fixed")
        logger.info("💡 Restart the backend to apply the fix:")
        logger.info("   pkill -f enhanced_enterprise_backend")
        logger.info("   ./START_ENHANCED_SYSTEM.sh")
    else:
        logger.warning("⚠️ Manual fix unsuccessful")
        logger.info("💡 Required actions:")
        logger.info("1. Check if automation handlers are properly installed")
        logger.info("2. Verify import paths in enhanced_enterprise_backend_with_context.py")
        logger.info("3. Restart system with ./START_ENHANCED_SYSTEM.sh")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Diagnostic interrupted by user")
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")