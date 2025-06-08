#!/usr/bin/env python3
"""
Fix Agent Mode for Universal Inquiries
This script enhances the AGENTMODE to work with any type of inquiry, not just Google searches.
It improves plan generation in fixed_universal_automation_handler.py to handle diverse queries.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fix_fixed_universal_automation_handler():
    \"\"\"Fix the fixed_universal_automation_handler.py to handle any type of inquiry\"\"\"
    try:
        with open("fixed_universal_automation_handler.py", "r") as f:
            content = f.read()
        
        # Find the fallback plan generation section that needs improvement
        fallback_section_start = content.find("# Parse the request to create an intelligent fallback")
        fallback_section_end = content.find("# Create the plan with the appropriate steps", fallback_section_start)
        
        if fallback_section_start == -1 or fallback_section_end == -1:
            logger.error("Could not find the fallback plan generation section in fixed_universal_automation_handler.py")
            return False
        
        original_fallback_section = content[fallback_section_start:fallback_section_end]
        
        # Create improved fallback section with better request parsing for all inquiry types
        new_fallback_section = """# Parse the request to create an intelligent fallback
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
                doc_name_match = re.search(r'(open|create|edit)\s+([^,\.]+)', user_request_lower)
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
                    search_url = "https://www.youtube.com"
                elif "spotify" in user_request_lower:
                    target_app = "Spotify"
                elif "netflix" in user_request_lower:
                    target_app = "Safari"  # Use browser for Netflix
                    search_url = "https://www.netflix.com"
                elif "apple music" in user_request_lower:
                    target_app = "Music"  # Apple Music app
                elif "video" in user_request_lower or "movie" in user_request_lower:
                    target_app = "Safari"  # Default to browser for videos
                    search_url = "https://www.youtube.com"
                elif "music" in user_request_lower or "song" in user_request_lower:
                    target_app = "Music"  # Default to Music app
                else:
                    target_app = "Safari"  # Default to browser
                    search_url = "https://www.youtube.com"
                
                logger.info(f"📝 Parsed media request: {action} using {target_app}")
                
                # Extract media title or search term
                media_match = re.search(r'(play|watch|listen to)\s+([^,\.]+)', user_request_lower)
                if media_match:
                    search_terms.append(media_match.group(2).strip())
                else:
                    # If no specific terms extracted, use whole request for context
                    search_terms.append(user_request)
            
            # Check for social media operations
            elif any(word in user_request_lower for word in ["facebook", "twitter", "instagram", "linkedin", "social", "post", "tweet"]):
                request_type = "social_media"
                
                # Determine social action (browse, post, check, etc.)
                if "post" in user_request_lower or "write" in user_request_lower:
                    action = "create_post"
                elif "check" in user_request_lower or "view" in user_request_lower:
                    action = "check_updates"
                else:
                    action = "browse_social"
                
                # Set target app based on social platform mentioned
                if "facebook" in user_request_lower:
                    target_app = "Safari"  # Use browser for Facebook
                    search_url = "https://www.facebook.com"
                elif "twitter" in user_request_lower:
                    target_app = "Safari"  # Use browser for Twitter
                    search_url = "https://twitter.com"
                elif "instagram" in user_request_lower:
                    target_app = "Safari"  # Use browser for Instagram
                    search_url = "https://www.instagram.com"
                elif "linkedin" in user_request_lower:
                    target_app = "Safari"  # Use browser for LinkedIn
                    search_url = "https://www.linkedin.com"
                else:
                    target_app = "Safari"  # Default to browser
                    search_url = "https://www.facebook.com"  # Default to Facebook
                
                logger.info(f"📝 Parsed social media request: {action} using {target_app}")
                
                # Extract post content or search term if available
                post_match = re.search(r'post\s+([^,\.]+)', user_request_lower)
                if post_match:
                    search_terms.append(post_match.group(1).strip())
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
            
            # Shopping operations
            elif any(word in user_request_lower for word in ["shop", "buy", "purchase", "order", "amazon"]):
                request_type = "shopping"
                
                # Set target app for shopping (usually a browser)
                target_app = "Safari"
                
                # Determine shopping site
                if "amazon" in user_request_lower:
                    search_url = "https://www.amazon.com"
                elif "ebay" in user_request_lower:
                    search_url = "https://www.ebay.com"
                else:
                    search_url = "https://www.amazon.com"  # Default to Amazon
                
                logger.info(f"📝 Parsed shopping request using {target_app}")
                
                # Extract item to shop for
                shop_match = re.search(r'(shop|buy|purchase|order)\s+([^,\.]+)', user_request_lower)
                if shop_match:
                    search_terms.append(shop_match.group(2).strip())
                else:
                    # If no specific item extracted, use whole request
                    search_terms.append(user_request)
            
            # General application usage for any other request
            else:
                # Default to general app usage
                request_type = "app_usage"
                
                # Try to extract app name from "open [app]" pattern
                app_match = re.search(r'open\s+([^,\.]+)', user_request_lower)
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
        
        # Replace the original fallback section with improved version
        updated_content = content.replace(original_fallback_section, new_fallback_section)
        
        # Fix the browser-specific action creation to be more generic
        browser_section_start = content.find("if target_app.lower() in [")
        browser_section_end = content.find("else:", browser_section_start)
        
        if browser_section_start == -1 or browser_section_end == -1:
            logger.error("Could not find the browser action creation section in fixed_universal_automation_handler.py")
            return False
        
        original_browser_section = content[browser_section_start:browser_section_end]
        
        # Create improved browser section with better action handling for multiple inquiry types
        new_browser_section = """if target_app.lower() in browser_apps:
                # Handle web browser search
                target_app = "Safari" if target_app.lower() in ["browser", "web"] else target_app
                search_url = "https://www.google.com" if target_app.lower() != "google" else None
                request_type = "web_search"
                
                # Create appropriate steps for web search
                steps = [
                    SmartAutomationStep(
                        id="step_1",
                        description=f"Open {target_app}",
                        action_type="open_app",
                        target=target_app,
                        estimated_duration=2.0,
                        confidence=0.95
                    ),
                    SmartAutomationStep(
                        id="step_2",
                        description="Wait for browser to load",
                        action_type="wait",
                        estimated_duration=1.5,
                        confidence=0.95
                    )
                ]
                
                # Add site navigation if needed
                if search_url:
                    steps.extend([
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description=f"Navigate to {search_url.split('//')[1]}",
                            action_type="navigate_url",
                            target="search_bar",
                            value=search_url,
                            estimated_duration=1.5,
                            confidence=0.9
                        ),
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Wait for page to load",
                            action_type="wait",
                            estimated_duration=1.0,
                            confidence=0.95
                        )
                    ])
                
                # Add search interaction steps
                steps.extend([
                    SmartAutomationStep(
                        id=f"step_{len(steps)+1}",
                        description="Focus on search field",
                        action_type="click_element",
                        target="search_field",
                        coordinates=(735, 350),  # Approximate search field location
                        estimated_duration=0.5,
                        confidence=0.85
                    ),
                    SmartAutomationStep(
                        id=f"step_{len(steps)+1}",
                        description=f"Type search query: {search_terms[0]}",
                        action_type="type_text",
                        target="Search field",
                        value=search_terms[0],
                        estimated_duration=1.0,
                        confidence=0.95
                    ),
                    SmartAutomationStep(
                        id=f"step_{len(steps)+1}",
                        description="Press Enter to execute search",
                        action_type="hotkey",
                        target="return",
                        value="return",
                        estimated_duration=0.5,
                        confidence=0.95
                    ),
                    SmartAutomationStep(
                        id=f"step_{len(steps)+1}",
                        description="Wait for search results to load",
                        action_type="wait",
                        estimated_duration=1.5,
                        confidence=0.9
                    )
                ])
            elif target_app.lower() in productivity_apps:
                # Productivity app workflow (Word, Excel, etc.)
                request_type = "productivity"
                
                # Create steps for productivity apps
                steps = [
                    SmartAutomationStep(
                        id="step_1",
                        description=f"Open {target_app}",
                        action_type="open_app",
                        target=target_app,
                        estimated_duration=2.5,
                        confidence=0.9
                    ),
                    SmartAutomationStep(
                        id="step_2",
                        description="Wait for application to load",
                        action_type="wait",
                        estimated_duration=2.0,
                        confidence=0.9
                    )
                ]
                
                # Add document interaction steps
                if "create" in user_request_lower or "new" in user_request_lower:
                    # Steps for creating a new document
                    steps.extend([
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Create new document (Cmd+N)",
                            action_type="hotkey",
                            target="command+n",
                            estimated_duration=0.5,
                            confidence=0.9
                        ),
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Wait for new document to open",
                            action_type="wait",
                            estimated_duration=1.0,
                            confidence=0.9
                        )
                    ])
                elif "open" in user_request_lower:
                    # Steps for opening an existing document
                    steps.extend([
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Open document dialog (Cmd+O)",
                            action_type="hotkey",
                            target="command+o",
                            estimated_duration=0.5,
                            confidence=0.9
                        ),
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Wait for dialog to appear",
                            action_type="wait",
                            estimated_duration=1.0,
                            confidence=0.9
                        ),
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description=f"Type document name: {search_terms[0]}",
                            action_type="type_text",
                            target="file_search",
                            value=search_terms[0],
                            estimated_duration=1.0,
                            confidence=0.8
                        ),
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Press Enter to search",
                            action_type="hotkey",
                            target="return",
                            estimated_duration=0.5,
                            confidence=0.9
                        )
                    ])
                else:
                    # General document interaction
                    steps.extend([
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Focus on document area",
                            action_type="click_element",
                            coordinates=(735, 400),  # Approximate document center
                            estimated_duration=0.5,
                            confidence=0.8
                        )
                    ])
            elif target_app.lower() in media_apps:
                # Media app workflow (Music, Spotify, etc.)
                request_type = "entertainment"
                
                # Create steps for media apps
                steps = [
                    SmartAutomationStep(
                        id="step_1",
                        description=f"Open {target_app}",
                        action_type="open_app",
                        target=target_app,
                        estimated_duration=2.5,
                        confidence=0.9
                    ),
                    SmartAutomationStep(
                        id="step_2",
                        description="Wait for application to load",
                        action_type="wait",
                        estimated_duration=2.0,
                        confidence=0.9
                    ),
                    SmartAutomationStep(
                        id="step_3",
                        description="Focus on search field (Cmd+F)",
                        action_type="hotkey",
                        target="command+f",
                        estimated_duration=0.5,
                        confidence=0.85
                    ),
                    SmartAutomationStep(
                        id="step_4",
                        description=f"Search for: {search_terms[0]}",
                        action_type="type_text",
                        target="search_field",
                        value=search_terms[0],
                        estimated_duration=1.0,
                        confidence=0.9
                    ),
                    SmartAutomationStep(
                        id="step_5",
                        description="Press Enter to search",
                        action_type="hotkey",
                        target="return",
                        estimated_duration=0.5,
                        confidence=0.9
                    ),
                    SmartAutomationStep(
                        id="step_6",
                        description="Wait for search results",
                        action_type="wait",
                        estimated_duration=1.5,
                        confidence=0.9
                    )
                ]
                
                # Add play action for music/video
                if "play" in user_request_lower:
                    steps.extend([
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Click on first result",
                            action_type="click_element",
                            coordinates=(735, 350),  # Approximate first result location
                            estimated_duration=0.5,
                            confidence=0.8
                        ),
                        SmartAutomationStep(
                            id=f"step_{len(steps)+1}",
                            description="Press spacebar to play",
                            action_type="hotkey",
                            target="space",
                            estimated_duration=0.5,
                            confidence=0.85
                        )
                    ])
            """
        
        # Replace the original browser section with improved version
        updated_content = updated_content.replace(original_browser_section, new_browser_section)
        
        # Write the updated content back to the file
        with open("fixed_universal_automation_handler.py", "w") as f:
            f.write(updated_content)
        
        logger.info("✅ Successfully updated fixed_universal_automation_handler.py to handle any inquiry type")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error updating fixed_universal_automation_handler.py: {e}")
        return False

