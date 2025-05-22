#!/usr/bin/env python3
"""
WebSocket Flow Test Script

This script tests the WebSocket-based communication between system components.
It connects to the bridge server as a monitoring client and observes the messages
being passed between components, ensuring data is flowing properly from sensors
to memory system.
"""
import asyncio
import json
import logging
import websockets
import argparse
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket_flow_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('websocket_flow_test')

class WebSocketFlowTester:
    """Tests the flow of data through WebSocket connections"""
    
    def __init__(self, bridge_uri="ws://localhost:8768", test_duration=60):
        self.bridge_uri = bridge_uri
        self.test_duration = test_duration
        self.message_counts = {
            "screen_sensor": 0,
            "process_sensor": 0,
            "memory_system": 0,
            "llm_service": 0,
            "welcome": 0,
            "connection_established": 0,
            "connection_acknowledged": 0,
            "sensor_data": 0,
            "other": 0
        }
        self.connected_clients = set()
        self.sensor_messages = {}
        self.start_time = None
        
    async def connect_to_bridge(self):
        """Connect to bridge server and monitor messages"""
        try:
            async with websockets.connect(self.bridge_uri) as websocket:
                logger.info(f"Connected to bridge server at {self.bridge_uri}")
                
                # Start test timer
                self.start_time = time.time()
                end_time = self.start_time + self.test_duration
                
                # Process incoming messages
                while time.time() < end_time:
                    try:
                        # Receive messages with a timeout so we can update progress
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        await self.process_message(message)
                        
                        # Log progress every 10 seconds
                        elapsed = time.time() - self.start_time
                        remaining = self.test_duration - elapsed
                        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                            logger.info(f"Test running for {int(elapsed)}s, {int(remaining)}s remaining")
                            self._log_message_counts()
                    
                    except asyncio.TimeoutError:
                        # This is expected when there are no messages
                        elapsed = time.time() - self.start_time
                        remaining = self.test_duration - elapsed
                        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                            logger.info(f"Test running for {int(elapsed)}s, {int(remaining)}s remaining")
                            self._log_message_counts()
                        continue
                    except Exception as e:
                        logger.error(f"Error receiving message: {e}")
                
                # Test complete
                logger.info(f"Test completed after {self.test_duration} seconds")
                self._log_message_counts()
                
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.error(f"Connection to bridge server failed: {e}")
            print(f"❌ Connection to bridge server failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"❌ Unexpected error: {e}")
            return False
            
        return True
        
    async def process_message(self, message):
        """Process a received WebSocket message"""
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            
            # Count message by type
            if msg_type in self.message_counts:
                self.message_counts[msg_type] += 1
            else:
                self.message_counts["other"] += 1
                
            # Process message based on type
            if msg_type == "welcome":
                logger.info("Received welcome message from bridge server")
                
            elif msg_type == "connection_established":
                payload = data.get('payload', {})
                client_type = payload.get('client', 'unknown')
                self.connected_clients.add(client_type)
                logger.info(f"Client connected: {client_type}")
                
            elif msg_type == "connection_acknowledged":
                client_type = data.get('client_type', 'unknown')
                logger.info(f"Connection acknowledged for client type: {client_type}")
                
            elif msg_type == "sensor_data":
                sensor_type = data.get('sensor_type', 'unknown')
                payload = data.get('payload', {})
                timestamp = data.get('timestamp', datetime.now().isoformat())
                
                if sensor_type not in self.sensor_messages:
                    self.sensor_messages[sensor_type] = []
                
                # Add message to sensor message history (limit to 5 most recent)
                self.sensor_messages[sensor_type].append({
                    "timestamp": timestamp,
                    "payload_size": len(json.dumps(payload)),
                    "payload_keys": list(payload.keys()) if isinstance(payload, dict) else []
                })
                if len(self.sensor_messages[sensor_type]) > 5:
                    self.sensor_messages[sensor_type].pop(0)
                    
                # Count by sensor type
                if sensor_type == "screen":
                    self.message_counts["screen_sensor"] += 1
                elif sensor_type == "process":
                    self.message_counts["process_sensor"] += 1
                    
                logger.info(f"Received {sensor_type} sensor data")
            
            else:
                logger.info(f"Received message of type: {msg_type}")
            
        except json.JSONDecodeError:
            logger.error(f"Received invalid JSON: {message[:100]}...")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _log_message_counts(self):
        """Log current message counts"""
        logger.info("Current message counts:")
        for msg_type, count in self.message_counts.items():
            logger.info(f"  {msg_type}: {count}")
        
        logger.info("Connected clients:")
        for client in self.connected_clients:
            logger.info(f"  {client}")
    
    def print_results(self):
        """Print test results"""
        print("\n===== WebSocket Flow Test Results =====")
        print(f"Test duration: {self.test_duration} seconds")
        print("\nMessage Counts:")
        
        for msg_type, count in sorted(self.message_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {msg_type}: {count}")
        
        print("\nConnected Clients:")
        for client in sorted(self.connected_clients):
            print(f"  {client}")
        
        print("\nSensor Data Flow:")
        for sensor_type, messages in self.sensor_messages.items():
            print(f"  {sensor_type} sensor: {len(messages)} messages")
            if messages:
                latest = messages[-1]
                print(f"    - Latest message: {latest['timestamp']}")
                print(f"    - Payload size: {latest['payload_size']} bytes")
                print(f"    - Payload keys: {', '.join(latest['payload_keys'])}")
        
        # Check if we received data from all expected components
        all_working = True
        expected_sensors = ["screen", "process"]
        for sensor in expected_sensors:
            if sensor not in self.sensor_messages or not self.sensor_messages[sensor]:
                print(f"\n⚠️ No messages received from {sensor} sensor!")
                all_working = False
        
        if "memory_system" not in self.connected_clients:
            print("\n⚠️ Memory system did not connect to bridge server!")
            all_working = False
            
        if all_working:
            print("\n✅ System appears to be working correctly!")
            print("Data is flowing from sensors through the bridge server.")
            
            # Check data flow rate
            for sensor_type, messages in self.sensor_messages.items():
                if len(messages) >= 2:
                    rate = len(messages) / self.test_duration
                    print(f"  - {sensor_type} sensor data rate: {rate:.2f} messages/second")
        else:
            print("\n⚠️ Some components may not be working correctly.")
            print("Check the individual component logs for more details.")
        
        print("\nTo check component logs, run:")
        print("  tail -f logs/bridge_server.log")
        print("  tail -f logs/sensors/screen_sensor/screen_sensor.log")
        print("  tail -f logs/sensors/process_sensor/process_sensor.log")
        print("  tail -f logs/memory/memory_system.log")
        print("  tail -f logs/memory/memory_connector.log")
        
        print("\n=======================================")

async def run_test(args):
    """Run the WebSocket flow test"""
    tester = WebSocketFlowTester(
        bridge_uri=args.bridge_uri,
        test_duration=args.duration
    )
    
    print(f"Starting WebSocket flow test...")
    print(f"Connecting to bridge server at {args.bridge_uri}")
    print(f"Test will run for {args.duration} seconds")
    print("Monitoring messages passing through the bridge server...")
    print("(This will take a while - please be patient)")
    
    success = await tester.connect_to_bridge()
    if success:
        tester.print_results()
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the WebSocket communication flow between system components")
    parser.add_argument('--bridge-uri', default="ws://localhost:8768", help="Bridge server URI")
    parser.add_argument('--duration', type=int, default=30, help="Test duration in seconds")
    args = parser.parse_args()
    
    try:
        asyncio.run(run_test(args))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Error running test: {e}")
        print(f"Error running test: {e}")