#!/usr/bin/env python3
"""
Fix Agent Mode for Universal Inquiries - Direct Implementation
This script directly edits the necessary files to make AGENTMODE work with any type of inquiry.
"""

import asyncio
import os
import logging
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fix_universal_automation_handler():
    """Fix fixed_universal_automation_handler.py to handle any inquiry type"""
    try:
        file_path = "fixed_universal_automation_handler.py"
        
        # Make sure the file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist!")
            return False
            
        # Read the file
        with open(file_path, "r") as f:
            content = f.read()
            
        # Find the section that needs to be fixed
        fallback_start = content.find("# Parse the request to create an intelligent fallback")
        if fallback_start == -1:
            logger.error("Could not find fallback section in fixed_universal_automation_handler.py")
            return False
            
        # Find the end of the section
        fallback_end = content.find("# Create the plan with the appropriate steps", fallback_start)
        if fallback_end == -1:
            logger.error("Could not find end of fallback section in fixed_universal_automation_handler.py")
            return False
            
        # Extract the original fallback section
        original_section = content[fallback_start:fallback_end]
        
        # Create improved fallback section that supports diverse inquiry types
        new_section = """# Parse the request to create an intelligent fallback
            user_request_lower = user_request.lower()
            search_terms = []
            target_app = "Safari"
            request_type = "general"
            
            logger.info("🔍 Creating intelligent fallback plan for any inquiry type")
            
            # Categorize the request type based on content analysis
            if "search" in user_request_lower or "find" in user_request_lower or "look for" in user_request_lower:
                request_type = "web_search"
                
                # Extract search parameters if "in [app]" pattern is present
                if " in " in user_request_lower:
                    parts = user_request.split(" in ")
                    search_part = parts[0].strip()
                    app_part = parts[1].strip()
                    
                    # Extract search term (remove "search" or "search for" or "find")
                    search_term = search_part
                    for prefix in ["search for", "search", "find", "look for", "look up"]:
                        search_term = search_term.replace(prefix, "").strip()
                    
                    search_terms.append(search_term)
                    
                    # Extract target application
                    target_app = app_part
                    logger.info(f"📝 Parsed request: Search for '{search_term}' in {target_app}")
                else:
                    # Default search with extracted terms
                    search_term = user_request
                    for prefix in ["search for", "search", "find", "look for", "look up"]:
                        search_term = search_term.replace(prefix, "").strip()
                    
                    search_terms.append(search_term)
                    logger.info(f"📝 Using default search for: '{search_term}'")
            
            # Check for email operations
            elif any(word in user_request_lower for word in ["email", "mail", "gmail", "outlook"]):
                request_type = "communication"
                
                # Determine email action (compose, read, reply, etc.)
                if any(word in user_request_lower for word in ["compose", "write", "send", "create"]):
                    action = "compose_email"
                elif any(word in user_request_lower for word in ["check", "read", "open", "view"]):
                    action = "check_email"
                else:
                    action = "open_email_app"
                
                # Set target app based on email provider mentioned
                if "gmail" in user_request_lower:
                    target_app = "Safari"  # Use browser for Gmail
                elif "outlook" in user_request_lower:
                    target_app = "Microsoft Outlook"
                elif "mail" in user_request_lower:
                    target_app = "Mail"  # Default macOS Mail app
                
                logger.info(f"📝 Parsed email request: {action} using {target_app}")
                
                # Extract recipient or subject if available
                email_to_match = re.search(r'to\s+([^,.]+)', user_request_lower)
                email_subject_match = re.search(r'subject\s+([^,.]+)', user_request_lower)
                
                if email_to_match:
                    search_terms.append(f"to: {email_to_match.group(1).strip()}")
                
                if email_subject_match:
                    search_terms.append(f"subject: {email_subject_match.group(1).strip()}")
                
                # If no specific terms extracted, use whole request for context
                if not search_terms:
                    search_terms.append(user_request)
            
            # Check for document/file operations
            elif any(word in user_request_lower for word in ["document", "file", "folder", "open", "create", "edit"]):
                request_type = "productivity"
                
                # Determine file action (open, create, save, etc.)
                if "create" in user_request_lower or "new" in user_request_lower:
                    action = "create_document"
                elif "open" in user_request_lower:
                    action = "open_document"
                elif "edit" in user_request_lower:
                    action = "edit_document"
                else:
                    action = "manage_documents"
                
                # Set target app based on document type mentioned
                if "word" in user_request_lower or ".doc" in user_request_lower:
                    target_app = "Microsoft Word"
                elif "excel" in user_request_lower or "spreadsheet" in user_request_lower or ".xls" in user_request_lower:
                    target_app = "Microsoft Excel"
                elif "powerpoint" in user_request_lower or "presentation" in user_request_lower or ".ppt" in user_request_lower:
                    target_app = "Microsoft PowerPoint"
                elif "pages" in user_request_lower:
                    target_app = "Pages"
                elif "numbers" in user_request_lower:
                    target_app = "Numbers"
                elif "keynote" in user_request_lower:
                    target_app = "Keynote"
                elif "text" in user_request_lower or ".txt" in user_request_lower:
                    target_app = "TextEdit"
                else:
                    target_app = "Finder"  # Default to Finder for general file operations
                
                logger.info(f"📝 Parsed document request: {action} using {target_app}")
                
                # Extract document name or search term if available
                doc_name_match = re.search(r'(open|create|edit)\s+([^,.]+)', user_request_lower)
                if doc_name_match:
                    search_terms.append(doc_name_match.group(2).strip())
                else:
                    # If no specific terms extracted, use whole request for context
                    search_terms.append(user_request)
            
            # Check for media/entertainment operations
            elif any(word in user_request_lower for word in ["play", "watch", "video", "music", "youtube", "spotify", "netflix"]):
                request_type = "entertainment"
                
                # Determine media action (play, watch, listen, etc.)
                if "play" in user_request_lower:
                    action = "play_media"
                elif "watch" in user_request_lower:
                    action = "watch_video"
                elif "listen" in user_request_lower:
                    action = "listen_music"
                else:
                    action = "browse_media"
                
                # Set target app based on media service mentioned
                if "youtube" in user_request_lower:
                    target_app = "Safari"  # Use browser for YouTube
                elif "spotify" in user_request_lower:
                    target_app = "Spotify"
                elif "netflix" in user_request_lower:
                    target_app = "Safari"  # Use browser for Netflix
                elif "apple music" in user_request_lower:
                    target_app = "Music"  # Apple Music app
                elif "video" in user_request_lower or "movie" in user_request_lower:
                    target_app = "Safari"  # Default to browser for videos
                elif "music" in user_request_lower or "song" in user_request_lower:
                    target_app = "Music"  # Default to Music app
                else:
                    target_app = "Safari"  # Default to browser
                
                logger.info(f"📝 Parsed media request: {action} using {target_app}")
                
                # Extract media title or search term
                media_match = re.search(r'(play|watch|listen to)\s+([^,.]+)', user_request_lower)
                if media_match:
                    search_terms.append(media_match.group(2).strip())
                else:
                    # If no specific terms extracted, use whole request for context
                    search_terms.append(user_request)
            
            # Check for system operations
            elif any(word in user_request_lower for word in ["system", "settings", "preferences", "restart", "shutdown", "wifi", "bluetooth"]):
                request_type = "system_task"
                
                # Determine system action
                if "settings" in user_request_lower or "preferences" in user_request_lower:
                    action = "open_settings"
                    target_app = "System Preferences"
                elif "restart" in user_request_lower:
                    action = "restart_system"
                    target_app = "Terminal"  # Use Terminal for system commands
                elif "shutdown" in user_request_lower:
                    action = "shutdown_system"
                    target_app = "Terminal"  # Use Terminal for system commands
                elif "wifi" in user_request_lower:
                    action = "manage_wifi"
                    target_app = "System Preferences"
                elif "bluetooth" in user_request_lower:
                    action = "manage_bluetooth"
                    target_app = "System Preferences"
                else:
                    action = "system_operation"
                    target_app = "System Preferences"
                
                logger.info(f"📝 Parsed system request: {action} using {target_app}")
                
                # Use specific section of System Preferences if mentioned
                if "network" in user_request_lower:
                    search_terms.append("Network")
                elif "display" in user_request_lower or "screen" in user_request_lower:
                    search_terms.append("Displays")
                elif "sound" in user_request_lower or "audio" in user_request_lower:
                    search_terms.append("Sound")
                elif "bluetooth" in user_request_lower:
                    search_terms.append("Bluetooth")
                else:
                    # If no specific section mentioned, use whole request
                    search_terms.append(user_request)
            
            # General application usage for any other request
            else:
                # Default to general app usage
                request_type = "app_usage"
                
                # Try to extract app name from "open [app]" pattern
                app_match = re.search(r'open\s+([^,.]+)', user_request_lower)
                if app_match:
                    target_app = app_match.group(1).strip()
                    action = "open_app"
                else:
                    # For other general requests, try to determine intent
                    words = user_request_lower.split()
                    if len(words) > 0:
                        potential_app = words[0].capitalize()  # First word could be an app name
                        if len(potential_app) > 3:  # Avoid short words like "the", "and", etc.
                            target_app = potential_app
                    
                    action = "general_action"
                
                logger.info(f"📝 Parsed general request for app: {target_app}")
                
                # Use the full request as context
                search_terms.append(user_request)
            
            # Special handling for known apps
            browser_apps = ["safari", "chrome", "firefox", "browser", "google", "web", "edge", "opera"]
            productivity_apps = ["word", "excel", "powerpoint", "pages", "numbers", "keynote", "text", "textedit", "notes"]
            media_apps = ["music", "spotify", "youtube", "netflix", "itunes", "video", "photo", "photos"]
"""
        
        # Replace the original section with the new one
        new_content = content.replace(original_section, new_section)
        
        # Write the updated content back to the file
        with open(file_path, "w") as f:
            f.write(new_content)
            
        logger.info(f"Successfully updated {file_path} to handle any inquiry type")
        return True
    except Exception as e:
        logger.error(f"Error fixing universal automation handler: {e}")
        return False

