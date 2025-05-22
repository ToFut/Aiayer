#!/usr/bin/env python3
"""
System Integration Test
Tests all system components working together end-to-end.
"""

import asyncio
import websockets
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemIntegrationTest:
    """Tests end-to-end system integration."""
    
    def __init__(self):
        self.ws_uri = "ws://localhost:8765"
        self.backend_uri = "ws://localhost:8767" 
        self.llm_uri = "ws://localhost:8766"
        
        self.test_results = {}
        self.websocket = None
        
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket server connectivity."""
        try:
            logger.info("Testing WebSocket connection...")
            
            async with websockets.connect(self.ws_uri) as ws:
                # Send test message
                test_message = {
                    "type": "connection_test",
                    "payload": {
                        "message": "Integration test connection",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                await ws.send(json.dumps(test_message))
                
                # Wait for response
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                response_data = json.loads(response)
                
                logger.info(f"WebSocket response: {response_data['type']}")
                return True
                
        except Exception as e:
            logger.error(f"WebSocket connection test failed: {e}")
            return False
    
    async def test_backend_integration(self) -> bool:
        """Test backend server integration."""
        try:
            logger.info("Testing backend integration...")
            
            async with websockets.connect(self.backend_uri) as ws:
                # Test LLM request
                test_query = {
                    "type": "llm_request",
                    "payload": {
                        "query": "System integration test - please respond with current time",
                        "context": {
                            "test_mode": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                }
                
                await ws.send(json.dumps(test_query))
                
                # Wait for response
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                response_data = json.loads(response)
                
                if response_data.get("type") == "query_response":
                    logger.info("Backend integration test successful")
                    logger.info(f"LLM Response: {response_data['payload']['response'][:100]}...")
                    return True
                else:
                    logger.error(f"Unexpected response type: {response_data.get('type')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Backend integration test failed: {e}")
            return False
    
    async def test_brain_router_modes(self) -> Dict[str, bool]:
        """Test brain router with different modes."""
        results = {}
        
        # Import brain router
        try:
            sys.path.append(os.path.dirname(__file__))
            from brain.core.brain_router import process_chat_request
            
            # Test different modes
            test_cases = [
                ("Agent", "Create a simple task plan for organizing files"),
                ("Ask", "What is the current system status?"), 
                ("Suggest", "What improvements can be made to the system?"),
                ("General", "Hello, how are you?")
            ]
            
            for mode, query in test_cases:
                try:
                    logger.info(f"Testing {mode} mode...")
                    
                    result = await process_chat_request(
                        mode=mode,
                        query=query,
                        user_id="integration_test",
                        session_id="test_session"
                    )
                    
                    if result["success"]:
                        logger.info(f"{mode} mode test successful")
                        logger.info(f"Response: {result['response'][:100]}...")
                        results[mode] = True
                    else:
                        logger.error(f"{mode} mode test failed: {result.get('response', 'No response')}")
                        results[mode] = False
                        
                except Exception as e:
                    logger.error(f"{mode} mode test error: {e}")
                    results[mode] = False
                    
                # Small delay between tests
                await asyncio.sleep(1)
                
        except ImportError as e:
            logger.error(f"Could not import brain router: {e}")
            for mode, _ in [("Agent", ""), ("Ask", ""), ("Suggest", ""), ("General", "")]:
                results[mode] = False
        
        return results
    
    async def test_chat_flow_integration(self) -> bool:
        """Test complete chat flow from WebSocket to LLM."""
        try:
            logger.info("Testing complete chat flow integration...")
            
            async with websockets.connect(self.ws_uri) as ws:
                # Register as test client
                register_message = {
                    "type": "register",
                    "client_type": "integration_test",
                    "payload": {
                        "timestamp": datetime.now().isoformat() 
                    }
                }
                
                await ws.send(json.dumps(register_message))
                
                # Wait for registration confirmation
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                response_data = json.loads(response)
                
                if response_data.get("type") != "registration_confirmed":
                    logger.error("Registration failed")
                    return False
                
                # Send chat message
                chat_message = {
                    "type": "chat_message",
                    "message": "Integration test: What is 2+2? Please respond with just the number.",
                    "timestamp": datetime.now().isoformat()
                }
                
                await ws.send(json.dumps(chat_message))
                
                # Wait for response
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                response_data = json.loads(response)
                
                if response_data.get("type") == "query_response":
                    response_text = response_data.get("payload", {}).get("response", "")
                    logger.info(f"Chat flow test successful")
                    logger.info(f"Response: {response_text[:100]}...")
                    return True
                else:
                    logger.error(f"Unexpected response type: {response_data.get('type')}")
                    return False
                    
        except Exception as e:
            logger.error(f"Chat flow integration test failed: {e}")
            return False
    
    async def test_memory_system_integration(self) -> bool:
        """Test memory system integration."""
        try:
            logger.info("Testing memory system integration...")
            
            # Test memory system by checking if it stores and retrieves context
            async with websockets.connect(self.backend_uri) as ws:
                # Send a message that should be remembered
                first_message = {
                    "type": "llm_request",
                    "payload": {
                        "query": "Remember this: My favorite color is blue.",
                        "context": {"test_memory": True}
                    }
                }
                
                await ws.send(json.dumps(first_message))
                response1 = await asyncio.wait_for(ws.recv(), timeout=20)
                
                # Small delay to allow memory storage
                await asyncio.sleep(2)
                
                # Ask about the remembered information
                second_message = {
                    "type": "llm_request", 
                    "payload": {
                        "query": "What is my favorite color?",
                        "context": {"test_memory": True}
                    }
                }
                
                await ws.send(json.dumps(second_message))
                response2 = await asyncio.wait_for(ws.recv(), timeout=20)
                response2_data = json.loads(response2)
                
                # Check if the response contains the remembered information
                response_text = response2_data.get("payload", {}).get("response", "").lower()
                
                if "blue" in response_text:
                    logger.info("Memory system integration test successful")
                    return True
                else:
                    logger.warning("Memory system may not be fully integrated")
                    return False
                    
        except Exception as e:
            logger.error(f"Memory system integration test failed: {e}")
            return False
    
    async def test_sensor_integration(self) -> Dict[str, bool]:
        """Test sensor integration."""
        results = {}
        
        try:
            # Test if sensors are providing data
            sensor_tests = [
                ("process_sensor", "Process sensor should detect running processes"),
                ("screen_sensor", "Screen sensor should capture screen data"),
                ("memory_system", "Memory system should maintain context")
            ]
            
            for sensor_name, description in sensor_tests:
                try:
                    # Check if sensor process is running
                    import subprocess
                    proc = subprocess.run(['pgrep', '-f', sensor_name], 
                                        capture_output=True, text=True)
                    
                    if proc.returncode == 0:
                        logger.info(f"{sensor_name} is running")
                        results[sensor_name] = True
                    else:
                        logger.warning(f"{sensor_name} is not running")
                        results[sensor_name] = False
                        
                except Exception as e:
                    logger.error(f"Error testing {sensor_name}: {e}")
                    results[sensor_name] = False
                    
        except Exception as e:
            logger.error(f"Sensor integration test failed: {e}")
            
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_success": True
        }
        
        logger.info("Starting system integration tests...")
        
        # Test WebSocket connectivity
        ws_success = await self.test_websocket_connection()
        results["tests"]["websocket_connection"] = ws_success
        
        # Test backend integration
        backend_success = await self.test_backend_integration()
        results["tests"]["backend_integration"] = backend_success
        
        # Test brain router modes
        brain_results = await self.test_brain_router_modes()
        results["tests"]["brain_router_modes"] = brain_results
        
        # Test chat flow
        chat_success = await self.test_chat_flow_integration()
        results["tests"]["chat_flow_integration"] = chat_success
        
        # Test memory system
        memory_success = await self.test_memory_system_integration()
        results["tests"]["memory_system_integration"] = memory_success
        
        # Test sensors
        sensor_results = await self.test_sensor_integration()
        results["tests"]["sensor_integration"] = sensor_results
        
        # Calculate overall success
        all_tests = [ws_success, backend_success, chat_success, memory_success]
        all_tests.extend(brain_results.values())
        all_tests.extend(sensor_results.values())
        
        success_count = sum(all_tests)
        total_count = len(all_tests)
        
        results["overall_success"] = success_count == total_count
        results["success_rate"] = f"{success_count}/{total_count} ({success_count/total_count*100:.1f}%)"
        
        return results
    
    def print_test_results(self, results: Dict[str, Any]):
        """Print formatted test results."""
        print("\n" + "="*60)
        print("SYSTEM INTEGRATION TEST RESULTS")
        print("="*60)
        
        print(f"Test Run: {results['timestamp']}")
        print(f"Overall Success: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
        print(f"Success Rate: {results['success_rate']}")
        print()
        
        # Individual test results
        tests = results["tests"]
        
        print("Component Tests:")
        print(f"  WebSocket Connection: {'✅' if tests.get('websocket_connection') else '❌'}")
        print(f"  Backend Integration: {'✅' if tests.get('backend_integration') else '❌'}")
        print(f"  Chat Flow Integration: {'✅' if tests.get('chat_flow_integration') else '❌'}")
        print(f"  Memory System Integration: {'✅' if tests.get('memory_system_integration') else '❌'}")
        print()
        
        print("Brain Router Modes:")
        brain_modes = tests.get("brain_router_modes", {})
        for mode, success in brain_modes.items():
            print(f"  {mode} Mode: {'✅' if success else '❌'}")
        print()
        
        print("Sensor Integration:")
        sensors = tests.get("sensor_integration", {})
        for sensor, success in sensors.items():
            print(f"  {sensor}: {'✅' if success else '❌'}")
        
        print("\n" + "="*60)

async def main():
    """Main function to run integration tests."""
    tester = SystemIntegrationTest()
    
    try:
        results = await tester.run_all_tests()
        
        # Print results
        tester.print_test_results(results)
        
        # Save results
        os.makedirs('logs/tests', exist_ok=True)
        with open('logs/tests/integration_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Exit with appropriate code
        sys.exit(0 if results["overall_success"] else 1)
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())