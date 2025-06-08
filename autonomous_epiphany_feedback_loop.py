#!/usr/bin/env python3
"""
Autonomous Epiphany Feedback Loop Integration

Integrates suggestion feedback learning with the autonomous epiphany system.
Creates a complete feedback loop for continuous improvement of suggestions.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import traceback
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autonomous_epiphany_feedback.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Import related modules
try:
    from memory.suggestion_memory import get_suggestion_memory
    SUGGESTION_MEMORY_AVAILABLE = True
except ImportError:
    SUGGESTION_MEMORY_AVAILABLE = False
    logger.warning("⚠️ Suggestion memory module not available")

try:
    from memory.suggestion_feedback_learner import get_feedback_learner
    FEEDBACK_LEARNER_AVAILABLE = True
except ImportError:
    FEEDBACK_LEARNER_AVAILABLE = False
    logger.warning("⚠️ Suggestion feedback learner not available")

try:
    from memory.action_item_extractor import get_action_extractor
    ACTION_EXTRACTOR_AVAILABLE = True
except ImportError:
    ACTION_EXTRACTOR_AVAILABLE = False
    logger.warning("⚠️ Action item extractor not available")

try:
    from neural_ui_suggestion_executor import get_neural_ui_executor
    NEURAL_UI_EXECUTOR_AVAILABLE = True
except ImportError:
    NEURAL_UI_EXECUTOR_AVAILABLE = False
    logger.warning("⚠️ Neural UI suggestion executor not available")

class AutonomousEpiphanyFeedbackLoop:
    """
    Integrates all components of the autonomous epiphany system with feedback learning.
    
    Key components:
    1. Suggestion Memory - Stores and manages suggestions
    2. Action Item Extractor - Extracts actionable items from screen content
    3. Feedback Learner - Learns from user feedback to improve suggestions
    4. Neural UI Executor - Executes suggestions using neural UI detection
    5. Feedback Loop - Connects all components for continuous improvement
    """
    
    def __init__(self):
        """Initialize the feedback loop system."""
        # Track component availability
        self.components_available = {
            "suggestion_memory": SUGGESTION_MEMORY_AVAILABLE,
            "feedback_learner": FEEDBACK_LEARNER_AVAILABLE,
            "action_extractor": ACTION_EXTRACTOR_AVAILABLE,
            "neural_ui_executor": NEURAL_UI_EXECUTOR_AVAILABLE
        }
        
        # Component instances (to be initialized on first use)
        self._suggestion_memory = None
        self._feedback_learner = None
        self._action_extractor = None
        self._neural_ui_executor = None
        
        # Feedback loop configuration
        self.min_confidence_threshold = 0.65
        self.high_confidence_threshold = 0.85
        self.feedback_update_interval = 60  # seconds
        
        # Statistics
        self.stats = {
            "suggestions_generated": 0,
            "suggestions_shown": 0,
            "suggestions_accepted": 0,
            "suggestions_rejected": 0,
            "suggestions_executed": 0,
            "execution_success_rate": 0.0,
            "avg_confidence": 0.0,
            "last_feedback_update": None
        }
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"✅ Autonomous Epiphany Feedback Loop initialized. "
                   f"Components available: {sum(self.components_available.values())}/4")
    
    async def process_screen_content(
        self, 
        screen_content: str, 
        active_app: str, 
        recent_activity: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process screen content to generate suggestions with feedback enhancement.
        
        Args:
            screen_content: Text content from the screen
            active_app: Name of the active application
            recent_activity: List of recent user activities
            
        Returns:
            Dict with processing results
        """
        try:
            start_time = time.time()
            
            # Check if action extractor is available
            if not self.components_available["action_extractor"]:
                raise ValueError("Action item extractor not available")
            
            # Get action extractor
            action_extractor = await self._get_action_extractor()
            
            # Extract suggestions from screen content
            extraction_result = await action_extractor.analyze_screen_content(
                screen_content=screen_content,
                active_app=active_app,
                recent_activity=recent_activity
            )
            
            # Check if there's a suggestion
            if not extraction_result.get("has_suggestion", False):
                return {
                    "has_suggestion": False,
                    "reason": extraction_result.get("reason", "No suggestion found"),
                    "processing_time": time.time() - start_time
                }
            
            # Apply feedback learning to enhance suggestion
            suggestion_id = extraction_result.get("id")
            if suggestion_id and self.components_available["feedback_learner"]:
                try:
                    # Get feedback learner
                    feedback_learner = await self._get_feedback_learner()
                    
                    # Get suggestion memory
                    memory = await self._get_suggestion_memory()
                    
                    # Get the suggestion
                    suggestion = await memory.get_suggestion(suggestion_id)
                    
                    if suggestion:
                        # Calculate quality score based on learned patterns
                        quality_score = await feedback_learner.get_suggestion_quality_score(suggestion)
                        
                        # Update confidence with learned quality
                        original_confidence = suggestion.get("confidence", 0.7)
                        enhanced_confidence = (original_confidence * 0.7) + (quality_score * 0.3)
                        
                        # Update suggestion with enhanced confidence
                        suggestion["original_confidence"] = original_confidence
                        suggestion["enhanced_confidence"] = enhanced_confidence
                        suggestion["confidence"] = enhanced_confidence
                        
                        # Remove and re-add suggestion with updated confidence
                        await memory.mark_suggestion_rejected(suggestion_id)
                        new_suggestion_id = await memory.add_suggestion(suggestion)
                        
                        if new_suggestion_id:
                            logger.info(f"✅ Enhanced suggestion confidence from {original_confidence:.2f} to {enhanced_confidence:.2f}")
                            suggestion_id = new_suggestion_id
                except Exception as e:
                    logger.error(f"❌ Error enhancing suggestion with feedback: {e}")
                    # Continue with original suggestion
            
            # Update stats
            self.stats["suggestions_generated"] += 1
            total_conf = self.stats["avg_confidence"] * (self.stats["suggestions_generated"] - 1)
            self.stats["avg_confidence"] = (total_conf + extraction_result.get("confidence", 0.0)) / self.stats["suggestions_generated"]
            
            # Return processed result
            result = {
                "has_suggestion": True,
                "suggestion_id": suggestion_id,
                "title": extraction_result.get("title"),
                "description": extraction_result.get("description"),
                "confidence": extraction_result.get("confidence"),
                "action_items": extraction_result.get("action_items"),
                "processing_time": time.time() - start_time
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing screen content: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "has_suggestion": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    async def handle_user_feedback(
        self, 
        suggestion_id: str, 
        feedback: str, 
        reason: Optional[str] = None
    ) -> bool:
        """
        Handle user feedback on a suggestion.
        
        Args:
            suggestion_id: ID of the suggestion
            feedback: Type of feedback ('accepted', 'rejected', 'executed', 'failed')
            reason: Optional reason for rejection
            
        Returns:
            bool: Success status
        """
        try:
            # Check if components are available
            if not self.components_available["suggestion_memory"]:
                raise ValueError("Suggestion memory not available")
            
            # Get suggestion memory
            memory = await self._get_suggestion_memory()
            
            # Update suggestion status based on feedback
            if feedback == "accepted":
                result = await memory.mark_suggestion_accepted(suggestion_id)
                if result:
                    self.stats["suggestions_accepted"] += 1
                    self.stats["suggestions_shown"] += 1
            elif feedback == "rejected":
                result = await memory.mark_suggestion_rejected(suggestion_id, reason)
                if result:
                    self.stats["suggestions_rejected"] += 1
                    self.stats["suggestions_shown"] += 1
            elif feedback == "executed":
                result = await memory.mark_suggestion_executed(suggestion_id, success=True)
                if result:
                    self.stats["suggestions_executed"] += 1
                    
                    # Update execution success rate
                    if self.stats["suggestions_executed"] > 0:
                        self.stats["execution_success_rate"] = (
                            (self.stats["execution_success_rate"] * (self.stats["suggestions_executed"] - 1) + 1.0) / 
                            self.stats["suggestions_executed"]
                        )
            elif feedback == "failed":
                result = await memory.mark_suggestion_executed(suggestion_id, success=False)
                if result:
                    # Update execution success rate
                    if self.stats["suggestions_executed"] > 0:
                        self.stats["execution_success_rate"] = (
                            (self.stats["execution_success_rate"] * (self.stats["suggestions_executed"] - 1) + 0.0) / 
                            self.stats["suggestions_executed"]
                        )
            else:
                logger.warning(f"⚠️ Unknown feedback type: {feedback}")
                return False
            
            # If feedback learner is available, process feedback
            if self.components_available["feedback_learner"]:
                feedback_learner = await self._get_feedback_learner()
                await feedback_learner.process_suggestion_feedback(suggestion_id, feedback)
            
            # Schedule feedback system update
            self.stats["last_feedback_update"] = datetime.now().isoformat()
            asyncio.create_task(self._update_feedback_system())
            
            logger.info(f"✅ Processed user feedback for suggestion {suggestion_id}: {feedback}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling user feedback: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def execute_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        """
        Execute a suggestion using the neural UI executor.
        
        Args:
            suggestion_id: ID of the suggestion to execute
            
        Returns:
            Dict with execution result
        """
        try:
            # Check if neural UI executor is available
            if not self.components_available["neural_ui_executor"]:
                raise ValueError("Neural UI executor not available")
            
            # Get neural UI executor
            executor = await self._get_neural_ui_executor()
            
            # Execute suggestion
            execution_result = await executor.execute_suggestion(suggestion_id)
            
            # Process execution feedback
            if execution_result.get("success", False):
                await self.handle_user_feedback(suggestion_id, "executed")
            else:
                await self.handle_user_feedback(suggestion_id, "failed")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Error executing suggestion: {e}")
            logger.error(traceback.format_exc())
            
            # Try to mark as failed
            try:
                await self.handle_user_feedback(suggestion_id, "failed")
            except:
                pass
            
            return {
                "suggestion_id": suggestion_id,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_top_suggestions(self, max_count: int = 3) -> List[Dict[str, Any]]:
        """
        Get top pending suggestions enhanced with feedback learning.
        
        Args:
            max_count: Maximum number of suggestions to return
            
        Returns:
            List of top suggestions
        """
        try:
            # Check if suggestion memory is available
            if not self.components_available["suggestion_memory"]:
                raise ValueError("Suggestion memory not available")
            
            # Get suggestion memory
            memory = await self._get_suggestion_memory()
            
            # Get all pending suggestions
            pending_suggestions = await memory.get_all_pending_suggestions()
            
            # Apply feedback learning to rank suggestions
            if self.components_available["feedback_learner"]:
                feedback_learner = await self._get_feedback_learner()
                
                # Calculate quality scores
                for suggestion in pending_suggestions:
                    quality_score = await feedback_learner.get_suggestion_quality_score(suggestion)
                    suggestion["quality_score"] = quality_score
                
                # Sort by quality score
                pending_suggestions.sort(key=lambda x: x.get("quality_score", 0.0), reverse=True)
            
            # Return top suggestions
            return pending_suggestions[:max_count]
            
        except Exception as e:
            logger.error(f"❌ Error getting top suggestions: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def get_feedback_system_insights(self) -> Dict[str, Any]:
        """
        Get insights and recommendations from the feedback system.
        
        Returns:
            Dict with system insights and recommendations
        """
        try:
            # Check if feedback learner is available
            if not self.components_available["feedback_learner"]:
                raise ValueError("Feedback learner not available")
            
            # Get feedback learner
            feedback_learner = await self._get_feedback_learner()
            
            # Get feedback stats
            feedback_stats = await feedback_learner.get_feedback_stats()
            
            # Get improvement suggestions
            improvements = await feedback_learner.get_improvement_suggestions()
            
            # Combine with system stats
            insights = {
                "system_stats": self.stats,
                "feedback_stats": feedback_stats,
                "improvement_suggestions": improvements,
                "timestamp": datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error getting feedback system insights: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _update_feedback_system(self) -> None:
        """Periodic update of the feedback system to apply learned patterns."""
        try:
            # Check if enough time has passed since last update
            if self.stats["last_feedback_update"]:
                last_update = datetime.fromisoformat(self.stats["last_feedback_update"])
                elapsed = (datetime.now() - last_update).total_seconds()
                
                if elapsed < self.feedback_update_interval:
                    return
            
            # Check if components are available
            if not (self.components_available["suggestion_memory"] and 
                    self.components_available["feedback_learner"]):
                return
            
            # Get components
            memory = await self._get_suggestion_memory()
            feedback_learner = await self._get_feedback_learner()
            
            # Apply learned threshold updates
            feedback_stats = await feedback_learner.get_feedback_stats()
            
            # Adaptive confidence threshold based on acceptance rate
            if feedback_stats.get("total_records", 0) >= 10:
                acceptance_rate = feedback_stats.get("acceptance_rate", 0.5)
                
                # Adjust thresholds based on acceptance rate
                if acceptance_rate < 0.3:
                    # Users are rejecting a lot, increase threshold
                    self.min_confidence_threshold = min(0.8, self.min_confidence_threshold + 0.05)
                elif acceptance_rate > 0.7:
                    # Users are accepting a lot, can lower threshold
                    self.min_confidence_threshold = max(0.5, self.min_confidence_threshold - 0.05)
            
            # Apply improvements to action extractor if available
            if self.components_available["action_extractor"]:
                action_extractor = await self._get_action_extractor()
                
                # Apply confidence threshold
                action_extractor.min_confidence = self.min_confidence_threshold
            
            logger.info(f"✅ Updated feedback system with min_confidence={self.min_confidence_threshold:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error updating feedback system: {e}")
    
    async def _get_suggestion_memory(self):
        """Get or initialize suggestion memory."""
        if self._suggestion_memory is None:
            from memory.suggestion_memory import get_suggestion_memory
            self._suggestion_memory = await get_suggestion_memory()
        return self._suggestion_memory
    
    async def _get_feedback_learner(self):
        """Get or initialize feedback learner."""
        if self._feedback_learner is None:
            from memory.suggestion_feedback_learner import get_feedback_learner
            self._feedback_learner = await get_feedback_learner()
        return self._feedback_learner
    
    async def _get_action_extractor(self):
        """Get or initialize action extractor."""
        if self._action_extractor is None:
            from memory.action_item_extractor import get_action_extractor
            self._action_extractor = await get_action_extractor()
        return self._action_extractor
    
    async def _get_neural_ui_executor(self):
        """Get or initialize neural UI executor."""
        if self._neural_ui_executor is None:
            from neural_ui_suggestion_executor import get_neural_ui_executor
            self._neural_ui_executor = await get_neural_ui_executor()
        return self._neural_ui_executor

# Singleton instance
_feedback_loop_instance = None

async def get_autonomous_epiphany_feedback_loop() -> AutonomousEpiphanyFeedbackLoop:
    """Get or create the global autonomous epiphany feedback loop instance."""
    global _feedback_loop_instance
    
    if _feedback_loop_instance is None:
        _feedback_loop_instance = AutonomousEpiphanyFeedbackLoop()
    
    return _feedback_loop_instance

# Example usage
if __name__ == "__main__":
    async def test_feedback_loop():
        """Test the autonomous epiphany feedback loop."""
        # Get feedback loop instance
        feedback_loop = await get_autonomous_epiphany_feedback_loop()
        
        # Create test screen content
        screen_content = """
        Inbox - user@example.com - Mail
        
        From: manager@example.com
        Subject: Team Meeting Thursday
        
        Hi team,
        
        Let's schedule a team meeting for Thursday at 3pm to discuss the new project timeline.
        
        Please come prepared with your status updates and any questions you may have.
        
        Best regards,
        Manager
        """
        
        active_app = "Mail"
        
        # Process screen content
        result = await feedback_loop.process_screen_content(
            screen_content=screen_content,
            active_app=active_app
        )
        
        # Check if there's a suggestion
        if result.get("has_suggestion", False):
            suggestion_id = result.get("suggestion_id")
            
            print(f"Generated suggestion: {result.get('title')}")
            print(f"Description: {result.get('description')}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Suggestion ID: {suggestion_id}")
            
            # Simulate user acceptance
            await feedback_loop.handle_user_feedback(suggestion_id, "accepted")
            
            # Get top suggestions
            top_suggestions = await feedback_loop.get_top_suggestions()
            print(f"Top suggestions count: {len(top_suggestions)}")
            
            # Get feedback insights
            insights = await feedback_loop.get_feedback_system_insights()
            print(f"System stats: {insights.get('system_stats')}")
        else:
            print(f"No suggestion generated: {result.get('reason')}")
    
    # Run the test
    asyncio.run(test_feedback_loop())