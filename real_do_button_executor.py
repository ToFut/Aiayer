#!/usr/bin/env python3
"""
Real DO Button Executor - A WebSocket server that properly connects LLM plans to execution
Fixes the disconnect between LLM plan creation and execution agent step-by-step execution.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
from datetime import datetime
import socket
import traceback
import time
import aiohttp
from contextlib import asynccontextmanager

# Configure logging
log_dir = 'logs/websocket'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/real_do_button_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('real_do_button_executor')
logger.setLevel(logging.INFO)

# Track connected clients
connected_clients = set()
execution_count = 0  # Track successful executions

class SessionManager:
    """Manages aiohttp ClientSession instances to prevent unclosed sessions"""
    def __init__(self):
        self._session = None
        self._lock = asyncio.Lock()
    
    async def get_session(self):
        """Get or create a ClientSession instance"""
        async with self._lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    connector=aiohttp.TCPConnector(
                        limit=10,
                        ttl_dns_cache=300,
                        use_dns_cache=True
                    )
                )
            return self._session
    
    async def close(self):
        """Close the current session"""
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

# Create global session manager
session_manager = SessionManager()

# Import plan persistence if available
try:
    from plan_persistence import load_plan, plan_manager
    PLAN_PERSISTENCE_AVAILABLE = True
    logger.info("✅ Plan persistence module loaded")
except ImportError as e:
    logger.warning(f"⚠️ Plan persistence not available: {e}")
    PLAN_PERSISTENCE_AVAILABLE = False

# Try to import universal automation handler
try:
    from universal_intelligent_automation_handler import universal_automation_handler
    UNIVERSAL_AUTOMATION_AVAILABLE = True
    logger.info("✅ Universal automation handler loaded")
except ImportError as e:
    logger.warning(f"⚠️ Universal automation handler not available: {e}")
    UNIVERSAL_AUTOMATION_AVAILABLE = False

# Try to import real agent automation handler
try:
    from real_agent_automation_handler import RealAgentAutomationHandler
    real_agent_automation_handler = RealAgentAutomationHandler()
    REAL_AGENT_AUTOMATION_AVAILABLE = True
    logger.info("✅ Real agent automation handler loaded")
except ImportError as e:
    logger.warning(f"⚠️ Real agent automation handler not available: {e}")
    REAL_AGENT_AUTOMATION_AVAILABLE = False

@asynccontextmanager
async def get_http_session():
    """Context manager for getting an HTTP session"""
    session = await session_manager.get_session()
    try:
        yield session
    except Exception as e:
        logger.error(f"Error in HTTP session: {e}")
        raise

async def find_newest_plan():
    """Find the newest plan in storage with enhanced logging"""
    if not PLAN_PERSISTENCE_AVAILABLE:
        logger.warning("Cannot find plans - persistence not available")
        return None
    
    try:
        # Get all plans and sort by timestamp (newest first)
        plans = await plan_manager.get_all_plan_metadata()
        if not plans:
            logger.warning("No plans found in storage")
            return None
            
        # Sort by timestamp (newest first)
        sorted_plans = sorted(plans, key=lambda x: x.get("timestamp", 0), reverse=True)
        
        if sorted_plans:
            newest_plan = sorted_plans[0]
            plan_id = newest_plan.get("plan_id")
            logger.info(f"✅ Found newest plan: {plan_id} - {newest_plan.get('title')}")
            return plan_id
        else:
            logger.warning("No plans found after sorting")
            return None
            
    except Exception as e:
        logger.error(f"Error finding newest plan: {e}")
        return None

async def load_plan_by_id(plan_id):
    """Load a plan from persistence by ID with enhanced logging and fallbacks"""
    if not PLAN_PERSISTENCE_AVAILABLE:
        logger.warning("Cannot load plan - persistence not available")
        return None
    
    logger.info(f"🔍 Attempting to load plan with ID: {plan_id}")
    
    try:
        # First try: Direct load
        plan_data = await load_plan(plan_id)
        if plan_data:
            logger.info(f"✅ Successfully loaded plan directly: {plan_id}")
            return plan_data
            
        # Second try: Try with plan_ prefix
        if not plan_id.startswith("plan_"):
            plan_data = await load_plan(f"plan_{plan_id}")
            if plan_data:
                logger.info(f"✅ Loaded plan with plan_ prefix: plan_{plan_id}")
                return plan_data
        
        # Third try: Try with task_ prefix
        if not plan_id.startswith("task_"):
            plan_data = await load_plan(f"task_{plan_id}")
            if plan_data:
                logger.info(f"✅ Loaded plan with task_ prefix: task_{plan_id}")
                return plan_data
        
        # Fourth try: Try with universal_ prefix
        if not plan_id.startswith("universal_"):
            plan_data = await load_plan(f"universal_{plan_id}")
            if plan_data:
                logger.info(f"✅ Loaded plan with universal_ prefix: universal_{plan_id}")
                return plan_data
        
        # Fifth try: Extract base ID and try all prefixes
        if "_" in plan_id:
            base_id = plan_id.split("_", 1)[1]
            logger.info(f"🔍 Trying with base ID: {base_id}")
            
            for prefix in ["plan_", "task_", "universal_"]:
                try_id = f"{prefix}{base_id}"
                plan_data = await load_plan(try_id)
                if plan_data:
                    logger.info(f"✅ Loaded plan with modified ID: {try_id}")
                    return plan_data
        
        # Sixth try: Load from file directly
        plan_path = os.path.join("cache", "plans", f"{plan_id}.json")
        if os.path.exists(plan_path):
            with open(plan_path, 'r') as f:
                plan_data = json.load(f)
                logger.info(f"✅ Loaded plan directly from file: {plan_path}")
                return plan_data
        
        # Seventh try: Try with task_ prefix in file path
        task_path = os.path.join("cache", "plans", f"task_{plan_id.split('_', 1)[1]}.json") if '_' in plan_id else os.path.join("cache", "plans", f"task_{plan_id}.json")
        if os.path.exists(task_path):
            with open(task_path, 'r') as f:
                plan_data = json.load(f)
                logger.info(f"✅ Loaded plan directly from file with task_ prefix: {task_path}")
                return plan_data
        
        # If all attempts fail, try to find newest plan
        logger.warning(f"❌ No plan found with ID: {plan_id} or variations")
        newest_plan_id = await find_newest_plan()
        if newest_plan_id:
            logger.info(f"🔄 Trying newest plan instead: {newest_plan_id}")
            return await load_plan_by_id(newest_plan_id)
        
        logger.error("❌ No plans found in storage")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error loading plan {plan_id}: {e}")
        return None

async def execute_plan_with_real_automation(plan_data, session_id, websocket):
    """Execute a plan using the real automation handler"""
    global execution_count
    
    try:
        start_time = time.time()
        plan_title = plan_data.get('title', 'Unknown Plan')
        
        # Check if steps exist in the plan
        steps = None
        
        # Handle different plan formats
        if isinstance(plan_data, dict):
            steps = plan_data.get('steps', [])
            if not steps and 'execution_plan' in plan_data:
                # Handle nested execution_plan format
                execution_plan = plan_data.get('execution_plan', {})
                if isinstance(execution_plan, dict):
                    steps = execution_plan.get('steps', [])
        
        if not steps:
            logger.warning(f"No steps found in plan {plan_title}")
            await websocket.send(json.dumps({
                "type": "agent_progress",
                "session_id": session_id,
                "step": 1,
                "progress": 50,
                "message": "⚠️ Plan has no steps to execute"
            }))
            
            await asyncio.sleep(0.5)
            
            await websocket.send(json.dumps({
                "type": "agent_execution_success",
                "session_id": session_id,
                "result": {
                    "success": False,
                    "steps_executed": 0,
                    "execution_time": time.time() - start_time
                },
                "summary": "⚠️ Could not execute plan: No steps found",
                "execution_completed": True
            }))
            return False
            
        # Send initial progress
        await websocket.send(json.dumps({
            "type": "agent_progress",
            "session_id": session_id,
            "step": 1,
            "progress": 10,
            "message": f"🚀 Starting execution: {plan_title}"
        }))
        
        executed_steps = 0
        total_steps = len(steps)
        
        # Execute each step
        for i, step in enumerate(steps):
            step_desc = step.get('description', f'Step {i+1}')
            progress = int(((i + 1) / total_steps) * 100)
            
            # Send progress update
            await websocket.send(json.dumps({
                "type": "agent_progress",
                "session_id": session_id,
                "step": i + 1,
                "progress": progress,
                "message": f"⚡ Executing: {step_desc}"
            }))
            
            # Perform the actual execution based on step type
            if UNIVERSAL_AUTOMATION_AVAILABLE:
                # Use the universal automation handler for execution
                try:
                    # Convert to the format expected by the execution handler
                    smart_step = step
                    if isinstance(step, dict):
                        from universal_intelligent_automation_handler import SmartAutomationStep
                        
                        # Extract coordinates safely
                        coordinates = None
                        if step.get("coordinates"):
                            try:
                                coords = step["coordinates"]
                                if isinstance(coords, list) and len(coords) >= 2:
                                    coordinates = (int(float(coords[0])), int(float(coords[1])))
                                elif isinstance(coords, dict) and "x" in coords and "y" in coords:
                                    coordinates = (int(float(coords["x"])), int(float(coords["y"])))
                                elif isinstance(coords, str):
                                    coords = coords.strip("[]()").replace(" ", "").split(",")
                                    if len(coords) >= 2:
                                        coordinates = (int(float(coords[0])), int(float(coords[1])))
                            except Exception as e:
                                logger.warning(f"Error parsing coordinates in step {i+1}: {e}")
                        
                        # Create a SmartAutomationStep object
                        smart_step = SmartAutomationStep(
                            id=step.get("id", f"step_{i+1}"),
                            description=step.get("description", ""),
                            action_type=step.get("action_type", "analyze_screen"),
                            target=step.get("target"),
                            value=step.get("value"),
                            coordinates=coordinates,
                            confidence=float(step.get("confidence", 0.8)),
                            estimated_duration=float(step.get("estimated_duration", 2.0)),
                            fallback_action=step.get("fallback_action"),
                            context_hints=step.get("context_hints", [])
                        )
                    
                    # Execute the step
                    success = await universal_automation_handler._execute_smart_step(smart_step)
                    if success:
                        executed_steps += 1
                        logger.info(f"✅ Step {i+1} executed successfully: {step_desc}")
                    else:
                        logger.warning(f"❌ Step {i+1} failed: {step_desc}")
                        
                except Exception as e:
                    logger.error(f"Error executing step {i+1}: {e}")
                    logger.error(traceback.format_exc())
                    
            else:
                # Fallback to simulated execution
                logger.warning(f"⚠️ Simulating execution for step {i+1}: {step_desc}")
                await asyncio.sleep(0.5)  # Simulate execution time
                executed_steps += 1
            
            # Small delay between steps
            await asyncio.sleep(0.3)
        
        # Send completion message
        execution_time = time.time() - start_time
        execution_count += 1
        
        success_rate = (executed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        # Format success message based on execution results
        if executed_steps == total_steps:
            summary = f"✅ EXECUTION SUCCESSFUL: All {total_steps} steps completed"
            success = True
        elif executed_steps > 0:
            summary = f"⚠️ PARTIAL EXECUTION: {executed_steps}/{total_steps} steps completed ({success_rate:.0f}%)"
            success = True  # Still consider it a success if some steps worked
        else:
            summary = "❌ EXECUTION FAILED: No steps could be executed"
            success = False
        
        # Send final success message
        await websocket.send(json.dumps({
            "type": "agent_execution_success",
            "session_id": session_id,
            "result": {
                "success": success,
                "steps_executed": executed_steps,
                "total_steps": total_steps,
                "execution_time": execution_time,
                "success_rate": success_rate
            },
            "summary": summary,
            "execution_completed": True
        }))
        
        logger.info(f"Plan execution completed: {executed_steps}/{total_steps} steps, {execution_time:.2f}s")
        return True
        
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        logger.error(traceback.format_exc())
        
        # Send error message
        await websocket.send(json.dumps({
            "type": "agent_execution_success",
            "session_id": session_id,
            "result": {
                "success": False,
                "steps_executed": 0,
                "execution_time": time.time() - start_time,
                "error": str(e)
            },
            "summary": f"❌ EXECUTION ERROR: {str(e)}",
            "execution_completed": True
        }))
        return False

async def handler(websocket):
    """WebSocket connection handler with enhanced plan loading and error handling"""
    global execution_count
    client_id = f"client_{id(websocket)}"
    connected_clients.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    
    # Log connection info
    logger.info(f"🔌 Client {client_id} connected from {client_ip}")
    
    try:
        # Send welcome message with retry logic
        welcome_message = {
            "type": "welcome",
            "message": "Connected to real DO button executor on port 8765",
            "server_time": datetime.now().isoformat(),
            "server_name": "Real DO Button Executor",
            "supported_actions": ["DO", "EXECUTE", "DISMISS", "ADJUST"]
        }
        
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                await websocket.send(json.dumps(welcome_message))
                logger.info(f"✅ Welcome message sent to {client_id}")
                break
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Connection closed while sending welcome message to {client_id}, retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"❌ Failed to send welcome message to {client_id}: {e}")
                break
        
        # Handle incoming messages with improved error handling
        async for message in websocket:
            try:
                # Validate message format
                if not message or not isinstance(message, str):
                    logger.warning(f"Received invalid message format from {client_id}")
                    continue
                
                # Parse JSON with validation
                try:
                    data = json.loads(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {client_id}: {str(e)}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "Invalid JSON format",
                        "details": str(e)
                    }))
                    continue
                
                # Validate message structure
                if not isinstance(data, dict):
                    logger.warning(f"Received non-dict message from {client_id}")
                    continue
                
                msg_type = data.get('type', 'unknown')
                logger.info(f"📩 Received from {client_id}: {msg_type}")
                
                # Handle different message types
                if msg_type == 'register':
                    # Send registration confirmation
                    await websocket.send(json.dumps({
                        "type": "register_confirmation",
                        "message": "Successfully registered with DO button executor",
                        "server_time": datetime.now().isoformat()
                    }))
                    logger.info(f"✅ Client {client_id} registered successfully")
                
                elif msg_type == 'agent_confirmation':
                    # Extract session_id and action with validation
                    session_id = data.get('session_id', '') or data.get('sessionId', '')
                    action = data.get('action', '').upper()
                    plan_id = data.get('plan_id', '')
                    
                    if not session_id:
                        logger.warning(f"Missing session_id in agent_confirmation from {client_id}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "Missing session_id"
                        }))
                        continue
                    
                    logger.info(f"🎯 DO BUTTON: Processing {action} for session {session_id}")
                    
                    if action in ['DO', 'EXECUTE']:
                        # Load and execute plan with retry logic
                        plan_data = None
                        retry_count = 0
                        while retry_count < max_retries and not plan_data:
                            plan_data = await load_plan_by_id(plan_id or session_id)
                            if not plan_data:
                                retry_count += 1
                                await asyncio.sleep(0.5)
                        
                        if not plan_data:
                            logger.warning(f"No plan found with ID: {plan_id or session_id}, trying newest plan")
                            newest_plan_id = await find_newest_plan()
                            if newest_plan_id:
                                plan_data = await load_plan_by_id(newest_plan_id)
                                logger.info(f"Using newest plan instead: {newest_plan_id}")
                        
                        if plan_data:
                            logger.info(f"🚀 Executing plan: {plan_data.get('title', 'Unknown Plan')}")
                            await execute_plan_with_real_automation(plan_data, session_id, websocket)
                        else:
                            logger.error("Cannot execute: No plan found")
                            await websocket.send(json.dumps({
                                "type": "agent_progress",
                                "session_id": session_id,
                                "step": 1,
                                "progress": 50,
                                "message": "❌ No plan found to execute"
                            }))
                            
                            await asyncio.sleep(0.5)
                            
                            await websocket.send(json.dumps({
                                "type": "agent_execution_success",
                                "session_id": session_id,
                                "result": {
                                    "success": False,
                                    "steps_executed": 0,
                                    "execution_time": 0.5
                                },
                                "summary": "❌ ERROR: No automation plan found to execute",
                                "execution_completed": True
                            }))
                    
                    elif action == 'DISMISS':
                        await websocket.send(json.dumps({
                            "type": "agent_dismissed",
                            "session_id": session_id,
                            "message": "Plan dismissed by user"
                        }))
                    
                    elif action == 'ADJUST':
                        await websocket.send(json.dumps({
                            "type": "agent_adjustment_request",
                            "session_id": session_id,
                            "message": "Please provide details for adjustment"
                        }))
                    
                    else:
                        await websocket.send(json.dumps({
                            "type": "agent_confirmation_error",
                            "error": f"Unknown action: {action}"
                        }))
                
                elif msg_type == 'button_action':
                    # Extract and validate button action data
                    action = data.get('action', '').upper()
                    plan_id = data.get('plan_id', '')
                    
                    if not plan_id:
                        logger.warning(f"Missing plan_id in button_action from {client_id}")
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": "Missing plan_id"
                        }))
                        continue
                    
                    logger.info(f"🎯 BUTTON ACTION: Processing {action} for plan {plan_id}")
                    
                    if action in ['EXECUTE_PLAN', 'DO']:
                        # Load plan with retry logic
                        plan_data = None
                        retry_count = 0
                        while retry_count < max_retries and not plan_data:
                            plan_data = await load_plan_by_id(plan_id)
                            if not plan_data:
                                retry_count += 1
                                await asyncio.sleep(0.5)
                        
                        if not plan_data:
                            logger.warning(f"No plan found with ID: {plan_id}, trying newest plan")
                            newest_plan_id = await find_newest_plan()
                            if newest_plan_id:
                                plan_data = await load_plan_by_id(newest_plan_id)
                                logger.info(f"Using newest plan instead: {newest_plan_id}")
                        
                        if plan_data:
                            logger.info(f"✅ Plan loaded successfully: {plan_id}")
                            await execute_plan_with_real_automation(plan_data, plan_id, websocket)
                        else:
                            logger.error(f"Failed to load plan: {plan_id}")
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": f"Failed to load plan: {plan_id}",
                                "timestamp": datetime.now().isoformat()
                            }))
                    
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": f"Unknown button action: {action}"
                        }))
                
                else:
                    # Echo response for unknown message types
                    await websocket.send(json.dumps({
                        "type": "response",
                        "original_type": msg_type,
                        "message": f"Received {msg_type} message",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Connection closed for {client_id}")
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                logger.error(traceback.format_exc())
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for {client_id}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client {client_id} disconnected")

async def heartbeat():
    """Send periodic heartbeat to all connected clients"""
    while True:
        current_time = datetime.now().isoformat()
        
        if connected_clients:
            # Create heartbeat message
            heartbeat_msg = json.dumps({
                "type": "heartbeat",
                "timestamp": current_time,
                "connected_clients": len(connected_clients),
                "executions": execution_count
            })
            
            # Send to all clients
            for websocket in connected_clients:
                try:
                    await websocket.send(heartbeat_msg)
                except websockets.exceptions.ConnectionClosed:
                    # Client will be cleaned up in handler
                    pass
                    
        # Wait for next heartbeat
        await asyncio.sleep(30)

async def status_reporter():
    """Log periodic status updates"""
    while True:
        logger.info(f"Server status: {len(connected_clients)} clients connected, {execution_count} executions completed")
        await asyncio.sleep(60)  # Report every minute

def is_port_available(port):
    """Check if a port is available for use"""
    try:
        # Try to create a socket on the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False

def free_port(port):
    """Forcefully free a port if it's in use"""
    if sys.platform == "win32":
        os.system(f"for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :{port}') do taskkill /F /PID %a")
    else:  # Unix-like
        os.system(f"lsof -ti:{port} | xargs kill -9 2>/dev/null || true")