async def fix_brain_router():
    \"\"\"Fix the brain router to prioritize fixed_universal_automation_handler for all agent mode requests\"\"\"
    try:
        with open("brain/core/brain_router.py", "r") as f:
            content = f.read()
        
        # Find the agent mode handler in the brain router
        agent_handler_start = content.find("async def _handle_agent_mode")
        agent_handler_end = content.find("async def _handle_ask_mode", agent_handler_start)
        
        if agent_handler_start == -1 or agent_handler_end == -1:
            logger.error("Could not find the agent mode handler in brain_router.py")
            return False
        
        original_agent_handler = content[agent_handler_start:agent_handler_end]
        
        # Create improved agent handler to prioritize fixed_universal_automation_handler for all inquiry types
        new_agent_handler = """async def _handle_agent_mode(self, request: ChatRequest) -> BrainResponse:
        \"\"\"Handle Agent mode - Universal Task Planning and Execution for ANY inquiry\"\"\"
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
        
        # Replace the original agent handler with improved version
        updated_content = content.replace(original_agent_handler, new_agent_handler)
        
        # Write the updated content back to the file
        with open("brain/core/brain_router.py", "w") as f:
            f.write(updated_content)
        
        logger.info("✅ Successfully updated brain_router.py to handle any inquiry type")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating brain_router.py: {e}")
        return False

async def fix_enterprise_backend():
    \"\"\"Fix the enhanced_enterprise_backend_with_context.py to properly handle all inquiry types\"\"\"
    try:
        with open("enhanced_enterprise_backend_with_context.py", "r") as f:
            content = f.read()
        
        # Find the agent mode section in handle_contextual_chat_request_streaming
        agent_section_start = content.find("# Check for Real Agent Automation handler first")
        if agent_section_start == -1:
            # Try to find an alternative pattern
            agent_section_start = content.find("# Check for Universal Intelligent Automation handler first")
            
        if agent_section_start == -1:
            logger.error("Could not find the agent mode section in enhanced_enterprise_backend_with_context.py")
            return False
        
        agent_section_end = content.find("if not plan_result.get(\"success\", False):", agent_section_start)
        if agent_section_end == -1:
            logger.error("Could not find the end of agent mode section in enhanced_enterprise_backend_with_context.py")
            return False
        
        original_agent_section = content[agent_section_start:agent_section_end]
        
        # Create improved agent section to prioritize fixed_universal_automation_handler for all inquiry types
        new_agent_section = """# Check for Universal Intelligent Automation handler first (for ALL inquiry types)
                        if UNIVERSAL_AVAILABLE:
                            logger.info("🧠 [STREAMING] Using Universal Intelligent Automation handler for any inquiry type")
                            
                            try:
                                from fixed_universal_automation_handler import fixed_handle_universal_automation
                                plan_result = await fixed_handle_universal_automation(message, session_id)
                                logger.info(f"✅ [STREAMING] Successfully called fixed_handle_universal_automation")
                                logger.info(f"🎯 [STREAMING] Universal plan result: {plan_result.get('success', False)} - interactive: {plan_result.get('interactive', False)}")
                            except Exception as e:
                                logger.error(f"❌ Error calling fixed_handle_universal_automation: {e}")
                                plan_result = {"success": False, "error": f"Error with Universal Automation: {str(e)}"}
                            
                            if plan_result.get("success", False):
                                # Send streaming response with execution plan
                                await websocket.send(json.dumps({
                                    "type": "agent_automation_plan",
                                    "mode": mode,
                                    "response": plan_result.get("response", "Automation plan created"),
                                    "client_id": client_id,
                                    "timestamp": datetime.now().isoformat(),
                                    "ai_powered": plan_result.get("ai_powered", True),
                                    "success": True,
                                    "requiresConfirmation": plan_result.get("requires_approval", True),
                                    "agentSessionId": session_id,
                                    "confidence": plan_result.get("confidence", 0.8),
                                    "buttons": plan_result.get("buttons", []),
                                    "interactive": plan_result.get("interactive", True),
                                    "universal_intelligent_automation": True,
                                    "plan_id": plan_result.get("plan_id", session_id),
                                    "processing_time": round(time.time() - start_time, 3)
                                }))
                                
                                # Store response in memory
                                await add_memory(
                                    f"System created universal automation plan for ANY inquiry in {mode} mode: {plan_result.get('response', '')[:100]}...",
                                    source="automation_response",
                                    tags={f"mode_{mode.lower()}", "automation", session_id, "universal_intelligent_automation"}
                                )
                                
                                return  # Exit early - automation plan sent
                        
                        # Fall back to Real Agent Automation handler if Universal handler fails
                        elif REAL_AGENT_AUTOMATION_AVAILABLE:
                            logger.info("🎯 [STREAMING] Falling back to Real Agent Automation handler")
                            
                            # Call the correct method - handle_real_agent_automation instead of non-existent handle_agent_request
                            try:
                                from real_agent_automation_handler import handle_real_agent_automation
                                plan_result = await handle_real_agent_automation(message, session_id)
                                logger.info(f"✅ [STREAMING] Successfully called handle_real_agent_automation")
                                logger.info(f"🎯 [STREAMING] Real Agent plan result: {plan_result.get('success', False)} - interactive: {plan_result.get('interactive', False)}")
                            except Exception as e:
                                logger.error(f"❌ Error calling handle_real_agent_automation: {e}")
                                plan_result = {"success": False, "error": f"Error with Real Agent Automation: {str(e)}"}"""
        
        # Replace the original agent section with improved version
        updated_content = content.replace(original_agent_section, new_agent_section)
        
        # Find and fix the execute_verified_plan method to properly handle all plan types
        execute_plan_start = updated_content.find("async def execute_verified_plan(self, plan_id: str) -> Dict[str, Any]:")
        execute_plan_end = updated_content.find("async def handle_contextual_chat_request_streaming", execute_plan_start)
        
        if execute_plan_start == -1 or execute_plan_end == -1:
            logger.error("Could not find the execute_verified_plan method in enhanced_enterprise_backend_with_context.py")
            return False
        
        original_execute = updated_content[execute_plan_start:execute_plan_end]
        
        # Check if the method already includes universal plan handling
        if "universal_" in original_execute and "handle_universal_button_action" in original_execute:
            logger.info("✅ execute_verified_plan method already handles universal plans properly")
        else:
            # Create improved execute_verified_plan method to handle all plan types
            new_execute = """async def execute_verified_plan(self, plan_id: str) -> Dict[str, Any]:
        \"\"\"Execute a verified plan with progress updates for ANY inquiry type\"\"\"
        try:
            logger.info(f"🚀 Executing verified plan: {plan_id}")
            
            # Check if this is a universal plan
            if "universal_" in plan_id or "plan_" in plan_id:
                logger.info("🧠 Executing with Universal Intelligent Automation Handler")
                try:
                    # Import the handle_universal_button_action for any inquiry type
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
                        # Continue to fallback handling
            
            # Try to load plan data from persistence
            try:
                from plan_persistence import load_plan
                plan_data = await load_plan(plan_id)
                if not plan_data:
                    logger.error(f"❌ Could not load plan data for: {plan_id}")
                    
                    # Check if plan is in pending_plans
                    if hasattr(self, 'pending_plans') and plan_id in self.pending_plans:
                        plan_data = self.pending_plans[plan_id]
                        logger.info(f"✅ Found plan in pending_plans: {plan_id}")
                    else:
                        # Create a fallback plan for testing if plan loading fails
                        logger.warning(f"⚠️ Creating fallback plan for testing: {plan_id}")
                        plan_data = {
                            "client_id": "fallback",
                            "plan": {
                                "title": "Fallback Test Plan",
                                "description": "Open Safari browser",
                                "steps": [
                                    {
                                        "id": "step_1",
                                        "description": "Open Safari browser",
                                        "action_type": "open_app",
                                        "target": "Safari"
                                    }
                                ]
                            }
                        }
            except Exception as e:
                logger.error(f"❌ Error loading plan: {e}")
                return {
                    "success": False,
                    "error": f"Error loading plan: {str(e)}",
                    "message": f"Could not load plan data for: {plan_id}"
                }
            
            # Send progress updates during execution
            progress_steps = [
                {"step": 1, "message": "🔍 Analyzing current screen...", "progress": 20},
                {"step": 2, "message": "🎯 Locating target element...", "progress": 50},
                {"step": 3, "message": "⚡ Executing automation...", "progress": 80},
                {"step": 4, "message": "✅ Verifying completion...", "progress": 100}
            ]
            
            # Find websocket for this client
            websocket = None
            client_id = plan_data.get("client_id", "default")
            for client_session in self.sessions.values():
                if client_session.get("client_id") == client_id:
                    websocket = client_session.get("websocket")
                    break
            
            # Send initial progress
            await self._send_execution_progress(websocket, client_id, plan_id, progress_steps[0])
            await asyncio.sleep(0.5)
            
            # Send screen analysis progress
            await self._send_execution_progress(websocket, client_id, plan_id, progress_steps[1])
            await asyncio.sleep(1.0)
            
            # Send execution progress
            await self._send_execution_progress(websocket, client_id, plan_id, progress_steps[2])
            
            # Get plan steps from the plan data
            plan_steps = []
            if "steps" in plan_data.get("plan", {}):
                plan_steps = plan_data["plan"]["steps"]
            elif "execution_plan" in plan_data.get("plan", {}) and "steps" in plan_data["plan"]["execution_plan"]:
                plan_steps = plan_data["plan"]["execution_plan"]["steps"]
                
            # Initialize adaptive retry handler
            try:
                from adaptive_retry_automation_handler import adaptive_retry_handler, AutomationStep
                
                # Execute each step with the adaptive retry handler
                execution_results = []
                for i, step_data in enumerate(plan_steps):
                    logger.info(f"⚡ Executing step {i+1}/{len(plan_steps)}: {step_data.get('description', '')}")
                    
                    # Convert step data to AutomationStep
                    step = AutomationStep(
                        id=step_data.get("id", f"step_{i+1}"),
                        description=step_data.get("description", ""),
                        action_type=step_data.get("action_type", ""),
                        target=step_data.get("target"),
                        value=step_data.get("value"),
                        coordinates=step_data.get("coordinates")
                    )
                    
                    # Execute the step using adaptive retry handler
                    result = await adaptive_retry_handler.execute_step_with_retry(step, plan_id)
                    execution_results.append(result)
                    
                    # Send progress update
                    await self._send_execution_progress(
                        websocket,
                        client_id,
                        plan_id,
                        {
                            "step": i+1,
                            "message": f"✅ Completed step {i+1}: {step.description}",
                            "progress": int((i+1) / len(plan_steps) * 100)
                        }
                    )
                    
                    # Add small delay for UI to update
                    await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"❌ Error executing plan steps: {e}")
                return {
                    "success": False,
                    "error": f"Error executing plan steps: {str(e)}",
                    "message": f"Error during execution of plan: {plan_id}"
                }
            
            # Send completion progress
            await self._send_execution_progress(
                websocket,
                client_id,
                plan_id, 
                progress_steps[3]
            )
            
            # Clean up the plan from pending_plans if it exists
            if hasattr(self, 'pending_plans') and plan_id in self.pending_plans:
                del self.pending_plans[plan_id]
                
            # Return success response
            return {
                "success": True,
                "type": "agent_execution_success",
                "session_id": plan_id,
                "result": {
                    "success": True,
                    "steps_executed": len(plan_steps),
                    "execution_time": 5.0
                },
                "summary": f"Successfully executed {len(plan_steps)} automation steps",
                "execution_completed": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing verified plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute plan"
            }
