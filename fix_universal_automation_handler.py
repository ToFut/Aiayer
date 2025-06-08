#!/usr/bin/env python3
"""
Fix Universal Automation Handler to support any inquiry type
"""

import os
import re

def fix_universal_automation_handler():
    """Fix the fixed_universal_automation_handler.py to handle any inquiry type"""
    file_path = "fixed_universal_automation_handler.py"
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False
    
    # Read the current content
    with open(file_path, "r") as f:
        content = f.read()
    
    # Find the section to replace
    start_marker = "# Parse the request to create an intelligent fallback"
    end_marker = "# Create the plan with the appropriate steps"
    
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker, start_pos)
    
    if start_pos == -1 or end_pos == -1:
        print("Error: Could not find section to replace")
        return False
    
    # Original section
    original_section = content[start_pos:end_pos]
    
    # New section with improved inquiry handling
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
                email_to_match = re.search(r'to (.+?)( about| with| subject| for|$)', user_request_lower)
                email_subject_match = re.search(r'subject (.+?)( to| with| about| for|$)', user_request_lower)
                
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
                doc_name_match = re.search(r'(open|create|edit) (.+?)( in| with| using| for|$)', user_request_lower)
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
                media_match = re.search(r'(play|watch|listen to) (.+?)( on| in| with| using| for|$)', user_request_lower)
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
                app_match = re.search(r'open (.+?)( and| to| for| with|$)', user_request_lower)
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
    
    # Replace the section
    new_content = content.replace(original_section, new_section)
    
    # Write the updated content
    with open(file_path, "w") as f:
        f.write(new_content)
    
    print(f"Updated {file_path} with improved inquiry handling")
    return True

# Run the fix
if __name__ == "__main__":
    fix_universal_automation_handler()