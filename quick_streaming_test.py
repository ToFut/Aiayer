#!/usr/bin/env python3
"""
Quick test for frame streaming
"""

import asyncio
import time
import logging
from realtime_screen_tcp_server import RealTimeScreenTCPServer
from realtime_agent_vision import RealTimeAgentVision

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_streaming():
    """Quick streaming test"""
    logger.info("🔒 Starting quick streaming test...")
    
    # Create secure server and agent
    server = RealTimeScreenTCPServer(host="127.0.0.1", port=9995)
    agent = RealTimeAgentVision(server_host="127.0.0.1", server_port=9995)
    
    try:
        # Start server
        server_task = asyncio.create_task(server.start_server())
        await asyncio.sleep(1)
        
        # Connect agent
        connected = await agent.connect_to_screen_server()
        if connected:
            logger.info("✅ Connected successfully")
            
            # Start vision system (includes frame receiving)
            vision_task = asyncio.create_task(agent.start_real_time_vision())
            
            # Wait and check frames
            await asyncio.sleep(5)
            
            # Stop vision
            agent.running = False
            
            summary = agent.get_vision_summary()
            logger.info(f"📊 Frames received: {summary['frames_received']}")
            logger.info(f"📊 FPS: {summary['fps']:.1f}")
            
            if summary['frames_received'] > 0:
                logger.info("✅ Frame streaming working!")
            else:
                logger.error("❌ No frames received")
            
            # Stop
            await agent.stop_vision()
        else:
            logger.error("❌ Connection failed")
        
        await server.stop_server()
        
    except Exception as e:
        logger.error(f"Test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_streaming())