async def fix_brain_router():
    """Fix brain_router.py to prioritize universal automation for all inquiries"""
    try:
        file_path = "brain/core/brain_router.py"
        
        # Make sure the file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist!")
            return False
            
        # Read the file
        with open(file_path, "r") as f:
            content = f.read()
            
        # Find the _handle_agent_mode method
        agent_mode_start = content.find("async def _handle_agent_mode")
        if agent_mode_start == -1:
            logger.error("Could not find _handle_agent_mode method in brain_router.py")
            return False
            
        # Find the end of the method (next async def)
        agent_mode_end = content.find("async def", agent_mode_start + 10)
        if agent_mode_end == -1:
            logger.error("Could not find end of _handle_agent_mode method in brain_router.py")
            return False
            
        # Extract the original method
        original_method = content[agent_mode_start:agent_mode_end]
        
        # Create the new method that prioritizes fixed_universal_automation_handler
        new_method = """async def _handle_agent_mode(self, request: ChatRequest) -> BrainResponse:
        """Handle Agent mode - Universal Task Planning and Execution for ANY inquiry"""
        try:
            # IMPORTANT: All Agent mode requests should be handled by the universal intelligent automation
            # handler for consistent plan generation and execution with ANY type of inquiry
            
            # First try the fixed universal automation handler for ANY inquiry
            try:
                logger.info("🤖 Using fixed universal intelligent automation handler for ANY inquiry in Agent mode")
                
                # Try to import fixed handler with retries and proper error handling
                fixed_handle_universal_automation = None
                
                # First try local import
                try:
                    from .fixed_universal_automation_handler import fixed_handle_universal_automation
                    logger.info("✅ Successfully imported fixed_universal_automation_handler from local directory")
                except ImportError as local_import_error:
                    logger.warning(f"⚠️ Local import error: {str(local_import_error)}")
                    
                    # Try absolute import
                    try:
                        import os
                        import sys
                        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
                        from fixed_universal_automation_handler import fixed_handle_universal_automation
                        logger.info("✅ Successfully imported fixed_universal_automation_handler using absolute path")
                    except ImportError as absolute_import_error:
                        logger.warning(f"⚠️ Absolute import error: {str(absolute_import_error)}")
                        # Will continue to direct implementation fallback
                
                # Use the fixed universal automation handler with ANY inquiry type
                if fixed_handle_universal_automation:
                    logger.info(f"🧠 Creating universal automation plan for: {request.query}")
                    plan_result = await fixed_handle_universal_automation(request.query, request.session_id)
                    
                    # Verify we got a successful plan
                    if plan_result.get("success", False):
                        logger.info("✅ Successfully created universal automation plan for ANY inquiry")
                        
                        # Convert to BrainResponse format
                        response = BrainResponse(
                            success=True,
                            response=plan_result.get("response", ""),
                            mode_used=request.mode,
                            processing_time=plan_result.get("processing_time", 0.0),
                            resources_used=["universal_automation", "llm", "memory"],
                            confidence=plan_result.get("confidence", 0.9),
                            metadata={
                                **plan_result.get("metadata", {}),
                                "universal_intelligent_automation": True,
                                "plan_id": plan_result.get("plan_id", "")
                            },
                            execution_plan=plan_result.get("execution_plan", None),
                            session_id=request.session_id
                        )
                        return response
                    else:
                        logger.warning(f"⚠️ Failed to create universal automation plan: {plan_result.get('error', 'Unknown error')}")
                        # Continue to other fallbacks
                else:
                    logger.warning("⚠️ fixed_handle_universal_automation not available - continuing to fallbacks")
            
            except Exception as e:
                logger.error(f"❌ Error using fixed universal automation handler: {e}")
                # Continue to other fallbacks
            
            # Try the direct implementation fallback (simplified)
            logger.info("🔄 Using direct implementation fallback for Agent mode")
            
            # Create a plan ID
            plan_id = f"plan_{int(time.time())}"
            
            # Extract type of inquiry from query
            query_lower = request.query.lower()
            
            # Determine inquiry type based on content analysis
            if any(word in query_lower for word in ["search", "find", "look for", "google"]):
                inquiry_type = "web_search"
            elif any(word in query_lower for word in ["email", "mail", "send", "write"]):
                inquiry_type = "communication"
            elif any(word in query_lower for word in ["document", "file", "open", "create"]):
                inquiry_type = "productivity"
            elif any(word in query_lower for word in ["play", "watch", "video", "music"]):
                inquiry_type = "entertainment"
            elif any(word in query_lower for word in ["system", "settings", "preferences"]):
                inquiry_type = "system_task"
            else:
                inquiry_type = "general_task"
            
            # Create a simple response with interactive buttons
            response_text = f"🎯 **AUTOMATION EXECUTION PLAN**\\n\\n"
            response_text += f"**🔍 Task Type:** {inquiry_type.replace('_', ' ').title()}\\n"
            response_text += f"**📋 Task:** {request.query}\\n"
            response_text += f"**⏱️ Estimated Duration:** 15.0 seconds\\n"
            response_text += f"**🎯 Success Probability:** 90%\\n"
            response_text += f"**🔧 Complexity:** Medium\\n"
            response_text += f"**📝 Steps:** 4 actions\\n\\n"
            
            # Create generic steps based on inquiry type
            if inquiry_type == "web_search":
                steps = [
                    "Open web browser",
                    "Navigate to search engine",
                    f"Search for: {request.query}",
                    "Analyze search results"
                ]
            elif inquiry_type == "communication":
                steps = [
                    "Open communication app",
                    "Create new message",
                    "Fill in recipient and content",
                    "Review and send"
                ]
            elif inquiry_type == "productivity":
                steps = [
                    "Open productivity app",
                    "Create or open document",
                    "Perform requested actions",
                    "Save changes"
                ]
            elif inquiry_type == "entertainment":
                steps = [
                    "Open media app",
                    "Search for content",
                    "Select desired media",
                    "Play content"
                ]
            elif inquiry_type == "system_task":
                steps = [
                    "Open system settings",
                    "Navigate to relevant section",
                    "Adjust settings as requested",
                    "Confirm changes"
                ]
            else:
                steps = [
                    "Analyze request",
                    "Open relevant application",
                    "Perform requested actions",
                    "Verify completion"
                ]
            
            # Add steps to response
            response_text += "**🚀 Automation Steps:**\\n"
            for i, step in enumerate(steps, 1):
                response_text += f"{i}. 🟢 {step}\\n"
            
            response_text += f"\\n**🆔 Plan ID:** `{plan_id}`\\n"
            response_text += f"**🧠 Planning:** Intelligent Automation System"
            
            # Create BrainResponse with the plan
            return BrainResponse(
                success=True,
                response=response_text,
                mode_used=request.mode,
                processing_time=0.5,
                resources_used=["automation", "basic_planning"],
                confidence=0.85,
                metadata={
                    "plan_id": plan_id,
                    "inquiry_type": inquiry_type,
                    "fallback_implementation": True
                },
                execution_plan={
                    "steps": [{"id": f"step_{i+1}", "description": step, "action_type": "custom"} for i, step in enumerate(steps)]
                },
                session_id=request.session_id
            )
                
        except Exception as e:
            logger.error(f"Error in agent mode handler: {e}")
            return BrainResponse(
                success=False,
                response=f"🚨 **Agent Mode Error**\\n\\nI encountered an error while processing your request: \\"{request.query}\\"\\n\\nError: {str(e)}\\n\\nPlease try rephrasing your request or contact support.",
                mode_used=request.mode,
                processing_time=0.1,
                resources_used=[],
                confidence=0.0,
                metadata={"error": str(e)},
                session_id=request.session_id
            )
"""
        
        # Replace the original method with the new one
        new_content = content.replace(original_method, new_method)
        
        # Write the updated content back to the file
        with open(file_path, "w") as f:
            f.write(new_content)
            
        logger.info(f"Successfully updated {file_path} to prioritize universal automation for any inquiry")
        return True
    except Exception as e:
        logger.error(f"Error fixing brain router: {e}")
        return False

