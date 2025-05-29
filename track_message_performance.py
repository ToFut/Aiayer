#!/usr/bin/env python3
"""
Message Performance Tracker
Tracks user messages and analyzes response times to identify bottlenecks
"""

import asyncio
import json
import websockets
import logging
import time
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('message_tracker')

class MessagePerformanceTracker:
    def __init__(self):
        self.tracking_data = []
        self.current_message = None
        self.start_time = None
        
    def start_tracking(self, message_data):
        """Start tracking a new message"""
        self.current_message = {
            'message': message_data.get('message', ''),
            'mode': message_data.get('mode', ''),
            'client_id': message_data.get('client_id', ''),
            'timestamp': datetime.now().isoformat(),
            'start_time': time.time(),
            'phases': []
        }
        self.start_time = time.time()
        logger.info(f"🔍 TRACKING: {self.current_message['mode']} mode - '{self.current_message['message']}'")
        
    def add_phase(self, phase_name, details=""):
        """Add a performance phase"""
        if self.current_message:
            elapsed = time.time() - self.start_time
            self.current_message['phases'].append({
                'phase': phase_name,
                'elapsed_time': elapsed,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })
            logger.info(f"📊 PHASE: {phase_name} (+{elapsed:.2f}s) - {details}")
            
    def finish_tracking(self, response_data=None):
        """Finish tracking and analyze performance"""
        if self.current_message:
            total_time = time.time() - self.start_time
            self.current_message['total_time'] = total_time
            self.current_message['response_received'] = response_data is not None
            
            if response_data:
                self.current_message['response_type'] = response_data.get('type', 'unknown')
                self.current_message['response_size'] = len(str(response_data))
                
            self.tracking_data.append(self.current_message)
            self.analyze_performance()
            self.current_message = None
            
    def analyze_performance(self):
        """Analyze the performance of the last message"""
        if not self.tracking_data:
            return
            
        data = self.tracking_data[-1]
        total_time = data['total_time']
        
        logger.info("=" * 60)
        logger.info(f"📊 PERFORMANCE ANALYSIS")
        logger.info(f"   Message: '{data['message']}'")
        logger.info(f"   Mode: {data['mode']}")
        logger.info(f"   Total Time: {total_time:.2f}s")
        
        # Analyze phases
        if data['phases']:
            logger.info("   Phase Breakdown:")
            prev_time = 0
            for i, phase in enumerate(data['phases']):
                phase_duration = phase['elapsed_time'] - prev_time
                logger.info(f"     {i+1}. {phase['phase']}: {phase_duration:.2f}s")
                if phase['details']:
                    logger.info(f"        Details: {phase['details']}")
                prev_time = phase['elapsed_time']
        
        # Performance assessment
        if total_time > 30:
            logger.warning("🐌 SLOW RESPONSE: >30 seconds")
        elif total_time > 10:
            logger.warning("⚠️  DELAYED RESPONSE: >10 seconds")
        else:
            logger.info("⚡ GOOD RESPONSE TIME")
            
        logger.info("=" * 60)

async def track_user_message(tracker, message):
    """Track a specific user message through the system"""
    try:
        uri = "ws://localhost:8767"
        tracker.start_tracking(message)
        
        async with websockets.connect(uri) as websocket:
            tracker.add_phase("WebSocket Connected")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            tracker.add_phase("Welcome Received", f"Type: {json.loads(welcome).get('type', 'unknown')}")
            
            # Send the message
            await websocket.send(json.dumps(message))
            tracker.add_phase("Message Sent", f"Size: {len(json.dumps(message))} bytes")
            
            # Wait for response with timeout and progress tracking
            response_start = time.time()
            response_received = False
            
            try:
                # Try to get response with timeout
                response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                response_time = time.time() - response_start
                tracker.add_phase("Response Received", f"Response time: {response_time:.2f}s")
                
                response_data = json.loads(response)
                tracker.finish_tracking(response_data)
                
                # Analyze response content
                response_text = response_data.get('response', '')
                if "FAST AUTOMATION PLAN" in response_text:
                    logger.error("❌ MOCK TEMPLATE DETECTED - Agent Mode fix not working!")
                elif response_data.get('type') == 'final_response' and len(response_text) > 50:
                    logger.info(f"✅ Real response received: {response_text[:100]}...")
                else:
                    logger.info(f"📝 Response type: {response_data.get('type', 'unknown')}")
                
                return response_data
                
            except asyncio.TimeoutError:
                tracker.add_phase("Response Timeout", "60 second timeout reached")
                tracker.finish_tracking()
                logger.error("⏰ TIMEOUT: No response after 60 seconds")
                return None
                
    except Exception as e:
        tracker.add_phase("Error", str(e))
        tracker.finish_tracking()
        logger.error(f"❌ Tracking failed: {e}")
        return None

