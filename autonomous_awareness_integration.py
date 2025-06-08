#!/usr/bin/env python3
"""
Autonomous Awareness Integration

This module integrates the autonomous awareness system with:
1. The existing memory system
2. The LLM planning components
3. The execution system
4. The overlay notification system

It provides real connections to these systems instead of the placeholders
in the main autonomous_awareness_system.py file.
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/autonomous_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutonomousIntegration")

# Create necessary directories
os.makedirs("logs", exist_ok=True)
os.makedirs("cache/autonomous_awareness", exist_ok=True)

# Import from autonomous awareness system
try:
    from autonomous_awareness_system import AutonomousAwarenessSystem
except ImportError:
    logger.error("Failed to import AutonomousAwarenessSystem. Make sure autonomous_awareness_system.py is in the same directory.")
    sys.exit(1)

# Import from memory system
try:
    from memory.memory_system import MemorySystem
    from memory.enhanced_semantic_search import EnhancedSemanticSearch
    from memory.conscious_memory import ConsciousMemory
except ImportError:
    logger.error("Failed to import memory system components. Check your PYTHONPATH.")
    MemorySystem = None
    EnhancedSemanticSearch = None
    ConsciousMemory = None

# Import from execution system
try:
    from universal_intelligent_automation_handler import UniversalIntelligentAutomationHandler
    from adaptive_retry_automation_handler import AdaptiveRetryAutomationHandler
except ImportError:
    logger.error("Failed to import automation handlers. Check your PYTHONPATH.")
    UniversalIntelligentAutomationHandler = None
    AdaptiveRetryAutomationHandler = None

# Import from LLM system
try:
    from llm.model import LLMModel
except ImportError:
    logger.error("Failed to import LLM model. Check your PYTHONPATH.")
    LLMModel = None

class EnhancedAutonomousAwarenessSystem(AutonomousAwarenessSystem):
    """Enhanced autonomous awareness system with real integrations."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize integration components
        self.memory_system = self._initialize_memory_system()
        self.semantic_search = self._initialize_semantic_search()
        self.conscious_memory = self._initialize_conscious_memory()
        self.automation_handler = self._initialize_automation_handler()
        self.llm_model = self._initialize_llm_model()
        self.ws_client = None
        
        # Additional settings for integration
        self.ws_url = "ws://localhost:8765"  # Overlay websocket URL
        self.llm_prompt_template = self._load_llm_prompt_template()
        
        logger.info("Enhanced Autonomous Awareness System initialized with integrations")
    
    def _initialize_memory_system(self) -> Optional[Any]:
        """Initialize the memory system integration."""
        if MemorySystem:
            try:
                return MemorySystem()
            except Exception as e:
                logger.error(f"Failed to initialize memory system: {e}")
        return None
    
    def _initialize_semantic_search(self) -> Optional[Any]:
        """Initialize the semantic search integration."""
        if EnhancedSemanticSearch:
            try:
                return EnhancedSemanticSearch()
            except Exception as e:
                logger.error(f"Failed to initialize semantic search: {e}")
        return None
    
    def _initialize_conscious_memory(self) -> Optional[Any]:
        """Initialize the conscious memory integration."""
        if ConsciousMemory:
            try:
                # First, ensure we have the required dependencies initialized
                llm_model = self._initialize_llm_model()
                memory_system = self._initialize_memory_system()
                
                # Initialize with the required parameters
                return ConsciousMemory(llm_provider=llm_model, memory_system=memory_system)
            except Exception as e:
                logger.error(f"Failed to initialize conscious memory: {e}")
        return None
    
    def _initialize_automation_handler(self) -> Optional[Any]:
        """Initialize the automation handler integration."""
        if UniversalIntelligentAutomationHandler:
            try:
                return UniversalIntelligentAutomationHandler()
            except Exception as e:
                logger.error(f"Failed to initialize automation handler: {e}")
        return None
    
    def _initialize_llm_model(self) -> Optional[Any]:
        """Initialize the LLM model integration."""
        if LLMModel:
            try:
                return LLMModel()
            except Exception as e:
                logger.error(f"Failed to initialize LLM model: {e}")
        return None
    
    def _load_llm_prompt_template(self) -> str:
        """Load the LLM prompt template for plan generation."""
        default_template = """
        You are an AI assistant that creates detailed automation plans.
        Based on the following user activity pattern:
        {pattern_description}
        
        Create a step-by-step automation plan that will help the user be more efficient.
        
        The plan should include:
        1. A clear title
        2. A brief description
        3. A sequence of steps with these details for each step:
           - Description of the action
           - Type of action (open_app, navigate_url, click_element, type_text, hotkey)
           - Target of the action
           - Value for the action (if applicable)
           - Screen coordinates (if applicable)
        
        Format the response as JSON.
        """
        
        # Try to load a custom template if available
        try:
            if os.path.exists("templates/automation_plan_prompt.txt"):
                with open("templates/automation_plan_prompt.txt", "r") as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"Failed to load custom prompt template: {e}")
        
        return default_template
    
    async def start(self):
        """Start the enhanced autonomous awareness system."""
        # Connect to websocket server for overlay communication
        self.ws_task = asyncio.create_task(self._maintain_ws_connection())
        
        # Start the base system
        await super().start()
    
    async def stop(self):
        """Stop the enhanced autonomous awareness system."""
        # Cancel websocket connection task if it exists
        if hasattr(self, 'ws_task'):
            self.ws_task.cancel()
            
        # Close websocket connection if it exists
        if self.ws_client and not self.ws_client.closed:
            await self.ws_client.close()
        
        # Stop the base system
        await super().stop()
    
    async def _maintain_ws_connection(self):
        """Maintain a websocket connection to the overlay."""
        while self.running:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.ws_client = websocket
                    logger.info(f"Connected to overlay websocket at {self.ws_url}")
                    
                    # Send initial registration message
                    await websocket.send(json.dumps({
                        "type": "register",
                        "client_type": "autonomous_awareness",
                        "client_id": f"auto_awareness_{int(time.time())}"
                    }))
                    
                    # Wait for messages (keeps connection alive)
                    while self.running:
                        try:
                            message = await websocket.recv()
                            await self._handle_ws_message(message)
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("Websocket connection closed, reconnecting...")
                            break
            except Exception as e:
                logger.error(f"Websocket connection error: {e}")
                self.ws_client = None
                
            # Wait before reconnecting
            if self.running:
                await asyncio.sleep(5)
    
    async def _handle_ws_message(self, message: str):
        """Handle incoming websocket messages."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "suggestion_response":
                # Handle user response to a suggestion
                suggestion_id = data.get("suggestion_id")
                approved = data.get("approved", False)
                await self.handle_user_feedback(suggestion_id, approved)
            
            elif message_type == "ping":
                # Respond to ping messages to keep connection alive
                if self.ws_client and not self.ws_client.closed:
                    await self.ws_client.send(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
        except json.JSONDecodeError:
            logger.error(f"Failed to parse websocket message: {message}")
        except Exception as e:
            logger.error(f"Error handling websocket message: {e}")
    
    async def _scan_memory_for_patterns(self) -> List[Dict]:
        """Scan memory for patterns using the real memory system."""
        patterns = []
        
        try:
            if self.semantic_search:
                # Use semantic search to find patterns in memory
                query = "activities that show repetitive user behavior or inefficient workflows"
                results = await asyncio.to_thread(
                    self.semantic_search.search,
                    query,
                    limit=10,
                    threshold=0.6
                )
                
                if results:
                    # Process search results into patterns
                    for result in results:
                        pattern = {
                            "type": "semantic_pattern",
                            "confidence": result.get("score", 0.7),
                            "context": result.get("context", "unknown"),
                            "details": result.get("content", "")
                        }
                        patterns.append(pattern)
            
            if self.conscious_memory:
                # Check conscious memory for recent activities
                recent_activities = await asyncio.to_thread(
                    self.conscious_memory.get_recent_activities,
                    limit=20
                )
                
                # Analyze for repetitive patterns
                if recent_activities:
                    # Simple analysis: look for similar activities in sequence
                    activity_counts = {}
                    for activity in recent_activities:
                        key = activity.get("activity_type", "unknown")
                        activity_counts[key] = activity_counts.get(key, 0) + 1
                    
                    # Create patterns for frequent activities
                    for activity_type, count in activity_counts.items():
                        if count >= 3:  # Threshold for repetition
                            pattern = {
                                "type": "repetitive_task",
                                "confidence": min(0.5 + (count * 0.1), 0.9),  # Higher count = higher confidence
                                "context": activity_type,
                                "details": f"User performed {activity_type} {count} times recently"
                            }
                            patterns.append(pattern)
        except Exception as e:
            logger.error(f"Error scanning memory for patterns: {e}")
        
        return patterns
    
    async def _generate_plan_for_pattern(self, pattern: Dict) -> Dict:
        """Generate an execution plan using the real LLM integration."""
        try:
            if self.llm_model:
                # Prepare the prompt for the LLM
                prompt = self.llm_prompt_template.format(
                    pattern_description=pattern.get("details", "Unknown pattern")
                )
                
                # Get plan from LLM
                response = await asyncio.to_thread(
                    self.llm_model.generate,
                    prompt,
                    max_tokens=2000,
                    temperature=0.7
                )
                
                # Parse the response as JSON
                try:
                    # Extract JSON from the response if needed
                    json_str = response
                    # If the response contains markdown code blocks, extract the JSON
                    if "```json" in response:
                        json_str = response.split("```json")[1].split("```")[0].strip()
                    elif "```" in response:
                        json_str = response.split("```")[1].split("```")[0].strip()
                    
                    plan = json.loads(json_str)
                    
                    # Ensure the plan has the required fields
                    if "task_id" not in plan:
                        plan["task_id"] = f"plan_{int(time.time())}"
                    if "title" not in plan:
                        plan["title"] = f"Automated {pattern['context']}"
                    if "description" not in plan:
                        plan["description"] = pattern.get("details", "Automated plan")
                    if "steps" not in plan:
                        plan["steps"] = []
                    
                    return plan
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
                    logger.debug(f"LLM response: {response}")
            
            # Fallback to placeholder plan
            return await super()._generate_plan_for_pattern(pattern)
        except Exception as e:
            logger.error(f"Error generating plan for pattern: {e}")
            return await super()._generate_plan_for_pattern(pattern)
    
    async def _deliver_suggestion(self, suggestion: Dict) -> bool:
        """Deliver a suggestion using the real overlay integration."""
        try:
            if self.ws_client and not self.ws_client.closed:
                # Format the suggestion message for the overlay
                message = {
                    "type": "suggestion",
                    "suggestion_id": suggestion.get("id"),
                    "title": suggestion.get("title"),
                    "message": suggestion.get("message"),
                    "confidence": suggestion.get("confidence"),
                    "timestamp": datetime.now().isoformat(),
                    "actions": [
                        {
                            "action_id": "approve",
                            "action_text": "Automate This",
                            "action_type": "primary"
                        },
                        {
                            "action_id": "reject",
                            "action_text": "No Thanks",
                            "action_type": "secondary"
                        }
                    ]
                }
                
                # Send to overlay
                await self.ws_client.send(json.dumps(message))
                
                # Mark as delivered
                suggestion["delivered"] = True
                return True
            else:
                logger.warning("Websocket connection not available for suggestion delivery")
                return False
        except Exception as e:
            logger.error(f"Error delivering suggestion: {e}")
            return await super()._deliver_suggestion(suggestion)
    
    async def _execute_plan(self, plan: Dict) -> Dict:
        """Execute a plan using the real automation handler."""
        try:
            if self.automation_handler:
                # Use the automation handler to execute the plan
                start_time = time.time()
                
                # Execute the plan
                result = await asyncio.to_thread(
                    self.automation_handler.execute_plan,
                    plan
                )
                
                execution_time = time.time() - start_time
                
                # Format the result
                return {
                    "success": result.get("success", False),
                    "execution_time": execution_time,
                    "error": result.get("error")
                }
            else:
                logger.warning("Automation handler not available, using fallback execution")
                return await super()._execute_plan(plan)
        except Exception as e:
            logger.error(f"Error executing plan: {e}")
            return {
                "success": False,
                "execution_time": 0,
                "error": str(e)
            }

async def main():
    """Main entry point for the enhanced autonomous awareness system."""
    system = EnhancedAutonomousAwarenessSystem()
    await system.start()
    
    try:
        # Keep the main task alive
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await asyncio.sleep(1)
        await system.stop()

if __name__ == "__main__":
    asyncio.run(main())