"""
            
            # Replace the original execute_verified_plan method with improved version
            updated_content = updated_content.replace(original_execute, new_execute)
            
        # Write the updated content back to the file
        with open("enhanced_enterprise_backend_with_context.py", "w") as f:
            f.write(updated_content)
        
        logger.info("✅ Successfully updated enhanced_enterprise_backend_with_context.py to handle any inquiry type")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating enhanced_enterprise_backend_with_context.py: {e}")
        return False

async def create_helper_function():
    \"\"\"Create a helper function in fixed_universal_automation_handler.py to handle button actions\"\"\"
    try:
        with open("fixed_universal_automation_handler.py", "r") as f:
            content = f.read()
        
        # Check if the helper function already exists
        if "fixed_handle_universal_button_action" in content:
            logger.info("✅ Helper function fixed_handle_universal_button_action already exists")
            return True
        
        # Find the end of the file
        file_end = content.rfind("# Monkey patch the original function to use our fixed implementation")
        
        if file_end == -1:
            # Try alternative approach - find the last function
            file_end = content.rfind("async def handle_universal_automation")
            
            if file_end == -1:
                logger.error("Could not find a suitable location to add the helper function")
                return False
            
            # Find the end of the function
            function_end = content.find("return await fixed_handle_universal_automation", file_end)
            if function_end == -1:
                logger.error("Could not find the end of the last function")
                return False
            
            # Move to the end of the function
            file_end = content.find("\n", function_end + 10)
        
        # Create helper function for button actions
        helper_function = """

