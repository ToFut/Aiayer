#!/usr/bin/env python3
"""
Interactive Approval Client
Rich UI/UX for plan approval, dismissal, and adjustment
Professional user interaction system
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
import websockets
from datetime import datetime

logger = logging.getLogger(__name__)

class InteractiveApprovalClient:
    """Rich client for handling plan approvals with professional UX"""
    
    def __init__(self, uri: str = "ws://localhost:8767"):
        self.uri = uri
        self.websocket = None
        self.client_id = None
        self.pending_approvals = {}
        self.active_plans = {}
        
    async def connect(self) -> bool:
        """Connect to the AI-powered backend"""
        try:
            print(f"🔌 Connecting to AI-Powered Enterprise Backend at {self.uri}...")
            
            self.websocket = await websockets.connect(self.uri)
            
            # Wait for welcome message
            welcome_msg = await self.websocket.recv()
            welcome_data = json.loads(welcome_msg)
            
            self.client_id = welcome_data.get('client_id')
            capabilities = welcome_data.get('capabilities', [])
            
            print(f"✅ Connected! Client ID: {self.client_id}")
            print(f"🎯 Server Capabilities: {', '.join(capabilities)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def send_agent_request(self, query: str) -> bool:
        """Send agent request and handle the approval workflow"""
        try:
            if not self.websocket:
                print("❌ Not connected to server")
                return False
            
            print(f"\n🤖 Sending Agent Request: {query}")
            print("⏳ AI is analyzing your request and creating an execution plan...")
            
            # Send the request
            request = {
                "type": "chat_request",
                "query": query,
                "mode": "agent",
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(request))
            
            # Listen for responses
            await self._listen_for_responses()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send request: {e}")
            return False
    
    async def _listen_for_responses(self):
        """Listen for and handle server responses"""
        try:
            timeout = 30  # 30 second timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Wait for response with timeout
                    response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    response_type = response_data.get('type')
                    
                    if response_type == 'approval_request':
                        await self._handle_approval_request(response_data)
                    elif response_type == 'chat_response':
                        await self._handle_chat_response(response_data)
                    elif response_type == 'execution_complete':
                        await self._handle_execution_complete(response_data)
                    elif response_type == 'plan_dismissed':
                        print("\n🗑️ Task dismissed as requested.")
                        break
                    elif response_type == 'error':
                        print(f"\n❌ Error: {response_data.get('payload', {}).get('message', 'Unknown error')}")
                        break
                    else:
                        print(f"\n📨 Received: {response_type}")
                    
                except asyncio.TimeoutError:
                    # Continue listening
                    continue
                    
        except Exception as e:
            print(f"❌ Error listening for responses: {e}")
    
    async def _handle_approval_request(self, response_data: Dict[str, Any]):
        """Handle approval request with rich interactive UI"""
        try:
            plan_id = response_data.get('plan_id')
            title = response_data.get('title', 'Task Execution Plan')
            plan_summary = response_data.get('plan_summary', {})
            execution_steps = response_data.get('execution_steps', [])
            success_criteria = response_data.get('success_criteria', [])
            options = response_data.get('options', {})
            
            # Store approval request
            self.pending_approvals[plan_id] = response_data
            
            # Display rich approval UI
            self._display_approval_ui(title, plan_summary, execution_steps, success_criteria, options)
            
            # Get user input
            user_choice = await self._get_user_approval_choice(plan_id, options)
            
            # Send response
            await self._send_approval_response(plan_id, user_choice)
            
        except Exception as e:
            print(f"❌ Error handling approval request: {e}")
    
    def _display_approval_ui(self, title: str, plan_summary: Dict[str, Any], 
                           execution_steps: list, success_criteria: list, options: Dict[str, Any]):
        """Display rich approval UI"""
        print("\n" + "=" * 80)
        print(f"🧪 {title}")
        print("=" * 80)
        
        print(f"\n📋 **PLAN SUMMARY**")
        print(f"   Request: {plan_summary.get('request', 'N/A')}")
        print(f"   Steps: {plan_summary.get('steps', 0)}")
        print(f"   Complexity: {plan_summary.get('complexity', 'unknown').title()}")
        print(f"   Estimated Time: {plan_summary.get('estimated_time', 'unknown')}")
        print(f"   Risk Level: {plan_summary.get('risk_level', 'unknown').title()}")
        
        print(f"\n🔧 **EXECUTION STEPS**")
        for step in execution_steps:
            print(f"   {step.get('number', '?')}. {step.get('title', 'Unknown Step')}")
            print(f"      └─ {step.get('description', 'No description')}")
            print(f"      └─ Duration: ~{step.get('estimated_duration', 0):.1f}s")
        
        print(f"\n✅ **SUCCESS CRITERIA**")
        for i, criterion in enumerate(success_criteria, 1):
            print(f"   {i}. {criterion}")
        
        print(f"\n🎯 **AVAILABLE ACTIONS**")
        for key, option in options.items():
            if isinstance(option, dict):
                label = option.get('label', key.title())
                description = option.get('description', 'No description')
                style_icon = {'success': '✅', 'danger': '❌', 'warning': '⚠️'}.get(option.get('style', ''), '🔘')
                print(f"   {style_icon} **{label}**: {description}")
        
        print("\n" + "=" * 80)
    
    async def _get_user_approval_choice(self, plan_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Get user choice with input validation"""
        try:
            while True:
                print(f"\n🤔 **Your Decision** (plan: {plan_id[:8]}...):")
                print("   [1] 🟢 APPROVE - Execute the plan as designed")
                print("   [2] 🔴 DISMISS - Cancel this task completely")
                print("   [3] 🟡 ADJUST  - Modify the plan before execution")
                
                choice = input("\n👉 Enter your choice (1-3): ").strip()
                
                if choice == '1':
                    return {'action': 'approve'}
                elif choice == '2':
                    return {'action': 'dismiss'}
                elif choice == '3':
                    return await self._get_adjustment_details(options)
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
                    
        except KeyboardInterrupt:
            print("\n🛑 User cancelled")
            return {'action': 'dismiss'}
        except Exception as e:
            print(f"❌ Error getting user choice: {e}")
            return {'action': 'dismiss'}
    
    async def _get_adjustment_details(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Get adjustment details from user"""
        try:
            print("\n🔧 **PLAN ADJUSTMENT OPTIONS**")
            
            adjust_options = options.get('adjust', {}).get('adjustment_options', {})
            
            if adjust_options:
                print("\nAvailable adjustments:")
                for i, (key, description) in enumerate(adjust_options.items(), 1):
                    print(f"   [{i}] {description}")
                
                adj_choice = input(f"\n👉 Select adjustment type (1-{len(adjust_options)}): ").strip()
                
                try:
                    adj_index = int(adj_choice) - 1
                    adj_keys = list(adjust_options.keys())
                    if 0 <= adj_index < len(adj_keys):
                        selected_adjustment = adj_keys[adj_index]
                        
                        # Get specific adjustment parameters
                        if selected_adjustment == 'modify_steps':
                            details = input("📝 Describe step modifications: ")
                        elif selected_adjustment == 'change_parameters':
                            details = input("⚙️ Describe parameter changes: ")
                        elif selected_adjustment == 'add_validation':
                            details = input("✅ Describe additional validation needed: ")
                        elif selected_adjustment == 'reduce_complexity':
                            details = input("🎯 Describe simplification preferences: ")
                        else:
                            details = input("📋 Describe your adjustments: ")
                        
                        return {
                            'action': 'adjust',
                            'adjustment_type': selected_adjustment,
                            'details': details,
                            'modifications': {
                                selected_adjustment: details
                            }
                        }
                except ValueError:
                    pass
            
            # Fallback to general adjustment
            details = input("📝 Describe your desired adjustments: ")
            return {
                'action': 'adjust',
                'adjustment_type': 'general',
                'details': details,
                'modifications': {'general': details}
            }
            
        except Exception as e:
            print(f"❌ Error getting adjustment details: {e}")
            return {'action': 'approve'}  # Fallback to approval
    
    async def _send_approval_response(self, plan_id: str, choice: Dict[str, Any]):
        """Send approval response to server"""
        try:
            response = {
                "type": "approval_response",
                "plan_id": plan_id,
                "response": choice['action'],
                "modifications": choice.get('modifications', {}),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(response))
            
            action_icons = {'approve': '🟢', 'dismiss': '🔴', 'adjust': '🟡'}
            icon = action_icons.get(choice['action'], '🔘')
            
            print(f"\n{icon} Response sent: {choice['action'].upper()}")
            
            if choice['action'] == 'adjust':
                print(f"   Adjustments: {choice.get('details', 'General modifications')}")
            
            print("⏳ Waiting for execution result...")
            
        except Exception as e:
            print(f"❌ Failed to send approval response: {e}")
    
    async def _handle_chat_response(self, response_data: Dict[str, Any]):
        """Handle chat response from server"""
        try:
            payload = response_data.get('payload', {})
            content = payload.get('response', 'No content')
            mode = payload.get('mode', 'unknown')
            success = payload.get('success', False)
            confidence = payload.get('confidence', 0.0)
            ai_powered = payload.get('ai_powered', False)
            
            status_icon = '✅' if success else '❌'
            ai_icon = '🧠' if ai_powered else '🔧'
            
            print(f"\n{status_icon} {ai_icon} **{mode.upper()} MODE RESPONSE** (confidence: {confidence:.1%})")
            print("-" * 60)
            print(content)
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Error handling chat response: {e}")
    
    async def _handle_execution_complete(self, response_data: Dict[str, Any]):
        """Handle execution completion"""
        try:
            plan_id = response_data.get('plan_id')
            result = response_data.get('result', {})
            
            print(f"\n🎉 **EXECUTION COMPLETED** (plan: {plan_id[:8]}...)")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Progress: {result.get('progress', 0):.1f}%")
            print(f"   Steps: {result.get('completed_steps', 0)}/{result.get('total_steps', 0)}")
            
            if result.get('errors'):
                print(f"   Errors: {len(result['errors'])}")
            
        except Exception as e:
            print(f"❌ Error handling execution complete: {e}")
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            print("👋 Disconnected from server")

async def main():
    """Interactive approval client demo"""
    client = InteractiveApprovalClient()
    
    try:
        if not await client.connect():
            return
        
        print("\n🎯 **AI-POWERED INTERACTIVE APPROVAL CLIENT**")
        print("   Send agent requests and interact with AI-generated execution plans")
        print("   Type 'quit' to exit")
        
        while True:
            try:
                print("\n" + "=" * 80)
                query = input("🤖 Enter your agent request: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    print("⚠️ Please enter a request")
                    continue
                
                await client.send_agent_request(query)
                
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
