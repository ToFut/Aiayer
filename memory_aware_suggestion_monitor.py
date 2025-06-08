#!/usr/bin/env python3
"""
memory_aware_suggestion_monitor.py - Proactive suggestion system based on memory triggers

This script monitors the memory system for potential suggestions, and when it detects
actions that should be suggested to the user, it automatically pushes them to the
NextGen overlay in Suggest mode. If the user accepts, it will switch to Agent mode
and execute the plan.

It implements a complete pipeline:
1. Monitors conscious memory for suggestion triggers
2. Extracts actionable suggestions
3. Pushes suggestions to the NextGen overlay 
4. Handles user acceptance by switching to Agent mode with a plan
5. Executes the plan if user clicks "Do It"
"""

import json
import sys
import asyncio
import websockets
import logging
import time
import os
import re
from datetime import datetime
import signal
import threading
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/memory/suggestion_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("suggestion_monitor")

# Configuration
WS_ENDPOINT = "ws://localhost:8765"
MEMORY_PATH = Path("/Users/segevbin/Desktop/SensAI/Aiayer/memory/conscious.json")
SCAN_INTERVAL = 5  # seconds
SUGGESTION_THRESHOLD = 0.7  # Confidence threshold for pushing suggestions

# Global state
last_modified_time = 0
processed_suggestions = set()
websocket_connection = None
running = True

# Enhanced prompts for the memory system
CONSCIOUS_MEMORY_SUGGESTION_PROMPT = """
When processing conscious memory, identify actionable suggestions based on:
1. User patterns and behaviors
2. Pending tasks or deadlines
3. Productivity opportunities
4. Workflow optimizations

For each potential suggestion:
- Assign a confidence score (0.0-1.0)
- Format as: "SUGGESTION: [title] | [message] | [confidence]"
- Include specific actions the system could perform
"""

class Suggestion:
    def __init__(self, title, message, confidence=0.75, actions=None, plan=None):
        self.id = f"suggestion_{int(time.time())}_{hash(title + message) % 10000}"
        self.title = title
        self.message = message
        self.confidence = confidence
        self.timestamp = datetime.now().isoformat()
        self.actions = actions or []
        self.plan = plan or {"steps": []}
        
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "actions": self.actions,
            "plan": self.plan
        }
        
    def to_notification_payload(self):
        """Creates a properly formatted notification payload for the NextGen overlay"""
        return {
            "success": True,
            "response": f"💡 {self.title}: {self.message}",
            "mode": "SUGGEST",
            "processing_time": 0.5,
            "enterprise_validated": True,
            "notification": True,
            "play_sound": True,
            "sound_type": "notification",
            "importance": "high" if self.confidence > 0.8 else "normal",
            "buttons": [
                {
                    "id": "do_it",
                    "text": "Yes, help me",
                    "action": "accept",
                    "style": "success"
                },
                {
                    "id": "dismiss",
                    "text": "No thanks",
                    "action": "dismiss",
                    "style": "danger"
                }
            ],
            "interactive": True,
            "plan_id": self.id,
            "timestamp": time.time(),
            "suggestion_data": self.to_dict()  # Include full suggestion data for later use
        }
        
    def to_agent_mode_payload(self):
        """Creates a payload to transition to Agent mode with a plan"""
        return {
            "success": True,
            "response": f"🤖 Ready to execute: {self.title}\n\n{self.message}\n\nI'll perform the following steps:",
            "mode": "Agent",
            "processing_time": 0.3,
            "enterprise_validated": True,
            "notification": False,
            "plan_id": self.id,
            "buttons": [
                {
                    "id": "execute_plan",
                    "text": "Execute Now",
                    "action": "execute_plan",
                    "style": "success"
                },
                {
                    "id": "cancel",
                    "text": "Cancel",
                    "action": "cancel",
                    "style": "danger"
                }
            ],
            "interactive": True,
            "requires_approval": True,
            "plan": {
                "id": self.id,
                "title": self.title,
                "steps": self.plan.get("steps", []),
                "estimated_duration": self.plan.get("estimated_duration", "30 seconds"),
                "risk_level": self.plan.get("risk_level", "low")
            }
        }