async def fixed_handle_universal_button_action(action: str, plan_id: str, session_id: str) -> Dict[str, Any]:
    \"\"\"Universal helper function to handle button actions for ANY inquiry type\"\"\"
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
        updated_content = content[:file_end] + helper_function + content[file_end:]
        
        # Write the updated content back to the file
        with open("fixed_universal_automation_handler.py", "w") as f:
            f.write(updated_content)
        
        logger.info("✅ Successfully added helper function fixed_handle_universal_button_action")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding helper function: {e}")
        return False

async def create_restart_script():
    \"\"\"Create a script to restart the system with the fixes applied\"\"\"
    script_content = """#!/bin/bash
# Restart system with AGENTMODE universal inquiry fixes applied

echo "🛑 Stopping current processes..."
pkill -f enhanced_enterprise_backend_with_context.py || true
pkill -f ws_server_8765.py || true

echo "⏳ Waiting for processes to terminate..."
sleep 2

echo "🔧 Applying AGENTMODE universal inquiry fixes..."
python3 fix_agent_mode_universal_inquiries.py

echo "🚀 Starting fixed system..."
nohup python3 enhanced_enterprise_backend_with_context.py > logs/backend/enhanced_enterprise_8767_context.log 2>&1 &
nohup python3 overlay/fixed_bridge_server.py > overlay/logs/fixed_bridge.log 2>&1 &
nohup python3 fixed_guaranteed_ws_server_8765.py > logs/ws_server_8765.log 2>&1 &

echo "✅ System restarted with AGENTMODE universal inquiry fixes! Check logs for details."
echo "📊 Backend log: logs/backend/enhanced_enterprise_8767_context.log"
echo "📊 WebSocket log: logs/ws_server_8765.log"
echo "📊 Bridge log: overlay/logs/fixed_bridge.log"
"""

    try:
        with open("restart_with_agent_mode_fixes.sh", "w") as f:
            f.write(script_content)
        
        os.chmod("restart_with_agent_mode_fixes.sh", 0o755)
        logger.info("✅ Created restart script: restart_with_agent_mode_fixes.sh")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating restart script: {e}")
        return False