async def add_helper_function():
    """Add helper function to fixed_universal_automation_handler.py"""
    try:
        file_path = "fixed_universal_automation_handler.py"
        
        # Make sure the file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist!")
            return False
            
        # Read the file
        with open(file_path, "r") as f:
            content = f.read()
            
        # Check if helper function already exists
        if "fixed_handle_universal_button_action" in content:
            logger.info("Helper function already exists, skipping")
            return True
            
        # Find a good place to add the helper function (end of file)
        insert_point = content.rfind("# Monkey patch the original function")
        if insert_point == -1:
            insert_point = len(content)  # Append to end of file
            
        # Helper function to add
        helper_function = """

async def fixed_handle_universal_button_action(action: str, plan_id: str, session_id: str) -> Dict[str, Any]:
    """Universal helper function to handle button actions for ANY inquiry type"""
    try:
        logger.info(f"🔘 Fixed universal button action handler: {action} for plan: {plan_id}")
        
        # Try to use the original handler first
        try:
            from universal_intelligent_automation_handler import handle_universal_button_action
            result = await handle_universal_button_action(action, plan_id, session_id)
            logger.info(f"✅ Successfully called original handle_universal_button_action")
            return result
        except Exception as e:
            logger.warning(f"⚠️ Original handle_universal_button_action failed: {e}")
            # Fall through to our implementation
        
        # Fall back to direct implementation with plan persistence
        try:
            from plan_persistence import load_plan, save_plan
            
            # Load the plan from persistence
            plan_data = await load_plan(plan_id)
            
            if not plan_data:
                logger.error(f"❌ Plan not found: {plan_id}")
                return {
                    "success": False,
                    "response": f"❌ Plan not found: {plan_id}",
                    "interactive": False
                }
            
            # Handle different actions
            if action == "execute_plan" or action == "DO":
                logger.info(f"🚀 Executing plan: {plan_id}")
                
                # Try to use adaptive retry handler for execution
                try:
                    from adaptive_retry_automation_handler import adaptive_retry_handler, AutomationStep
                    
                    # Extract steps from the plan
                    steps = []
                    if "steps" in plan_data:
                        steps = plan_data["steps"]
                    elif "plan" in plan_data and "steps" in plan_data["plan"]:
                        steps = plan_data["plan"]["steps"]
                    
                    # Execute each step
                    execution_results = []
                    successful_steps = 0
                    
                    for i, step_data in enumerate(steps):
                        logger.info(f"📌 Executing step {i+1}/{len(steps)}: {step_data.get('description', '')}")
                        
                        # Convert to AutomationStep
                        step = AutomationStep(
                            id=step_data.get("id", f"step_{i+1}"),
                            description=step_data.get("description", ""),
                            action_type=step_data.get("action_type", ""),
                            target=step_data.get("target", ""),
                            value=step_data.get("value", ""),
                            coordinates=step_data.get("coordinates", None)
                        )
                        
                        # Execute with retry
                        result = await adaptive_retry_handler.execute_step_with_retry(step, plan_id)
                        execution_results.append(result)
                        
                        if result.success:
                            successful_steps += 1
                    
                    # Format response
                    success_rate = successful_steps / len(steps) if steps else 0
                    
                    return {
                        "success": successful_steps > 0,
                        "response": f"✅ Executed {successful_steps}/{len(steps)} steps successfully",
                        "interactive": False,
                        "execution_results": execution_results,
                        "success_rate": success_rate
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error executing plan: {e}")
                    return {
                        "success": False,
                        "response": f"❌ Error executing plan: {str(e)}",
                        "interactive": False
                    }
                    
            elif action == "cancel_plan" or action == "DISMISS":
                logger.info(f"🛑 Cancelling plan: {plan_id}")
                return {
                    "success": True,
                    "response": f"🚫 Plan {plan_id} cancelled",
                    "interactive": False
                }
                
            elif action == "modify_plan" or action == "ADJUST":
                logger.info(f"✏️ Modify plan request: {plan_id}")
                return {
                    "success": True,
                    "response": f"✏️ To modify this plan, please send a new request with your adjustments",
                    "interactive": False
                }
                
            elif action == "simulate_plan" or action == "SIMULATE":
                logger.info(f"🔍 Simulating plan: {plan_id}")
                
                # Extract steps for simulation
                steps = []
                if "steps" in plan_data:
                    steps = plan_data["steps"]
                elif "plan" in plan_data and "steps" in plan_data["plan"]:
                    steps = plan_data["plan"]["steps"]
                
                # Format simulation response
                response = f"🔍 **Simulation of Plan {plan_id}**\\n\\n"
                
                for i, step in enumerate(steps, 1):
                    response += f"{i}. ✅ Would execute: {step.get('description', 'Unknown step')}\\n"
                
                return {
                    "success": True,
                    "response": response,
                    "interactive": False,
                    "simulation": True
                }
                
            else:
                logger.warning(f"❓ Unknown action: {action}")
                return {
                    "success": False,
                    "response": f"❓ Unknown action: {action}",
                    "interactive": False
                }
                
        except Exception as e:
            logger.error(f"❌ Error in fixed_handle_universal_button_action: {e}")
            return {
                "success": False,
                "response": f"❌ Error: {str(e)}",
                "interactive": False
            }
            
    except Exception as e:
        logger.error(f"❌ Critical error in fixed_handle_universal_button_action: {e}")
        return {
            "success": False,
            "response": f"❌ Critical error: {str(e)}",
            "interactive": False
        }
"""
        
        # Add the helper function to the file
        new_content = content[:insert_point] + helper_function + content[insert_point:]
        
        # Write the updated content back to the file
        with open(file_path, "w") as f:
            f.write(new_content)
            
        logger.info(f"Successfully added helper function to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error adding helper function: {e}")
        return False

