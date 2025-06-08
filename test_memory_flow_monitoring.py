#!/usr/bin/env python3
"""
Test script to monitor the memory flow from sensors through LLM processing to memory storage
"""

import asyncio
import json
import logging
import websockets
import time
import os
import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/memory_flow_test.log")
    ]
)
logger = logging.getLogger("memory_flow_test")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Sample sensor data to simulate different inputs
SAMPLE_SENSOR_DATA = [
    # Screen sensor data
    {
        "type": "add_sensor_data",
        "sensor_type": "screen",
        "data": {
            "timestamp": datetime.datetime.now().isoformat(),
            "active_window": "Test Window - Google Chrome",
            "screen_content": "This is test content that should be processed by the LLM and stored in memory",
            "application": {
                "name": "Google Chrome",
                "view": "browser",
                "workflow_stage": "web research"
            }
        }
    },
    # Process sensor data
    {
        "type": "add_sensor_data",
        "sensor_type": "process",
        "data": {
            "timestamp": datetime.datetime.now().isoformat(),
            "active_apps": [
                "Google Chrome",
                "Terminal",
                "Code",
                "Slack",
                "Spotify"
            ],
            "window_title": "Test Process Window"
        }
    }
]

async def monitor_memory_flow():
    """Monitor the flow of data from sensors through LLM to memory storage"""
    # Backend server for sensor data and memory operations
    backend_uri = "ws://localhost:8767"
    
    logger.info(f"Connecting to backend at {backend_uri}...")
    
    try:
        async with websockets.connect(backend_uri) as websocket:
            logger.info("Connected to backend server")
            
            # Wait for welcome message
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received welcome: {response_data.get('type')}")
            
            # Register client
            await websocket.send(json.dumps({
                "type": "register",
                "client": "memory_flow_test",
                "version": "1.0.0"
            }))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Registration response: {response_data.get('type')}")
            
            # Check initial system state
            await websocket.send(json.dumps({
                "type": "get_system_stats"
            }))
            
            response = await websocket.recv()
            initial_stats = json.loads(response)
            
            if initial_stats.get("type") == "system_stats":
                logger.info("Initial system stats:")
                logger.info(f"Memory system available: {initial_stats.get('memory_system_available', False)}")
                memory_stats = initial_stats.get("stats", {})
                logger.info(f"Total memories: {memory_stats.get('total_memories', 0)}")
                logger.info(f"Short-term memories: {memory_stats.get('short_term_count', 0)}")
                logger.info(f"Long-term memories: {memory_stats.get('long_term_count', 0)}")
            else:
                logger.error(f"Failed to get initial system stats: {initial_stats}")
                return
            
            # Send sample sensor data
            logger.info(f"Sending {len(SAMPLE_SENSOR_DATA)} sample sensor data items...")
            
            for i, sensor_data in enumerate(SAMPLE_SENSOR_DATA):
                logger.info(f"Sending {sensor_data['sensor_type']} sensor data...")
                await websocket.send(json.dumps(sensor_data))
                
                # Wait for acknowledgment
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "sensor_data_response":
                        success = response_data.get("success", False)
                        if success:
                            logger.info(f"✅ Successfully processed {sensor_data['sensor_type']} sensor data")
                        else:
                            logger.error(f"❌ Failed to process {sensor_data['sensor_type']} sensor data: {response_data.get('error', 'Unknown error')}")
                    else:
                        logger.warning(f"Unexpected response type: {response_data.get('type')}")
                        
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for response to {sensor_data['sensor_type']} data")
                
                # Give the system time to process the data
                await asyncio.sleep(2)
            
            # Wait for LLM processing (which happens periodically)
            logger.info("Waiting for LLM processing to complete (15 seconds)...")
            await asyncio.sleep(15)
            
            # Check final system state
            await websocket.send(json.dumps({
                "type": "get_system_stats"
            }))
            
            response = await websocket.recv()
            final_stats = json.loads(response)
            
            if final_stats.get("type") == "system_stats":
                logger.info("Final system stats:")
                logger.info(f"Memory system available: {final_stats.get('memory_system_available', False)}")
                memory_stats = final_stats.get("stats", {})
                logger.info(f"Total memories: {memory_stats.get('total_memories', 0)}")
                logger.info(f"Short-term memories: {memory_stats.get('short_term_count', 0)}")
                logger.info(f"Long-term memories: {memory_stats.get('long_term_count', 0)}")
                
                # Compare with initial stats
                initial_total = initial_stats.get("stats", {}).get("total_memories", 0)
                final_total = memory_stats.get("total_memories", 0)
                
                if final_total > initial_total:
                    logger.info(f"✅ Memory count increased from {initial_total} to {final_total}")
                    logger.info("✅ Memory flow is working: Sensors -> LLM -> Memory storage")
                else:
                    logger.warning(f"⚠️ Memory count didn't increase: {initial_total} -> {final_total}")
                    logger.warning("⚠️ Memory flow may not be working correctly")
            else:
                logger.error(f"Failed to get final system stats: {final_stats}")
            
            # Try to search for our added content
            logger.info("Searching for added content...")
            await websocket.send(json.dumps({
                "type": "search_memory",
                "query": "test content processed by LLM",
                "top_k": 5
            }))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                search_results = json.loads(response)
                
                if search_results.get("type") == "search_results":
                    results = search_results.get("results", [])
                    logger.info(f"Search returned {len(results)} results")
                    
                    if results:
                        found = False
                        for i, result in enumerate(results):
                            content = result.get("content", "")
                            score = result.get("score", 0)
                            logger.info(f"Result {i+1}: Score {score:.3f} - {content[:50]}...")
                            
                            if "test content" in content.lower():
                                found = True
                                logger.info(f"✅ Found our test content in search results!")
                        
                        if not found:
                            logger.warning("⚠️ Test content not found in search results")
                    else:
                        logger.warning("⚠️ No search results returned")
                else:
                    logger.error(f"Unexpected search response: {search_results}")
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for search results")
            
    except Exception as e:
        logger.error(f"Error monitoring memory flow: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting memory flow monitoring")
    asyncio.run(monitor_memory_flow())
    logger.info("Memory flow monitoring completed")