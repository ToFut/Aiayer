#!/usr/bin/env python3
"""
Debug DO Button with Neural UI Setup
"""

import asyncio
import json
import websockets
import uuid
import logging
import sys
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/debug_do_button.log')
    ]
)
logger = logging.getLogger("debug_do_button")

# Connection URLs
PROXY_URL = "ws://localhost:8766"  # Fix DO Button Connection Bridge
BACKEND_URL = "ws://localhost:8767/ws"  # Enhanced Enterprise Backend
DO_BUTTON_URL = "ws://localhost:8765"  # Ultimate DO Button Server
NEURAL_UI_URL = "ws://localhost:8768"  # Neural UI Detector Server

# Flag to import plan_persistence module
try_persistence = True

async def connect_to_websocket(url: str) -> Optional[websockets.WebSocketClientProtocol]:
    """Connect to a WebSocket server"""
    try:
        logger.info(f"Connecting to {url}...")
        connection = await websockets.connect(url)
        welcome = await connection.recv()
        logger.info(f"Connected to {url}: {welcome[:100]}...")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to {url}: {e}")
        return None

async def create_test_plan() -> str:
    """Create a test plan in the backend and return its ID"""
    try:
        # Connect to backend
        connection = await connect_to_websocket(BACKEND_URL)
        if not connection:
            logger.error("Failed to connect to backend")
            return ""
        
        # Register with backend
        await connection.send(json.dumps({
            "type": "register",
            "client_type": "debug_client",
            "version": "1.0.0"
        }))
        reg_response = await connection.recv()
        logger.info(f"Registration response: {reg_response[:100]}...")
        
        # Create a test plan (agent mode message)
        plan_id = f"test_plan_{uuid.uuid4()}"
        
        agent_message = {
            "type": "agent_mode_message",
            "message": "Search for information about neural networks",
            "mode": "agent",
            "client_id": "debug_client",
            "timestamp": int(time.time() * 1000),
            "session_id": plan_id
        }
        
        await connection.send(json.dumps(agent_message))
        
        # Wait for plan creation
        while True:
            response = await connection.recv()
            data = json.loads(response)
            logger.info(f"Received response type: {data.get('type')}")
            
            if data.get('type') == 'agent_automation_plan':
                logger.info(f"✅ Plan created with ID: {data.get('agentSessionId') or data.get('plan_id')}")
                plan_id = data.get('agentSessionId') or data.get('plan_id')
                break
            elif data.get('type') == 'error':
                logger.error(f"Error creating plan: {data.get('error')}")
                return ""
        
        await connection.close()
        return plan_id
    except Exception as e:
        logger.error(f"Error creating test plan: {e}")
        return ""

async def check_plan_exists(plan_id: str) -> bool:
    """Check if a plan exists in the backend"""
    try:
        # Try to import plan_persistence first
        plan_data = None
        if try_persistence:
            try:
                from plan_persistence import load_plan
                logger.info("✅ plan_persistence module imported successfully")
                
                # Try to load the plan
                plan_data = await load_plan(plan_id)
                if plan_data:
                    logger.info(f"✅ Plan {plan_id} loaded from persistence")
                    return True
            except ImportError as e:
                logger.warning(f"⚠️ plan_persistence module not available: {e}")
            except Exception as e:
                logger.error(f"❌ Error loading plan from persistence: {e}")
        
        # Connect to backend
        connection = await connect_to_websocket(BACKEND_URL)
        if not connection:
            logger.error("Failed to connect to backend")
            return False
        
        # Query for plan
        await connection.send(json.dumps({
            "type": "query_plan",
            "plan_id": plan_id
        }))
        
        # Wait for response
        response = await connection.recv()
        data = json.loads(response)
        
        await connection.close()
        
        if data.get('found', False):
            logger.info(f"✅ Plan {plan_id} found in backend")
            return True
        else:
            logger.warning(f"⚠️ Plan {plan_id} not found in backend")
            return False
    except Exception as e:
        logger.error(f"Error checking plan: {e}")
        return False

async def execute_plan_via_do_button(plan_id: str) -> bool:
    """Execute a plan using the DO button through the proxy"""
    try:
        # Connect to proxy
        connection = await connect_to_websocket(PROXY_URL)
        if not connection:
            logger.error("Failed to connect to proxy")
            return False
        
        # Create DO button action
        do_action = {
            "type": "agent_confirmation",
            "sessionId": plan_id,
            "action": "DO",
            "timestamp": int(time.time() * 1000)
        }
        
        logger.info(f"Sending DO button action for plan {plan_id}")
        await connection.send(json.dumps(do_action))
        
        # Wait for response
        response = await connection.recv()
        data = json.loads(response)
        
        await connection.close()
        
        if data.get('type') == 'agent_execution_success':
            logger.info(f"✅ Plan executed successfully: {data.get('summary', 'No summary')}")
            return True
        else:
            logger.error(f"❌ Plan execution failed: {data.get('error', 'No error message')}")
            return False
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        return False

