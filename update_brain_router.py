#!/usr/bin/env python3
"""
Update Brain Router to Prioritize Fixed Universal Automation Handler
This script updates brain_router.py to prioritize fixed_universal_automation_handler for all inquiry types
"""

import os
import re

def update_brain_router():
    """Update brain_router.py to prioritize fixed universal automation handler"""
    file_path = "brain/core/brain_router.py"
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
    
    # Read the current content
    with open(file_path, "r") as f:
        content = f.read()
    
    # Find the _handle_agent_mode method
    agent_mode_handler_pattern = r"async def _handle_agent_mode\(self, request: ChatRequest\)(.*?)async def _handle_ask_mode"
    agent_mode_handler_match = re.search(agent_mode_handler_pattern, content, re.DOTALL)
    
    if not agent_mode_handler_match:
        print("Could not find _handle_agent_mode method in brain_router.py")
        return False
    
    # Extract the handler method
    handler_code = agent_mode_handler_match.group(1)
    
    # Update the handler to prioritize fixed_universal_automation_handler for all inquiry types
    # by modifying the direct implementation section
    direct_implementation_pattern = r"# Improved direct implementation of fixed_handle_universal_automation(.*?)async def fixed_handle_universal_automation\(query, session_id\):(.*?)return \{"
    direct_implementation_match = re.search(direct_implementation_pattern, handler_code, re.DOTALL)
    
    if not direct_implementation_match:
        print("Could not find the direct implementation section")
        return False
    
    direct_implementation = direct_implementation_match.group(2)
    
    # Update the direct implementation to handle all inquiry types
    new_direct_implementation = """
            \"\"\"Enhanced direct implementation with better request parsing\"\"\"
            logger.info("Using enhanced direct implementation for query: " + query)
            
            # Parse query to create a more intelligent plan
            query_lower = query.lower()
            plan_id = f"plan_{int(time.time())}"
            
            # Initialize variables
            search_term = ""
            target_app = "Safari"
            request_type = "general"
            steps = []
            
            # Default response settings
            response_title = "Execute Task"
            success_probability = 85
            complexity = "Medium"
            estimated_duration = 15.0
            
            # Categorize the request type based on content analysis
            if "search" in query_lower or "find" in query_lower or "look for" in query_lower or "google" in query_lower:
                request_type = "web_search"
                # Extract search terms
                search_pattern = r"search (?:for )?[\"']?([^\"']+)[\"']?"
                search_match = re.search(search_pattern, query_lower)
                if search_match:
                    search_term = search_match.group(1)
                else:
                    # Remove search-related words
                    search_term = query_lower.replace("search for", "").replace("search", "").replace("find", "").replace("look for", "").strip()
                
                # Determine target browser
                if "chrome" in query_lower:
                    target_app = "Chrome"
                elif "firefox" in query_lower:
                    target_app = "Firefox"
                elif "edge" in query_lower:
                    target_app = "Edge"
                else:
                    target_app = "Safari"
                
                steps = [
                    {"id": "step_1", "description": f"Open {target_app}", "action_type": "open_app"},
                    {"id": "step_2", "description": "Navigate to Google", "action_type": "navigate_url"},
                    {"id": "step_3", "description": f"Type search query: {search_term}", "action_type": "type_text"},
                    {"id": "step_4", "description": "Press Enter to search", "action_type": "hotkey"}
                ]
                
                response_title = f"Search for {search_term}"
                success_probability = 90
                
            # Check for email operations
            elif any(word in query_lower for word in ["email", "mail", "gmail", "outlook"]):
                request_type = "communication"
                
                # Default to Gmail
                target_app = "Gmail"
                if "outlook" in query_lower:
                    target_app = "Outlook"
                
                # Extract recipient and subject if available
                recipient = "recipient"
                subject = "your subject"
                
                recipient_pattern = r"to ([a-zA-Z\s]+)"
                recipient_match = re.search(recipient_pattern, query)
                if recipient_match:
                    recipient = recipient_match.group(1)
                
                subject_pattern = r"(?:about|regarding|subject) [\"']?([^\"']+)[\"']?"
                subject_match = re.search(subject_pattern, query)
                if subject_match:
                    subject = subject_match.group(1)
                
                if "compose" in query_lower or "write" in query_lower or "send" in query_lower or "new" in query_lower:
                    steps = [
                        {"id": "step_1", "description": f"Open {target_app}", "action_type": "open_app"},
                        {"id": "step_2", "description": "Click Compose button", "action_type": "click_element"},
                        {"id": "step_3", "description": f"Enter recipient: {recipient}", "action_type": "type_text"},
                        {"id": "step_4", "description": "Tab to subject field", "action_type": "hotkey"},
                        {"id": "step_5", "description": f"Enter subject: {subject}", "action_type": "type_text"}
                    ]
                    response_title = f"Compose email to {recipient}"
                else:
                    # General email operations
                    steps = [
                        {"id": "step_1", "description": f"Open {target_app}", "action_type": "open_app"},
                        {"id": "step_2", "description": "Navigate to inbox", "action_type": "click_element"}
                    ]
                    response_title = f"Open {target_app}"
                
                success_probability = 85
                complexity = "Medium"
                
            # Check for document/file operations
            elif any(word in query_lower for word in ["document", "file", "folder", "open", "create", "edit"]):
                request_type = "productivity"
                
                # Determine document type
                doc_type = "document"
                if "spreadsheet" in query_lower or "excel" in query_lower:
                    doc_type = "spreadsheet"
                    target_app = "Excel" if "excel" in query_lower else "Numbers"
                elif "presentation" in query_lower or "powerpoint" in query_lower or "slides" in query_lower:
                    doc_type = "presentation"
                    target_app = "PowerPoint" if "powerpoint" in query_lower else "Keynote"
                elif "word" in query_lower:
                    target_app = "Word"
                else:
                    target_app = "Pages"
                
                # Create or open
                if "create" in query_lower or "new" in query_lower:
                    steps = [
                        {"id": "step_1", "description": f"Open {target_app}", "action_type": "open_app"},
                        {"id": "step_2", "description": f"Create new {doc_type}", "action_type": "click_element"}
                    ]
                    response_title = f"Create new {doc_type}"
                else:
                    steps = [
                        {"id": "step_1", "description": f"Open {target_app}", "action_type": "open_app"},
                        {"id": "step_2", "description": "Open recent documents", "action_type": "click_element"}
                    ]
                    response_title = f"Open {doc_type}"
                
                success_probability = 85
                complexity = "Medium"
                
            # Check for media/entertainment operations
            elif any(word in query_lower for word in ["play", "watch", "video", "music", "youtube", "spotify", "netflix"]):
                request_type = "entertainment"
                
                # Determine media service
                media_title = "content"
                if "youtube" in query_lower:
                    target_app = "YouTube"
                    media_pattern = r"(?:watch|play) [\"']?([^\"']+)[\"']? on youtube"
                    media_match = re.search(media_pattern, query_lower)
                    if media_match:
                        media_title = media_match.group(1)
                    else:
                        media_title = query_lower.replace("youtube", "").replace("watch", "").replace("play", "").replace("video", "").strip()
                elif "spotify" in query_lower or "music" in query_lower:
                    target_app = "Spotify"
                    media_pattern = r"(?:play|listen to) [\"']?([^\"']+)[\"']?"
                    media_match = re.search(media_pattern, query_lower)
                    if media_match:
                        media_title = media_match.group(1)
                    else:
                        media_title = query_lower.replace("spotify", "").replace("music", "").replace("play", "").replace("listen to", "").strip()
                elif "netflix" in query_lower:
                    target_app = "Netflix"
                    media_pattern = r"(?:watch|play) [\"']?([^\"']+)[\"']? on netflix"
                    media_match = re.search(media_pattern, query_lower)
                    if media_match:
                        media_title = media_match.group(1)
                    else:
                        media_title = query_lower.replace("netflix", "").replace("watch", "").replace("play", "").strip()
                else:
                    target_app = "Safari"
                
                steps = [
                    {"id": "step_1", "description": f"Open {target_app}", "action_type": "open_app"},
                    {"id": "step_2", "description": "Navigate to search", "action_type": "click_element"},
                    {"id": "step_3", "description": f"Search for: {media_title}", "action_type": "type_text"},
                    {"id": "step_4", "description": "Press Enter to search", "action_type": "hotkey"},
                    {"id": "step_5", "description": "Click on result", "action_type": "click_element"}
                ]
                
                response_title = f"Play {media_title} on {target_app}"
                success_probability = 80
                complexity = "Medium"
                
            # Check for system operations
            elif any(word in query_lower for word in ["system", "settings", "preferences", "restart", "shutdown", "wifi", "bluetooth"]):
                request_type = "system_task"
                
                if "wifi" in query_lower or "network" in query_lower:
                    target_app = "System Preferences"
                    steps = [
                        {"id": "step_1", "description": "Open System Preferences", "action_type": "open_app"},
                        {"id": "step_2", "description": "Click on Network", "action_type": "click_element"},
                        {"id": "step_3", "description": "Select Wi-Fi", "action_type": "click_element"}
                    ]
                    response_title = "Configure Wi-Fi Settings"
                elif "bluetooth" in query_lower:
                    target_app = "System Preferences"
                    steps = [
                        {"id": "step_1", "description": "Open System Preferences", "action_type": "open_app"},
                        {"id": "step_2", "description": "Click on Bluetooth", "action_type": "click_element"}
                    ]
                    response_title = "Configure Bluetooth Settings"
                elif "restart" in query_lower:
                    target_app = "System"
                    steps = [
                        {"id": "step_1", "description": "Click Apple menu", "action_type": "click_element"},
                        {"id": "step_2", "description": "Click Restart", "action_type": "click_element"},
                        {"id": "step_3", "description": "Confirm restart", "action_type": "click_element"}
                    ]
                    response_title = "Restart System"
                    success_probability = 70
                    complexity = "High"
                else:
                    target_app = "System Preferences"
                    steps = [
                        {"id": "step_1", "description": "Open System Preferences", "action_type": "open_app"}
                    ]
                    response_title = "Open System Settings"
                
                success_probability = 75
                complexity = "Medium-High"
                
            # General application usage for any other request
            else:
                # Default to general app usage
                request_type = "app_usage"
                
                # Try to extract app name
                app_pattern = r"(?:open|start|launch|run) ([a-zA-Z0-9\s]+)"
                app_match = re.search(app_pattern, query)
                if app_match:
                    target_app = app_match.group(1).strip()
                else:
                    # Try to identify an app in the query
                    known_apps = ["Safari", "Chrome", "Firefox", "Mail", "Calendar", "Notes", "Reminders", 
                                 "Maps", "Photos", "Music", "App Store", "Messages", "FaceTime", "Terminal",
                                 "Word", "Excel", "PowerPoint", "Outlook", "Zoom", "Slack", "Discord"]
                    
                    for app in known_apps:
                        if app.lower() in query_lower:
                            target_app = app
                            break
                
                steps = [
                    {"id": "step_1", "description": f"Open {target_app}", "action_type": "open_app"}
                ]
                
                # Check for additional actions
                if "search" in query_lower:
                    steps.append({"id": "step_2", "description": "Click on search field", "action_type": "click_element"})
                    steps.append({"id": "step_3", "description": "Enter search term", "action_type": "type_text"})
                elif "click" in query_lower:
                    steps.append({"id": "step_2", "description": "Locate and click element", "action_type": "click_element"})
                
                response_title = f"Open {target_app}"
                success_probability = 80
                complexity = "Low"
            
            # Format the response with appropriate markers
            response_text = f\"\"\"🎯 **AUTOMATION EXECUTION PLAN**

**🔍 Task Type:** {request_type.replace('_', ' ').title()}
**📋 Task:** {response_title}
**⏱️ Estimated Duration:** {estimated_duration} seconds
**🎯 Success Probability:** {success_probability}%
**🔧 Complexity:** {complexity}
**📝 Steps:** {len(steps)} actions

**🚀 Automation Steps:**
\"\"\"

            # Add steps to the response
            for i, step in enumerate(steps, 1):
                response_text += f\"{i}. 🟢 {step['description']}\\n\"
            
            response_text += f\"\"\"
**🆔 Plan ID:** `{plan_id}`
**🧠 Planning:** Enhanced Universal Intelligent System

*Automation System: ✅ Ready*\"\"\"
            
            return {
"""
    
    # Replace the direct implementation
    updated_handler_code = handler_code.replace(direct_implementation, new_direct_implementation)
    
    # Replace the handler in the content
    updated_content = content.replace(agent_mode_handler_match.group(1), updated_handler_code)
    
    # Write the updated content
    with open(file_path, "w") as f:
        f.write(updated_content)
    
    print(f"Updated {file_path} to prioritize fixed universal automation handler for all inquiry types")
    return True

# Run the function
if __name__ == "__main__":
    update_brain_router()