async def connect_websocket():
    """Establishes and maintains a WebSocket connection"""
    global websocket_connection
    
    while running:
        try:
            # Check if connection is None or needs to be refreshed
            # Instead of checking .closed attribute, we'll implement a connection check
            connection_active = False
            if websocket_connection is not None:
                try:
                    # Try a simple ping to check if connection is still active
                    pong = await asyncio.wait_for(websocket_connection.ping(), timeout=2)
                    connection_active = True
                except:
                    # If ping fails, connection is likely closed or invalid
                    connection_active = False
                    websocket_connection = None
            
            if websocket_connection is None or not connection_active:
                logger.info(f"Connecting to WebSocket at {WS_ENDPOINT}...")
                websocket_connection = await websockets.connect(WS_ENDPOINT)
                logger.info("Connected to WebSocket server")
                
                # Start the message handler in a separate task
                asyncio.create_task(handle_incoming_messages())
                
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            websocket_connection = None
            
        # Check connection periodically
        await asyncio.sleep(10)

async def handle_incoming_messages():
    """Handles incoming WebSocket messages, particularly button actions"""
    global websocket_connection
    
    if websocket_connection is None:
        return
        
    try:
        # Make a local copy of the connection for this handler
        ws = websocket_connection
        
        # Handle messages in a loop
        while True:
            try:
                # Use wait_for to prevent indefinite blocking
                message = await asyncio.wait_for(ws.recv(), timeout=30)
                
                try:
                    data = json.loads(message)
                    logger.info(f"Received message: {data.get('type', 'unknown')}")
                    
                    # Handle button actions from suggestions
                    if data.get("type") == "button_action":
                        action = data.get("action")
                        plan_id = data.get("plan_id")
                        
                        if action == "accept" and plan_id:
                            # User accepted the suggestion, switch to Agent mode
                            await handle_suggestion_acceptance(plan_id)
                        elif action == "execute_plan" and plan_id:
                            # User confirmed execution in Agent mode
                            await handle_execution_confirmation(plan_id)
                    
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode message: {message}")
                    
            except asyncio.TimeoutError:
                # This is normal, just continue the loop
                continue
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Error receiving message: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")
    
    # If we got here, the connection is likely closed
    websocket_connection = None

async def handle_suggestion_acceptance(suggestion_id):
    """When user accepts a suggestion, transition to Agent mode with plan"""
    logger.info(f"User accepted suggestion: {suggestion_id}")
    
    # Find the original suggestion in our memory
    suggestion_file = Path(f"memory/suggestions/{suggestion_id}.json")
    if not suggestion_file.exists():
        logger.error(f"Cannot find suggestion data for ID: {suggestion_id}")
        return
        
    try:
        with open(suggestion_file, "r") as f:
            suggestion_data = json.load(f)
            
        # Create a Suggestion object from the data
        suggestion = Suggestion(
            suggestion_data["title"], 
            suggestion_data["message"],
            suggestion_data["confidence"],
            suggestion_data["actions"],
            suggestion_data["plan"]
        )
        
        # Create agent mode payload
        agent_payload = suggestion.to_agent_mode_payload()
        
        # Send to overlay
        if websocket_connection and not websocket_connection.closed:
            await websocket_connection.send(json.dumps(agent_payload))
            logger.info(f"Sent Agent mode transition for suggestion: {suggestion_id}")
        
    except Exception as e:
        logger.error(f"Error handling suggestion acceptance: {str(e)}")

async def handle_execution_confirmation(plan_id):
    """When user confirms execution in Agent mode, execute the plan"""
    logger.info(f"User confirmed execution of plan: {plan_id}")
    
    # Find the plan in our memory
    suggestion_file = Path(f"memory/suggestions/{plan_id}.json")
    if not suggestion_file.exists():
        logger.error(f"Cannot find plan data for ID: {plan_id}")
        return
        
    try:
        with open(suggestion_file, "r") as f:
            suggestion_data = json.load(f)
            
        # Execute each step in the plan
        plan = suggestion_data.get("plan", {})
        steps = plan.get("steps", [])
        
        if not steps:
            logger.warning(f"Plan {plan_id} has no steps to execute")
            return
            
        # Send execution start notification
        start_notification = {
            "type": "execution_progress",
            "progress": 0,
            "currentStep": "Starting execution...",
            "stepNumber": 0,
            "totalSteps": len(steps)
        }
        
        if websocket_connection and not websocket_connection.closed:
            await websocket_connection.send(json.dumps(start_notification))
        
        # Execute each step with progress updates
        for i, step in enumerate(steps):
            step_number = i + 1
            progress = int((step_number / len(steps)) * 100)
            
            # Update progress
            progress_update = {
                "type": "execution_progress",
                "progress": progress,
                "currentStep": step.get("description", f"Step {step_number}"),
                "stepNumber": step_number,
                "totalSteps": len(steps)
            }
            
            if websocket_connection and not websocket_connection.closed:
                await websocket_connection.send(json.dumps(progress_update))
            
            # Actually execute the step (this would call into the automation system)
            logger.info(f"Executing step {step_number}/{len(steps)}: {step.get('description', 'Unknown step')}")
            
            # Simulate execution time
            await asyncio.sleep(1)
        
        # Send completion notification
        completion_notification = {
            "type": "execution_complete",
            "result": f"Successfully completed all {len(steps)} steps for '{suggestion_data['title']}'",
            "timestamp": datetime.now().isoformat()
        }
        
        if websocket_connection and not websocket_connection.closed:
            await websocket_connection.send(json.dumps(completion_notification))
            logger.info(f"Completed execution of plan: {plan_id}")
        
    except Exception as e:
        logger.error(f"Error handling execution confirmation: {str(e)}")
        
        # Send error notification
        error_notification = {
            "type": "error",
            "message": f"Failed to execute plan: {str(e)}"
        }
        
        if websocket_connection and not websocket_connection.closed:
            await websocket_connection.send(json.dumps(error_notification))

