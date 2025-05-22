#!/usr/bin/env python3
"""
Simple Connection Test
Tests WebSocket connections to running servers without timeout issues
"""
import asyncio
import json
import logging
import websockets
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection(url, server_name):
    """Test connection to a WebSocket server."""
    try:
        logger.info(f"Testing {server_name} at {url}...")
        
        # Connect without timeout parameter
        websocket = await websockets.connect(url)
        
        # Send test message
        test_message = {
            "type": "register",
            "payload": {
                "client_type": "ui",
                "test": True
            }
        }
        
        await websocket.send(json.dumps(test_message))
        logger.info(f"  ✅ {server_name}: Successfully sent registration message")
        
        # Wait for response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            logger.info(f"  ✅ {server_name}: Received response - {response_data.get('type', 'unknown')}")
            
            # Send a user query to test LLM integration
            if response_data.get('type') == 'registration_confirmed':
                query_message = {
                    "type": "user_interaction",
                    "payload": {
                        "type": "query",
                        "query": "Hello, can you help me with something?",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                }
                
                await websocket.send(json.dumps(query_message))
                logger.info(f"  📤 {server_name}: Sent test query")
                
                # Wait for AI response
                try:
                    ai_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    ai_data = json.loads(ai_response)
                    if ai_data.get('type') == 'query_response':
                        content = ai_data.get('payload', {}).get('response', '')
                        if content and len(content.strip()) > 10:
                            logger.info(f"  🤖 {server_name}: Received meaningful AI response ({len(content)} chars)")
                            logger.info(f"      Response: {content[:100]}...")
                            return True
                        else:
                            logger.warning(f"  ⚠️  {server_name}: AI response too short or empty")
                    else:
                        logger.info(f"  📨 {server_name}: Received {ai_data.get('type')} instead of query_response")
                except asyncio.TimeoutError:
                    logger.warning(f"  ⏰ {server_name}: No AI response within 10 seconds")
            
        except asyncio.TimeoutError:
            logger.warning(f"  ⏰ {server_name}: No registration response within 5 seconds")
        
        await websocket.close()
        return True
        
    except ConnectionRefusedError:
        logger.error(f"  ❌ {server_name}: Connection refused")
        return False
    except Exception as e:
        logger.error(f"  ❌ {server_name}: Error - {e}")
        return False

async def main():
    """Test all servers."""
    logger.info("🔍 Simple WebSocket Connection Test")
    logger.info("=" * 50)
    
    servers = {
        "Main WebSocket Server": "ws://localhost:8765",
        "Bridge Server": "ws://localhost:8766", 
        "Backend Server": "ws://localhost:8767"
    }
    
    results = {}
    for name, url in servers.items():
        results[name] = await test_connection(url, name)
        await asyncio.sleep(1)  # Brief delay between tests
    
    logger.info("\n🎯 Test Results:")
    logger.info("=" * 50)
    
    working_count = 0
    for name, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        logger.info(f"{status}: {name}")
        if success:
            working_count += 1
    
    logger.info(f"\n📊 Summary: {working_count}/{len(servers)} servers working")
    
    if working_count == len(servers):
        logger.info("🎉 All servers are working! The overlay should be able to connect.")
    elif working_count > 0:
        logger.info("⚠️  Some servers are working. Check logs for issues with failed servers.")
    else:
        logger.error("❌ No servers are working. Check server startup logs.")
    
    return working_count > 0

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)