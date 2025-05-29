"""
Universal Data Access Planner
Analyzes any user message and determines what data sources need to be accessed
and creates execution plans for deep data retrieval using TeamViewer-style automation.
"""

import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class UniversalDataAccessPlanner:
    """
    Analyzes user queries and creates execution plans for accessing various data sources
    using the existing TeamViewer-style screen automation infrastructure.
    """
    
    def __init__(self):
        self.data_source_patterns = {
            "email": {
                "patterns": [
                    r"\b(email|emails|mail|inbox|message|messages)\b",
                    r"\b(gmail|outlook|thunderbird|mail\.app)\b",
                    r"\bsent (to|from)\b",
                    r"\bemails? (from|to|containing|about)\b",
                    r"\b(unread|new) (email|mail|messages?)\b"
                ],
                "applications": ["Mail", "Gmail", "Outlook", "Thunderbird"],
                "priority": "high"
            },
            "browser_history": {
                "patterns": [
                    r"\b(browse|browsed|visited|website|site|url)\b",
                    r"\b(history|browser history|web history)\b",
                    r"\bwent to\b",
                    r"\b(chrome|safari|firefox|edge) history\b",
                    r"\bvisited (today|yesterday|this week)\b"
                ],
                "applications": ["Chrome", "Safari", "Firefox", "Edge"],
                "priority": "high"
            },
            "files": {
                "patterns": [
                    r"\b(file|files|document|documents|folder|folders)\b",
                    r"\b(created|modified|saved|downloaded)\b",
                    r"\.(pdf|doc|docx|txt|xlsx|ppt|pptx|png|jpg|jpeg)\b",
                    r"\bfinder\b",
                    r"\b(desktop|downloads|documents) folder\b"
                ],
                "applications": ["Finder", "Explorer", "File Manager"],
                "priority": "medium"
            },
            "calendar": {
                "patterns": [
                    r"\b(calendar|appointment|meeting|event|schedule)\b",
                    r"\b(today|tomorrow|this week|next week)\b",
                    r"\b(at \d{1,2}:\d{2}|at \d{1,2}(am|pm))\b",
                    r"\bmeeting with\b"
                ],
                "applications": ["Calendar", "Outlook Calendar", "Google Calendar"],
                "priority": "medium"
            },
            "notes": {
                "patterns": [
                    r"\b(note|notes|note-taking|notebook)\b",
                    r"\b(obsidian|notion|evernote|onenote|apple notes)\b",
                    r"\bwrote down\b",
                    r"\bjotted down\b"
                ],
                "applications": ["Notes", "Obsidian", "Notion", "Evernote", "OneNote"],
                "priority": "low"
            },
            "system_info": {
                "patterns": [
                    r"\b(running|open|active|processes?)\b",
                    r"\b(apps?|applications?|programs?)\b",
                    r"\bsystem (info|information|status)\b",
                    r"\bwhat.*(running|open|active)\b"
                ],
                "applications": ["Activity Monitor", "Task Manager", "System"],
                "priority": "high"
            },
            "chat_history": {
                "patterns": [
                    r"\b(chat|conversation|messages?|slack|discord|teams)\b",
                    r"\btalked (to|with|about)\b",
                    r"\bsaid (to|about)\b",
                    r"\bdiscussed\b"
                ],
                "applications": ["Slack", "Discord", "Teams", "Messages", "WhatsApp"],
                "priority": "medium"
            }
        }
        
        self.time_patterns = {
            "today": r"\btoday\b",
            "yesterday": r"\byesterday\b",
            "this_week": r"\bthis week\b",
            "last_week": r"\blast week\b",
            "this_month": r"\bthis month\b",
            "specific_time": r"\b(\d{1,2}:\d{2}|at \d{1,2}(am|pm))\b",
            "relative_time": r"\b(\d+) (minutes?|hours?|days?) ago\b"
        }
    
    async def analyze_query(self, user_message: str) -> Dict[str, Any]:
        """
        Analyze user message and determine what data sources need to be accessed.
        Returns a comprehensive execution plan.
        """
        logger.info(f"Analyzing query: {user_message}")
        
        # Convert to lowercase for pattern matching
        message_lower = user_message.lower()
        
        # Detect data sources needed
        detected_sources = self._detect_data_sources(message_lower)
        
        # Extract time constraints
        time_constraints = self._extract_time_constraints(message_lower)
        
        # Extract search terms and keywords
        search_terms = self._extract_search_terms(user_message)
        
        # Create execution plan
        execution_plan = await self._create_execution_plan(
            detected_sources, time_constraints, search_terms, user_message
        )
        
        return {
            "original_query": user_message,
            "detected_sources": detected_sources,
            "time_constraints": time_constraints,
            "search_terms": search_terms,
            "execution_plan": execution_plan,
            "estimated_complexity": self._estimate_complexity(detected_sources),
            "timestamp": datetime.now().isoformat()
        }
    
    def _detect_data_sources(self, message: str) -> List[Dict[str, Any]]:
        """Detect which data sources are mentioned in the message."""
        detected = []
        
        for source_name, source_config in self.data_source_patterns.items():
            confidence = 0
            matched_patterns = []
            
            for pattern in source_config["patterns"]:
                if re.search(pattern, message, re.IGNORECASE):
                    confidence += 1
                    matched_patterns.append(pattern)
            
            if confidence > 0:
                detected.append({
                    "source": source_name,
                    "confidence": confidence / len(source_config["patterns"]),
                    "matched_patterns": matched_patterns,
                    "applications": source_config["applications"],
                    "priority": source_config["priority"]
                })
        
        # Sort by confidence and priority
        detected.sort(key=lambda x: (x["confidence"], x["priority"] == "high"), reverse=True)
        return detected
    
    def _extract_time_constraints(self, message: str) -> Dict[str, Any]:
        """Extract time-related constraints from the message."""
        constraints = {}
        
        for time_type, pattern in self.time_patterns.items():
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                constraints[time_type] = matches
        
        # Convert to actual time ranges
        time_range = self._convert_to_time_range(constraints)
        
        return {
            "raw_constraints": constraints,
            "time_range": time_range
        }
    
    def _extract_search_terms(self, message: str) -> List[str]:
        """Extract relevant search terms and keywords from the message."""
        # Remove common words and extract meaningful terms
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "from", "up", "about", "into", "through", "during",
            "what", "where", "when", "why", "how", "can", "could", "would", "should",
            "i", "you", "he", "she", "it", "we", "they", "me", "my", "your", "his",
            "her", "its", "our", "their", "this", "that", "these", "those"
        }
        
        # Extract words that might be search terms
        words = re.findall(r'\b\w+\b', message.lower())
        search_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]*)"', message)
        quoted_phrases.extend(re.findall(r"'([^']*)'", message))
        
        # Combine and deduplicate
        all_terms = search_terms + quoted_phrases
        return list(set(all_terms))
    
    def _convert_to_time_range(self, constraints: Dict[str, Any]) -> Optional[Dict[str, datetime]]:
        """Convert time constraints to actual datetime ranges."""
        if not constraints:
            return None
        
        now = datetime.now()
        
        if "today" in constraints:
            return {
                "start": now.replace(hour=0, minute=0, second=0),
                "end": now.replace(hour=23, minute=59, second=59)
            }
        elif "yesterday" in constraints:
            yesterday = now - timedelta(days=1)
            return {
                "start": yesterday.replace(hour=0, minute=0, second=0),
                "end": yesterday.replace(hour=23, minute=59, second=59)
            }
        elif "this_week" in constraints:
            days_since_monday = now.weekday()
            start_of_week = now - timedelta(days=days_since_monday)
            return {
                "start": start_of_week.replace(hour=0, minute=0, second=0),
                "end": now
            }
        elif "last_week" in constraints:
            days_since_monday = now.weekday()
            start_of_this_week = now - timedelta(days=days_since_monday)
            start_of_last_week = start_of_this_week - timedelta(days=7)
            end_of_last_week = start_of_this_week - timedelta(seconds=1)
            return {
                "start": start_of_last_week.replace(hour=0, minute=0, second=0),
                "end": end_of_last_week
            }
        
        return None
    
    async def _create_execution_plan(self, detected_sources: List[Dict], 
                                   time_constraints: Dict, search_terms: List[str],
                                   original_query: str) -> Dict[str, Any]:
        """Create a detailed execution plan for data access."""
        
        plan = {
            "steps": [],
            "estimated_duration": 0,
            "complexity": "low",
            "requires_user_interaction": False
        }
        
        for i, source in enumerate(detected_sources):
            source_name = source["source"]
            step = await self._create_source_access_plan(
                source_name, source["applications"], time_constraints, 
                search_terms, original_query
            )
            step["order"] = i + 1
            plan["steps"].append(step)
            plan["estimated_duration"] += step.get("estimated_duration", 30)
        
        plan["complexity"] = self._estimate_complexity(detected_sources)
        plan["requires_user_interaction"] = any(
            step.get("requires_interaction", False) for step in plan["steps"]
        )
        
        return plan
    
    async def _create_source_access_plan(self, source_name: str, applications: List[str],
                                       time_constraints: Dict, search_terms: List[str],
                                       original_query: str) -> Dict[str, Any]:
        """Create specific access plan for a data source."""
        
        base_plan = {
            "source": source_name,
            "applications": applications,
            "actions": [],
            "estimated_duration": 30,
            "requires_interaction": False,
            "verification_steps": []
        }
        
        if source_name == "email":
            base_plan.update({
                "actions": [
                    {
                        "type": "launch_application",
                        "target": applications[0],
                        "fallback_targets": applications[1:],
                        "verification": "window_title_contains"
                    },
                    {
                        "type": "navigate_to_search",
                        "method": "keyboard_shortcut",
                        "shortcut": "cmd+f" if "Mac" in str(applications) else "ctrl+f"
                    },
                    {
                        "type": "perform_search",
                        "search_terms": search_terms,
                        "time_constraints": time_constraints,
                        "search_fields": ["subject", "sender", "content"]
                    },
                    {
                        "type": "extract_results",
                        "method": "ocr_and_scraping",
                        "target_elements": ["email_list", "email_content"]
                    }
                ],
                "estimated_duration": 45,
                "verification_steps": [
                    "verify_application_launched",
                    "verify_search_interface_visible",
                    "verify_results_displayed"
                ]
            })
        
        elif source_name == "browser_history":
            base_plan.update({
                "actions": [
                    {
                        "type": "launch_application",
                        "target": applications[0],
                        "fallback_targets": applications[1:]
                    },
                    {
                        "type": "open_history",
                        "method": "keyboard_shortcut",
                        "shortcut": "cmd+y" if "Safari" in applications[0] else "ctrl+h"
                    },
                    {
                        "type": "perform_search",
                        "search_terms": search_terms,
                        "time_constraints": time_constraints
                    },
                    {
                        "type": "extract_results",
                        "method": "ocr_and_scraping",
                        "target_elements": ["history_list", "timestamps", "urls"]
                    }
                ],
                "estimated_duration": 35
            })
        
        elif source_name == "files":
            base_plan.update({
                "actions": [
                    {
                        "type": "launch_application",
                        "target": "Finder" if "Mac" else "Explorer"
                    },
                    {
                        "type": "navigate_to_search",
                        "method": "keyboard_shortcut",
                        "shortcut": "cmd+f" if "Mac" else "ctrl+f"
                    },
                    {
                        "type": "perform_search",
                        "search_terms": search_terms,
                        "time_constraints": time_constraints,
                        "search_locations": ["Desktop", "Documents", "Downloads"]
                    },
                    {
                        "type": "extract_results",
                        "method": "file_metadata_and_ocr",
                        "target_elements": ["file_names", "dates", "sizes", "paths"]
                    }
                ],
                "estimated_duration": 40
            })
        
        elif source_name == "system_info":
            base_plan.update({
                "actions": [
                    {
                        "type": "capture_screen",
                        "purpose": "current_state_analysis"
                    },
                    {
                        "type": "launch_system_monitor",
                        "target": "Activity Monitor" if "Mac" else "Task Manager",
                        "shortcut": "cmd+space" if "Mac" else "ctrl+shift+esc"
                    },
                    {
                        "type": "extract_process_info",
                        "method": "ocr_and_scraping",
                        "target_elements": ["process_names", "cpu_usage", "memory_usage"]
                    }
                ],
                "estimated_duration": 20
            })
        
        return base_plan
    
    def _estimate_complexity(self, detected_sources: List[Dict]) -> str:
        """Estimate the complexity of the execution plan."""
        if len(detected_sources) == 0:
            return "none"
        elif len(detected_sources) == 1:
            return "low"
        elif len(detected_sources) <= 3:
            return "medium"
        else:
            return "high"

