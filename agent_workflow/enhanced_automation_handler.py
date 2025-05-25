#!/usr/bin/env python3
"""
Enhanced Automation Handler
Integrates the enhanced automation system with the existing agent workflow.
Handles natural language commands and executes them via the automation system.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_agent_automation import EnhancedAgentAutomation

# Configure logging
os.makedirs('logs/agent_workflow', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent_workflow/enhanced_automation_handler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_automation_handler')

class EnhancedAutomationHandler:
    """
    Handles enhanced automation commands within the agent workflow system.
    Integrates natural language understanding with precise UI automation.
    """
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.automation = EnhancedAgentAutomation(llava_url)
        self.command_history = []
        self.active_session = None
        self.learning_mode = True  # Learn from successful/failed commands
        
        # Command categories for routing
        self.command_categories = {
            "automation": [
                "click", "press", "tap", "select", "hit", "touch",
                "type", "enter", "write", "input", "fill",
                "scroll", "swipe", "move",
                "drag", "drop",
                "double click", "right click", "context menu"
            ],
            "query": [
                "what", "where", "show", "list", "find", "search",
                "describe", "analyze", "identify", "detect"
            ],
            "navigation": [
                "go to", "navigate", "open", "switch to", "focus on"
            ]
        }
        
        logger.info("Enhanced Automation Handler initialized")
    
    async def create_execution_plan(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an execution plan without executing it.
        
        Args:
            instruction: Natural language instruction from user
            context: Optional context about current state
            
        Returns:
            Dict with execution plan details
        """
        try:
            logger.info(f"Creating execution plan for: '{instruction}'")
            
            # Use the automation system to generate a plan
            if self.automation:
                # Create a plan using the automation system
                parsed_command = await self.automation._parse_command(instruction)
                if not parsed_command["success"]:
                    return {
                        "success": False,
                        "error": "Could not understand command",
                        "instruction": instruction
                    }
                
                # Analyze screen to find target elements
                analysis_result = await self.automation._analyze_current_screen()
                if not analysis_result or "elements" not in analysis_result:
                    return {
                        "success": False,
                        "error": "Could not analyze screen",
                        "instruction": instruction
                    }
                
                # Find target elements
                element_matches = await self.automation._find_target_elements(
                    parsed_command, 
                    analysis_result["elements"]
                )
                
                # Always create a plan, even with weak matches - let the user decide
                if not element_matches:
                    # Create a fallback plan with manual target selection
                    logger.warning(f"No good target matches found for '{parsed_command.get('target_description', 'unknown')}', creating fallback plan")
                    
                    # Try to find ANY text fields or clickable elements as fallback
                    fallback_elements = [
                        elem for elem in analysis_result["elements"]
                        if elem.get("element_type") in ["text_field", "input_field", "button", "text_element"]
                    ][:5]  # Take top 5 as options
                    
                    if fallback_elements:
                        # Use the first fallback element with low confidence
                        element_matches = [{
                            **fallback_elements[0],
                            "confidence": 0.3,  # Low confidence to indicate uncertainty
                            "match_reason": "fallback_best_guess",
                            "alternatives": fallback_elements[1:4]  # Provide alternatives
                        }]
                        logger.info(f"Created fallback plan with {len(element_matches)} weak matches")
                    else:
                        # Last resort: create a generic screen center plan
                        element_matches = [{
                            "element_text": "Screen center (manual guidance needed)",
                            "element_type": "fallback_target",
                            "position": {"x": 640, "y": 360},  # Screen center approximation
                            "confidence": 0.1,
                            "match_reason": "no_targets_found",
                            "alternatives": []
                        }]
                        logger.warning("Created minimal fallback plan - user guidance required")
                
                # Create execution plan
                execution_plan = await self.automation._create_execution_plan(parsed_command, element_matches)
                
                return {
                    "success": True,
                    "execution_plan": execution_plan,
                    "instruction": instruction,
                    "confidence_score": element_matches[0]["confidence"] if element_matches else 0
                }
            else:
                return {
                    "success": False,
                    "error": "Automation system not available",
                    "instruction": instruction
                }
                
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": f"Plan creation failed: {str(e)}",
                "instruction": instruction
            }

    async def handle_user_instruction(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle user instruction and route to appropriate handler.
        
        Args:
            instruction: Natural language instruction from user
            context: Optional context about current state
            
        Returns:
            Dict with execution results and metadata
        """
        try:
            logger.info(f"Handling user instruction: '{instruction}'")
            
            # Record the instruction
            command_record = {
                "timestamp": datetime.now().isoformat(),
                "instruction": instruction,
                "context": context,
                "result": None,
                "success": False,
                "category": None
            }
            
            # Categorize the instruction
            category = self._categorize_instruction(instruction)
            command_record["category"] = category
            
            # Route to appropriate handler
            if category == "automation":
                result = await self._handle_automation_command(instruction, context)
            elif category == "query":
                result = await self._handle_query_command(instruction, context)
            elif category == "navigation":
                result = await self._handle_navigation_command(instruction, context)
            else:
                # Try automation as fallback
                logger.info(f"Unknown category, trying automation for: {instruction}")
                result = await self._handle_automation_command(instruction, context)
            
            # Update command record
            command_record["result"] = result
            command_record["success"] = result.get("success", False)
            
            # Learn from the result if enabled
            if self.learning_mode:
                await self._learn_from_result(command_record)
            
            # Add to history
            self.command_history.append(command_record)
            
            # Limit history size
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]
            
            return {
                "success": result.get("success", False),
                "category": category,
                "execution_result": result,
                "instruction": instruction,
                "timestamp": command_record["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Error handling instruction '{instruction}': {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "instruction": instruction,
                "category": "error"
            }
    
    def _categorize_instruction(self, instruction: str) -> str:
        """Categorize instruction to route to appropriate handler"""
        instruction_lower = instruction.lower().strip()
        
        # Check each category
        for category, keywords in self.command_categories.items():
            for keyword in keywords:
                if keyword in instruction_lower:
                    return category
        
        # Default to automation for action-oriented commands
        action_words = ["do", "make", "perform", "execute", "run"]
        if any(word in instruction_lower for word in action_words):
            return "automation"
        
        return "unknown"
    
    async def _handle_automation_command(self, instruction: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle automation commands via the enhanced automation system"""
        try:
            logger.info(f"Executing automation command: {instruction}")
            
            # Check if we have a stored plan with pre-parsed details
            if context and "stored_plan" in context:
                stored_plan = context["stored_plan"]
                logger.info(f"Using stored plan details: {stored_plan.get('action', 'unknown')} action")
                
                # Execute with stored plan details to avoid re-parsing
                result = await self.automation.execute_command(instruction, stored_plan)
            else:
                # Execute the command using enhanced automation (normal flow)
                result = await self.automation.execute_command(instruction)
            
            # Add additional metadata
            result["handler"] = "automation"
            result["instruction_type"] = "automation_command"
            
            if result["success"]:
                logger.info(f"Automation command succeeded: {instruction}")
            else:
                logger.warning(f"Automation command failed: {instruction} - {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in automation command: {e}")
            return {
                "success": False,
                "error": str(e),
                "handler": "automation"
            }
    
    async def _handle_query_command(self, instruction: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle query commands that ask about screen content"""
        try:
            logger.info(f"Handling query command: {instruction}")
            
            # Get current screen elements
            elements = await self.automation.get_available_elements()
            
            instruction_lower = instruction.lower()
            
            if "what" in instruction_lower and "button" in instruction_lower:
                # List available buttons
                buttons = [elem for elem in elements if elem.get("element_type") == "button"]
                return {
                    "success": True,
                    "handler": "query",
                    "query_type": "list_buttons",
                    "result": f"Found {len(buttons)} buttons: " + ", ".join([elem.get("element_text", "unnamed") for elem in buttons[:10]]),
                    "elements": buttons
                }
            
            elif "what" in instruction_lower and ("element" in instruction_lower or "available" in instruction_lower):
                # List all available elements
                return {
                    "success": True,
                    "handler": "query",
                    "query_type": "list_elements",
                    "result": f"Found {len(elements)} interactive elements on screen",
                    "elements": elements[:20]  # Limit to first 20
                }
            
            elif "where" in instruction_lower:
                # Find specific element
                target = instruction_lower.replace("where", "").replace("is", "").strip()
                if target:
                    matching_elements = []
                    for elem in elements:
                        if target in elem.get("element_text", "").lower():
                            matching_elements.append(elem)
                    
                    if matching_elements:
                        return {
                            "success": True,
                            "handler": "query",
                            "query_type": "find_element",
                            "result": f"Found {len(matching_elements)} elements matching '{target}'",
                            "elements": matching_elements
                        }
                    else:
                        return {
                            "success": False,
                            "handler": "query",
                            "query_type": "find_element",
                            "result": f"No elements found matching '{target}'",
                            "available_elements": [elem.get("element_text", "unnamed") for elem in elements[:10]]
                        }
            
            # Default query response
            return {
                "success": True,
                "handler": "query",
                "query_type": "general",
                "result": f"Screen analysis complete. Found {len(elements)} interactive elements.",
                "instruction": instruction
            }
            
        except Exception as e:
            logger.error(f"Error in query command: {e}")
            return {
                "success": False,
                "error": str(e),
                "handler": "query"
            }
    
    async def _handle_navigation_command(self, instruction: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle navigation commands"""
        try:
            logger.info(f"Handling navigation command: {instruction}")
            
            instruction_lower = instruction.lower()
            
            if "go to" in instruction_lower or "navigate to" in instruction_lower:
                # Extract target
                target = instruction_lower.replace("go to", "").replace("navigate to", "").strip()
                
                # Try to find and click the target
                result = await self.automation.execute_command(f"click {target}")
                result["handler"] = "navigation"
                result["navigation_type"] = "go_to"
                return result
            
            elif "open" in instruction_lower:
                # Try to open something
                target = instruction_lower.replace("open", "").strip()
                result = await self.automation.execute_command(f"click {target}")
                result["handler"] = "navigation"
                result["navigation_type"] = "open"
                return result
            
            # Default to automation handling
            result = await self._handle_automation_command(instruction, context)
            result["handler"] = "navigation"
            return result
            
        except Exception as e:
            logger.error(f"Error in navigation command: {e}")
            return {
                "success": False,
                "error": str(e),
                "handler": "navigation"
            }
    
    async def _learn_from_result(self, command_record: Dict[str, Any]):
        """Learn from command execution results to improve future performance"""
        try:
            instruction = command_record["instruction"]
            success = command_record["success"]
            result = command_record["result"]
            
            # Simple learning: track successful patterns
            if success:
                logger.debug(f"Learning: Successful command pattern - {instruction}")
                # Could implement pattern recognition here
            else:
                logger.debug(f"Learning: Failed command - {instruction}, reason: {result.get('error', 'unknown')}")
                # Could implement failure analysis here
            
            # For now, just log for future ML implementation
            
        except Exception as e:
            logger.debug(f"Error in learning system: {e}")
    
    async def get_command_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions based on current screen content and history"""
        try:
            suggestions = []
            
            # Get current screen elements
            elements = await self.automation.get_available_elements()
            
            partial_lower = partial_command.lower()
            
            # Suggest clickable elements
            if "click" in partial_lower:
                for elem in elements[:5]:  # Top 5 elements
                    text = elem.get("element_text", "")
                    if text and len(text) > 1:
                        suggestions.append(f"click the {text}")
            
            # Suggest typing commands for text fields
            elif "type" in partial_lower:
                text_fields = [elem for elem in elements if elem.get("element_type") in ["textfield", "input"]]
                for field in text_fields[:3]:
                    text = field.get("element_text", "text field")
                    suggestions.append(f"type [your text] in the {text}")
            
            # Suggest based on successful command history
            for record in reversed(self.command_history[-10:]):  # Last 10 commands
                if record["success"] and partial_lower in record["instruction"].lower():
                    suggestions.append(record["instruction"])
            
            return list(set(suggestions))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting command suggestions: {e}")
            return []
    
    async def get_screen_summary(self) -> Dict[str, Any]:
        """Get a summary of current screen content for user awareness"""
        try:
            elements = await self.automation.get_available_elements()
            
            # Categorize elements
            element_types = {}
            for elem in elements:
                elem_type = elem.get("element_type", "unknown")
                element_types[elem_type] = element_types.get(elem_type, 0) + 1
            
            # Get notable elements
            buttons = [elem for elem in elements if elem.get("element_type") == "button"][:5]
            text_fields = [elem for elem in elements if elem.get("element_type") in ["textfield", "input"]][:3]
            
            return {
                "total_elements": len(elements),
                "element_types": element_types,
                "notable_buttons": [elem.get("element_text", "unnamed") for elem in buttons],
                "text_fields": [elem.get("element_text", "text field") for elem in text_fields],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting screen summary: {e}")
            return {"error": str(e)}
    
    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent command history"""
        return self.command_history[-limit:] if self.command_history else []
    
    def stop(self):
        """Stop the automation handler"""
        if self.automation:
            self.automation.stop()
        logger.info("Enhanced Automation Handler stopped")

# Test and demo functions
async def test_automation_handler():
    """Test the automation handler with sample commands"""
    handler = EnhancedAutomationHandler()
    
    test_commands = [
        "what buttons are available?",
        "click the submit button",
        "type hello world in the search box",
        "where is the save button?",
        "scroll down"
    ]
    
    print("🤖 Testing Enhanced Automation Handler")
    print("=" * 50)
    
    for command in test_commands:
        print(f"\n🔍 Testing: '{command}'")
        result = await handler.handle_user_instruction(command)
        
        if result["success"]:
            print(f"✅ Success: {result.get('execution_result', {}).get('action', 'completed')}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Small delay between commands
        await asyncio.sleep(1)
    
    # Show screen summary
    print(f"\n📊 Screen Summary:")
    summary = await handler.get_screen_summary()
    print(json.dumps(summary, indent=2))
    
    handler.stop()

async def main():
    """Main function for testing or CLI usage"""
    if len(sys.argv) > 1:
        # CLI mode - execute single command
        command = " ".join(sys.argv[1:])
        handler = EnhancedAutomationHandler()
        
        print(f"🤖 Executing: '{command}'")
        result = await handler.handle_user_instruction(command)
        
        if result["success"]:
            print("✅ Command executed successfully")
            if "execution_result" in result:
                exec_result = result["execution_result"]
                if "target_element" in exec_result:
                    target = exec_result["target_element"]
                    print(f"   Target: {target.get('element_text', 'unknown')} ({target.get('element_type', 'unknown')})")
                if "confidence" in exec_result:
                    print(f"   Confidence: {exec_result['confidence']:.2f}")
        else:
            print("❌ Command failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
            # Show available elements if target not found
            if "available_elements" in result.get("execution_result", {}):
                available = result["execution_result"]["available_elements"]
                if available:
                    print(f"   Available elements: {', '.join(available[:5])}")
        
        handler.stop()
    else:
        # Test mode
        await test_automation_handler()

if __name__ == "__main__":
    asyncio.run(main())