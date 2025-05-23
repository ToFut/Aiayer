#!/usr/bin/env python3
"""
Deep Dive Mode Tester - Tests each mode individually for contextual behavior
"""

import asyncio
import json
import websockets
import time
from datetime import datetime

class DeepDiveModeeTester:
    def __init__(self):
        self.brain_router_url = "ws://localhost:8765"
        self.enterprise_backend_url = "ws://localhost:8767"
        
    async def test_agent_mode_deep(self, websocket, server_name):
        """Deep dive test for Agent mode - UI automation with context"""
        print(f"\n🎯 DEEP DIVE: AGENT MODE - {server_name}")
        print("=" * 60)
        print("Expected: UI automation responses with contextual memory")
        print("Should learn patterns, remember preferences, provide execution details")
        
        agent_tests = [
            {
                "message": "click on the Documents folder",
                "expected_context": "UI automation, file navigation",
                "test_description": "Basic UI automation request"
            },
            {
                "message": "help me organize my files",
                "expected_context": "File management, organization patterns",
                "test_description": "File organization automation"
            },
            {
                "message": "click on the same Documents folder again",
                "expected_context": "Should reference previous click action",
                "test_description": "Repetitive action with memory"
            },
            {
                "message": "open the Chrome browser",
                "expected_context": "Application launching, browser usage",
                "test_description": "Application automation"
            },
            {
                "message": "type 'hello world' in the search box",
                "expected_context": "Text input, search patterns",
                "test_description": "Text input automation"
            },
            {
                "message": "help me automate my daily workflow",
                "expected_context": "Should reference previous actions and suggest patterns",
                "test_description": "Workflow automation with historical context"
            }
        ]
        
        for i, test in enumerate(agent_tests, 1):
            print(f"\n🧪 Agent Test {i}: {test['test_description']}")
            print(f"📝 Message: '{test['message']}'")
            print(f"🎯 Expected Context: {test['expected_context']}")
            
            request = {
                "type": "chat_request",
                "mode": "Agent",
                "message": test["message"],
                "session_id": f"agent_test_session_{int(time.time())}"
            }
            
            await websocket.send(json.dumps(request))
            response_raw = await asyncio.wait_for(websocket.recv(), timeout=20)
            response = json.loads(response_raw)
            
            # Get response content with better error handling
            response_text = response.get('response', '')
            if not response_text:
                payload = response.get('payload', {})
                response_text = payload.get('response', '')
            if not response_text:
                response_text = f"No response field found. Full response: {response}"
            context_used = response.get('context_used', {})
            context_metrics = response.get('context_metrics', {})
            
            print(f"📥 Response: {response_text}")
            print(f"📊 Context Used: {context_used}")
            print(f"🧠 Context Metrics: {context_metrics}")
            
            # Analyze Agent mode quality
            agent_indicators = ['🎯', 'execute', 'click', 'automation', 'locate', 'perform']
            context_indicators = ['previous', 'similar', 'based on', 'recall', 'pattern']
            
            has_agent_nature = any(indicator in response_text.lower() for indicator in agent_indicators)
            has_context_awareness = any(indicator in response_text.lower() for indicator in context_indicators)
            
            print(f"✅ Agent Nature: {'YES' if has_agent_nature else 'NO'}")
            print(f"🧠 Context Awareness: {'YES' if has_context_awareness else 'NO'}")
            
            if not has_agent_nature:
                print("❌ ISSUE: Response doesn't reflect Agent mode nature")
            if not has_context_awareness and i > 1:  # First response might not have context
                print("❌ ISSUE: No contextual awareness detected")
            
            print("-" * 50)
            await asyncio.sleep(3)  # Allow memory to process
            
    async def test_ask_mode_deep(self, websocket, server_name):
        """Deep dive test for Ask mode - Knowledge retrieval with context"""
        print(f"\n💭 DEEP DIVE: ASK MODE - {server_name}")
        print("=" * 60)
        print("Expected: Knowledge retrieval with semantic search")
        print("Should search memory, provide contextual answers, reference conversations")
        
        ask_tests = [
            {
                "message": "what is the system status?",
                "expected_context": "System information, operational status",
                "test_description": "System status query"
            },
            {
                "message": "what files have I been working with?",
                "expected_context": "File activity, work patterns",
                "test_description": "Personal activity query"
            },
            {
                "message": "what did we talk about before?",
                "expected_context": "Conversation history, previous interactions",
                "test_description": "Conversation memory query"
            },
            {
                "message": "how many chat modes are available?",
                "expected_context": "System capabilities, mode information",
                "test_description": "System knowledge query"
            },
            {
                "message": "what automation tasks did I request?",
                "expected_context": "Should reference previous Agent mode requests",
                "test_description": "Cross-mode memory query"
            },
            {
                "message": "tell me about my usage patterns",
                "expected_context": "Should analyze all previous interactions",
                "test_description": "Pattern analysis query"
            }
        ]
        
        for i, test in enumerate(ask_tests, 1):
            print(f"\n🧪 Ask Test {i}: {test['test_description']}")
            print(f"📝 Message: '{test['message']}'")
            print(f"🎯 Expected Context: {test['expected_context']}")
            
            request = {
                "type": "chat_request",
                "mode": "Ask",
                "message": test["message"],
                "session_id": f"ask_test_session_{int(time.time())}"
            }
            
            await websocket.send(json.dumps(request))
            response_raw = await asyncio.wait_for(websocket.recv(), timeout=20)
            response = json.loads(response_raw)
            
            # Get response content with better error handling
            response_text = response.get('response', '')
            if not response_text:
                payload = response.get('payload', {})
                response_text = payload.get('response', '')
            if not response_text:
                response_text = f"No response field found. Full response: {response}"
            context_used = response.get('context_used', {})
            context_metrics = response.get('context_metrics', {})
            
            print(f"📥 Response: {response_text}")
            print(f"📊 Context Used: {context_used}")
            print(f"🧠 Context Metrics: {context_metrics}")
            
            # Analyze Ask mode quality
            ask_indicators = ['💭', 'based on', 'information', 'search', 'recall', 'knowledge']
            memory_indicators = ['conversation', 'previous', 'history', 'remember', 'interactions']
            
            has_ask_nature = any(indicator in response_text.lower() for indicator in ask_indicators)
            has_memory_access = any(indicator in response_text.lower() for indicator in memory_indicators)
            has_relevant_memories = context_used.get('relevant_memories', 0) > 0
            
            print(f"✅ Ask Nature: {'YES' if has_ask_nature else 'NO'}")
            print(f"🧠 Memory Access: {'YES' if has_memory_access else 'NO'}")
            print(f"📚 Relevant Memories Found: {context_used.get('relevant_memories', 0)}")
            
            if not has_ask_nature:
                print("❌ ISSUE: Response doesn't reflect Ask mode nature")
            if not has_relevant_memories and i > 2:  # Should have memories after a few interactions
                print("❌ ISSUE: No relevant memories being retrieved")
            
            print("-" * 50)
            await asyncio.sleep(3)
            
    async def test_suggest_mode_deep(self, websocket, server_name):
        """Deep dive test for Suggest mode - Recommendations with context"""
        print(f"\n💡 DEEP DIVE: SUGGEST MODE - {server_name}")
        print("=" * 60)
        print("Expected: Personalized recommendations based on usage patterns")
        print("Should analyze behavior, suggest improvements, provide actionable advice")
        
        suggest_tests = [
            {
                "message": "how can I improve my workflow?",
                "expected_context": "Work patterns, efficiency suggestions",
                "test_description": "Workflow optimization request"
            },
            {
                "message": "suggest better file organization",
                "expected_context": "File activity patterns, organization strategies",
                "test_description": "File management suggestions"
            },
            {
                "message": "what automation should I set up?",
                "expected_context": "Should reference Agent mode usage patterns",
                "test_description": "Automation recommendations"
            },
            {
                "message": "help me be more productive",
                "expected_context": "Overall usage analysis, productivity tips",
                "test_description": "Productivity enhancement"
            },
            {
                "message": "based on my questions, what should I learn?",
                "expected_context": "Should analyze Ask mode queries for learning gaps",
                "test_description": "Learning recommendations"
            },
            {
                "message": "optimize my daily routine",
                "expected_context": "Comprehensive pattern analysis and suggestions",
                "test_description": "Routine optimization with full context"
            }
        ]
        
        for i, test in enumerate(suggest_tests, 1):
            print(f"\n🧪 Suggest Test {i}: {test['test_description']}")
            print(f"📝 Message: '{test['message']}'")
            print(f"🎯 Expected Context: {test['expected_context']}")
            
            request = {
                "type": "chat_request",
                "mode": "Suggest",
                "message": test["message"],
                "session_id": f"suggest_test_session_{int(time.time())}"
            }
            
            await websocket.send(json.dumps(request))
            response_raw = await asyncio.wait_for(websocket.recv(), timeout=20)
            response = json.loads(response_raw)
            
            # Get response content with better error handling
            response_text = response.get('response', '')
            if not response_text:
                payload = response.get('payload', {})
                response_text = payload.get('response', '')
            if not response_text:
                response_text = f"No response field found. Full response: {response}"
            context_used = response.get('context_used', {})
            context_metrics = response.get('context_metrics', {})
            
            print(f"📥 Response: {response_text}")
            print(f"📊 Context Used: {context_used}")
            print(f"🧠 Context Metrics: {context_metrics}")
            
            # Analyze Suggest mode quality
            suggest_indicators = ['💡', 'suggest', 'recommend', 'consider', 'improve', 'optimize']
            pattern_indicators = ['based on', 'patterns', 'usage', 'behavior', 'analysis']
            actionable_indicators = ['create', 'set up', 'implement', 'use', 'try']
            
            has_suggest_nature = any(indicator in response_text.lower() for indicator in suggest_indicators)
            has_pattern_analysis = any(indicator in response_text.lower() for indicator in pattern_indicators)
            has_actionable_advice = any(indicator in response_text.lower() for indicator in actionable_indicators)
            
            print(f"✅ Suggest Nature: {'YES' if has_suggest_nature else 'NO'}")
            print(f"📊 Pattern Analysis: {'YES' if has_pattern_analysis else 'NO'}")
            print(f"🎯 Actionable Advice: {'YES' if has_actionable_advice else 'NO'}")
            
            if not has_suggest_nature:
                print("❌ ISSUE: Response doesn't reflect Suggest mode nature")
            if not has_pattern_analysis and i > 2:
                print("❌ ISSUE: No pattern analysis detected")
            if not has_actionable_advice:
                print("❌ ISSUE: Suggestions are not actionable enough")
            
            print("-" * 50)
            await asyncio.sleep(3)
            
    async def test_general_mode_deep(self, websocket, server_name):
        """Deep dive test for General mode - Conversational with context"""
        print(f"\n🤖 DEEP DIVE: GENERAL MODE - {server_name}")
        print("=" * 60)
        print("Expected: Natural conversation with context awareness")
        print("Should maintain conversation flow, reference history, be personable")
        
        general_tests = [
            {
                "message": "hello, how are you today?",
                "expected_context": "Greeting, conversation starter",
                "test_description": "Initial greeting"
            },
            {
                "message": "what can you help me with?",
                "expected_context": "Capabilities overview, personalized to user",
                "test_description": "Capabilities inquiry"
            },
            {
                "message": "I've been using you for automation tasks",
                "expected_context": "Should reference Agent mode usage",
                "test_description": "Conversational reference to usage"
            },
            {
                "message": "thank you for all your help",
                "expected_context": "Should acknowledge specific help provided",
                "test_description": "Gratitude expression"
            },
            {
                "message": "tell me something interesting",
                "expected_context": "Should be contextual to user's interests/usage",
                "test_description": "Open-ended conversational request"
            },
            {
                "message": "goodbye for now",
                "expected_context": "Farewell with session summary",
                "test_description": "Conversation closure"
            }
        ]
        
        for i, test in enumerate(general_tests, 1):
            print(f"\n🧪 General Test {i}: {test['test_description']}")
            print(f"📝 Message: '{test['message']}'")
            print(f"🎯 Expected Context: {test['expected_context']}")
            
            request = {
                "type": "chat_request",
                "mode": "General",
                "message": test["message"],
                "session_id": f"general_test_session_{int(time.time())}"
            }
            
            await websocket.send(json.dumps(request))
            response_raw = await asyncio.wait_for(websocket.recv(), timeout=20)
            response = json.loads(response_raw)
            
            # Get response content with better error handling
            response_text = response.get('response', '')
            if not response_text:
                payload = response.get('payload', {})
                response_text = payload.get('response', '')
            if not response_text:
                response_text = f"No response field found. Full response: {response}"
            context_used = response.get('context_used', {})
            context_metrics = response.get('context_metrics', {})
            
            print(f"📥 Response: {response_text}")
            print(f"📊 Context Used: {context_used}")
            print(f"🧠 Context Metrics: {context_metrics}")
            
            # Analyze General mode quality
            general_indicators = ['🤖', 'help', 'assist', 'here', 'glad', 'welcome']
            conversational_indicators = ['you', 'your', 'we', 'our', 'together']
            context_indicators = ['recall', 'remember', 'previous', 'interactions', 'history']
            
            has_general_nature = any(indicator in response_text.lower() for indicator in general_indicators)
            has_conversational_tone = any(indicator in response_text.lower() for indicator in conversational_indicators)
            has_context_reference = any(indicator in response_text.lower() for indicator in context_indicators)
            
            print(f"✅ General Nature: {'YES' if has_general_nature else 'NO'}")
            print(f"💬 Conversational Tone: {'YES' if has_conversational_tone else 'NO'}")
            print(f"🧠 Context Reference: {'YES' if has_context_reference else 'NO'}")
            
            if not has_general_nature:
                print("❌ ISSUE: Response doesn't reflect General mode nature")
            if not has_conversational_tone:
                print("❌ ISSUE: Not conversational enough")
            if not has_context_reference and i > 2:
                print("❌ ISSUE: No context references in conversation")
            
            print("-" * 50)
            await asyncio.sleep(3)
    
    async def run_deep_dive_tests(self):
        """Run comprehensive deep dive tests"""
        print("🔬 STARTING DEEP DIVE MODE TESTING")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().isoformat()}")
        
        # Test Brain Router
        try:
            print(f"\n🧠 TESTING BRAIN ROUTER: {self.brain_router_url}")
            async with websockets.connect(self.brain_router_url, ping_timeout=15) as websocket:
                # Get connection info
                connection_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                connection_data = json.loads(connection_msg)
                print(f"✅ Connected: {connection_data.get('message', '')}")
                
                # Test each mode
                await self.test_agent_mode_deep(websocket, "Brain Router")
                await self.test_ask_mode_deep(websocket, "Brain Router")
                await self.test_suggest_mode_deep(websocket, "Brain Router")
                await self.test_general_mode_deep(websocket, "Brain Router")
                
        except Exception as e:
            print(f"❌ Brain Router testing failed: {e}")
        
        # Test Enterprise Backend
        try:
            print(f"\n🏢 TESTING ENTERPRISE BACKEND: {self.enterprise_backend_url}")
            async with websockets.connect(self.enterprise_backend_url, ping_timeout=15) as websocket:
                # Get connection info
                connection_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                connection_data = json.loads(connection_msg)
                print(f"✅ Connected: {connection_data.get('message', '')}")
                
                # Test each mode
                await self.test_agent_mode_deep(websocket, "Enterprise Backend")
                await self.test_ask_mode_deep(websocket, "Enterprise Backend")
                await self.test_suggest_mode_deep(websocket, "Enterprise Backend")
                await self.test_general_mode_deep(websocket, "Enterprise Backend")
                
        except Exception as e:
            print(f"❌ Enterprise Backend testing failed: {e}")
        
        print("\n" + "=" * 80)
        print("🏁 DEEP DIVE TESTING COMPLETE")
        print("=" * 80)
        print("📋 Review the test results above to identify any issues")
        print("🔧 Look for responses that don't match mode nature or lack context")
        print(f"🕐 Completed at: {datetime.now().isoformat()}")

async def main():
    """Main function"""
    tester = DeepDiveModeeTester()
    await tester.run_deep_dive_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Deep dive testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Deep dive testing error: {e}")