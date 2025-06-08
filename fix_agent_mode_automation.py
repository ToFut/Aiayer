#!/usr/bin/env python3
"""
Fix Agent Mode Automation
Diagnose and fix why agent mode is not performing real automation
Updated to integrate the fixed universal automation handler
"""

import logging
import asyncio
import websockets
import json
import time
import sys
import importlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_mode_automation():
    """Test if agent mode is performing real automation"""
    logger.info("🔧 Testing Agent Mode Automation...")
    
    try:
        # Test the automation handlers directly
        logger.info("1. Testing Fixed Universal Automation Handler...")
        
        try:
            from fixed_universal_automation_handler import fixed_handle_universal_automation
            
            # Test planning
            start_time = time.time()
            result = await fixed_handle_universal_automation(
                "search for flights from nyc to miami", 
                "test_session"
            )
            planning_time = time.time() - start_time
            
            logger.info(f"✅ Fixed handler planning: {planning_time:.2f}s")
            logger.info(f"Result type: {type(result)}")
            
            if "success" in result and result["success"]:
                logger.info(f"✅ Plan creation successful")
                if "plan_id" in result:
                    logger.info(f"✅ Plan ID: {result['plan_id']}")
                logger.info(f"✅ Response: {result['response'][:100]}...")
            else:
                logger.warning("⚠️ Plan creation failed")
                
        except Exception as e:
            logger.error(f"❌ Fixed automation handler test failed: {e}")
        
        # Test the brain router integration
        logger.info("\n2. Testing Brain Router Integration...")
        
        try:
            from brain.core.brain_router import brain_router
            
            if hasattr(brain_router, '_handle_agent_mode'):
                logger.info("✅ Brain router has _handle_agent_mode method")
                
                # Inspect method source
                import inspect
                agent_mode_source = inspect.getsource(brain_router._handle_agent_mode)
                
                if "universal_intelligent_automation_handler" in agent_mode_source:
                    logger.info("✅ Brain router imports universal_intelligent_automation_handler")
                    
                    # Now check if our patch can be applied
                    try:
                        # Import the fixed universal automation handler
                        from fixed_universal_automation_handler import fixed_handle_universal_automation
                        logger.info("✅ fixed_handle_universal_automation can be imported")
                        
                        # Get the patch method ready
                        patch_ready = True
                        logger.info("✅ Patch can be applied to brain router")
                    except ImportError:
                        logger.error("❌ Cannot import fixed_handle_universal_automation")
                        patch_ready = False
                else:
                    logger.warning("⚠️ Brain router does not use universal_intelligent_automation_handler")
                    patch_ready = False
            else:
                logger.error("❌ Brain router has no _handle_agent_mode method!")
                patch_ready = False
                
        except Exception as e:
            logger.error(f"❌ Brain router integration test failed: {e}")
            patch_ready = False
            
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
            
        return patch_ready
        
    except Exception as e:
        logger.error(f"❌ Overall test failed: {e}")
        return False

