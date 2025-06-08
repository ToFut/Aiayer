#!/usr/bin/env python3
"""
Action Item Extractor

Service for extracting actionable items from screen content using LLM.
This module serves as the bridge between contextual memory analysis and suggestion generation.
"""

import asyncio
import json
import logging
import os
import time
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import traceback
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/action_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('logs/memory', exist_ok=True)

# Import suggestion memory (dynamic import to avoid circular references)
try:
    from memory.suggestion_memory import get_suggestion_memory
except ImportError:
    logger.warning("⚠️ Suggestion memory module not available, will try to import when needed")

class ActionItemExtractor:
    """
    Extracts actionable items from screen content and context using LLM analysis.
    Provides structured output for autonomous suggestions.
    """
    
    def __init__(self, llm_provider=None):
        """
        Initialize the action item extractor.
        
        Args:
            llm_provider: LLM provider instance for text generation
        """
        self.llm_provider = llm_provider
        self.logger = logger
        
        # Suggestion patterns
        self.suggestion_pattern = r"SUGGESTION:\s*([^|]+)\|\s*([^|]+)\|\s*([\d\.]+)"
        self.action_items_pattern = r"ACTION_ITEMS:([\s\S]+?)(?=\n\n|$)"
        self.action_item_line_pattern = r"- ([a-z_]+):\s*(.+)"
        
        # Confidence thresholds
        self.min_confidence = 0.65
        self.high_confidence = 0.85
        
        # Performance tracking
        self.extraction_stats = {
            "requests": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "avg_extraction_time": 0.0,
            "avg_confidence": 0.0
        }
        
        self.logger.info("✅ ActionItemExtractor initialized")
    
    async def analyze_screen_content(
        self, 
        screen_content: str, 
        active_app: str, 
        recent_activity: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze screen content to extract actionable suggestions.
        
        Args:
            screen_content: Text content from the screen
            active_app: Name of the active application
            recent_activity: List of recent user activities
            
        Returns:
            result: Dictionary with analysis results
        """
        start_time = time.time()
        
        self.extraction_stats["requests"] += 1
        
        try:
            # Prepare LLM prompt
            prompt = self._build_analysis_prompt(screen_content, active_app, recent_activity)
            
            # Call LLM for analysis
            if self.llm_provider:
                response = await self._call_llm(prompt)
            else:
                # Use fallback method if no LLM provider
                response = await self._fallback_llm_call(prompt)
            
            # Extract suggestions and action items
            extraction_result = self._parse_llm_response(response)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update stats
            if extraction_result["has_suggestion"]:
                self.extraction_stats["successful_extractions"] += 1
                
                # Update average confidence
                total_conf = self.extraction_stats["avg_confidence"] * (self.extraction_stats["successful_extractions"] - 1)
                self.extraction_stats["avg_confidence"] = (
                    total_conf + extraction_result["confidence"]
                ) / self.extraction_stats["successful_extractions"]
                
                # Update suggestion memory if confidence is high enough
                if extraction_result["confidence"] >= self.min_confidence:
                    await self._store_suggestion(extraction_result)
            else:
                self.extraction_stats["failed_extractions"] += 1
            
            # Update average extraction time
            total_time = self.extraction_stats["avg_extraction_time"] * (self.extraction_stats["requests"] - 1)
            self.extraction_stats["avg_extraction_time"] = (total_time + processing_time) / self.extraction_stats["requests"]
            
            # Add processing metadata
            extraction_result["processing_time"] = processing_time
            extraction_result["timestamp"] = datetime.now().isoformat()
            
            return extraction_result
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing screen content: {e}")
            self.logger.error(traceback.format_exc())
            
            self.extraction_stats["failed_extractions"] += 1
            
            return {
                "has_suggestion": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_analysis_prompt(
        self, 
        screen_content: str, 
        active_app: str, 
        recent_activity: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build the LLM prompt for action extraction."""
        # Truncate screen content if too long
        if len(screen_content) > 2000:
            screen_content = screen_content[:1997] + "..."
        
        # Format recent activity
        activity_text = "No recent activity recorded."
        if recent_activity and len(recent_activity) > 0:
            activity_lines = []
            for activity in recent_activity[-5:]:  # Last 5 activities
                if isinstance(activity, dict):
                    timestamp = activity.get('timestamp', 'unknown time')
                    app = activity.get('app', 'unknown app')
                    action = activity.get('action', 'unknown action')
                    activity_lines.append(f"- At {timestamp}, in {app}: {action}")
            
            if activity_lines:
                activity_text = "\n".join(activity_lines)
        
        # Build the complete prompt
        prompt = f"""You are an automation assistant analyzing screen content.

CURRENT SCREEN CONTENT:
{screen_content}

ACTIVE APPLICATION:
{active_app}

RECENT USER ACTIVITY:
{activity_text}

Based on this information, identify if there's a valuable automation opportunity. 
If yes, provide:
1. A brief title for the suggestion
2. A clear description of what can be automated
3. A confidence score (0.0-1.0)
4. Specific action items required to complete this automation
5. Any contextual information to remember

Format your response as follows if you find an opportunity:
SUGGESTION: [title] | [description] | [confidence]
ACTION_ITEMS:
- [action_type]: [details]
- [action_type]: [details]
...

Valid action_types include: open_app, click, input_text, select_option, press_key, wait, scroll, navigate_to, extract_info

If no clear automation opportunity exists, respond with "NO_SUGGESTION".
"""
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM provider to generate a response."""
        try:
            if not self.llm_provider:
                raise ValueError("No LLM provider available")
            
            # Call LLM with the prompt
            response = await self.llm_provider.generate_response(
                messages=[
                    {"role": "system", "content": "You are an AI assistant that analyzes screen content to identify automation opportunities."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error calling LLM: {e}")
            raise
    
    async def _fallback_llm_call(self, prompt: str) -> str:
        """Fallback method when no LLM provider is available."""
        self.logger.warning("⚠️ Using fallback LLM call method")
        
        try:
            # Try to import and use local LLM
            import sys
            import os
            
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            try:
                from llm.llm_service import LLMService
                llm_service = LLMService(model_name="llama3.2:1b")
                await llm_service.start()
                
                response = await llm_service.generate_response(
                    messages=[
                        {"role": "system", "content": "You are an AI assistant that analyzes screen content to identify automation opportunities."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                await llm_service.stop()
                return response
                
            except ImportError:
                # If can't import LLM service, try direct Ollama API call
                self.logger.warning("⚠️ LLM service not available, trying direct Ollama API call")
                
                import aiohttp
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "llama3.2:1b",
                            "prompt": prompt,
                            "temperature": 0.7,
                            "max_tokens": 1024
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("response", "NO_SUGGESTION")
                        else:
                            raise Exception(f"Ollama API returned status {response.status}")
                
        except Exception as e:
            self.logger.error(f"❌ Error in fallback LLM call: {e}")
            self.logger.error(traceback.format_exc())
            
            # Return a safe default when all else fails
            return "NO_SUGGESTION"
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract suggestion and action items."""
        try:
            # Check for explicit NO_SUGGESTION response
            if "NO_SUGGESTION" in response:
                return {
                    "has_suggestion": False,
                    "reason": "LLM determined no actionable suggestions",
                    "raw_response": response
                }
            
            # Extract suggestion parts using regex
            suggestion_match = re.search(self.suggestion_pattern, response)
            if not suggestion_match:
                return {
                    "has_suggestion": False,
                    "reason": "No structured suggestion found in response",
                    "raw_response": response
                }
            
            # Extract title, description, and confidence
            title = suggestion_match.group(1).strip()
            description = suggestion_match.group(2).strip()
            
            try:
                confidence = float(suggestion_match.group(3).strip())
                # Ensure confidence is between 0 and 1
                confidence = max(0.0, min(1.0, confidence))
            except:
                confidence = 0.5  # Default confidence if parsing fails
            
            # Extract action items
            action_items = []
            action_items_match = re.search(self.action_items_pattern, response)
            
            if action_items_match:
                action_items_text = action_items_match.group(1).strip()
                action_item_lines = action_items_text.split('\n')
                
                for line in action_item_lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    item_match = re.search(self.action_item_line_pattern, line)
                    if item_match:
                        action_type = item_match.group(1).strip()
                        details = item_match.group(2).strip()
                        
                        # Parse details into structured format based on action type
                        if action_type == "open_app":
                            action_items.append({
                                "type": action_type,
                                "target": details
                            })
                        elif action_type == "click":
                            action_items.append({
                                "type": action_type,
                                "target": details
                            })
                        elif action_type == "input_text":
                            # Try to split into target and value
                            parts = details.split(" as ", 1)
                            if len(parts) == 2:
                                action_items.append({
                                    "type": action_type,
                                    "target": parts[0].strip(),
                                    "value": parts[1].strip().strip('"\'')
                                })
                            else:
                                action_items.append({
                                    "type": action_type,
                                    "value": details
                                })
                        else:
                            # Generic parsing for other action types
                            action_items.append({
                                "type": action_type,
                                "details": details
                            })
            
            # Create context from active app and timestamp
            context = {
                "source": "screen_analysis",
                "timestamp": datetime.now().isoformat()
            }
            
            # Create suggestion object
            suggestion = {
                "has_suggestion": True,
                "id": f"sugg_{str(uuid.uuid4())[:8]}",
                "title": title,
                "description": description,
                "confidence": confidence,
                "action_items": action_items,
                "context": context,
                "raw_response": response
            }
            
            return suggestion
            
        except Exception as e:
            self.logger.error(f"❌ Error parsing LLM response: {e}")
            self.logger.error(traceback.format_exc())
            
            return {
                "has_suggestion": False,
                "reason": f"Error parsing response: {str(e)}",
                "raw_response": response
            }
    
    async def _store_suggestion(self, extraction_result: Dict[str, Any]) -> Optional[str]:
        """Store extracted suggestion in global suggestion memory."""
        try:
            # Prepare suggestion object for storage
            suggestion = {
                "id": extraction_result.get("id"),
                "title": extraction_result.get("title"),
                "description": extraction_result.get("description"),
                "confidence": extraction_result.get("confidence"),
                "action_items": extraction_result.get("action_items"),
                "context": extraction_result.get("context")
            }
            
            # Get suggestion memory instance
            try:
                from memory.suggestion_memory import get_suggestion_memory
                memory = await get_suggestion_memory()
            except ImportError:
                self.logger.error("❌ Could not import suggestion memory")
                return None
            
            # Add suggestion to memory
            suggestion_id = await memory.add_suggestion(suggestion)
            
            if suggestion_id:
                self.logger.info(f"✅ Stored suggestion in global memory: {suggestion_id}")
                return suggestion_id
            else:
                self.logger.warning("⚠️ Failed to store suggestion in memory")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error storing suggestion: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get current extraction statistics."""
        return self.extraction_stats.copy()

# Singleton instance
_extractor_instance = None

async def get_action_extractor(llm_provider=None) -> ActionItemExtractor:
    """Get or create the global action extractor instance."""
    global _extractor_instance
    
    if _extractor_instance is None:
        _extractor_instance = ActionItemExtractor(llm_provider)
    
    return _extractor_instance

# Example usage
if __name__ == "__main__":
    async def test_action_extraction():
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
        
        # Get extractor
        extractor = await get_action_extractor()
        
        # Analyze content
        result = await extractor.analyze_screen_content(
            screen_content=screen_content,
            active_app=active_app
        )
        
        # Print results
        print(json.dumps(result, indent=2))
    
    # Run the test
    asyncio.run(test_action_extraction())