"""
Improved Agent Mode Handler - Smart Task Planning and Execution

Handles Agent mode requests with intelligent intent classification.
Only creates automation plans when the user actually wants automation,
otherwise delegates to appropriate handlers for information/suggestions.
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, Any, List, Optional
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from brain.core.brain_router import BrainResponse, ChatRequest, ChatMode

# Import intent classifier
try:
    from intent_classifier import classify_user_intent, Intent
    INTENT_CLASSIFIER_AVAILABLE = True
except ImportError:
    INTENT_CLASSIFIER_AVAILABLE = False

logger = logging.getLogger(__name__)

class ImprovedAgentModeHandler:
    """Enhanced Agent mode handler with smart intent classification"""
    
    def __init__(self):
        self.universal_handler = None
        self.ask_handler = None
        self.suggest_handler = None
        self.initialization_error = None
        
        # Initialize universal automation handler
        try:
            from universal_intelligent_automation_handler import universal_automation_handler
            self.universal_handler = universal_automation_handler
            logger.info("🤖 Universal Automation Handler loaded")
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"Failed to initialize Universal Automation Handler: {e}")
        
        # Initialize other mode handlers for delegation
        try:
            from brain.handlers.enhanced_ask_mode_handler import handle_enhanced_ask_mode
            self.ask_handler = handle_enhanced_ask_mode
            logger.info("🧠 Ask Mode Handler loaded for delegation")
        except Exception as e:
            logger.warning(f"Ask Mode Handler not available: {e}")
        
        try:
            from brain.handlers.suggest_mode_handler import handle_suggest_mode
            self.suggest_handler = handle_suggest_mode
            logger.info("💡 Suggest Mode Handler loaded for delegation")
        except Exception as e:
            logger.warning(f"Suggest Mode Handler not available: {e}")
        
        logger.info("🚀 Improved Agent Mode Handler initialized with smart intent classification")
    
    async def handle_request(self, request: ChatRequest) -> BrainResponse:
        """Handle Agent mode request with smart intent classification"""
        start_time = time.time()
        
        try:
            logger.info(f"Smart Agent mode handling request: {request.query[:100]}...")
            
            # Step 1: Classify user intent
            if INTENT_CLASSIFIER_AVAILABLE:
                intent_result = classify_user_intent(request.query)
                logger.info(f"Intent classified: {intent_result.intent.value} (confidence: {intent_result.confidence:.2f})")
                logger.info(f"Reasoning: {intent_result.reasoning}")
                
                # Step 2: Route based on intent, not just mode
                if intent_result.intent == Intent.INFORMATION_REQUEST and self.ask_handler:
                    logger.info("🧠 Delegating to Ask Mode Handler for information request")
                    return await self._delegate_to_ask_mode(request, intent_result)
                
                elif intent_result.intent == Intent.SUGGESTION_REQUEST and self.suggest_handler:
                    logger.info("💡 Delegating to Suggest Mode Handler for suggestion request")
                    return await self._delegate_to_suggest_mode(request, intent_result)
                
                elif intent_result.intent == Intent.AUTOMATION_REQUEST and self.universal_handler:
                    logger.info("🤖 Creating automation plan for automation request")
                    return await self._handle_automation_request(request, intent_result, start_time)
                
                elif intent_result.intent == Intent.UNKNOWN:
                    logger.info("❓ Unknown intent - defaulting to automation planning")
                    return await self._handle_automation_request(request, intent_result, start_time)
                
                else:
                    logger.warning(f"No handler available for intent: {intent_result.intent.value}")
                    return await self._handle_fallback_response(request, start_time)
            
            else:
                logger.warning("Intent classifier not available - defaulting to automation")
                # Fallback to original behavior if classifier not available
                if not self.universal_handler:
                    return await self._handle_fallback_response(request, start_time)
                
                return await self._handle_automation_request(request, None, start_time)
                
        except Exception as e:
            logger.error(f"Error in ImprovedAgentModeHandler: {e}")
            return await self._handle_error_response(request, start_time, str(e))
    
    async def _delegate_to_ask_mode(self, request: ChatRequest, intent_result) -> BrainResponse:
        """Delegate information requests to Ask Mode Handler"""
        try:
            # Create a temporary request with Ask mode
            ask_request = ChatRequest(
                mode=ChatMode.ASK,
                query=request.query,
                user_id=request.user_id,
                session_id=request.session_id,
                timestamp=request.timestamp,
                context=request.context
            )
            
            response = await self.ask_handler(ask_request)
            
            # Add metadata indicating this was routed from Agent mode
            response.metadata.update({
                "original_mode": "Agent",
                "routed_to": "Ask",
                "intent_classification": intent_result.intent.value,
                "intent_confidence": intent_result.confidence,
                "intent_reasoning": intent_result.reasoning
            })
            
            logger.info(f"Successfully delegated to Ask Mode (confidence: {intent_result.confidence:.2f})")
            return response
            
        except Exception as e:
            logger.error(f"Error delegating to Ask Mode: {e}")
            return await self._handle_fallback_response(request, time.time())
    
    async def _delegate_to_suggest_mode(self, request: ChatRequest, intent_result) -> BrainResponse:
        """Delegate suggestion requests to Suggest Mode Handler"""
        try:
            # Create a temporary request with Suggest mode
            suggest_request = ChatRequest(
                mode=ChatMode.SUGGEST,
                query=request.query,
                user_id=request.user_id,
                session_id=request.session_id,
                timestamp=request.timestamp,
                context=request.context
            )
            
            response = await self.suggest_handler(suggest_request)
            
            # Add metadata indicating this was routed from Agent mode
            response.metadata.update({
                "original_mode": "Agent",
                "routed_to": "Suggest",
                "intent_classification": intent_result.intent.value,
                "intent_confidence": intent_result.confidence,
                "intent_reasoning": intent_result.reasoning
            })
            
            logger.info(f"Successfully delegated to Suggest Mode (confidence: {intent_result.confidence:.2f})")
            return response
            
        except Exception as e:
            logger.error(f"Error delegating to Suggest Mode: {e}")
            return await self._handle_fallback_response(request, time.time())
    
    async def _handle_automation_request(self, request: ChatRequest, intent_result, start_time: float) -> BrainResponse:
        """Handle automation requests using Universal Automation Handler"""
        try:
            if not self.universal_handler:
                return await self._handle_fallback_response(request, start_time)
            
            # Use universal automation handler to create detailed plan
            automation_result = await self.universal_handler.create_universal_automation_plan(
                request.query, 
                request.user_id or "default_user"
            )
            
            # Check if auto-execution is appropriate for simple/safe commands
            should_auto_execute = self._should_auto_execute(request.query, automation_result)
            
            # Check for explicit execution requests (user wants immediate action)
            force_execute = self._check_force_execute(request.query)
            if force_execute:
                should_auto_execute = True
                logger.info(f"🎯 Force execution detected in query: {request.query}")
            
            if should_auto_execute and automation_result["success"]:
                logger.info(f"🚀 Auto-executing simple command: {request.query}")
                # Execute immediately for simple, safe commands
                execution_result = await self.universal_handler.handle_button_action(
                    "execute_plan", 
                    automation_result.get("plan_id"), 
                    request.user_id or "default_user"
                )
                
                if execution_result.get("success", False):
                    return BrainResponse(
                        success=True,
                        response=f"✅ **Task Completed!**\n\n{execution_result.get('response', 'Command executed successfully.')}\n\n*This was a simple command that was executed automatically.*",
                        mode_used=ChatMode.AGENT,
                        processing_time=time.time() - start_time,
                        resources_used=["memory", "llm", "automation", "execution"],
                        confidence=0.95,
                        metadata={
                            "auto_executed": True,
                            "original_plan": automation_result,
                            "execution_result": execution_result
                        }
                    )
            
            if automation_result["success"]:
                # Format successful automation plan response
                response_text = automation_result["response"]
                
                # Add interactive buttons for execution control
                interactive_data = {
                    "buttons": automation_result.get("buttons", []),
                    "plan_id": automation_result.get("plan_id"),
                    "request_type": automation_result.get("request_type", "general"),
                    "complexity_score": automation_result.get("complexity_score", 0.5),
                    "success_probability": automation_result.get("success_probability", 0.8),
                    "automation_available": automation_result.get("automation_available", False)
                }
                
                metadata = {
                    "automation_plan_created": True,
                    "requires_approval": automation_result.get("requires_approval", True),
                    "interactive_data": interactive_data,
                    "universal_planning": True,
                    "planning_method": "advanced_llm"
                }
                
                # Add intent classification metadata if available
                if intent_result:
                    metadata.update({
                        "intent_classification": intent_result.intent.value,
                        "intent_confidence": intent_result.confidence,
                        "intent_reasoning": intent_result.reasoning
                    })
                
                return BrainResponse(
                    success=True,
                    response=response_text,
                    mode_used=ChatMode.AGENT,
                    processing_time=automation_result.get("processing_time", time.time() - start_time),
                    resources_used=["memory", "llm", "automation", "universal_planning"],
                    confidence=0.9,
                    metadata=metadata
                )
            else:
                # Handle automation planning failure
                error_message = automation_result.get("response", "Failed to create automation plan")
                
                return BrainResponse(
                    success=False,
                    response=f"I encountered an issue creating your automation plan:\n\n{error_message}\n\nPlease try rephrasing your request or providing more specific details.",
                    mode_used=ChatMode.AGENT,
                    processing_time=time.time() - start_time,
                    resources_used=["llm"],
                    confidence=0.3,
                    metadata={
                        "automation_plan_created": False,
                        "error": error_message,
                        "suggestion": "Try providing more specific details about what you want to accomplish"
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in automation request handling: {e}")
            return await self._handle_fallback_response(request, start_time)
    
    def _should_auto_execute(self, query: str, automation_result: Dict[str, Any]) -> bool:
        """Determine if a command should be auto-executed based on safety criteria"""
        try:
            query_lower = query.lower().strip()
            
            # Simple, safe commands that can be auto-executed
            safe_commands = [
                # Search operations
                "search", "find", "look for", "show me",
                # Navigation
                "go to", "open", "visit", "navigate",
                # Simple actions
                "click", "press", "tap", "select",
                # Information requests that require automation
                "what is", "tell me about", "show", "display"
            ]
            
            # Unsafe commands that should always require approval
            unsafe_patterns = [
                "delete", "remove", "uninstall", "format",
                "download", "install", "purchase", "buy",
                "send", "email", "message", "post", "publish",
                "change password", "login", "logout", "sign out",
                "close", "quit", "exit", "shutdown", "restart"
            ]
            
            # Check for unsafe patterns first
            for unsafe in unsafe_patterns:
                if unsafe in query_lower:
                    return False
            
            # Check if it's a simple command
            for safe in safe_commands:
                if safe in query_lower:
                    # Additional safety checks
                    complexity_score = automation_result.get("complexity_score", 0.5)
                    success_probability = automation_result.get("success_probability", 0.8)
                    
                    # Auto-execute only if:
                    # 1. Low complexity (< 0.6)
                    # 2. High success probability (> 0.8)
                    # 3. No sensitive actions detected
                    if complexity_score < 0.6 and success_probability > 0.8:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in auto-execute check: {e}")
            return False  # Default to requiring approval
    
    def _check_force_execute(self, query: str) -> bool:
        """Check if user explicitly wants immediate execution"""
        query_lower = query.lower().strip()
        
        # Phrases that indicate user wants immediate execution
        force_phrases = [
            "just do it", "do it now", "execute immediately",
            "run it", "go ahead", "proceed", "execute",
            "do this now", "make it happen", "just execute",
            "run this", "perform this action", "carry out"
        ]
        
        return any(phrase in query_lower for phrase in force_phrases)
    
    async def _handle_error_response(self, request: ChatRequest, start_time: float, error: str) -> BrainResponse:
        """Handle errors in request processing"""
        return BrainResponse(
            success=False,
            response=f"I encountered an error while processing your request: {error}\n\nPlease try again or contact support if the issue persists.",
            mode_used=ChatMode.AGENT,
            processing_time=time.time() - start_time,
            resources_used=[],
            confidence=0.0,
            metadata={"error": error, "handler": "improved_agent_mode"}
        )
    
    async def handle_button_action(self, action: str, plan_id: str, user_id: str) -> Dict[str, Any]:
        """Handle interactive button actions (DO, DISMISS, ADJUST, SIMULATE)"""
        try:
            if not self.universal_handler:
                return {
                    "success": False,
                    "response": "❌ Universal automation handler not available.",
                    "interactive": False
                }
            
            # Delegate to universal handler
            result = await self.universal_handler.handle_button_action(action, plan_id, user_id)
            
            # Add metadata for response formatting
            result["handler"] = "improved_agent_mode"
            result["action_taken"] = action
            result["timestamp"] = time.time()
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling button action: {e}")
            return {
                "success": False,
                "response": f"❌ Error processing action: {str(e)}",
                "interactive": False,
                "error": str(e)
            }
    
    async def _handle_fallback_response(self, request: ChatRequest, start_time: float) -> BrainResponse:
        """Handle request when universal automation is not available"""
        
        response_text = f"🤖 **Agent Mode - Basic Planning**\n\n"
        response_text += f"**Task:** {request.query}\n\n"
        response_text += "I understand you want me to help with this task. However, the advanced automation system is currently not available.\n\n"
        response_text += "**What I can help with:**\n"
        response_text += "• Break down your request into steps\n"
        response_text += "• Provide guidance on how to accomplish your goal\n"
        response_text += "• Suggest specific actions you can take\n\n"
        
        # Provide basic task breakdown
        steps = await self._create_basic_task_breakdown(request.query)
        response_text += "**Suggested Approach:**\n"
        for i, step in enumerate(steps, 1):
            response_text += f"{i}. {step}\n"
        
        response_text += f"\n*Advanced automation features will be available once the system is fully loaded.*"
        
        return BrainResponse(
            success=True,
            response=response_text,
            mode_used=ChatMode.AGENT,
            processing_time=time.time() - start_time,
            resources_used=["basic_planning"],
            confidence=0.6,
            metadata={
                "automation_plan_created": False,
                "fallback_mode": True,
                "initialization_error": self.initialization_error,
                "basic_planning": True
            }
        )
    
    async def _handle_error_response(self, request: ChatRequest, start_time: float, error: str) -> BrainResponse:
        """Handle error cases with helpful guidance"""
        
        response_text = f"🚨 **Agent Mode - Error Encountered**\n\n"
        response_text += f"I encountered an error while processing your request: \"{request.query}\"\n\n"
        response_text += f"**Error Details:** {error}\n\n"
        response_text += "**Troubleshooting Steps:**\n"
        response_text += "1. Try rephrasing your request with more specific details\n"
        response_text += "2. Break down complex tasks into smaller steps\n"
        response_text += "3. Ensure your request is clear and actionable\n\n"
        response_text += "**Example requests that work well:**\n"
        response_text += "• \"Search for flights from NYC to Miami\"\n"
        response_text += "• \"Open Safari and search for Python tutorials\"\n"
        response_text += "• \"Find MacBook deals on Amazon\"\n"
        response_text += "• \"Open Calculator and compute 15 * 27\""
        
        return BrainResponse(
            success=False,
            response=response_text,
            mode_used=ChatMode.AGENT,
            processing_time=time.time() - start_time,
            resources_used=[],
            confidence=0.0,
            metadata={
                "error": error,
                "automation_plan_created": False,
                "troubleshooting_provided": True
            }
        )
    
    async def _create_basic_task_breakdown(self, query: str) -> List[str]:
        """Create basic task breakdown when automation is not available"""
        query_lower = query.lower()
        
        # Flight search
        if "flight" in query_lower and "search" in query_lower:
            return [
                "Open a web browser (Safari, Chrome, etc.)",
                "Navigate to a flight search website (Google Flights, Expedia, etc.)",
                "Enter your departure and destination cities",
                "Select your travel dates",
                "Review flight options and prices",
                "Choose the best option for your needs"
            ]
        
        # Web search
        elif "search" in query_lower or "find" in query_lower:
            search_term = query.replace("search", "").replace("find", "").strip()
            return [
                "Open a web browser",
                "Navigate to Google or your preferred search engine",
                f"Search for: {search_term}",
                "Review the search results",
                "Click on relevant links to get more information"
            ]
        
        # App usage
        elif "open" in query_lower:
            app_name = self._extract_app_name(query)
            return [
                f"Press Cmd+Space to open Spotlight",
                f"Type '{app_name}' and press Enter",
                "Wait for the application to launch",
                "Use the application for your intended purpose"
            ]
        
        # Shopping
        elif "buy" in query_lower or "shop" in query_lower or "deals" in query_lower:
            return [
                "Open a web browser",
                "Navigate to your preferred shopping website",
                "Search for the product you want",
                "Compare prices and reviews",
                "Add items to cart and proceed to checkout"
            ]
        
        # General task
        else:
            return [
                "Analyze what you want to accomplish",
                "Identify the tools or applications needed",
                "Break the task into smaller, manageable steps",
                "Execute each step systematically",
                "Verify that you've achieved your goal"
            ]
    
    def _extract_app_name(self, query: str) -> str:
        """Extract application name from query"""
        app_mapping = {
            "safari": "Safari",
            "chrome": "Chrome", 
            "firefox": "Firefox",
            "calculator": "Calculator",
            "notes": "Notes",
            "textedit": "TextEdit",
            "finder": "Finder",
            "terminal": "Terminal",
            "calendar": "Calendar"
        }
        
        query_lower = query.lower()
        for keyword, app_name in app_mapping.items():
            if keyword in query_lower:
                return app_name
        
        # Try to extract from "open X" pattern
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() == "open" and i + 1 < len(words):
                return words[i + 1].title()
        
        return "the application"

# Create singleton instance
improved_agent_mode_handler = ImprovedAgentModeHandler()

# Export the handler function
async def handle_improved_agent_mode(request: ChatRequest) -> BrainResponse:
    """Entry point for improved Agent mode handling"""
    return await improved_agent_mode_handler.handle_request(request)

async def handle_agent_button_action(action: str, plan_id: str, user_id: str) -> Dict[str, Any]:
    """Entry point for handling interactive button actions"""
    return await improved_agent_mode_handler.handle_button_action(action, plan_id, user_id)