async def check_neural_ui_do_button_handler():
    """Check if neural_ui_do_button_handler module is available"""
    try:
        from neural_ui_do_button_handler import handle_proxy_message
        logger.info("✅ neural_ui_do_button_handler module imported successfully")
        return True
    except ImportError as e:
        logger.warning(f"⚠️ neural_ui_do_button_handler module not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error importing neural_ui_do_button_handler: {e}")
        return False

async def debug_pending_plans_in_backend():
    """Debug pending plans in the backend"""
    try:
        # Connect to backend
        connection = await connect_to_websocket(BACKEND_URL)
        if not connection:
            logger.error("Failed to connect to backend")
            return
        
        # Send debug command
        await connection.send(json.dumps({
            "type": "debug_pending_plans"
        }))
        
        # Wait for response
        response = await connection.recv()
        data = json.loads(response)
        
        await connection.close()
        
        if 'pending_plans' in data:
            plans = data['pending_plans']
            logger.info(f"Found {len(plans)} pending plans in backend")
            for plan_id in plans:
                logger.info(f"  - {plan_id}")
        else:
            logger.warning("No pending plans found or backend doesn't support debug command")
    except Exception as e:
        logger.error(f"Error debugging pending plans: {e}")

async def fix_plan_id_format(plan_id: str) -> str:
    """Add 'universal_' prefix if needed to match what the handler expects"""
    if not plan_id.startswith("universal_"):
        return f"universal_{plan_id}"
    return plan_id

async def main():
    """Main debug function"""
    logger.info("=== Debugging DO Button with Neural UI Setup ===")
    
    # Step 1: Check connections to all servers
    logger.info("\nStep 1: Checking connections to all servers...")
    backend_conn = await connect_to_websocket(BACKEND_URL)
    do_button_conn = await connect_to_websocket(DO_BUTTON_URL)
    neural_ui_conn = await connect_to_websocket(NEURAL_UI_URL)
    proxy_conn = await connect_to_websocket(PROXY_URL)
    
    if backend_conn:
        await backend_conn.close()
    if do_button_conn:
        await do_button_conn.close()
    if neural_ui_conn:
        await neural_ui_conn.close()
    if proxy_conn:
        await proxy_conn.close()
    
    # Step 2: Check if neural_ui_do_button_handler is available
    logger.info("\nStep 2: Checking if neural_ui_do_button_handler is available...")
    handler_available = await check_neural_ui_do_button_handler()
    
    # Step 3: Create a test plan
    logger.info("\nStep 3: Creating a test plan...")
    plan_id = await create_test_plan()
    if not plan_id:
        logger.error("Failed to create test plan, exiting")
        return
    
    # Step 4: Verify the plan exists
    logger.info(f"\nStep 4: Verifying plan {plan_id} exists...")
    plan_exists = await check_plan_exists(plan_id)
    if not plan_exists:
        # Try fixing the plan ID format
        fixed_plan_id = await fix_plan_id_format(plan_id)
        logger.info(f"Trying with fixed plan ID format: {fixed_plan_id}")
        plan_exists = await check_plan_exists(fixed_plan_id)
        if plan_exists:
            plan_id = fixed_plan_id
    
    # Step 5: Debug pending plans in backend
    logger.info("\nStep 5: Debugging pending plans in backend...")
    await debug_pending_plans_in_backend()
    
    # Step 6: Execute the plan using DO button
    logger.info(f"\nStep 6: Executing plan {plan_id} using DO button...")
    execution_success = await execute_plan_via_do_button(plan_id)
    
    # Summary
    logger.info("\n=== Debug Summary ===")
    logger.info(f"Backend connection: {'✅ Success' if backend_conn else '❌ Failed'}")
    logger.info(f"DO Button Server connection: {'✅ Success' if do_button_conn else '❌ Failed'}")
    logger.info(f"Neural UI Server connection: {'✅ Success' if neural_ui_conn else '❌ Failed'}")
    logger.info(f"Proxy connection: {'✅ Success' if proxy_conn else '❌ Failed'}")
    logger.info(f"neural_ui_do_button_handler: {'✅ Available' if handler_available else '❌ Not available'}")
    logger.info(f"Plan creation: {'✅ Success' if plan_id else '❌ Failed'}")
    logger.info(f"Plan verification: {'✅ Success' if plan_exists else '❌ Failed'}")
    logger.info(f"Plan execution: {'✅ Success' if execution_success else '❌ Failed'}")
    
    if not execution_success:
        logger.info("\n=== Recommendations ===")
        
        if not handler_available:
            logger.info("1. Add the missing save_plan function to plan_persistence.py")
            logger.info("   - The module has load_plan but is missing save_plan, which is needed by the proxy")
        
        if not plan_exists:
            logger.info("2. Fix the plan ID format or how plans are stored in the backend")
            logger.info("   - The backend might be using a different format for plan IDs")
        
        logger.info("3. Check the DO button server logs for more information")
        logger.info("   - tail -f logs/do_button/ultimate_do_button_server.log")
        
        logger.info("4. Check the proxy logs for more information")
        logger.info("   - tail -f logs/do_button_fix/connection_fix.log")

if __name__ == "__main__":
    asyncio.run(main())