def analyze_backend_logs(tracker):
    """Analyze backend logs for performance insights"""
    try:
        log_file = "logs/backend/enhanced_enterprise_8767.log"
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        # Look for recent performance indicators
        recent_lines = lines[-100:]  # Last 100 lines
        
        logger.info("🔍 BACKEND LOG ANALYSIS:")
        
        # Check for LLM timeouts
        llm_timeouts = [line for line in recent_lines if "timeout" in line.lower()]
        if llm_timeouts:
            logger.warning(f"⚠️  Found {len(llm_timeouts)} LLM timeout warnings")
            for timeout in llm_timeouts[-3:]:  # Show last 3
                logger.warning(f"   {timeout.strip()}")
        
        # Check for handler usage
        universal_usage = [line for line in recent_lines if "Universal" in line and "handler" in line]
        if universal_usage:
            logger.info("✅ Universal handler is being used")
        else:
            logger.warning("⚠️  No recent Universal handler usage found")
            
        # Check for errors
        error_lines = [line for line in recent_lines if "ERROR" in line]
        if error_lines:
            logger.warning(f"⚠️  Found {len(error_lines)} recent errors")
            for error in error_lines[-3:]:  # Show last 3
                logger.warning(f"   {error.strip()}")
                
    except Exception as e:
        logger.error(f"❌ Could not analyze backend logs: {e}")

async def comprehensive_message_test():
    """Run comprehensive message tracking tests"""
    tracker = MessagePerformanceTracker()
    
    logger.info("🚀 Starting Comprehensive Message Performance Analysis")
    logger.info("=" * 80)
    
    # First, analyze backend logs
    analyze_backend_logs(tracker)
    logger.info("")
    
    # Test different types of messages
    test_messages = [
        {
            "type": "chat_request",
            "message": "hello",
            "mode": "Ask",
            "client_id": "perf_test_1",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "chat_request", 
            "message": "open calculator",
            "mode": "Agent",
            "client_id": "perf_test_2",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "chat_request",
            "message": "search Spotify omer adam",
            "mode": "Agent",
            "client_id": "perf_test_3",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"\n🧪 TEST {i}/3: {message['mode']} mode - '{message['message']}'")
        logger.info("-" * 60)
        
        result = await track_user_message(tracker, message)
        
        if result:
            logger.info(f"✅ Test {i} completed successfully")
        else:
            logger.error(f"❌ Test {i} failed or timed out")
        
        # Wait between tests
        if i < len(test_messages):
            logger.info("⏳ Waiting 5 seconds before next test...")
            await asyncio.sleep(5)
    
    # Final analysis
    logger.info("\n" + "=" * 80)
    logger.info("📊 FINAL PERFORMANCE SUMMARY")
    logger.info("=" * 80)
    
    if tracker.tracking_data:
        avg_time = sum(d['total_time'] for d in tracker.tracking_data) / len(tracker.tracking_data)
        logger.info(f"Average response time: {avg_time:.2f}s")
        
        slow_responses = [d for d in tracker.tracking_data if d['total_time'] > 10]
        if slow_responses:
            logger.warning(f"Slow responses (>10s): {len(slow_responses)}/{len(tracker.tracking_data)}")
            for slow in slow_responses:
                logger.warning(f"  - {slow['mode']} '{slow['message']}': {slow['total_time']:.2f}s")
        
        # Check for mock templates
        mock_responses = 0
        for data in tracker.tracking_data:
            if any("FAST AUTOMATION PLAN" in phase.get('details', '') for phase in data.get('phases', [])):
                mock_responses += 1
        
        if mock_responses > 0:
            logger.error(f"❌ Mock templates detected: {mock_responses} responses")
        else:
            logger.info("✅ No mock templates detected - Agent Mode fix working!")
    
    return tracker.tracking_data

if __name__ == "__main__":
    # Run the comprehensive test
    results = asyncio.run(comprehensive_message_test())
    
    # Save results to file
    with open("message_performance_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n📄 Results saved to: message_performance_results.json")
    print("🔍 Use this data to identify performance bottlenecks!")