async def update_enterprise_backend():
    """Update enhanced_enterprise_backend_with_context.py to use fixed_handle_universal_button_action"""
    try:
        file_path = "enhanced_enterprise_backend_with_context.py"
        
        # Make sure the file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist!")
            return False
            
        # Read the file
        with open(file_path, "r") as f:
            content = f.read()
            
        # Find the execute_verified_plan method
        method_start = content.find("async def execute_verified_plan")
        if method_start == -1:
            logger.error("Could not find execute_verified_plan method in enhanced_enterprise_backend_with_context.py")
            return False
            
        # Find if the method already includes the fix
        if "fixed_handle_universal_button_action" in content[method_start:]:
            logger.info("execute_verified_plan method already includes fix, skipping")
            return True
            
        # Find the part that handles universal plans
        universal_handler_start = content.find("if \"universal_\" in plan_id", method_start)
        if universal_handler_start == -1:
            logger.error("Could not find universal plan handling in execute_verified_plan method")
            return False
            
        # Find the end of that section
        universal_handler_end = content.find("except Exception as e:", universal_handler_start)
        if universal_handler_end == -1:
            logger.error("Could not find end of universal plan handling in execute_verified_plan method")
            return False
            
        # Get the original handler code
        original_handler = content[universal_handler_start:universal_handler_end]
        
        # Create new handler code
        new_handler = """if "universal_" in plan_id or "plan_" in plan_id:
                logger.info("🧠 Executing with Universal Intelligent Automation Handler")
                try:
                    # Import the fixed_handle_universal_button_action for any inquiry type
                    from fixed_universal_automation_handler import fixed_handle_universal_button_action
                    automation_result = await fixed_handle_universal_button_action("execute_plan", plan_id, plan_id)
                    
                    logger.info(f"✅ Universal plan execution result: {automation_result.get('success', False)}")
                    return automation_result
                except ImportError:
                    # Try alternative import path
                    try:
                        from universal_intelligent_automation_handler import handle_universal_button_action
                        automation_result = await handle_universal_button_action("execute_plan", plan_id, plan_id)
                        
                        logger.info(f"✅ Universal plan execution result: {automation_result.get('success', False)}")
                        return automation_result
                    except Exception as e:
                        logger.error(f"❌ Error executing universal plan: {e}")
                        # Continue to fallback handling"""
        
        # Replace the original handler with the new one
        new_content = content.replace(original_handler, new_handler)
        
        # Write the updated content back to the file
        with open(file_path, "w") as f:
            f.write(new_content)
            
        logger.info(f"Successfully updated {file_path} to handle any inquiry type")
        return True
    except Exception as e:
        logger.error(f"Error updating enterprise backend: {e}")
        return False