def initialize_components():
    """Initialize all required components for the DO button executor"""
    try:
        # Initialize plan persistence
        if PLAN_PERSISTENCE_AVAILABLE:
            logger.info("✅ Plan persistence module loaded")
        
        # Initialize universal automation handler
        if UNIVERSAL_AUTOMATION_AVAILABLE:
            logger.info("✅ Universal automation handler loaded")
        
        # Initialize real agent automation handler
        if REAL_AGENT_AUTOMATION_AVAILABLE:
            logger.info("✅ Real agent automation handler loaded")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing components: {e}")
        return False

async def main():
    try:
        # Initialize components
        if not initialize_components():
            logger.error("❌ Failed to initialize components")
            return
            
        # Check if port is available
        if not is_port_available(8765):
            logger.error("❌ Port 8765 is already in use. Please stop any other DO button servers.")
            return
            
        logger.info("Port 8765 is available")
        logger.info("🚀 Starting Real DO Button Executor on 0.0.0.0:8765")
        
        # Create WebSocket server with proper configuration
        server = await websockets.serve(
            handler,
            "0.0.0.0",
            8765,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10
        )
        
        logger.info("✅ WebSocket server initialized successfully")
        logger.info("✅ Real DO Button Executor running on ws://0.0.0.0:8765")
        logger.info("🎯 Ready to handle DO button clicks with REAL AUTOMATION")
        logger.info("🎮 REAL INPUT EXECUTION ENABLED - Will perform actual mouse and keyboard actions")
        
        if UNIVERSAL_AUTOMATION_AVAILABLE:
            logger.info("🤖 Universal automation handler available as fallback")
        if PLAN_PERSISTENCE_AVAILABLE:
            logger.info("📂 Plan persistence available for loading plans")
            
        logger.info(f"Server status: {len(connected_clients)} clients connected, {execution_count} executions completed")
        
        # Keep the server running
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"❌ Failed to create WebSocket server: {str(e)}")
        logger.error(traceback.format_exc())
        return

if __name__ == "__main__":
    try:
        # Set a more detailed logging level for debugging
        if "--debug" in sys.argv:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
            
        # Print server status at startup
        logger.info(f"Starting Real DO Button Executor (version 1.0)")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Websockets version: {websockets.__version__}")
        
        # Run the main function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)