def extract_suggestions_from_memory(memory_data):
    """
    Extracts actionable suggestions from the conscious memory data
    
    Looks for patterns in the memory that indicate the user might benefit
    from a suggestion, such as repeated tasks, inefficient workflows, etc.
    """
    suggestions = []
    
    # Ensure memory directory exists
    os.makedirs("memory/suggestions", exist_ok=True)
    
    # Parse memory data for suggestion patterns
    insights = memory_data.get("insights", [])
    recent_activities = memory_data.get("recent_activities", [])
    
    # Look for explicit suggestion markers in insights
    for insight in insights:
        content = insight.get("content", "")
        
        # Check for suggestion pattern (added by the enhanced conscious memory prompt)
        suggestion_match = re.search(r"SUGGESTION:\s+([^|]+)\s*\|\s*([^|]+)\s*\|\s*([0-9.]+)", content)
        if suggestion_match:
            title = suggestion_match.group(1).strip()
            message = suggestion_match.group(2).strip()
            confidence = float(suggestion_match.group(3))
            
            # Create suggestion with a basic plan
            suggestion = Suggestion(
                title=title,
                message=message,
                confidence=confidence,
                actions=["automate", "optimize", "schedule"],
                plan={
                    "steps": [
                        {"description": f"Analyze current {title.lower()} pattern", "type": "analysis"},
                        {"description": f"Implement {message.split()[0].lower()} automation", "type": "action"},
                        {"description": "Verify completion and report results", "type": "verification"}
                    ],
                    "estimated_duration": "1 minute",
                    "risk_level": "low"
                }
            )
            
            # Skip if we've already processed this suggestion
            if suggestion.id in processed_suggestions:
                continue
                
            # Save suggestion to disk
            with open(f"memory/suggestions/{suggestion.id}.json", "w") as f:
                json.dump(suggestion.to_dict(), f, indent=2)
                
            suggestions.append(suggestion)
            processed_suggestions.add(suggestion.id)
    
    # Also look for patterns in recent activities that might trigger suggestions
    if recent_activities:
        # Example: Detect repeated manual tasks
        task_counts = {}
        for activity in recent_activities:
            task = activity.get("task", "")
            if task:
                task_counts[task] = task_counts.get(task, 0) + 1
                
        # Suggest automation for frequently repeated tasks
        for task, count in task_counts.items():
            if count >= 3 and "manual" in task.lower():
                suggestion = Suggestion(
                    title=f"Automate Repetitive Task",
                    message=f"I noticed you've done '{task}' {count} times recently. Would you like me to automate this for you?",
                    confidence=0.8,
                    actions=["automate"],
                    plan={
                        "steps": [
                            {"description": "Record the steps you take for this task", "type": "analysis"},
                            {"description": "Create an automated workflow", "type": "action"},
                            {"description": "Run the automation with your approval", "type": "execution"}
                        ],
                        "estimated_duration": "2 minutes",
                        "risk_level": "low"
                    }
                )
                
                # Skip if we've already processed this suggestion
                if suggestion.id in processed_suggestions:
                    continue
                    
                # Save suggestion to disk
                with open(f"memory/suggestions/{suggestion.id}.json", "w") as f:
                    json.dump(suggestion.to_dict(), f, indent=2)
                    
                suggestions.append(suggestion)
                processed_suggestions.add(suggestion.id)
    
    return suggestions

