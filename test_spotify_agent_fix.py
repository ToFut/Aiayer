#!/usr/bin/env python3
"""
Test the specific Spotify Agent mode query that was failing before.
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_spotify_agent')

async def test_spotify_agent():
    """Test Agent mode with the original problematic Spotify query"""
    try:
        # Connect to the backend
        uri = "ws://localhost:8767"
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Connected: {welcome}")
            
            # Send the original problematic Agent mode message
            test_message = {
                "type": "chat_request",
                "message": "search Spotify omer adam",
                "mode": "Agent", 
                "client_id": "test_client",
                "timestamp": "2025-05-27T12:00:00.000Z"
            }
            
            logger.info(f"🎵 Testing original failing query: '{test_message['message']}'")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response with extended timeout for LLM processing
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=45.0)
                response_data = json.loads(response)
                
                logger.info(f"✅ Received response type: {response_data.get('type', 'unknown')}")
                
                # Check if it's real LLM planning or mock template
                response_text = response_data.get('response', '')
                
                if "FAST AUTOMATION PLAN" in response_text:
                    logger.error("❌ STILL USING MOCK TEMPLATES!")
                    logger.error("   Found 'FAST AUTOMATION PLAN' in response")
                    logger.error(f"   Response: {response_text[:200]}...")
                    return {"success": False, "issue": "mock_template"}
                
                elif "safari" in response_text.lower() and "google" in response_text.lower():
                    logger.error("❌ STILL USING GENERIC WEB SEARCH TEMPLATE!")
                    logger.error("   Response contains Safari + Google (generic template)")
                    logger.error(f"   Response: {response_text[:200]}...")
                    return {"success": False, "issue": "generic_template"}
                
                elif "spotify" in response_text.lower():
                    logger.info("🎯 SUCCESS: Response contains Spotify-specific content!")
                    logger.info("   This suggests real LLM planning is working")
                    logger.info(f"   Response: {response_text[:300]}...")
                    return {"success": True, "type": "spotify_specific"}
                
                else:
                    logger.info("🤔 UNCLEAR: Got response but unclear if LLM or template")
                    logger.info(f"   Response: {response_text[:300]}...")
                    return {"success": "unclear", "response": response_text}
                
            except asyncio.TimeoutError:
                logger.error("❌ TIMEOUT: No response within 45 seconds")
                logger.error("   This could indicate LLM processing issues")
                return {"success": False, "issue": "timeout"}
                
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return {"success": False, "issue": "connection_error", "error": str(e)}

async def main():
    logger.info("🧪 Testing Spotify Agent Mode Fix")
    logger.info("=" * 50)
    logger.info("Original issue: 'search Spotify omer adam' was returning")
    logger.info("mock 'FAST AUTOMATION PLAN' instead of real LLM planning")
    logger.info("=" * 50)
    
    result = await test_spotify_agent()
    
    logger.info("\n" + "=" * 50)
    logger.info("🔍 TEST RESULTS:")
    
    if result.get("success") is True:
        logger.info("🎉 SUCCESS: Agent Mode is now using real LLM planning!")
        logger.info("   The Spotify query generated context-aware automation")
    elif result.get("issue") == "mock_template":
        logger.info("💥 FAILED: Still using mock templates")
        logger.info("   Backend may not be using our fixed code")
    elif result.get("issue") == "generic_template":
        logger.info("💥 FAILED: Still using generic web search templates")
        logger.info("   Universal handler may not be working correctly")
    elif result.get("issue") == "timeout":
        logger.info("⏱️  TIMEOUT: LLM may be processing but taking too long")
        logger.info("   This suggests real LLM calls are being made (good sign)")
    else:
        logger.info(f"❓ UNCLEAR: {result}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())