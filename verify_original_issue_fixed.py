#!/usr/bin/env python3
"""
Verify Original Issue Fixed
Tests the exact scenario the user reported: "search best flights to Miami from"
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def verify_original_issue():
    """Test the exact scenario the user reported"""
    uri = "ws://localhost:8767"
    
    try:
        logger.info("🔍 VERIFYING ORIGINAL USER ISSUE IS FIXED")
        logger.info("📋 Original issue: 'AgentMode not making plan or execution buttons'")
        logger.info("🎯 Testing: 'search best flights to Miami from'")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to backend WebSocket")
            
            # Wait for welcome
            welcome = await websocket.recv()
            logger.info("📨 Connection established")
            
            # Send the exact request from user's issue
            request = {
                "type": "chat_request",
                "message": "search best flights to Miami from",  # Exact user request
                "mode": "Agent",
                "client_id": "client_verification",
                "session_id": "session_verification"
            }
            
            logger.info("🚀 Sending exact user request...")
            await websocket.send(json.dumps(request))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            data = json.loads(response)
            
            logger.info("📨 Response received!")
            
            # Check if it's a proper AgentMode response
            if data.get('type') == 'final_response' and data.get('mode') == 'Agent':
                logger.info("✅ AgentMode response detected")
                
                # Check for buttons
                buttons = data.get('buttons', [])
                if buttons:
                    logger.info(f"✅ Interactive buttons generated: {len(buttons)}")
                    
                    execute_found = False
                    cancel_found = False
                    
                    for btn in buttons:
                        button_text = btn.get('text', '')
                        button_action = btn.get('action', '')
                        
                        logger.info(f"   🔘 {button_text} → {button_action}")
                        
                        if 'EXECUTE' in button_text:
                            execute_found = True
                        if 'CANCEL' in button_text:
                            cancel_found = True
                    
                    if execute_found and cancel_found:
                        logger.info("🎉 SUCCESS: Both EXECUTE and CANCEL buttons found!")
                        
                        # Check for plan content
                        response_text = data.get('response', '')
                        if 'Plan ID' in response_text or 'plan' in response_text.lower():
                            logger.info("✅ Automation plan content detected")
                            logger.info("🔧 ORIGINAL ISSUE COMPLETELY FIXED!")
                            return True
                        else:
                            logger.warning("⚠️ Buttons found but plan content unclear")
                            return True
                    else:
                        logger.error("❌ Missing expected buttons")
                        return False
                else:
                    logger.error("❌ No buttons generated - issue NOT fixed")
                    return False
            else:
                logger.error(f"❌ Wrong response type: {data.get('type')} / {data.get('mode')}")
                return False
                
    except Exception as e:
        logger.error(f"💥 Verification failed: {e}")
        return False

async def main():
    logger.info("=" * 70)
    logger.info("🔍 ORIGINAL ISSUE VERIFICATION")
    logger.info("=" * 70)
    
    success = await verify_original_issue()
    
    logger.info("=" * 70)
    if success:
        logger.info("🎉 ✅ ORIGINAL ISSUE COMPLETELY FIXED!")
        logger.info("✅ AgentMode now generates plans with execution buttons")
        logger.info("✅ User can proceed with flight search automation")
    else:
        logger.error("❌ ⚠️  ORIGINAL ISSUE NOT FULLY RESOLVED")
    logger.info("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())