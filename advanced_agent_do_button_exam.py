#!/usr/bin/env python3
"""
Advanced test script for the comprehensive DO button examination system
This script extends the existing exam framework with more realistic scenarios
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
import random
import threading
import signal

# Configure logging
os.makedirs('logs/exams', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/exams/advanced_do_button_exam.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('advanced_do_button_exam')

# Track all test results
test_results = []
active_sessions = {}
exam_stats = {}

# Default screenshots directory
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Advanced exam definitions
advanced_exams = {
    'browser_search': {
        'title': 'Web Browser Search',
        'difficulty': 'medium',
        'description': 'Test the agent\'s ability to use a search engine interface',
        'instructions': 'Ask the agent to search for "artificial intelligence news" in the search bar and click the search button.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'browser_search.png'),
        'expected_actions': [
            {
                'type': 'text',
                'target': 'search_box',
                'text': 'artificial intelligence news',
                'description': 'Type "artificial intelligence news" in the search box'
            },
            {
                'type': 'click',
                'target': 'search_button',
                'description': 'Click the search button'
            }
        ]
    },
    'email_compose': {
        'title': 'Email Composition',
        'difficulty': 'hard',
        'description': 'Test the agent\'s ability to compose an email with multiple fields',
        'instructions': 'Ask the agent to compose an email to contact@example.com with the subject "Meeting Request" and message body "Can we schedule a meeting for next week? Thanks!"',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'email_compose.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'compose_button',
                'description': 'Click the compose button'
            },
            {
                'type': 'text',
                'target': 'to_field',
                'text': 'contact@example.com',
                'description': 'Enter recipient email'
            },
            {
                'type': 'text',
                'target': 'subject_field',
                'text': 'Meeting Request',
                'description': 'Enter email subject'
            },
            {
                'type': 'text',
                'target': 'body_field',
                'text': 'Can we schedule a meeting for next week? Thanks!',
                'description': 'Enter email body'
            },
            {
                'type': 'click',
                'target': 'send_button',
                'description': 'Click the send button'
            }
        ]
    },
    'spreadsheet_data': {
        'title': 'Spreadsheet Data Entry',
        'difficulty': 'expert',
        'description': 'Test the agent\'s ability to work with a spreadsheet interface',
        'instructions': 'Ask the agent to add sales data to the spreadsheet: Product A sold 250 units, Product B sold 175 units, and Product C sold 320 units.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'spreadsheet.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'cell_b2',
                'description': 'Click on cell B2'
            },
            {
                'type': 'text',
                'target': 'cell_b2',
                'text': '250',
                'description': 'Enter 250 for Product A'
            },
            {
                'type': 'click',
                'target': 'cell_b3',
                'description': 'Click on cell B3'
            },
            {
                'type': 'text',
                'target': 'cell_b3',
                'text': '175',
                'description': 'Enter 175 for Product B'
            },
            {
                'type': 'click',
                'target': 'cell_b4',
                'description': 'Click on cell B4'
            },
            {
                'type': 'text',
                'target': 'cell_b4',
                'text': '320',
                'description': 'Enter 320 for Product C'
            }
        ]
    },
    'calendar_event': {
        'title': 'Calendar Event Creation',
        'difficulty': 'hard',
        'description': 'Test the agent\'s ability to create a calendar event',
        'instructions': 'Ask the agent to create a new meeting event titled "Team Sync" for next Monday at 2:00 PM with a duration of 1 hour.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'calendar.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'new_event_button',
                'description': 'Click the new event button'
            },
            {
                'type': 'text',
                'target': 'event_title',
                'text': 'Team Sync',
                'description': 'Enter event title'
            },
            {
                'type': 'click',
                'target': 'date_field',
                'description': 'Click on date field'
            },
            {
                'type': 'click',
                'target': 'next_monday',
                'description': 'Select next Monday'
            },
            {
                'type': 'click',
                'target': 'time_field',
                'description': 'Click on time field'
            },
            {
                'type': 'text',
                'target': 'time_field',
                'text': '2:00 PM',
                'description': 'Enter start time'
            },
            {
                'type': 'click',
                'target': 'duration_field',
                'description': 'Click duration field'
            },
            {
                'type': 'text',
                'target': 'duration_field',
                'text': '1:00',
                'description': 'Set duration to 1 hour'
            },
            {
                'type': 'click',
                'target': 'save_button',
                'description': 'Click save button'
            }
        ]
    },
    'social_media_post': {
        'title': 'Social Media Post',
        'difficulty': 'medium',
        'description': 'Test the agent\'s ability to create and publish a social media post',
        'instructions': 'Ask the agent to create a social media post with the text "Excited to announce our new product launch next week! #innovation #technology" and publish it.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'social_media.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'post_field',
                'description': 'Click on the post composition field'
            },
            {
                'type': 'text',
                'target': 'post_field',
                'text': 'Excited to announce our new product launch next week! #innovation #technology',
                'description': 'Enter post text with hashtags'
            },
            {
                'type': 'click',
                'target': 'publish_button',
                'description': 'Click the publish button'
            }
        ]
    },
    'file_management': {
        'title': 'File Management',
        'difficulty': 'expert',
        'description': 'Test the agent\'s ability to navigate file systems and manage files',
        'instructions': 'Ask the agent to create a new folder named "Project Files", then move the document "quarterly_report.docx" into that folder.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'file_explorer.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'new_folder_button',
                'description': 'Click the new folder button'
            },
            {
                'type': 'text',
                'target': 'folder_name_field',
                'text': 'Project Files',
                'description': 'Enter the folder name'
            },
            {
                'type': 'click',
                'target': 'create_button',
                'description': 'Click the create button'
            },
            {
                'type': 'click',
                'target': 'quarterly_report_file',
                'description': 'Click on the quarterly report file'
            },
            {
                'type': 'click',
                'target': 'move_to_button',
                'description': 'Click on the move to button'
            },
            {
                'type': 'click',
                'target': 'project_files_folder',
                'description': 'Select the Project Files folder as destination'
            },
            {
                'type': 'click',
                'target': 'confirm_move_button',
                'description': 'Click the confirm move button'
            }
        ]
    },
    'code_editing': {
        'title': 'Code Editing',
        'difficulty': 'expert',
        'description': 'Test the agent\'s ability to edit code in an IDE',
        'instructions': 'Ask the agent to find the function "calculateTotal" in the code editor and add a comment explaining that it calculates the sum of prices including tax.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'code_editor.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'search_icon',
                'description': 'Click the search icon'
            },
            {
                'type': 'text',
                'target': 'search_field',
                'text': 'calculateTotal',
                'description': 'Enter "calculateTotal" in the search field'
            },
            {
                'type': 'click',
                'target': 'search_result',
                'description': 'Click on the search result'
            },
            {
                'type': 'click',
                'target': 'line_before_function',
                'description': 'Click on the line before the function declaration'
            },
            {
                'type': 'text',
                'target': 'editor',
                'text': '// This function calculates the sum of prices including tax',
                'description': 'Add the comment explaining the function'
            }
        ]
    },
    'shopping_cart': {
        'title': 'Online Shopping Cart',
        'difficulty': 'medium',
        'description': 'Test the agent\'s ability to navigate an e-commerce site and add items to cart',
        'instructions': 'Ask the agent to add the wireless headphones to the shopping cart, then proceed to checkout.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'shopping_cart.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'headphones_product',
                'description': 'Click on the wireless headphones product'
            },
            {
                'type': 'click',
                'target': 'add_to_cart_button',
                'description': 'Click the add to cart button'
            },
            {
                'type': 'click',
                'target': 'view_cart_button',
                'description': 'Click the view cart button'
            },
            {
                'type': 'click',
                'target': 'checkout_button',
                'description': 'Click the checkout button'
            }
        ]
    },
    'pdf_form': {
        'title': 'PDF Form Filling',
        'difficulty': 'hard',
        'description': 'Test the agent\'s ability to fill out a PDF form',
        'instructions': 'Ask the agent to fill out the PDF form with Name: "John Smith", Email: "john.smith@example.com", and check the "Subscribe to newsletter" box.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'pdf_form.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'name_field',
                'description': 'Click the name field'
            },
            {
                'type': 'text',
                'target': 'name_field',
                'text': 'John Smith',
                'description': 'Enter the name'
            },
            {
                'type': 'click',
                'target': 'email_field',
                'description': 'Click the email field'
            },
            {
                'type': 'text',
                'target': 'email_field',
                'text': 'john.smith@example.com',
                'description': 'Enter the email address'
            },
            {
                'type': 'click',
                'target': 'subscribe_checkbox',
                'description': 'Click the subscribe checkbox'
            },
            {
                'type': 'click',
                'target': 'save_form_button',
                'description': 'Click the save form button'
            }
        ]
    },
    'data_visualization': {
        'title': 'Data Visualization Tool',
        'difficulty': 'expert',
        'description': 'Test the agent\'s ability to work with a data visualization interface',
        'instructions': 'Ask the agent to create a bar chart showing sales data by quarter, add a title "Quarterly Sales Performance", and export it as a PNG file.',
        'screenshot': os.path.join(SCREENSHOTS_DIR, 'data_viz.png'),
        'expected_actions': [
            {
                'type': 'click',
                'target': 'chart_type_dropdown',
                'description': 'Click on the chart type dropdown'
            },
            {
                'type': 'click',
                'target': 'bar_chart_option',
                'description': 'Select bar chart option'
            },
            {
                'type': 'click',
                'target': 'data_selector',
                'description': 'Click on the data selector'
            },
            {
                'type': 'click',
                'target': 'sales_by_quarter_option',
                'description': 'Select sales by quarter dataset'
            },
            {
                'type': 'click',
                'target': 'chart_title_field',
                'description': 'Click on the chart title field'
            },
            {
                'type': 'text',
                'target': 'chart_title_field',
                'text': 'Quarterly Sales Performance',
                'description': 'Enter chart title'
            },
            {
                'type': 'click',
                'target': 'export_button',
                'description': 'Click the export button'
            },
            {
                'type': 'click',
                'target': 'png_format_option',
                'description': 'Select PNG format option'
            },
            {
                'type': 'click',
                'target': 'export_confirm_button',
                'description': 'Click the confirm export button'
            }
        ]
    }
}

# Add advanced plans to the execution map
advanced_plans = {
    exam_id: {
        'steps': exam['expected_actions']
    } for exam_id, exam in advanced_exams.items()
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
        'timestamp': time.time(),
        'start_time': time.time()
    }
    
    # Track exam stats
    if exam_id not in exam_stats:
        exam_stats[exam_id] = {
            'attempts': 0,
            'successful': 0,
            'partial': 0,
            'failed': 0,
            'avg_time': 0,
            'total_time': 0
        }
    exam_stats[exam_id]['attempts'] += 1
    
    # Send progress update
    await websocket.send(json.dumps({
        "type": "agent_progress",
        "session_id": session_id,
        "step": 1,
        "progress": 30,
        "message": "Analyzing screen and generating plan..."
    }))
    
    # Simulate some processing time based on difficulty
    exam = advanced_exams.get(exam_id)
    processing_delay = 1.0  # Default delay
    if exam:
        difficulty = exam.get('difficulty', 'medium')
        if difficulty == 'easy':
            processing_delay = 0.8
        elif difficulty == 'medium':
            processing_delay = 1.2
        elif difficulty == 'hard':
            processing_delay = 1.5
        elif difficulty == 'expert':
            processing_delay = 2.0
    
    await asyncio.sleep(processing_delay)
    
    # Try to find a matching plan based on exam_id
    plan = advanced_plans.get(exam_id)
    
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
    # Debug - log full data
    logger.debug(f"Button action data: {json.dumps(data, indent=2)}")
    
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
                # Add a small random delay to simulate real-world variability
                step_delay = 0.5 + random.uniform(0, 0.3)
                await asyncio.sleep(step_delay)
                
                progress = 33 + int(((i + 1) / len(steps)) * 67)
                await websocket.send(json.dumps({
                    "type": "agent_progress",
                    "session_id": session_id,
                    "step": i + 2,
                    "progress": progress,
                    "message": f"Executing: {step.get('description', f'Step {i+1}')}"
                }))
                
                # Simulate occasional failures for testing robustness
                if random.random() < 0.05:  # 5% chance of step failure
                    logger.warning(f"Simulating step failure for step {i+1} in session {session_id}")
                    await websocket.send(json.dumps({
                        "type": "agent_execution_warning",
                        "session_id": session_id,
                        "message": f"Warning: Step {i+1} encountered difficulty but will attempt to continue",
                        "step": i + 1,
                        "recovery": True
                    }))
                    # Add a recovery delay
                    await asyncio.sleep(0.8)
            
            # Calculate execution time
            execution_time = time.time() - session.get('start_time', time.time())
            session['execution_time'] = execution_time
            
            # Update exam stats
            exam_id = session.get('exam_id', 'unknown')
            if exam_id in exam_stats:
                stats = exam_stats[exam_id]
                stats['successful'] += 1
                stats['total_time'] += execution_time
                stats['avg_time'] = stats['total_time'] / stats['successful']
            
            # Final success message
            await asyncio.sleep(1)
            await websocket.send(json.dumps({
                "type": "agent_execution_success",
                "session_id": session_id,
                "result": {
                    "success": True,
                    "steps_executed": len(steps),
                    "execution_time": execution_time
                },
                "summary": f"Successfully executed {len(steps)} steps in {execution_time:.2f} seconds",
                "execution_completed": True,
                "performance_metrics": {
                    "execution_time": execution_time,
                    "avg_step_time": execution_time / len(steps) if steps else 0,
                    "accuracy": 100.0  # Would be calculated based on expected vs actual in real implementation
                }
            }))
            
            # Add to test results
            test_results.append({
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "exam_id": session.get('exam_id', 'unknown'),
                "message": session.get('last_message', ''),
                "plan": plan,
                "success": True,
                "execution_time": execution_time,
                "difficulty": advanced_exams.get(exam_id, {}).get('difficulty', 'unknown')
            })
            
            logger.info(f"Execution completed for session {session_id} in {execution_time:.2f}s")
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
        
        # Update stats
        session = active_sessions.get(session_id, None)
        if session:
            exam_id = session.get('exam_id', 'unknown')
            if exam_id in exam_stats:
                exam_stats[exam_id]['failed'] += 1
        
        logger.info(f"Plan dismissed for session {session_id}")

async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    client_id = f"client_{id(websocket)}"
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    
    logger.info(f"Client {client_id} connected from {client_ip}")
    
    # Send welcome message
    await websocket.send(json.dumps({
        "type": "welcome",
        "message": "Connected to Advanced DO Button Exam Server",
        "server_time": datetime.now().isoformat(),
        "available_exams": list(advanced_exams.keys())
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
                elif msg_type == 'get_exam_details':
                    # New message type to get detailed exam information
                    exam_id = data.get('exam_id')
                    if exam_id in advanced_exams:
                        exam_data = advanced_exams[exam_id].copy()
                        # Include stats if available
                        if exam_id in exam_stats:
                            exam_data['stats'] = exam_stats[exam_id]
                        await websocket.send(json.dumps({
                            "type": "exam_details",
                            "exam_id": exam_id,
                            "details": exam_data
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "error": f"Exam {exam_id} not found"
                        }))
                elif msg_type == 'get_all_exams':
                    # Return a list of all available exams with stats
                    exams_with_stats = {}
                    for exam_id, exam in advanced_exams.items():
                        exam_copy = exam.copy()
                        # Include stats if available
                        if exam_id in exam_stats:
                            exam_copy['stats'] = exam_stats[exam_id]
                        exams_with_stats[exam_id] = exam_copy
                    
                    await websocket.send(json.dumps({
                        "type": "all_exams",
                        "exams": exams_with_stats
                    }))
                elif msg_type == 'get_stats':
                    # Return statistics for all exams
                    await websocket.send(json.dumps({
                        "type": "exam_stats",
                        "stats": exam_stats
                    }))
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
            filename = f"logs/exams/results/advanced_exam_results_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "results_count": len(test_results),
                    "results": test_results,
                    "exam_stats": exam_stats
                }, f, indent=2)
            
            logger.info(f"Saved {len(test_results)} test results to {filename}")
    except Exception as e:
        logger.error(f"Error saving test results: {e}")

def generate_sample_screenshots():
    """Generate placeholder screenshots for testing purposes"""
    try:
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        # Create directory if it doesn't exist
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        
        # Create sample screenshots for each exam
        for exam_id, exam in advanced_exams.items():
            # Create a blank image
            img = Image.new('RGB', (800, 600), color=(240, 240, 240))
            draw = ImageDraw.Draw(img)
            
            # Try to use a font if available
            try:
                # Try to find a system font
                font_path = None
                if os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
                    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
                elif os.path.exists('/System/Library/Fonts/Helvetica.ttc'):
                    font_path = '/System/Library/Fonts/Helvetica.ttc'
                
                font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
                small_font = ImageFont.truetype(font_path, 14) if font_path else ImageFont.load_default()
            except Exception:
                # Fallback to default font
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Draw title
            draw.text((50, 30), exam.get('title', 'Sample Test'), fill=(0, 0, 0), font=font)
            
            # Draw difficulty
            difficulty = exam.get('difficulty', 'medium')
            difficulty_colors = {
                'easy': (0, 150, 0),
                'medium': (255, 165, 0),
                'hard': (255, 0, 0),
                'expert': (128, 0, 128)
            }
            draw.text((50, 70), f"Difficulty: {difficulty.capitalize()}", 
                     fill=difficulty_colors.get(difficulty, (0, 0, 0)), font=small_font)
            
            # Draw description
            description = exam.get('description', '')
            draw.text((50, 100), description, fill=(0, 0, 0), font=small_font)
            
            # Draw UI elements based on expected actions
            expected_actions = exam.get('expected_actions', [])
            
            # Map action targets to positions
            target_positions = {}
            
            # Create UI elements based on expected actions
            y_position = 150
            for i, action in enumerate(expected_actions):
                target = action.get('target', '')
                action_type = action.get('type', '')
                
                # Only add each target once
                if target not in target_positions:
                    # Calculate position (ensure elements don't overlap)
                    x_position = 50 + ((i % 3) * 250)
                    if i > 0 and i % 3 == 0:
                        y_position += 80
                    
                    # Store position
                    target_positions[target] = (x_position, y_position, x_position + 200, y_position + 40)
                    
                    # Draw element based on type
                    if action_type == 'click':
                        # Draw a button
                        draw.rectangle(target_positions[target], outline=(0, 0, 0), fill=(200, 200, 200))
                        draw.text((x_position + 10, y_position + 10), target, fill=(0, 0, 0), font=small_font)
                    elif action_type == 'text':
                        # Draw a text field
                        draw.rectangle(target_positions[target], outline=(0, 0, 0), fill=(255, 255, 255))
                        draw.text((x_position + 10, y_position + 10), target, fill=(150, 150, 150), font=small_font)
            
            # Save image
            screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{exam_id}.png")
            img.save(screenshot_path)
            logger.info(f"Generated sample screenshot for {exam_id} at {screenshot_path}")
            
            # Update exam data with the actual screenshot path
            advanced_exams[exam_id]['screenshot'] = screenshot_path
    except ImportError:
        logger.warning("PIL not available. Cannot generate sample screenshots.")
        logger.warning("Install with: pip install pillow numpy")
    except Exception as e:
        logger.error(f"Error generating sample screenshots: {e}")
        logger.error(traceback.format_exc())

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, saving results and exiting...")
        save_test_results()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    parser = argparse.ArgumentParser(description='Advanced DO Button Exam Server')
    parser.add_argument('--port', type=int, default=8766, help='WebSocket server port (default: 8766)')
    parser.add_argument('--host', type=str, default='localhost', help='WebSocket server host (default: localhost)')
    parser.add_argument('--open-browser', action='store_true', help='Open exam page in browser')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--generate-screenshots', action='store_true', help='Generate sample screenshots')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Generate sample screenshots if requested
    if args.generate_screenshots:
        generate_sample_screenshots()
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Start WebSocket server
    logger.info(f"Starting Advanced WebSocket server on {args.host}:{args.port}")
    
    try:
        # Start cleanup task
        cleanup_task = asyncio.create_task(cleanup_sessions())
        
        # Start WebSocket server with updated parameters for websockets 15.0.1
        server = await websockets.serve(
            websocket_handler,
            host=args.host,
            port=args.port,
            ping_interval=30,
            ping_timeout=60,
            close_timeout=30
        )
        
        # Open browser if requested
        if args.open_browser:
            # Get the current directory
            current_dir = os.path.abspath(os.path.dirname(__file__))
            
            # Construct the path to the HTML file
            html_path = os.path.join(current_dir, "advanced_agent_do_button_exam.html")
            
            # Check if the file exists, if not create a basic version
            if not os.path.exists(html_path):
                logger.info(f"Creating basic HTML interface at {html_path}")
                with open(html_path, 'w') as f:
                    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Agent DO Button Exam</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #2e7d32; }
        .container { max-width: 1200px; margin: 0 auto; }
        .exam-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .exam-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .exam-card h3 { margin-top: 0; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-bottom: 10px; }
        .badge-easy { background-color: #e8f5e9; color: #2e7d32; }
        .badge-medium { background-color: #fff3e0; color: #e65100; }
        .badge-hard { background-color: #ffebee; color: #c62828; }
        .badge-expert { background-color: #f3e5f5; color: #6a1b9a; }
        .connection-status { padding: 10px; margin-bottom: 20px; border-radius: 4px; }
        .connected { background-color: #e8f5e9; color: #2e7d32; }
        .disconnected { background-color: #ffebee; color: #c62828; }
        .log { height: 200px; overflow-y: auto; background-color: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Advanced Agent DO Button Exam Framework</h1>
        
        <div id="connectionStatus" class="connection-status disconnected">
            Disconnected
        </div>
        
        <div class="exam-grid" id="examGrid">
            <!-- Exams will be populated here -->
            <div class="exam-card">Loading exams...</div>
        </div>
        
        <h2>Message Log</h2>
        <div id="log" class="log"></div>
    </div>

    <script>
        const connectionStatus = document.getElementById('connectionStatus');
        const examGrid = document.getElementById('examGrid');
        const log = document.getElementById('log');
        let ws = null;
        
        // Connect to WebSocket server
        function connect() {
            connectionStatus.textContent = 'Connecting...';
            connectionStatus.className = 'connection-status';
            
            ws = new WebSocket('ws://localhost:8766');
            
            ws.onopen = function() {
                connectionStatus.textContent = 'Connected';
                connectionStatus.className = 'connection-status connected';
                addToLog('Connected to WebSocket server');
                
                // Request all exams
                ws.send(JSON.stringify({type: 'get_all_exams'}));
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addToLog(`Received: ${data.type}`);
                
                if (data.type === 'all_exams') {
                    displayExams(data.exams);
                }
            };
            
            ws.onclose = function() {
                connectionStatus.textContent = 'Disconnected';
                connectionStatus.className = 'connection-status disconnected';
                addToLog('Disconnected from WebSocket server');
                
                // Try to reconnect after 3 seconds
                setTimeout(connect, 3000);
            };
            
            ws.onerror = function(error) {
                connectionStatus.textContent = 'Connection Error';
                connectionStatus.className = 'connection-status disconnected';
                addToLog(`WebSocket error: ${error}`);
            };
        }
        
        // Display exams in the grid
        function displayExams(exams) {
            examGrid.innerHTML = '';
            
            for (const [examId, exam] of Object.entries(exams)) {
                const card = document.createElement('div');
                card.className = 'exam-card';
                
                const badge = document.createElement('div');
                badge.className = `badge badge-${exam.difficulty}`;
                badge.textContent = exam.difficulty.charAt(0).toUpperCase() + exam.difficulty.slice(1);
                
                const title = document.createElement('h3');
                title.textContent = exam.title;
                
                const description = document.createElement('p');
                description.textContent = exam.description;
                
                card.appendChild(badge);
                card.appendChild(title);
                card.appendChild(description);
                
                // Add stats if available
                if (exam.stats) {
                    const stats = document.createElement('div');
                    stats.innerHTML = `
                        <small>
                            Attempts: ${exam.stats.attempts}<br>
                            Success rate: ${exam.stats.successful > 0 ? 
                                Math.round((exam.stats.successful / exam.stats.attempts) * 100) : 0}%
                        </small>
                    `;
                    card.appendChild(stats);
                }
                
                examGrid.appendChild(card);
            }
        }
        
        // Add message to the log
        function addToLog(message) {
            const now = new Date().toLocaleTimeString();
            log.innerHTML += `[${now}] ${message}<br>`;
            log.scrollTop = log.scrollHeight;
        }
        
        // Connect when page loads
        window.addEventListener('load', connect);
    </script>
</body>
</html>""")
            
            # Convert to URL format
            url = f"file://{html_path}"
            
            logger.info(f"Opening exam page in browser: {url}")
            webbrowser.open(url)
        
        logger.info(f"Advanced DO Button Exam Server running at ws://{args.host}:{args.port}")
        logger.info("Press Ctrl+C to stop the server")
        
        # Keep the server running
        # Create a never-completing future
        stop_event = asyncio.Event()
        await stop_event.wait()
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