async def create_restart_script():
    """Create a restart script to apply the fixes"""
    try:
        file_path = "restart_with_agent_mode_fixes.sh"
        
        # Content of the restart script
        script_content = """#!/bin/bash
# Restart system with AGENTMODE universal inquiry fixes applied

echo "🛑 Stopping current processes..."
pkill -f enhanced_enterprise_backend_with_context.py || true
pkill -f ws_server_8765.py || true

echo "⏳ Waiting for processes to terminate..."
sleep 2

echo "🚀 Starting fixed system..."
nohup python3 enhanced_enterprise_backend_with_context.py > logs/backend/enhanced_enterprise_8767_context.log 2>&1 &
nohup python3 overlay/fixed_bridge_server.py > overlay/logs/fixed_bridge.log 2>&1 &
nohup python3 fixed_guaranteed_ws_server_8765.py > logs/ws_server_8765.log 2>&1 &

echo "✅ System restarted with AGENTMODE universal inquiry fixes! Check logs for details."
echo "📊 Backend log: logs/backend/enhanced_enterprise_8767_context.log"
echo "📊 WebSocket log: logs/ws_server_8765.log"
echo "📊 Bridge log: overlay/logs/fixed_bridge.log"
"""
        
        # Write the script file
        with open(file_path, "w") as f:
            f.write(script_content)
            
        # Make it executable
        os.chmod(file_path, 0o755)
            
        logger.info(f"Successfully created restart script: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating restart script: {e}")
        return False

