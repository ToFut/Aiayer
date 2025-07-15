#!/usr/bin/env python3
"""
Comprehensive Automation Test - Test the entire pipeline from plan generation to execution
"""
import asyncio
import json
import time
import sys
import os
import websockets
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_backend_connection():
    """Test backend connection and registration"""
    print("🔌 Testing Backend Connection...")
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            # Register with backend
            register_message = {
                "type": "register",
                "client_id": "test_client",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(register_message))
            
            # Wait for registration response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") in ["registration_confirmed", "connection_established"]:
                print("✅ Backend connection successful")
                return websocket
            else:
                print(f"❌ Backend registration failed: {response_data}")
                return None
                
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return None

async def test_agent_mode_plan_generation(websocket):
    """Test agent mode plan generation"""
    print("🤖 Testing Agent Mode Plan Generation...")
    
    try:
        # Send chat request in agent mode
        chat_message = {
            "type": "chat_request",
            "message": "Write Segev in Google",
            "mode": "Agent",
            "client_id": "test_client",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(chat_message))
        
        # Wait for plan response
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("type") == "plan_generated":
            plan = response_data.get("plan", {})
            steps = plan.get("steps", [])
            print(f"✅ Plan generated with {len(steps)} steps")
            
            # Print plan details
            for i, step in enumerate(steps):
                action_type = step.get("action_type", "unknown")
                description = step.get("description", "No description")
                print(f"  Step {i+1}: {action_type} - {description}")
            
            return plan
        else:
            print(f"❌ Plan generation failed: {response_data}")
            return None
            
    except Exception as e:
        print(f"❌ Agent mode test failed: {e}")
        return None

async def test_plan_execution(websocket, plan):
    """Test plan execution"""
    print("⚡ Testing Plan Execution...")
    
    try:
        # Send execute request
        execute_message = {
            "type": "execute_plan",
            "plan_id": plan.get("plan_id", "test_plan"),
            "client_id": "test_client",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(execute_message))
        
        # Wait for execution responses
        execution_started = False
        execution_completed = False
        step_count = 0
        
        while not execution_completed:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                
                if response_data.get("type") == "execution_started":
                    execution_started = True
                    print("✅ Execution started")
                    
                elif response_data.get("type") == "execution_progress":
                    step_count += 1
                    step_type = response_data.get("step_type", "unknown")
                    description = response_data.get("description", "No description")
                    print(f"  ✅ Step {step_count}: {step_type} - {description}")
                    
                elif response_data.get("type") == "execution_completed":
                    execution_completed = True
                    print("✅ Execution completed")
                    
                elif response_data.get("type") == "execution_error":
                    print(f"❌ Execution error: {response_data.get('error', 'Unknown error')}")
                    return False
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for execution response")
                break
        
        return execution_started and execution_completed
        
    except Exception as e:
        print(f"❌ Plan execution test failed: {e}")
        return False

async def test_input_controller_directly():
    """Test input controller directly"""
    print("🎮 Testing Input Controller Directly...")
    
    try:
        from agent_workflow.input_controller import InputController
        
        # Initialize input controller
        controller = InputController(safety_level="low")
        print("✅ Input controller initialized")
        
        # Test basic operations
        current_x, current_y = controller.get_current_position()
        print(f"✅ Current position: ({current_x}, {current_y})")
        
        # Test mouse movement
        print("🎯 Testing mouse movement...")
        success = controller.move_to(100, 100, duration=1.0)
        print(f"✅ Mouse movement: {'SUCCESS' if success else 'FAILED'}")
        
        # Test click
        print("🖱️ Testing click...")
        success = controller.click()
        print(f"✅ Click: {'SUCCESS' if success else 'FAILED'}")
        
        # Test text typing
        print("⌨️ Testing text typing...")
        success = controller.type_text("TEST")
        print(f"✅ Text typing: {'SUCCESS' if success else 'FAILED'}")
        
        # Test key press
        print("🔤 Testing key press...")
        success = controller.press_key("enter")
        print(f"✅ Key press: {'SUCCESS' if success else 'FAILED'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Input controller test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_overlay_integration():
    """Test overlay integration"""
    print("🖥️ Testing Overlay Integration...")
    
    try:
        # Test overlay connection
        uri = "ws://localhost:1421"
        async with websockets.connect(uri) as websocket:
            # Send test message to overlay
            test_message = {
                "type": "test",
                "message": "Testing overlay connection",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print("✅ Overlay connection successful")
            return True
            
    except Exception as e:
        print(f"❌ Overlay integration failed: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive automation test"""
    print("🚀 Starting Comprehensive Automation Test...")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Input Controller
    print("\n1️⃣ Testing Input Controller...")
    results["input_controller"] = await test_input_controller_directly()
    
    # Test 2: Backend Connection
    print("\n2️⃣ Testing Backend Connection...")
    websocket = await test_backend_connection()
    results["backend_connection"] = websocket is not None
    
    if websocket:
        # Test 3: Agent Mode Plan Generation
        print("\n3️⃣ Testing Agent Mode Plan Generation...")
        plan = await test_agent_mode_plan_generation(websocket)
        results["plan_generation"] = plan is not None
        
        if plan:
            # Test 4: Plan Execution
            print("\n4️⃣ Testing Plan Execution...")
            results["plan_execution"] = await test_plan_execution(websocket, plan)
        
        await websocket.close()
    
    # Test 5: Overlay Integration
    print("\n5️⃣ Testing Overlay Integration...")
    results["overlay_integration"] = await test_overlay_integration()
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    # Overall assessment
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Automation system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Automation Test...")
    print("⚠️  This will test mouse and keyboard control!")
    print("Press Ctrl+C to cancel, or any key to continue...")
    
    try:
        input()  # Wait for user confirmation
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        sys.exit(0)
    
    # Run comprehensive test
    asyncio.run(run_comprehensive_test()) 