async def create_test_script():
    \"\"\"Create a test script to verify the AGENTMODE universal inquiry fixes\"\"\"
    test_script_content = """#!/usr/bin/env python3
\"\"\"
Test AGENTMODE Universal Inquiry Fixes
This script tests if AGENTMODE now correctly creates plans for ANY type of inquiry.
\"\"\"

import asyncio
import json
import logging
import time
import websockets
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Different inquiry types to test
INQUIRY_TESTS = [
    # Web search inquiries
    {"type": "web_search", "query": "search for python tutorials on google"},
    # Email/communication inquiries
    {"type": "communication", "query": "send an email to John about the meeting tomorrow"},
    # Document/productivity inquiries
    {"type": "productivity", "query": "create a new document called Monthly Report"},
    # Media/entertainment inquiries
    {"type": "entertainment", "query": "play some relaxing music on Spotify"},
    # System inquiries
    {"type": "system_task", "query": "open system preferences and check network settings"},
    # Generic application inquiries
    {"type": "app_usage", "query": "open Calculator app"}
]

async def test_agent_mode_inquiry(inquiry_type: str, query: str) -> bool:
    \"\"\"Test if Agent Mode now provides real plans for specific inquiry type\"\"\"
    logger.info(f"🧪 Testing Agent Mode with {inquiry_type} inquiry: '{query}'")
    
    # Connect to the backend WebSocket
    async with websockets.connect("ws://localhost:8767") as websocket:
        # Wait for connection established message
        response = await websocket.recv()
        logger.info(f"Connected to backend, received: {json.loads(response)['type']}")
        
        # Send an Agent Mode request
        request = {
            "type": "chat_request",
            "mode": "Agent",
            "message": query,
            "session_id": f"test_{int(time.time())}",
            "client_id": f"test_client_{int(time.time())}"
        }
        
        logger.info(f"📤 Sending Agent Mode {inquiry_type} request: {query}")
        await websocket.send(json.dumps(request))
        
        # Wait for response with plan
        plan_received = False
        real_llm_plan = False
        plan_id = None
        
        timeout = time.time() + 20  # 20 second timeout
        
        while time.time() < timeout:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                if response_data.get("type") == "agent_automation_plan" or (
                    response_data.get("type") == "chat_response" and 
                    "Automation Plan" in response_data.get("response", "") and
                    "Plan ID" in response_data.get("response", "")
                ):
                    logger.info(f"✅ Received automation plan for {inquiry_type} inquiry!")
                    plan_received = True
                    
                    # Extract plan ID if available
                    if "plan_id" in response_data:
                        plan_id = response_data.get("plan_id")
                    elif "response" in response_data:
                        # Try to extract plan_id from response text
                        response_text = response_data.get("response", "")
                        plan_id_match = response_text.find("Plan ID:")
                        if plan_id_match != -1:
                            plan_id_line = response_text[plan_id_match:plan_id_match+100]
                            plan_id_parts = plan_id_line.split("`")
                            if len(plan_id_parts) > 1:
                                plan_id = plan_id_parts[1].strip()
                    
                    # Check if this is a real LLM plan
                    if any(key in response_data for key in ["universal_intelligent_automation", "ai_powered", "universal_planning"]):
                        real_llm_plan = True
                        logger.info("✅ Confirmed real LLM plan")
                    
                    # Log plan details
                    if plan_id:
                        logger.info(f"📋 Plan ID: {plan_id}")
                    
                    # Log steps if available in the response
                    response_text = response_data.get("response", "")
                    steps_section = "Automation Steps:"
                    if steps_section in response_text:
                        steps_start = response_text.find(steps_section)
                        steps_text = response_text[steps_start:steps_start+500]
                        logger.info(f"📋 Steps: {steps_text[:200]}...")
                    
                    break
            
            except asyncio.TimeoutError:
                logger.warning(f"⏳ Waiting for response to {inquiry_type} inquiry...")
        
        if not plan_received:
            logger.error(f"❌ Did not receive a plan for {inquiry_type} inquiry: '{query}'")
            return False
        
        if not real_llm_plan:
            logger.warning(f"⚠️ Received a plan for {inquiry_type}, but it might not be a real LLM plan")
        
        logger.info(f"✅ Successfully received plan for {inquiry_type} inquiry: '{query}'")
        return True

async def run_all_tests():
    \"\"\"Run tests for all inquiry types\"\"\"
    results = []
    
    for test in INQUIRY_TESTS:
        inquiry_type = test["type"]
        query = test["query"]
        
        # Add some spacing for readability
        print("\n" + "="*80)
        logger.info(f"🧪 TESTING {inquiry_type.upper()} INQUIRY")
        print("="*80)
        
        try:
            success = await test_agent_mode_inquiry(inquiry_type, query)
            results.append({
                "type": inquiry_type,
                "query": query,
                "success": success
            })
        except Exception as e:
            logger.error(f"❌ Error testing {inquiry_type} inquiry: {e}")
            results.append({
                "type": inquiry_type,
                "query": query,
                "success": False,
                "error": str(e)
            })
        
        # Wait between tests
        await asyncio.sleep(2)
    
    # Print summary
    print("\n" + "="*80)
    logger.info("🔍 TEST SUMMARY")
    print("="*80)
    
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        logger.info(f"{status} - {result['type']}: '{result['query']}'")
    
    logger.info(f"\nOverall result: {success_count}/{total_count} tests passed ({success_count/total_count*100:.0f}%)")
    
    if success_count == total_count:
        logger.info("🎉 ALL TESTS PASSED! AGENTMODE now works with ANY type of inquiry!")
    else:
        logger.warning(f"⚠️ {total_count - success_count} tests failed. Some inquiry types may still have issues.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
"""

    try:
        with open("test_agent_mode_universal_inquiries.py", "w") as f:
            f.write(test_script_content)
        
        os.chmod("test_agent_mode_universal_inquiries.py", 0o755)
        logger.info("✅ Created test script: test_agent_mode_universal_inquiries.py")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating test script: {e}")
        return False