class DataAccessExecutor:
    """
    Executes the data access plans using the existing TeamViewer-style infrastructure.
    """
    
    def __init__(self, backend_instance):
        """Initialize with reference to the enhanced backend."""
        self.backend = backend_instance
        self.logger = logging.getLogger(__name__)
    
    async def execute_plan(self, execution_plan: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Execute the complete data access plan."""
        results = {
            "success": True,
            "data_collected": {},
            "errors": [],
            "execution_log": [],
            "screenshots": []
        }
        
        try:
            for step in execution_plan["steps"]:
                step_result = await self._execute_step(step, websocket)
                results["data_collected"][step["source"]] = step_result
                results["execution_log"].append({
                    "step": step["source"],
                    "timestamp": datetime.now().isoformat(),
                    "success": step_result.get("success", False),
                    "duration": step_result.get("duration", 0)
                })
                
                if not step_result.get("success", False):
                    results["errors"].append({
                        "step": step["source"],
                        "error": step_result.get("error", "Unknown error")
                    })
        
        except Exception as e:
            self.logger.error(f"Error executing plan: {e}")
            results["success"] = False
            results["errors"].append({"general_error": str(e)})
        
        return results
    
    async def _execute_step(self, step: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Execute a single step in the data access plan."""
        start_time = datetime.now()
        
        try:
            # Take initial screenshot
            initial_screen = await self.backend.capture_screen_fast()
            
            # Execute each action in the step
            for action in step["actions"]:
                action_result = await self._execute_action(action, websocket)
                if not action_result.get("success", False):
                    return {
                        "success": False,
                        "error": f"Action failed: {action['type']}",
                        "duration": (datetime.now() - start_time).total_seconds()
                    }
            
            # Take final screenshot and extract data
            final_screen = await self.backend.capture_screen_fast()
            extracted_data = await self._extract_data_from_screen(final_screen, step)
            
            return {
                "success": True,
                "data": extracted_data,
                "duration": (datetime.now() - start_time).total_seconds(),
                "screenshots": {
                    "before": initial_screen,
                    "after": final_screen
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error executing step {step['source']}: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds()
            }
    
    async def _execute_action(self, action: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Execute a specific action using the backend's automation capabilities."""
        try:
            if action["type"] == "launch_application":
                return await self._launch_application(action)
            elif action["type"] == "navigate_to_search":
                return await self._navigate_to_search(action)
            elif action["type"] == "perform_search":
                return await self._perform_search(action)
            elif action["type"] == "extract_results":
                return await self._extract_results(action)
            elif action["type"] == "capture_screen":
                screen = await self.backend.capture_screen_fast()
                return {"success": True, "screenshot": screen}
            else:
                return {"success": False, "error": f"Unknown action type: {action['type']}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _launch_application(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Launch the specified application."""
        # Use existing backend automation to launch app
        automation_action = {
            "type": "agent",
            "message": f"Launch {action['target']} application",
            "action_type": "launch_app",
            "target_app": action["target"]
        }
        
        result = await self.backend.handle_agent_execution_with_verification(
            automation_action, "system", None
        )
        
        return {"success": result.get("success", False)}
    
    async def _navigate_to_search(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to search interface using keyboard shortcuts."""
        if action["method"] == "keyboard_shortcut":
            # Use backend's keyboard automation
            automation_action = {
                "type": "keyboard",
                "shortcut": action["shortcut"]
            }
            
            result = await self.backend.execute_action_with_verification(
                automation_action, None
            )
            
            return {"success": result.get("success", False)}
        
        return {"success": False, "error": "Unsupported navigation method"}
    
    async def _perform_search(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Perform search with the specified terms."""
        search_query = " ".join(action["search_terms"])
        
        automation_action = {
            "type": "type_text",
            "text": search_query
        }
        
        result = await self.backend.execute_action_with_verification(
            automation_action, None
        )
        
        return {"success": result.get("success", False)}
    
    async def _extract_results(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Extract results from the current screen."""
        screen = await self.backend.capture_screen_fast()
        
        # Use OCR and visual analysis to extract data
        extracted_data = await self._extract_data_from_screen(screen, action)
        
        return {
            "success": True,
            "extracted_data": extracted_data
        }
    
    async def _extract_data_from_screen(self, screen, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from screen using OCR and visual analysis."""
        # This would integrate with the backend's visual processing capabilities
        # For now, return placeholder structure
        return {
            "raw_text": "OCR extracted text would go here",
            "structured_data": [],
            "confidence": 0.8,
            "extraction_method": context.get("method", "ocr_and_scraping")
        }

# Integration function to add to existing backend
async def integrate_universal_data_access(backend_instance):
    """
    Integrate universal data access capabilities into the existing backend.
    """
    planner = UniversalDataAccessPlanner()
    executor = DataAccessExecutor(backend_instance)
    
    # Add methods to backend instance
    backend_instance.universal_planner = planner
    backend_instance.data_executor = executor
    
    # Add new handler method
    async def handle_universal_data_access(self, user_message: str, websocket=None) -> Dict[str, Any]:
        """Handle universal data access for any user message."""
        try:
            # Analyze the query
            analysis = await self.universal_planner.analyze_query(user_message)
            
            # If no data sources detected, return normal response
            if not analysis["detected_sources"]:
                return {
                    "type": "normal_response",
                    "requires_deep_access": False,
                    "analysis": analysis
                }
            
            # Execute the data access plan
            execution_results = await self.data_executor.execute_plan(
                analysis["execution_plan"], websocket
            )
            
            return {
                "type": "deep_data_access",
                "requires_deep_access": True,
                "analysis": analysis,
                "execution_results": execution_results,
                "success": execution_results["success"]
            }
            
        except Exception as e:
            logger.error(f"Error in universal data access: {e}")
            return {
                "type": "error",
                "requires_deep_access": False,
                "error": str(e)
            }
    
    # Bind the method to the backend instance
    import types
    backend_instance.handle_universal_data_access = types.MethodType(
        handle_universal_data_access, backend_instance
    )
    
    return backend_instance

if __name__ == "__main__":
    # Test the planner
    async def test_planner():
        planner = UniversalDataAccessPlanner()
        
        test_queries = [
            "What emails did I receive today?",
            "Show me websites I visited yesterday",
            "Find files I created this week",
            "What apps are currently running?",
            "Who did I chat with on Slack today?",
            "Find my meeting notes from yesterday"
        ]
        
        for query in test_queries:
            print(f"\n=== Testing Query: {query} ===")
            analysis = await planner.analyze_query(query)
            print(json.dumps(analysis, indent=2, default=str))
    
    asyncio.run(test_planner())