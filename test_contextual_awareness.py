#!/usr/bin/env python3
"""
Test Contextual Awareness

This script tests the full system flow from sensors to memory to LLM responses,
verifying that contextual information is properly integrated.
"""
import asyncio
import json
import logging
import websockets
import time
import os
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_contextual_awareness.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# WebSocket server URI
WS_URI = "ws://localhost:8767"

class ContextualAwarenessTest:
    """Test the system's contextual awareness."""
    
    def __init__(self, uri=WS_URI, verbose=False):
        """Initialize the test with WebSocket URI."""
        self.uri = uri
        self.verbose = verbose
        self.ws = None
        self.results = {
            "process_sensor": False,
            "screen_sensor": False,
            "file_sensor": False,
            "memory_integration": False,
            "llm_response": False,
            "total_tests": 0,
            "passed_tests": 0
        }
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.ws = await websockets.connect(self.uri)
            logger.info(f"Connected to WebSocket server at {self.uri}")
            
            # Wait for welcome message
            response = await self.ws.recv()
            data = json.loads(response)
            
            if data.get("type") == "connection_established":
                logger.info("Connection established with server")
                return True
            else:
                logger.error(f"Unexpected response: {data}")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket connection closed")
    
    async def send_message(self, message_type, payload):
        """Send a message to the WebSocket server."""
        try:
            message = {
                "type": message_type,
                "payload": payload
            }
            await self.ws.send(json.dumps(message))
            logger.info(f"Sent {message_type} message")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def receive_message(self, timeout=10):
        """Receive a message from the WebSocket server with timeout."""
        try:
            response = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            data = json.loads(response)
            if self.verbose:
                logger.info(f"Received message: {data}")
            return data
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for response")
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    async def test_process_sensor(self):
        """Test process sensor data integration."""
        self.results["total_tests"] += 1
        
        logger.info("TESTING PROCESS SENSOR INTEGRATION")
        
        # Send simulated process sensor data
        process_data = {
            "sensor_type": "process",
            "data": {
                "active_window": "TestEditor",
                "active_app": "CodeEditor",
                "active_apps": ["CodeEditor", "Terminal", "Browser"],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send the data
        if not await self.send_message("sensor_data", {
            "sensor_type": "process",
            "data": process_data["data"]
        }):
            logger.error("Failed to send process sensor data")
            return False
        
        # Wait for acknowledgment
        response = await self.receive_message()
        if not response or response.get("type") != "sensor_data_received":
            logger.error(f"Unexpected response: {response}")
            return False
        
        logger.info("Process sensor data accepted by server")
        
        # Verify the data was integrated by querying for context
        if not await self.send_message("status_request", {}):
            logger.error("Failed to send status request")
            return False
        
        # Receive status response
        status = await self.receive_message()
        if not status or status.get("type") != "status_response":
            logger.error("Did not receive status response")
            return False
        
        # Check if the process data is reflected in the status
        if "context_data_size" in status.get("payload", {}):
            logger.info(f"Context data size: {status['payload']['context_data_size']}")
            self.results["process_sensor"] = True
            self.results["passed_tests"] += 1
            return True
        
        logger.error("Process sensor data not reflected in context")
        return False
    
    async def test_screen_sensor(self):
        """Test screen sensor data integration."""
        self.results["total_tests"] += 1
        
        logger.info("TESTING SCREEN SENSOR INTEGRATION")
        
        # Send simulated screen sensor data
        screen_data = {
            "sensor_type": "screen",
            "data": {
                "screen_text": "This is a test screen content for contextual awareness testing.",
                "has_images": True,
                "has_videos": False,
                "window": "TestWindow",
                "active_window": "TestWindow",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send the data
        if not await self.send_message("sensor_data", {
            "sensor_type": "screen",
            "data": screen_data["data"]
        }):
            logger.error("Failed to send screen sensor data")
            return False
        
        # Wait for acknowledgment
        response = await self.receive_message()
        if not response or response.get("type") != "sensor_data_received":
            logger.error(f"Unexpected response: {response}")
            return False
        
        logger.info("Screen sensor data accepted by server")
        
        # Verify the data was integrated with a query related to screen content
        query = "What's on my screen?"
        if not await self.send_message("query", {
            "query": query
        }):
            logger.error("Failed to send query")
            return False
        
        # Check if response contains screen data
        response = await self.receive_message(timeout=15)  # Longer timeout for LLM
        
        if not response:
            logger.error("No response received for screen content query")
            return False
        
        # Analyze response for screen content reference
        try:
            if isinstance(response, dict) and "content" in response:
                content = response["content"]
                
                # Check if the response references the test content
                if "test screen content" in content.lower() or "contextual awareness testing" in content.lower():
                    logger.info("Response correctly referenced screen content")
                    self.results["screen_sensor"] = True
                    self.results["passed_tests"] += 1
                    return True
                else:
                    logger.warning(f"Response does not reference screen content: {content[:200]}")
            else:
                logger.error(f"Unexpected response format: {response}")
        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
        
        return False
    
    async def test_file_sensor(self):
        """Test file sensor data integration."""
        self.results["total_tests"] += 1
        
        logger.info("TESTING FILE SENSOR INTEGRATION")
        
        # Send simulated file sensor data
        file_data = {
            "sensor_type": "file",
            "data": {
                "files": [
                    "test_file1.py",
                    "test_file2.py",
                    "test_config.yaml"
                ],
                "current_file": {
                    "name": "test_contextual_awareness.py",
                    "path": "/Users/segevbin/Desktop/SensAI/Aiayer/test_contextual_awareness.py",
                    "type": "text"
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send the data
        if not await self.send_message("sensor_data", {
            "sensor_type": "file",
            "data": file_data["data"]
        }):
            logger.error("Failed to send file sensor data")
            return False
        
        # Wait for acknowledgment
        response = await self.receive_message()
        if not response or response.get("type") != "sensor_data_received":
            logger.error(f"Unexpected response: {response}")
            return False
        
        logger.info("File sensor data accepted by server")
        
        # Verify the data was integrated with a query related to current file
        query = "What file am I working on?"
        if not await self.send_message("query", {
            "query": query
        }):
            logger.error("Failed to send query")
            return False
        
        # Check if response contains file information
        response = await self.receive_message(timeout=15)  # Longer timeout for LLM
        
        if not response:
            logger.error("No response received for file query")
            return False
        
        # Analyze response for file reference
        try:
            if isinstance(response, dict) and "content" in response:
                content = response["content"]
                
                # Check if the response references the test file
                if "test_contextual_awareness.py" in content:
                    logger.info("Response correctly referenced current file")
                    self.results["file_sensor"] = True
                    self.results["passed_tests"] += 1
                    return True
                else:
                    logger.warning(f"Response does not reference current file: {content[:200]}")
            else:
                logger.error(f"Unexpected response format: {response}")
        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
        
        return False
    
    async def test_memory_integration(self):
        """Test memory integration with context."""
        self.results["total_tests"] += 1
        
        logger.info("TESTING MEMORY INTEGRATION")
        
        # Send a message to be stored in memory
        memory_message = "Remember this specific phrase: MEMORY_TEST_TOKEN_8765"
        if not await self.send_message("query", {
            "query": memory_message
        }):
            logger.error("Failed to send memory message")
            return False
        
        # Wait for response
        response = await self.receive_message(timeout=15)
        if not response:
            logger.error("No response received for memory message")
            return False
        
        logger.info("Memory message sent and acknowledged")
        
        # Wait a moment for memory to process
        await asyncio.sleep(3)
        
        # Now query to retrieve the memory
        query = "What was the specific phrase I asked you to remember?"
        if not await self.send_message("query", {
            "query": query
        }):
            logger.error("Failed to send memory retrieval query")
            return False
        
        # Check if response contains the memory token
        response = await self.receive_message(timeout=15)
        
        if not response:
            logger.error("No response received for memory retrieval query")
            return False
        
        # Analyze response for memory token
        try:
            if isinstance(response, dict) and "content" in response:
                content = response["content"]
                
                # Check if the response references the memory token
                if "MEMORY_TEST_TOKEN_8765" in content:
                    logger.info("Response correctly retrieved memory token")
                    self.results["memory_integration"] = True
                    self.results["passed_tests"] += 1
                    return True
                else:
                    logger.warning(f"Response does not contain memory token: {content[:200]}")
            else:
                logger.error(f"Unexpected response format: {response}")
        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
        
        return False
    
    async def test_llm_with_context(self):
        """Test LLM responses with multiple context elements."""
        self.results["total_tests"] += 1
        
        logger.info("TESTING LLM WITH MULTIPLE CONTEXT ELEMENTS")
        
        # Set up a complex context with screen, process and file data
        screen_data = {
            "sensor_type": "screen",
            "data": {
                "screen_text": "# Final Contextual Awareness Test\n\nThis is testing the LLM's ability to combine multiple contexts.",
                "has_images": False,
                "window": "MultiContextTest",
                "active_window": "MultiContextTest",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        process_data = {
            "sensor_type": "process",
            "data": {
                "active_window": "MultiContextTest",
                "active_app": "TestSuite",
                "active_apps": ["TestSuite", "Terminal", "Browser"],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        file_data = {
            "sensor_type": "file",
            "data": {
                "files": ["test_file1.py", "test_file2.py", "complex_context.yaml"],
                "current_file": {
                    "name": "complex_context.yaml",
                    "path": "/Users/segevbin/Desktop/SensAI/Aiayer/complex_context.yaml",
                    "type": "text"
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send all context data
        await self.send_message("sensor_data", {
            "sensor_type": "screen",
            "data": screen_data["data"]
        })
        
        await self.receive_message()  # Get acknowledgment
        
        await self.send_message("sensor_data", {
            "sensor_type": "process",
            "data": process_data["data"]
        })
        
        await self.receive_message()  # Get acknowledgment
        
        await self.send_message("sensor_data", {
            "sensor_type": "file",
            "data": file_data["data"]
        })
        
        await self.receive_message()  # Get acknowledgment
        
        logger.info("All context data sent")
        
        # Now send a query that requires combining all contexts
        query = "Summarize my current context including what's on my screen, what application I'm using, and what file I'm working on."
        if not await self.send_message("query", {
            "query": query
        }):
            logger.error("Failed to send context query")
            return False
        
        # Check if response correctly combines all contexts
        response = await self.receive_message(timeout=20)  # Longer timeout for complex query
        
        if not response:
            logger.error("No response received for context query")
            return False
        
        # Analyze response for all context elements
        try:
            if isinstance(response, dict) and "content" in response:
                content = response["content"]
                
                # Define criteria for success - must reference all context elements
                screen_referenced = "contextual awareness test" in content.lower() or "multiple contexts" in content.lower()
                app_referenced = "multicontexttest" in content.lower().replace(" ", "") or "testsuite" in content.lower()
                file_referenced = "complex_context.yaml" in content.lower() or "complex context yaml" in content.lower()
                
                if screen_referenced and app_referenced and file_referenced:
                    logger.info("Response correctly referenced all context elements")
                    self.results["llm_response"] = True
                    self.results["passed_tests"] += 1
                    return True
                else:
                    logger.warning(f"Response missing some context elements (screen: {screen_referenced}, " +
                                   f"app: {app_referenced}, file: {file_referenced})")
                    logger.warning(f"Response: {content[:300]}")
            else:
                logger.error(f"Unexpected response format: {response}")
        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
        
        return False
    
    async def run_all_tests(self):
        """Run all contextual awareness tests."""
        logger.info("=== STARTING CONTEXTUAL AWARENESS TESTS ===")
        
        # Connect to WebSocket server
        if not await self.connect():
            logger.error("Failed to connect to WebSocket server")
            return self.results
        
        try:
            # Run all tests
            await self.test_process_sensor()
            await self.test_screen_sensor()
            await self.test_file_sensor()
            await self.test_memory_integration()
            await self.test_llm_with_context()
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
        finally:
            # Close connection
            await self.close()
        
        # Calculate success rate
        if self.results["total_tests"] > 0:
            success_rate = (self.results["passed_tests"] / self.results["total_tests"]) * 100
            self.results["success_rate"] = f"{success_rate:.2f}%"
        else:
            self.results["success_rate"] = "0.00%"
        
        # Log results
        logger.info("=== CONTEXTUAL AWARENESS TEST RESULTS ===")
        logger.info(f"Process Sensor Integration: {'PASS' if self.results['process_sensor'] else 'FAIL'}")
        logger.info(f"Screen Sensor Integration: {'PASS' if self.results['screen_sensor'] else 'FAIL'}")
        logger.info(f"File Sensor Integration: {'PASS' if self.results['file_sensor'] else 'FAIL'}")
        logger.info(f"Memory Integration: {'PASS' if self.results['memory_integration'] else 'FAIL'}")
        logger.info(f"LLM Context Integration: {'PASS' if self.results['llm_response'] else 'FAIL'}")
        logger.info(f"Overall Success Rate: {self.results['success_rate']}")
        
        return self.results

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test contextual awareness")
    parser.add_argument("--uri", default=WS_URI, help="WebSocket server URI")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    # Ensure log directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run tests
    tester = ContextualAwarenessTest(uri=args.uri, verbose=args.verbose)
    results = await tester.run_all_tests()
    
    # Print summary
    print("\n=== CONTEXTUAL AWARENESS TEST SUMMARY ===")
    print(f"Process Sensor Integration: {'✅ PASS' if results['process_sensor'] else '❌ FAIL'}")
    print(f"Screen Sensor Integration: {'✅ PASS' if results['screen_sensor'] else '❌ FAIL'}")
    print(f"File Sensor Integration: {'✅ PASS' if results['file_sensor'] else '❌ FAIL'}")
    print(f"Memory Integration: {'✅ PASS' if results['memory_integration'] else '❌ FAIL'}")
    print(f"LLM Context Integration: {'✅ PASS' if results['llm_response'] else '❌ FAIL'}")
    print(f"Overall Success Rate: {results['success_rate']}")
    
if __name__ == "__main__":
    asyncio.run(main())