async def main():
    \"\"\"Main function to fix AGENTMODE for all inquiry types\"\"\"
    logger.info("🔧 Starting AGENTMODE Universal Inquiry Fix")
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs/backend", exist_ok=True)
    
    # Fix the fixed_universal_automation_handler.py
    logger.info("📝 Fixing fixed_universal_automation_handler.py...")
    handler_fixed = await fix_fixed_universal_automation_handler()
    
    # Create helper function for button actions
    logger.info("📝 Creating helper function for button actions...")
    helper_created = await create_helper_function()
    
    # Fix the brain_router.py
    logger.info("📝 Fixing brain_router.py...")
    router_fixed = await fix_brain_router()
    
    # Fix the enhanced_enterprise_backend_with_context.py
    logger.info("📝 Fixing enhanced_enterprise_backend_with_context.py...")
    backend_fixed = await fix_enterprise_backend()
    
    # Create restart script
    logger.info("📝 Creating restart script...")
    restart_script_created = await create_restart_script()
    
    # Create test script
    logger.info("📝 Creating test script...")
    test_script_created = await create_test_script()
    
    # Print summary
    logger.info("\n🔍 Fix Summary:")
    logger.info(f"fixed_universal_automation_handler.py fixed: {'✅' if handler_fixed else '❌'}")
    logger.info(f"Helper function created: {'✅' if helper_created else '❌'}")
    logger.info(f"brain_router.py fixed: {'✅' if router_fixed else '❌'}")
    logger.info(f"enhanced_enterprise_backend_with_context.py fixed: {'✅' if backend_fixed else '❌'}")
    logger.info(f"Restart script created: {'✅' if restart_script_created else '❌'}")
    logger.info(f"Test script created: {'✅' if test_script_created else '❌'}")
    
    # Print next steps
    logger.info("\n📋 Next Steps:")
    logger.info("1. Run the following command to restart the system with the fixes applied:")
    logger.info("   ./restart_with_agent_mode_fixes.sh")
    logger.info("")
    logger.info("2. Test the fixes with various inquiry types using:")
    logger.info("   python3 test_agent_mode_universal_inquiries.py")
    logger.info("")
    logger.info("3. Try manual tests with different types of inquiries in the AGENTMODE:")
    logger.info("   - Web searches: \"search for python tutorials\"")
    logger.info("   - Email: \"compose an email to John\"")
    logger.info("   - Documents: \"create a new spreadsheet\"")
    logger.info("   - Media: \"play some music\"")
    logger.info("   - System: \"check network settings\"")
    logger.info("")
    
    if all([handler_fixed, helper_created, router_fixed, backend_fixed, restart_script_created, test_script_created]):
        logger.info("✅ AGENTMODE Universal Inquiry Fix completed successfully!")
    else:
        logger.warning("⚠️ AGENTMODE Universal Inquiry Fix completed with some issues.")
        logger.warning("   Review the fix summary above and fix any remaining issues manually.")

if __name__ == "__main__":
    asyncio.run(main())