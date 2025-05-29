#!/usr/bin/env python3
"""
Deep Dive Debug: Agent Mode Root Cause Analysis
Traces the complete execution flow to find why Agent Mode isn't working
"""

import asyncio
import json
import websockets
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentModeDebugger:
    def __init__(self):
        self.websocket = None
        self.message_count = 0
        self.responses = []
    
    async def connect_to_backend(self):
        """Connect to the backend WebSocket"""
        try:
            self.websocket = await websockets.connect("ws://localhost:8767")
            logger.info("✅ Connected to backend WebSocket")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to backend: {e}")
            return False
    
    async def send_agent_request(self, message: str):
        """Send an Agent Mode request and capture the response"""
        if not self.websocket:
            logger.error("❌ Not connected to backend")
            return None
        
        self.message_count += 1
        request_id = f"debug_{self.message_count}_{int(time.time())}"
        
        # Create Agent Mode request
        request = {
            "type": "chat_request",
            "mode": "agent",  # This should trigger Agent Mode
            "message": message,
            "session_id": request_id,
            "client_id": f"debug_client_{self.message_count}",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"📤 Sending Agent Mode request:")
        logger.info(f"   Message: '{message}'")
        logger.info(f"   Mode: {request['mode']}")
        logger.info(f"   Type: {request['type']}")
        
        try:
            # Send request
            await self.websocket.send(json.dumps(request))
            logger.info(f"✅ Request sent at {datetime.now().strftime('%H:%M:%S')}")
            
            # Wait for response
            logger.info("⏳ Waiting for response...")
            
            response_data = None
            timeout = 30  # 30 second timeout
            start_time = time.time()
            
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
                response_data = json.loads(response)
                elapsed = time.time() - start_time
                
                logger.info(f"📥 Response received in {elapsed:.2f}s:")
                logger.info(f"   Type: {response_data.get('type', 'unknown')}")
                logger.info(f"   Mode: {response_data.get('mode', 'unknown')}")
                logger.info(f"   Success: {response_data.get('success', 'unknown')}")
                
                # Check for Agent Mode indicators
                has_buttons = bool(response_data.get('buttons', []))
                requires_confirmation = response_data.get('requiresConfirmation', False)
                is_interactive = response_data.get('interactive', False)
                has_plan_id = bool(response_data.get('plan_id', ''))
                is_real_agent = response_data.get('real_agent_automation', False)
                
                logger.info(f"🔍 Agent Mode Analysis:")
                logger.info(f"   Has Buttons: {has_buttons}")
                logger.info(f"   Requires Confirmation: {requires_confirmation}")
                logger.info(f"   Interactive: {is_interactive}")
                logger.info(f"   Has Plan ID: {has_plan_id}")
                logger.info(f"   Real Agent Handler: {is_real_agent}")
                
                # Analyze response content
                response_text = response_data.get('response', '')
                if len(response_text) > 200:
                    response_preview = response_text[:200] + "..."
                else:
                    response_preview = response_text
                
                logger.info(f"💬 Response Content: '{response_preview}'")
                
                # Determine if it's working correctly
                is_execution_plan = (has_buttons or requires_confirmation or is_interactive or has_plan_id)
                is_conversational = not is_execution_plan and len(response_text) > 50 and not has_plan_id
                
                if is_real_agent and is_execution_plan:
                    logger.info("✅ SUCCESS: Agent Mode working correctly!")
                    logger.info("🎯 Real Agent Automation Handler is being used")
                    logger.info("🔘 Should show DO/DISMISS/ADJUST buttons")
                    status = "SUCCESS"
                elif is_execution_plan:
                    logger.info("⚠️ PARTIAL: Execution plan detected but not using Real Agent Handler")
                    logger.info("🔄 Using fallback automation handler")
                    status = "PARTIAL"
                elif is_conversational:
                    logger.info("❌ FAILED: Getting conversational response instead of execution plan")
                    logger.info("🚨 Agent Mode is not working as expected")
                    status = "FAILED"
                else:
                    logger.info("❓ UNCLEAR: Unexpected response format")
                    status = "UNCLEAR"
                
                # Store response for analysis
                self.responses.append({
                    'request': request,
                    'response': response_data,
                    'status': status,
                    'elapsed_time': elapsed,
                    'timestamp': datetime.now().isoformat()
                })
                
                return response_data
                
            except asyncio.TimeoutError:
                logger.error(f"⏰ Timeout waiting for response after {timeout}s")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error sending request: {e}")
            return None
    
    async def run_comprehensive_test(self):
        """Run comprehensive Agent Mode tests"""
        
        print("🔬 Agent Mode Deep Dive Analysis")
        print("=" * 60)
        
        # Connect to backend
        if not await self.connect_to_backend():
            print("❌ Cannot connect to backend. Make sure it's running on port 8767")
            return False
        
        # Test messages that should trigger Agent Mode
        test_messages = [
            "open Google and search Miami flights",
            "search Omer Adam in Spotify", 
            "click the calculator button",
            "open Safari and navigate to YouTube",
            "find best restaurants in New York"
        ]
        
        print(f"\n🧪 Testing {len(test_messages)} Agent Mode requests...")
        
        results = []
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Test {i}/{len(test_messages)} ---")
            response = await self.send_agent_request(message)
            
            if response:
                results.append(response)
            else:
                logger.error(f"❌ Test {i} failed - no response")
            
            # Wait between tests
            await asyncio.sleep(2)
        
        # Analyze results
        print(f"\n📊 ANALYSIS SUMMARY:")
        print("=" * 60)
        
        success_count = sum(1 for r in self.responses if r['status'] == 'SUCCESS')
        partial_count = sum(1 for r in self.responses if r['status'] == 'PARTIAL')
        failed_count = sum(1 for r in self.responses if r['status'] == 'FAILED')
        
        print(f"✅ Success: {success_count}/{len(self.responses)}")
        print(f"⚠️ Partial: {partial_count}/{len(self.responses)}")
        print(f"❌ Failed: {failed_count}/{len(self.responses)}")
        
        if success_count == len(self.responses):
            print("\n🎉 EXCELLENT: Agent Mode is working perfectly!")
        elif success_count + partial_count == len(self.responses):
            print("\n⚠️ NEEDS IMPROVEMENT: Agent Mode partially working")
        else:
            print("\n🚨 CRITICAL: Agent Mode has serious issues")
        
        # Detailed analysis
        print(f"\n🔍 DETAILED FINDINGS:")
        
        real_agent_count = sum(1 for r in self.responses if r['response'].get('real_agent_automation', False))
        interactive_count = sum(1 for r in self.responses if r['response'].get('interactive', False))
        button_count = sum(1 for r in self.responses if bool(r['response'].get('buttons', [])))
        
        print(f"   🎯 Using Real Agent Handler: {real_agent_count}/{len(self.responses)}")
        print(f"   🎮 Interactive Responses: {interactive_count}/{len(self.responses)}")
        print(f"   🔘 Responses with Buttons: {button_count}/{len(self.responses)}")
        
        # Response types analysis
        response_types = {}
        for r in self.responses:
            response_type = r['response'].get('type', 'unknown')
            response_types[response_type] = response_types.get(response_type, 0) + 1
        
        print(f"   📋 Response Types: {response_types}")
        
        # Identify root cause
        print(f"\n🎯 ROOT CAUSE ANALYSIS:")
        
        if real_agent_count == 0:
            print("❌ PRIMARY ISSUE: Real Agent Automation Handler is NOT being used")
            print("💡 FIX: Check backend handler initialization and routing logic")
        elif interactive_count == 0:
            print("❌ PRIMARY ISSUE: Responses are not interactive (no execution plans)")
            print("💡 FIX: Check Agent Mode detection and response formatting")
        elif button_count == 0:
            print("❌ PRIMARY ISSUE: No buttons in responses (frontend won't show DO/DISMISS/ADJUST)")
            print("💡 FIX: Check response format and button generation")
        else:
            print("✅ Agent Mode appears to be working correctly")
        
        # Save detailed report
        with open(f"agent_mode_debug_report_{int(time.time())}.json", "w") as f:
            json.dump({
                'summary': {
                    'total_tests': len(self.responses),
                    'success_count': success_count,
                    'partial_count': partial_count,
                    'failed_count': failed_count,
                    'real_agent_usage': real_agent_count,
                    'interactive_responses': interactive_count,
                    'responses_with_buttons': button_count
                },
                'responses': self.responses,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved: agent_mode_debug_report_{int(time.time())}.json")
        
        await self.websocket.close()
        return success_count == len(self.responses)

async def main():
    """Main debug function"""
    debugger = AgentModeDebugger()
    
    try:
        success = await debugger.run_comprehensive_test()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Debug interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Debug failed: {e}")
        logger.error(f"Debug error: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())