#!/usr/bin/env python3
"""
Test script for the comprehensive DO button examination system
This script sets up the WebSocket server and launches the exam framework
"""
import asyncio
import websockets
import json
import time
import logging
import os
import sys
import webbrowser
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback

# Configure logging
os.makedirs('logs/exams', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/exams/do_button_exam.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('do_button_exam')

# Track all test results
test_results = []
active_sessions = {}

# Available plans - would normally be loaded from a database or API
exam_plans = {
    'exam1': {
        'steps': [
            {
                'type': 'click',
                'target': 'target1',
                'description': 'Click on the button'
            }
        ]
    },
    'exam2': {
        'steps': [
            {
                'type': 'text',
                'target': 'input1',
                'text': 'Hello world',
                'description': 'Type "Hello world" in the input field'
            }
        ]
    },
    'exam3': {
        'steps': [
            {
                'type': 'text',
                'target': 'name',
                'text': 'John Doe',
                'description': 'Type "John Doe" in the name field'
            },
            {
                'type': 'text',
                'target': 'email',
                'text': 'john@example.com',
                'description': 'Type "john@example.com" in the email field'
            },
            {
                'type': 'click',
                'target': 'register',
                'description': 'Click the Register button'
            }
        ]
    },
    'exam4': {
        'steps': [
            {
                'type': 'click',
                'target': 'btn3',
                'description': 'Click on Button 3'
            }
        ]
    },
    'exam5': {
        'steps': [
            {
                'type': 'text',
                'target': 'firstName',
                'text': 'Jane',
                'description': 'Type "Jane" in First Name field'
            },
            {
                'type': 'text',
                'target': 'lastName',
                'text': 'Smith',
                'description': 'Type "Smith" in Last Name field'
            },
            {
                'type': 'text',
                'target': 'email',
                'text': 'jane.smith@example.com',
                'description': 'Type "jane.smith@example.com" in Email field'
            },
            {
                'type': 'click',
                'target': 'country',
                'description': 'Click on Country dropdown'
            },
            {
                'type': 'click',
                'target': 'subscribe',
                'description': 'Click Subscribe checkbox'
            },
            {
                'type': 'click',
                'target': 'submitForm',
                'description': 'Click Submit Form button'
            }
        ]
    },
    'exam6': {
        'steps': [
            {
                'type': 'click',
                'target': 'rightBtn',
                'description': 'Click the button on the right side'
            }
        ]
    },
    'exam7': {
        'steps': [
            {
                'type': 'click',
                'target': 'add2',
                'description': 'Click Add to Cart for the Wireless Keyboard'
            }
        ]
    },
    'exam8': {
        'steps': [
            {
                'type': 'click',
                'target': 'showOptions',
                'description': 'Click the Show Options button'
            },
            {
                'type': 'click',
                'target': 'option3',
                'description': 'Click on Option 3'
            }
        ]
    },
    'exam9': {
        'steps': [
            {
                'type': 'click',
                'target': 'startDemo',
                'description': 'Click the START DEMO button'
            }
        ]
    },
    'exam10': {
        'steps': [
            {
                'type': 'click',
                'target': 'next1',
                'description': 'Click Next Step button in Step 1'
            },
            {
                'type': 'text',
                'target': 'address',
                'text': '123 Main St',
                'description': 'Enter shipping address'
            },
            {
                'type': 'text',
                'target': 'city',
                'text': 'New York',
                'description': 'Enter city'
            },
            {
                'type': 'click',
                'target': 'next2',
                'description': 'Click Next Step button in Step 2'
            },
            {
                'type': 'text',
                'target': 'cardNumber',
                'text': '4111111111111111',
                'description': 'Enter credit card number'
            },
            {
                'type': 'click',
                'target': 'placeOrder',
                'description': 'Click Place Order button'
            }
        ]
    }
}

async def handle_agent_request(data, websocket):
    """Handle incoming agent mode request"""
    session_id = data.get('session_id', f"session_{int(time.time())}")
    message = data.get('message', '')
    exam_id = data.get('exam_id', 'unknown')
    
    logger.info(f"Received agent request for session {session_id}: {message}")
    
    # Store session for later use
    active_sessions[session_id] = {
        'exam_id': exam_id,
        'last_message': message,
        'timestamp': time.time()
    }
    
    # Send progress update
    await websocket.send(json.dumps({
        "type": "agent_progress",
        "session_id": session_id,
        "step": 1,
        "progress": 30,
        "message": "Analyzing message and generating plan..."
    }))
    
    # Simulate some processing time
    await asyncio.sleep(1)
    
    # Try to find a matching plan based on exam_id
    plan = exam_plans.get(exam_id, None)
    
    if plan:
        # Send progress update
        await websocket.send(json.dumps({
            "type": "agent_progress",
            "session_id": session_id,
            "step": 2,
            "progress": 60,
            "message": "Plan generated and ready for execution"
        }))
        
        # Send plan to client
        await websocket.send(json.dumps({
            "type": "plan_created",
            "session_id": session_id,
            "plan": plan
        }))
        
        # Store plan in session
        active_sessions[session_id]['plan'] = plan
        logger.info(f"Generated plan for {session_id}: {plan}")
    else:
        # Send error message
        await websocket.send(json.dumps({
            "type": "error",
            "session_id": session_id,
            "error": f"No plan available for exam: {exam_id}"
        }))
        logger.error(f"No plan available for exam: {exam_id}")

async def handle_button_action(data, websocket):
    """Handle button_action messages (EXECUTE_PLAN)"""
    plan_id = data.get('plan_id', '')
    session_id = data.get('session_id', plan_id)
    action = data.get('action', '').upper()
    
    logger.info(f"Received button action: {action} for plan {plan_id}")
    
    if action == 'EXECUTE_PLAN' or action == 'DO':
        # Send progress updates
        await websocket.send(json.dumps({
            "type": "agent_progress",
            "session_id": session_id,
            "step": 1,
            "progress": 33,
            "message": "Starting execution..."
        }))
        
        # Get plan from active sessions
        session = active_sessions.get(session_id, None)
        if session and 'plan' in session:
            plan = session['plan']
            steps = plan.get('steps', [])
            
            # Send progress for each step with delay
            for i, step in enumerate(steps):
                await asyncio.sleep(0.5)  # Delay between steps
                
                progress = 33 + int(((i + 1) / len(steps)) * 67)
                await websocket.send(json.dumps({
                    "type": "agent_progress",
                    "session_id": session_id,
                    "step": i + 2,
                    "progress": progress,
                    "message": f"Executing: {step.get('description', f'Step {i+1}')}"
                }))
            
            # Final success message
            await asyncio.sleep(1)
            await websocket.send(json.dumps({
                "type": "agent_execution_success",
                "session_id": session_id,
                "result": {
                    "success": True,
                    "steps_executed": len(steps),
                    "execution_time": len(steps) * 0.5
                },
                "summary": f"Successfully executed {len(steps)} steps",
                "execution_completed": True
            }))
            
            # Add to test results
            test_results.append({
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "exam_id": session.get('exam_id', 'unknown'),
                "message": session.get('last_message', ''),
                "plan": plan,
                "success": True
            })
            
            logger.info(f"Execution completed for session {session_id}")
        else:
            # No plan found
            await websocket.send(json.dumps({
                "type": "agent_execution_error",
                "session_id": session_id,
                "error": f"No plan found for session {session_id}"
            }))
            logger.error(f"No plan found for session {session_id}")

async def handle_agent_confirmation(data, websocket):
    """Handle agent_confirmation messages (DO/DISMISS)"""
    session_id = data.get('session_id', '')
    action = data.get('action', '').upper()
    
    logger.info(f"Received agent confirmation: {action} for session {session_id}")
    
    if action == 'DO':
        # Redirect to button_action handler
        await handle_button_action({
            "type": "button_action",
            "action": "EXECUTE_PLAN",
            "plan_id": session_id,
            "session_id": session_id
        }, websocket)
    elif action == 'DISMISS':
        # Send dismissal message
        await websocket.send(json.dumps({
            "type": "agent_dismissed",
            "session_id": session_id,
            "message": "Plan dismissed by user"
        }))
        
        logger.info(f"Plan dismissed for session {session_id}")

async def websocket_handler(websocket, path):
    """Handle WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    
    logger.info(f"Client {client_id} connected from {client_ip}")
    
    # Send welcome message
    await websocket.send(json.dumps({
        "type": "welcome",
        "message": "Connected to DO Button Exam Server",
        "server_time": datetime.now().isoformat()
    }))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type', '').lower()
                
                logger.debug(f"Received message from {client_id}: {msg_type}")
                
                # Route message based on type
                if msg_type == 'agent_request':
                    await handle_agent_request(data, websocket)
                elif msg_type == 'button_action':
                    await handle_button_action(data, websocket)
                elif msg_type == 'agent_confirmation':
                    await handle_agent_confirmation(data, websocket)
                elif msg_type == 'do_button':
                    # Treat do_button same as agent_confirmation with DO action
                    data['action'] = 'DO'
                    await handle_agent_confirmation(data, websocket)
                else:
                    # Generic acknowledgment
                    await websocket.send(json.dumps({
                        "type": "response",
                        "message": f"Received {msg_type} message"
                    }))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                logger.error(traceback.format_exc())
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Server error: {str(e)}"
                }))
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for {client_id}")
    except Exception as e:
        logger.error(f"Unexpected error for {client_id}: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info(f"Client {client_id} disconnected")

async def cleanup_sessions():
    """Periodically clean up expired sessions"""
    while True:
        try:
            now = time.time()
            expired = []
            
            # Find expired sessions (older than 30 minutes)
            for session_id, session in active_sessions.items():
                if now - session.get('timestamp', 0) > 1800:  # 30 minutes
                    expired.append(session_id)
            
            # Remove expired sessions
            for session_id in expired:
                del active_sessions[session_id]
                logger.info(f"Removed expired session: {session_id}")
            
            # Save test results periodically
            save_test_results()
            
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(600)  # On error, wait 10 minutes

def save_test_results():
    """Save test results to a file"""
    try:
        if test_results:
            os.makedirs('logs/exams/results', exist_ok=True)
            
            # Create a timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/exams/results/exam_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "results_count": len(test_results),
                    "results": test_results
                }, f, indent=2)
            
            logger.info(f"Saved {len(test_results)} test results to {filename}")
    except Exception as e:
        logger.error(f"Error saving test results: {e}")

async def main():
    parser = argparse.ArgumentParser(description='DO Button Exam Server')
    parser.add_argument('--port', type=int, default=8765, help='WebSocket server port (default: 8765)')
    parser.add_argument('--host', type=str, default='localhost', help='WebSocket server host (default: localhost)')
    parser.add_argument('--open-browser', action='store_true', help='Open exam page in browser')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Start WebSocket server
    logger.info(f"Starting WebSocket server on {args.host}:{args.port}")
    
    try:
        # Start cleanup task
        cleanup_task = asyncio.create_task(cleanup_sessions())
        
        # Start WebSocket server
        server = await websockets.serve(
            websocket_handler,
            args.host,
            args.port,
            ping_interval=30,
            ping_timeout=60,
            close_timeout=30
        )
        
        # Open browser if requested
        if args.open_browser:
            # Get the current directory
            current_dir = os.path.abspath(os.path.dirname(__file__))
            
            # Construct the path to the HTML file
            html_path = os.path.join(current_dir, "agent_do_button_exam.html")
            
            # Convert to URL format
            url = f"file://{html_path}"
            
            logger.info(f"Opening exam page in browser: {url}")
            webbrowser.open(url)
        
        logger.info(f"DO Button Exam Server running at ws://{args.host}:{args.port}")
        logger.info("Press Ctrl+C to stop the server")
        
        # Keep the server running
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Save final results
        save_test_results()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())