#!/usr/bin/env python3
"""
Autonomous Awareness System

This module provides a continuous autonomous system that:
1. Monitors system state, user activity, and memory
2. Generates proactive suggestions based on patterns
3. Evaluates and scores suggestions for relevance
4. Delivers high-confidence suggestions to the user
5. Executes plans when approved
6. Continuously learns from outcomes

The system stays alive through an infinite loop with proper error handling
and graceful shutdown mechanisms.
"""

import asyncio
import json
import logging
import os
import signal
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/autonomous_awareness.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutonomousAwareness")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class AutonomousAwarenessSystem:
    """Manages continuous awareness, suggestion generation, and execution."""
    
    def __init__(self):
        self.running = False
        self.loop = None
        self.tasks = []
        self.last_suggestion_time = 0
        self.suggestion_cooldown = 60  # Seconds between suggestions
        self.min_confidence_threshold = 0.75  # Minimum confidence to show suggestion
        self.executed_plans = []
        self.suggestion_history = []
        self.current_suggestion = None
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Load persistence if available
        self._load_persistence()
        
        logger.info("Autonomous Awareness System initialized")
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop()
    
    def _load_persistence(self):
        """Load persistence data from file."""
        try:
            if os.path.exists("cache/autonomous_awareness/state.json"):
                with open("cache/autonomous_awareness/state.json", "r") as f:
                    state = json.load(f)
                    self.executed_plans = state.get("executed_plans", [])
                    self.suggestion_history = state.get("suggestion_history", [])
                    logger.info(f"Loaded persistence data: {len(self.executed_plans)} executed plans, "
                                f"{len(self.suggestion_history)} historical suggestions")
        except Exception as e:
            logger.error(f"Error loading persistence data: {e}")
    
    def _save_persistence(self):
        """Save persistence data to file."""
        try:
            os.makedirs("cache/autonomous_awareness", exist_ok=True)
            state = {
                "executed_plans": self.executed_plans,
                "suggestion_history": self.suggestion_history,
                "last_update": datetime.now().isoformat()
            }
            with open("cache/autonomous_awareness/state.json", "w") as f:
                json.dump(state, f, indent=2)
            logger.info("Saved persistence data")
        except Exception as e:
            logger.error(f"Error saving persistence data: {e}")
    
    async def start(self):
        """Start the autonomous awareness system."""
        if self.running:
            logger.warning("System already running")
            return
        
        self.running = True
        self.loop = asyncio.get_event_loop()
        
        # Create and start tasks
        self.tasks = [
            self.loop.create_task(self._memory_monitor_loop()),
            self.loop.create_task(self._suggestion_generator_loop()),
            self.loop.create_task(self._suggestion_delivery_loop()),
            self.loop.create_task(self._execution_monitor_loop()),
            self.loop.create_task(self._persistence_loop())
        ]
        
        logger.info("Autonomous Awareness System started")
    
    def stop(self):
        """Stop the autonomous awareness system."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Save persistence before exit
        self._save_persistence()
        
        logger.info("Autonomous Awareness System stopped")
    
    async def _memory_monitor_loop(self):
        """Monitor memory for patterns and insights continuously."""
        logger.info("Memory monitor loop started")
        
        while self.running:
            try:
                await self._scan_memory_for_patterns()
                await asyncio.sleep(15)  # Check memory every 15 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory monitor loop: {e}")
                await asyncio.sleep(5)  # Short delay on error
        
        logger.info("Memory monitor loop stopped")
    
    async def _suggestion_generator_loop(self):
        """Generate suggestions based on patterns and user context."""
        logger.info("Suggestion generator loop started")
        
        while self.running:
            try:
                suggestions = await self._generate_suggestions()
                if suggestions:
                    for suggestion in suggestions:
                        # Only add new suggestions with sufficient confidence
                        if (suggestion["confidence"] >= self.min_confidence_threshold and
                                not self._is_duplicate_suggestion(suggestion)):
                            self.suggestion_history.append(suggestion)
                            logger.info(f"Generated new suggestion: {suggestion['title']} "
                                        f"(confidence: {suggestion['confidence']})")
                
                await asyncio.sleep(30)  # Generate suggestions every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in suggestion generator loop: {e}")
                await asyncio.sleep(5)
        
        logger.info("Suggestion generator loop stopped")
    
    async def _suggestion_delivery_loop(self):
        """Deliver suggestions to the user via the overlay."""
        logger.info("Suggestion delivery loop started")
        
        while self.running:
            try:
                # Check if we can send a suggestion (cooldown period)
                current_time = time.time()
                if (current_time - self.last_suggestion_time >= self.suggestion_cooldown and
                        not self.current_suggestion):
                    
                    # Get the highest confidence suggestion we haven't delivered yet
                    best_suggestion = self._get_best_suggestion()
                    
                    if best_suggestion:
                        success = await self._deliver_suggestion(best_suggestion)
                        if success:
                            self.current_suggestion = best_suggestion
                            self.last_suggestion_time = current_time
                            logger.info(f"Delivered suggestion: {best_suggestion['title']}")
                
                await asyncio.sleep(5)  # Check for delivery opportunity every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in suggestion delivery loop: {e}")
                await asyncio.sleep(5)
        
        logger.info("Suggestion delivery loop stopped")
    
    async def _execution_monitor_loop(self):
        """Monitor and execute plans when approved by user."""
        logger.info("Execution monitor loop started")
        
        while self.running:
            try:
                # Check for user approval of current suggestion
                if self.current_suggestion and self.current_suggestion.get("approved", False):
                    plan = self.current_suggestion.get("plan")
                    if plan:
                        logger.info(f"Executing plan for suggestion: {self.current_suggestion['title']}")
                        result = await self._execute_plan(plan)
                        
                        # Record execution result
                        execution_record = {
                            "plan_id": plan.get("task_id"),
                            "suggestion_id": self.current_suggestion.get("id"),
                            "title": self.current_suggestion.get("title"),
                            "timestamp": datetime.now().isoformat(),
                            "success": result.get("success", False),
                            "error": result.get("error"),
                            "execution_time": result.get("execution_time")
                        }
                        self.executed_plans.append(execution_record)
                        
                        # Clear current suggestion after execution
                        self.current_suggestion = None
                
                await asyncio.sleep(3)  # Check for execution opportunity every 3 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in execution monitor loop: {e}")
                await asyncio.sleep(5)
        
        logger.info("Execution monitor loop stopped")
    
    async def _persistence_loop(self):
        """Periodically save system state for persistence."""
        logger.info("Persistence loop started")
        
        while self.running:
            try:
                self._save_persistence()
                await asyncio.sleep(300)  # Save every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in persistence loop: {e}")
                await asyncio.sleep(60)
        
        logger.info("Persistence loop stopped")
    
    async def _scan_memory_for_patterns(self) -> List[Dict]:
        """Scan memory for patterns that could lead to suggestions."""
        try:
            # Placeholder for actual memory scanning implementation
            # In a real implementation, this would connect to the memory system
            # and scan for patterns like repeated tasks, inefficient workflows, etc.
            
            # Example memory scanning logic:
            # 1. Check recent applications used
            # 2. Identify repetitive patterns
            # 3. Look for explicit suggestion markers
            # 4. Detect navigation patterns that could be optimized
            
            # For demonstration, we'll return a dummy pattern
            return [{
                "type": "repetitive_task",
                "confidence": 0.85,
                "context": "web search workflow",
                "details": "User has performed similar web searches 3 times in the last hour"
            }]
        except Exception as e:
            logger.error(f"Error scanning memory for patterns: {e}")
            return []
    
    async def _generate_suggestions(self) -> List[Dict]:
        """Generate suggestions based on memory patterns."""
        try:
            # Get patterns from memory
            patterns = await self._scan_memory_for_patterns()
            suggestions = []
            
            for pattern in patterns:
                # Convert pattern to suggestion
                if pattern["type"] == "repetitive_task":
                    suggestion = {
                        "id": f"sugg_{int(time.time())}_{len(self.suggestion_history)}",
                        "title": f"Automate {pattern['context']}",
                        "message": f"I noticed you frequently perform this task. Would you like me to automate it?",
                        "confidence": pattern["confidence"],
                        "timestamp": datetime.now().isoformat(),
                        "delivered": False,
                        "approved": False,
                        "type": "automation",
                        "context": pattern["details"],
                        "plan": await self._generate_plan_for_pattern(pattern)
                    }
                    suggestions.append(suggestion)
            
            return suggestions
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    async def _generate_plan_for_pattern(self, pattern: Dict) -> Dict:
        """Generate an execution plan for a specific pattern."""
        try:
            # Placeholder for actual plan generation logic
            # In a real implementation, this would call the LLM service
            # to generate a detailed execution plan
            
            # Example plan structure based on the system's existing format
            plan = {
                "task_id": f"plan_{int(time.time())}",
                "title": f"Automated {pattern['context']}",
                "description": f"Automation plan for {pattern['details']}",
                "request_type": "automation",
                "steps": [
                    {
                        "id": "step_1",
                        "description": "Open browser",
                        "action_type": "open_app",
                        "target": "Safari",
                        "value": "",
                        "coordinates": None
                    },
                    {
                        "id": "step_2",
                        "description": "Navigate to search engine",
                        "action_type": "navigate_url",
                        "target": "browser",
                        "value": "https://www.google.com",
                        "coordinates": None
                    }
                ],
                "complexity_score": 0.4,
                "estimated_duration": 10
            }
            
            return plan
        except Exception as e:
            logger.error(f"Error generating plan for pattern: {e}")
            return {}
    
    def _is_duplicate_suggestion(self, suggestion: Dict) -> bool:
        """Check if a suggestion is a duplicate of one we've already seen."""
        for existing in self.suggestion_history:
            if (existing["title"] == suggestion["title"] and 
                    existing["context"] == suggestion["context"]):
                return True
        return False
    
    def _get_best_suggestion(self) -> Optional[Dict]:
        """Get the best undelivered suggestion based on confidence."""
        undelivered = [s for s in self.suggestion_history 
                       if not s.get("delivered", False)]
        
        if not undelivered:
            return None
        
        # Sort by confidence (descending)
        undelivered.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        return undelivered[0]
    
    async def _deliver_suggestion(self, suggestion: Dict) -> bool:
        """Deliver a suggestion to the user via the overlay."""
        try:
            # Placeholder for actual delivery logic
            # In a real implementation, this would send a websocket message
            # to the overlay to display the suggestion
            
            # Mark the suggestion as delivered
            suggestion["delivered"] = True
            
            # Simulate sending to overlay
            logger.info(f"OVERLAY: New suggestion - {suggestion['title']}: {suggestion['message']}")
            
            return True
        except Exception as e:
            logger.error(f"Error delivering suggestion: {e}")
            return False
    
    async def _execute_plan(self, plan: Dict) -> Dict:
        """Execute an approved plan."""
        try:
            # Placeholder for actual execution logic
            # In a real implementation, this would use the universal_intelligent_automation_handler
            # to execute each step of the plan
            
            logger.info(f"Executing plan: {plan['title']}")
            
            # Simulate execution of each step
            for i, step in enumerate(plan.get("steps", [])):
                logger.info(f"Executing step {i+1}/{len(plan.get('steps', []))}: {step['description']}")
                # Simulate step execution time
                await asyncio.sleep(1)
            
            return {
                "success": True,
                "execution_time": len(plan.get("steps", [])),
                "error": None
            }
        except Exception as e:
            logger.error(f"Error executing plan: {e}")
            return {
                "success": False,
                "execution_time": 0,
                "error": str(e)
            }

    async def handle_user_feedback(self, suggestion_id: str, approved: bool) -> bool:
        """Handle user feedback for a suggestion."""
        try:
            # Find the suggestion
            for suggestion in self.suggestion_history:
                if suggestion.get("id") == suggestion_id:
                    suggestion["approved"] = approved
                    logger.info(f"Suggestion {suggestion_id} {'approved' if approved else 'rejected'}")
                    
                    # If this is the current suggestion, update it
                    if (self.current_suggestion and 
                            self.current_suggestion.get("id") == suggestion_id):
                        self.current_suggestion["approved"] = approved
                    
                    # If rejected, clear current suggestion
                    if not approved and self.current_suggestion and self.current_suggestion.get("id") == suggestion_id:
                        self.current_suggestion = None
                    
                    return True
            
            logger.warning(f"Suggestion {suggestion_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error handling user feedback: {e}")
            return False

async def main():
    """Main entry point for the autonomous awareness system."""
    system = AutonomousAwarenessSystem()
    await system.start()
    
    try:
        # Keep the main task alive
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await asyncio.sleep(1)
        system.stop()

if __name__ == "__main__":
    asyncio.run(main())