async def send_suggestion(suggestion):
    """Sends a suggestion to the NextGen overlay"""
    global websocket_connection
    
    if websocket_connection is None or websocket_connection.closed:
        logger.error("Cannot send suggestion: WebSocket not connected")
        return False
    
    try:
        # Create notification payload
        payload = suggestion.to_notification_payload()
        
        # Send to overlay
        await websocket_connection.send(json.dumps(payload))
        logger.info(f"Sent suggestion to overlay: {suggestion.title}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending suggestion: {str(e)}")
        return False

async def monitor_memory():
    """Monitors the conscious memory file for changes and extracts suggestions"""
    global last_modified_time
    
    while running:
        try:
            # Check if memory file exists
            if not MEMORY_PATH.exists():
                logger.warning(f"Memory file not found: {MEMORY_PATH}")
                await asyncio.sleep(SCAN_INTERVAL)
                continue
                
            # Check if file has been modified
            current_mtime = os.path.getmtime(MEMORY_PATH)
            if current_mtime <= last_modified_time:
                await asyncio.sleep(SCAN_INTERVAL)
                continue
                
            # Update last modified time
            last_modified_time = current_mtime
            
            # Read memory file
            with open(MEMORY_PATH, "r") as f:
                memory_data = json.load(f)
                
            # Extract suggestions
            suggestions = extract_suggestions_from_memory(memory_data)
            
            # Send suggestions above threshold
            for suggestion in suggestions:
                if suggestion.confidence >= SUGGESTION_THRESHOLD:
                    await send_suggestion(suggestion)
                    logger.info(f"Processed suggestion: {suggestion.title} (confidence: {suggestion.confidence})")
                else:
                    logger.debug(f"Skipped low-confidence suggestion: {suggestion.title} (confidence: {suggestion.confidence})")
                    
        except Exception as e:
            logger.error(f"Error monitoring memory: {str(e)}")
            
        # Wait before next scan
        await asyncio.sleep(SCAN_INTERVAL)

def update_conscious_memory_prompt():
    """Updates the conscious memory system to include suggestion extraction"""
    try:
        # Check if memory system has a prompt file
        prompt_path = Path("/Users/segevbin/Desktop/SensAI/Aiayer/memory/prompts/conscious_memory.txt")
        if not prompt_path.exists():
            logger.warning("Cannot find conscious memory prompt file")
            return
            
        # Read existing prompt
        with open(prompt_path, "r") as f:
            current_prompt = f.read()
            
        # Check if our suggestion extraction is already included
        if "SUGGESTION:" in current_prompt:
            logger.info("Conscious memory prompt already includes suggestion extraction")
            return
            
        # Add our suggestion extraction
        new_prompt = current_prompt + "\n\n" + CONSCIOUS_MEMORY_SUGGESTION_PROMPT
        
        # Backup the original prompt
        backup_path = prompt_path.with_suffix(".bak")
        with open(backup_path, "w") as f:
            f.write(current_prompt)
            
        # Write the updated prompt
        with open(prompt_path, "w") as f:
            f.write(new_prompt)
            
        logger.info("Updated conscious memory prompt with suggestion extraction")
        
    except Exception as e:
        logger.error(f"Error updating conscious memory prompt: {str(e)}")

def signal_handler(sig, frame):
    """Handles process termination signals"""
    global running
    logger.info("Shutting down memory suggestion monitor...")
    running = False
    
    # Stop the event loop
    if asyncio.get_event_loop().is_running():
        asyncio.get_event_loop().stop()

async def main():
    """Main entry point"""
    global running
    
    logger.info("Starting memory-aware suggestion monitor")
    
    # Update conscious memory prompt to extract suggestions
    update_conscious_memory_prompt()
    
    # Start the WebSocket connection
    connection_task = asyncio.create_task(connect_websocket())
    
    # Start memory monitoring
    memory_task = asyncio.create_task(monitor_memory())
    
    # Keep running until interrupted
    try:
        while running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Tasks cancelled")
    finally:
        # Cancel all tasks
        connection_task.cancel()
        memory_task.cancel()
        
        logger.info("Memory suggestion monitor stopped")

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create necessary directories
    os.makedirs("memory/suggestions", exist_ok=True)
    os.makedirs("logs/memory", exist_ok=True)
    
    # Run the main coroutine
    asyncio.run(main())