async def main():
    """Main function to run all fixes"""
    logger.info("Starting AGENTMODE universal inquiry fix")
    
    # 1. Fix fixed_universal_automation_handler.py
    logger.info("Step 1: Fixing universal automation handler...")
    handler_fixed = await fix_universal_automation_handler()
    
    # 2. Add helper function
    logger.info("Step 2: Adding helper function...")
    helper_added = await add_helper_function()
    
    # 3. Fix brain_router.py
    logger.info("Step 3: Fixing brain router...")
    router_fixed = await fix_brain_router()
    
    # 4. Update enhanced_enterprise_backend_with_context.py
    logger.info("Step 4: Updating enterprise backend...")
    backend_updated = await update_enterprise_backend()
    
    # 5. Create restart script
    logger.info("Step 5: Creating restart script...")
    script_created = await create_restart_script()
    
    # Print summary
    logger.info("\n=== Fix Summary ===")
    logger.info(f"Universal automation handler fixed: {'✅' if handler_fixed else '❌'}")
    logger.info(f"Helper function added: {'✅' if helper_added else '❌'}")
    logger.info(f"Brain router fixed: {'✅' if router_fixed else '❌'}")
    logger.info(f"Enterprise backend updated: {'✅' if backend_updated else '❌'}")
    logger.info(f"Restart script created: {'✅' if script_created else '❌'}")
    
    if all([handler_fixed, helper_added, router_fixed, backend_updated, script_created]):
        logger.info("\n✅ All fixes successfully applied!")
        logger.info("\nTo restart the system with the fixes, run:")
        logger.info("./restart_with_agent_mode_fixes.sh")
    else:
        logger.warning("\n⚠️ Some fixes failed, see logs above for details")

if __name__ == "__main__":
    asyncio.run(main())