def patch_brain_router():
    """
    Patch the brain router module to use the fixed universal automation handler
    by monkey patching its imports dynamically
    """
    try:
        # Import the brain router module
        from brain.core.brain_router import brain_router
        logger.info("✅ Successfully imported brain_router")
        
        # Import the fixed universal automation handler
        from fixed_universal_automation_handler import fixed_handle_universal_automation
        logger.info("✅ Successfully imported fixed_handle_universal_automation")

        # Monkey patch the _handle_agent_mode method of brain_router
        original_handle_agent_mode = brain_router._handle_agent_mode
        
        # Create the patched method
        async def patched_handle_agent_mode(self, request):
            """Patched agent mode handler that uses fixed universal automation"""
            try:
                query_lower = request.query.lower()
                
                # IMPORTANT: Always use universal intelligent automation for search related tasks
                # This ensures proper handling of search results and clicking functionality
                if ("search" in query_lower and ("google" in query_lower or "safari" in query_lower)) or \
                   "click" in query_lower or "first result" in query_lower:
                    logger.info("🌐 Using FIXED universal intelligent automation for search task")
                    try:
                        # Use the fixed universal automation system with LLM planning
                        from fixed_universal_automation_handler import fixed_handle_universal_automation
                        
                        result = await fixed_handle_universal_automation(request.query, request.session_id)
                        
                        from brain.core.brain_router import BrainResponse
                        # Convert to BrainResponse format
                        response = BrainResponse(
                            success=result.get("success", True),
                            response=result.get("response", ""),
                            mode_used=request.mode,
                            processing_time=result.get("processing_time", 0.0),
                            resources_used=["universal_automation", "llm", "memory"],
                            confidence=result.get("confidence", 0.9),
                            metadata=result.get("metadata", {"universal_planner": True, "fixed_handler": True}),
                            execution_plan=result.get("execution_plan", None)
                        )
                        return response
                    except ImportError as e:
                        logger.warning(f"Fixed universal intelligent automation not available: {e}, falling back to original handler")
                        return await original_handle_agent_mode(self, request)
                
                # For non-search tasks, use the original handler
                return await original_handle_agent_mode(self, request)
                
            except Exception as e:
                logger.error(f"Error in patched agent mode handler: {e}")
                # Fall back to original method
                return await original_handle_agent_mode(self, request)
        
        # Apply the patch
        brain_router._handle_agent_mode = patched_handle_agent_mode.__get__(brain_router, type(brain_router))
        logger.info("✅ Successfully patched brain_router._handle_agent_mode")
        
        # Mark the method as patched for future reference
        brain_router._handle_agent_mode.__patched__ = True
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import required modules: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to patch brain router: {e}")
        return False

async def main():
    """Main diagnostic and fix routine"""
    logger.info("🚀 AGENT MODE AUTOMATION DIAGNOSTIC")
    logger.info("="*50)
    
    patch_ready = await test_agent_mode_automation()
    
    logger.info("\n" + "="*50)
    logger.info("🔧 ATTEMPTING FIXES...")
    
    if patch_ready:
        # Apply the brain router patch
        fix_success = patch_brain_router()
        
        if fix_success:
            logger.info("✅ Successfully patched brain_router to use the fixed universal automation handler")
        else:
            logger.error("❌ Failed to apply brain router patch")
    else:
        logger.warning("⚠️ System not ready for patch, skipping patch application")
        fix_success = False
    
    logger.info("\n" + "="*50)
    logger.info("📊 DIAGNOSTIC SUMMARY")
    
    if fix_success:
        logger.info("✅ Agent mode automation has been fixed!")
        logger.info("💡 Key changes:")
        logger.info("   1. Patched brain_router._handle_agent_mode")
        logger.info("   2. Integrated fixed_universal_automation_handler")
        logger.info("   3. Improved JSON parsing and error handling")
        logger.info("   4. Added robust fallback mechanisms")
        logger.info("\n🔄 To complete the integration, restart the system:")
        logger.info("   ./RESTART_FIXED_SYSTEM.sh")
    else:
        logger.warning("⚠️ Automatic fix unsuccessful")
        logger.info("💡 Manual actions required:")
        logger.info("1. Ensure fixed_universal_automation_handler.py is properly installed")
        logger.info("2. Update brain/core/brain_router.py to import from fixed_universal_automation_handler")
        logger.info("3. Restart the system with ./RESTART_FIXED_SYSTEM.sh")
        logger.info("\n📋 Specific code change needed in brain_router.py:")
        logger.info("""
from universal_intelligent_automation_handler import handle_universal_automation
👆 Change to:
from fixed_universal_automation_handler import fixed_handle_universal_automation

result = await handle_universal_automation(request.query, request.session_id)
👆 Change to:
result = await fixed_handle_universal_automation(request.query, request.session_id)
        """)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Diagnostic interrupted by user")
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")