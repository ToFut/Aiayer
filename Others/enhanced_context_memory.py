#!/usr/bin/env python3
"""
Enhanced Context Memory System
Integrates visual understanding from LLaVA with process classification
to create meaningful contextual relationships between what the user sees
and what they're doing.
"""
import os
import logging
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import traceback

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/enhanced_context_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_context_memory')

class EnhancedContextMemory:
    """
    Enhanced context memory system that integrates:
    1. LLaVA visual understanding of screen content
    2. Process classification to distinguish foreground/background apps
    3. Relationship modeling between screen, process, and file data
    4. Action and workflow inference
    """
    
    def __init__(self, memory_system=None, llava_processor=None):
        self.memory_system = memory_system
        self.llava_processor = llava_processor
        
        # Context memory storage
        self.context_memory = {
            "activities": [],           # User activities with timestamps
            "application_context": {},  # Per-application context
            "relationships": {},        # Relationships between memory items
            "by_timestamp": {},         # Timeline organization
            "recent_screens": [],       # Recent screen data (limited)
            "recent_processes": [],     # Recent process data (limited)
            "recent_files": []          # Recent file data (limited)
        }
        
        # Maximum items to keep in recent lists
        self.max_recent_items = 10
        
        # Initialize dir for context snapshots
        self.snapshot_dir = "memory/context_snapshots"
        os.makedirs(self.snapshot_dir, exist_ok=True)
        
        # Load existing context if available
        self._load_context()
    
    def _load_context(self):
        """Load existing context memory if available"""
        try:
            context_file = os.path.join("memory", "context_memory.json")
            if os.path.exists(context_file):
                with open(context_file, "r") as f:
                    data = json.load(f)
                    if data and isinstance(data, dict):
                        # Update with any existing fields that are valid
                        for key in self.context_memory:
                            if key in data:
                                self.context_memory[key] = data[key]
                logger.info(f"Loaded context memory with {len(self.context_memory['activities'])} activities")
        except Exception as e:
            logger.error(f"Error loading context memory: {e}")
    
    def _save_context(self):
        """Save context memory to file"""
        try:
            context_file = os.path.join("memory", "context_memory.json")
            with open(context_file, "w") as f:
                json.dump(self.context_memory, f, indent=2)
            logger.info(f"Saved context memory with {len(self.context_memory['activities'])} activities")
            
            # Create a timestamped snapshot occasionally
            if int(time.time()) % 900 < 10:  # Every ~15 minutes (900 seconds)
                snapshot_file = os.path.join(self.snapshot_dir, f"context_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(snapshot_file, "w") as f:
                    json.dump(self.context_memory, f, indent=2)
                logger.info(f"Created context snapshot: {snapshot_file}")
        except Exception as e:
            logger.error(f"Error saving context memory: {e}")
    
    async def process_screen_with_llava(self, screen_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process screen captures with LLaVA for visual understanding
        
        Args:
            screen_data: Screen data dictionary containing image and window info
            
        Returns:
            Enhanced screen data with LLaVA analysis
        """
        if not self.llava_processor:
            logger.warning("No LLaVA processor available, skipping visual analysis")
            return screen_data
            
        try:
            logger.info("Processing screen with LLaVA")
            
            # Get relevant process context
            process_context = None
            if self.context_memory["recent_processes"]:
                process_context = {"processes": self.context_memory["recent_processes"][0]}
            
            # Get image data
            image = None
            if "image" in screen_data and screen_data["image"]:
                image = screen_data["image"]
            elif "image_base64" in screen_data and screen_data["image_base64"]:
                image = screen_data["image_base64"]
            
            if not image:
                logger.warning("No image data found in screen_data")
                return screen_data
            
            # Process with LLaVA
            llava_result = await self.llava_processor.analyze_screen(image, process_context)
            if llava_result and "error" not in llava_result:
                # Add LLaVA analysis to screen data
                screen_data["llava_description"] = llava_result.get("llava_description", "")
                screen_data["visual_context"] = llava_result.get("visual_context", "")
                screen_data["screen_elements"] = llava_result.get("screen_elements", [])
                screen_data["application"] = llava_result.get("application", {})
                
                # Add email data if present
                if "email_data" in llava_result:
                    screen_data["email_data"] = llava_result["email_data"]
                
                # Add form data if present
                if "form_data" in llava_result:
                    screen_data["form_data"] = llava_result["form_data"]
                
                # Add process classification if present
                if "process_classification" in llava_result:
                    screen_data["process_classification"] = llava_result["process_classification"]
                    
                # Mark as significant action if we have good context
                if llava_result.get("application", {}).get("workflow_stage"):
                    screen_data["is_significant_action"] = True
                
                logger.info(f"LLaVA analysis successful: {len(screen_data['llava_description']) if 'llava_description' in screen_data else 0} chars")
            else:
                logger.warning(f"LLaVA analysis failed: {llava_result.get('error', 'unknown error')}")
            
            return screen_data
        
        except Exception as e:
            logger.error(f"Error in LLaVA processing: {e}")
            logger.error(traceback.format_exc())
            return screen_data
    
    def classify_processes(self, processes_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize processes as foreground, supporting, or background
        
        Args:
            processes_data: Process data from sensor
            
        Returns:
            Classified processes dictionary
        """
        try:
            active_window = processes_data.get("active_window", "Unknown Window")
            active_apps = processes_data.get("active_apps", [])
            
            # Use LLaVA processor for classification if available
            if self.llava_processor:
                # Convert to format expected by LLaVA processor
                proc_list = []
                for app in active_apps:
                    if isinstance(app, dict):
                        proc_list.append(app)
                    else:
                        proc_list.append({"name": str(app)})
                        
                # Add active window info
                if active_window and active_window != "Unknown Window":
                    for proc in proc_list:
                        if isinstance(proc, dict) and proc.get("name", "") in active_window:
                            proc["is_active"] = True
                            proc["window_title"] = active_window
                
                return self.llava_processor.classify_processes(proc_list)
            
            # Fallback classification if LLaVA processor not available
            foreground = []
            supporting = []
            background = []
            
            # Find the foreground application
            if active_window and active_window != "Unknown Window":
                active_app_name = None
                # Try to determine active app from window title
                for app in active_apps:
                    app_name = app.get("name") if isinstance(app, dict) else str(app)
                    if app_name in active_window:
                        active_app_name = app_name
                        break
                
                # If found, add to foreground
                if active_app_name:
                    foreground.append(active_app_name)
                    active_app = active_app_name
                else:
                    # Just use the first app as a fallback
                    if active_apps:
                        first_app = active_apps[0]
                        app_name = first_app.get("name") if isinstance(first_app, dict) else str(first_app)
                        foreground.append(app_name)
                        active_app = app_name
                    else:
                        active_app = "Unknown Application"
            else:
                active_app = "Unknown Application"
                
            # Classify remaining processes
            for proc in active_apps:
                process_name = proc.get("name") if isinstance(proc, dict) else str(proc)
                process_type = proc.get("type") if isinstance(proc, dict) else "application"
                
                # Skip if already added to foreground
                if process_name in foreground:
                    continue
                    
                # Supporting processes for browsers and known apps
                if (process_type == "browser" and "Helper" in process_name) or \
                   (active_app in process_name) or \
                   any(helper in process_name for helper in ["Renderer", "GPU", "Plugin", "Helper"]):
                    supporting.append(process_name)
                # Background system processes
                elif process_name.endswith(("d", "daemon")) or \
                     any(system in process_name.lower() for system in [
                        "system", "finder", "spotlight", "service", "daemon", "helper",
                        "agent", "update", "background", "monitor"
                     ]):
                    background.append(process_name)
                # Other applications
                else:
                    background.append(process_name)
            
            return {
                "foreground": foreground,
                "supporting": supporting,
                "background": background,
                "active_window": active_window,
                "active_app": active_app
            }
            
        except Exception as e:
            logger.error(f"Error classifying processes: {e}")
            logger.error(traceback.format_exc())
            return {
                "foreground": [],
                "supporting": [],
                "background": [],
                "active_window": "Unknown",
                "active_app": "Unknown"
            }
    
    async def update_context_memory(self, screen_data: Dict[str, Any], process_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update context memory with meaningful relationships between screen and process data
        
        Args:
            screen_data: Processed screen data with LLaVA analysis
            process_data: Processed process data with classifications
            
        Returns:
            Activity record created
        """
        try:
            timestamp = datetime.now().isoformat()
            screen_id = screen_data.get("memory_id", f"screen_{int(time.time())}")
            process_id = process_data.get("memory_id", f"process_{int(time.time())}")
            
            # Create activity record
            activity = {
                "timestamp": timestamp,
                "screen_id": screen_id,
                "process_id": process_id,
                "application": process_data.get("active_app", "Unknown"),
                "window": process_data.get("active_window", "Unknown"),
                "action": self._infer_user_action(screen_data, process_data),
                "content_summary": (screen_data.get("visual_context", "") or screen_data.get("llava_description", ""))[:100],
                "importance": self._calculate_importance(screen_data, process_data)
            }
            
            # Add to context memory
            self.context_memory["activities"].append(activity)
            # Limit to most recent 100 activities
            self.context_memory["activities"] = self.context_memory["activities"][-100:]
            
            # Update application context
            app_name = activity["application"]
            if app_name not in self.context_memory["application_context"]:
                self.context_memory["application_context"][app_name] = {
                    "views": [],
                    "frequency": 0,
                    "last_active": timestamp,
                    "importance": 0.5
                }
            
            ctx = self.context_memory["application_context"][app_name]
            ctx["frequency"] += 1
            ctx["last_active"] = timestamp
            ctx["importance"] = min(1.0, ctx["importance"] + 0.05)
            
            # Add view if not already present
            view_name = activity["window"]
            if view_name and view_name not in ctx["views"]:
                ctx["views"].append(view_name)
            
            # Setup relationships between memory items
            self.context_memory["relationships"][screen_id] = [process_id]
            self.context_memory["relationships"][process_id] = [screen_id]
            
            # Organize by timestamp
            self.context_memory["by_timestamp"][timestamp] = [screen_id, process_id]
            
            # Update recent items lists
            self._update_recent_items("recent_screens", screen_data)
            self._update_recent_items("recent_processes", process_data)
            
            # Save updated context
            self._save_context()
            
            return activity
            
        except Exception as e:
            logger.error(f"Error updating context memory: {e}")
            logger.error(traceback.format_exc())
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _update_recent_items(self, list_name: str, item: Dict[str, Any]):
        """Update list of recent items, keeping only max_recent_items"""
        if list_name not in self.context_memory:
            self.context_memory[list_name] = []
            
        # Add new item to beginning
        self.context_memory[list_name].insert(0, item)
        
        # Trim to max length
        self.context_memory[list_name] = self.context_memory[list_name][:self.max_recent_items]
    
    def _infer_user_action(self, screen_data: Dict[str, Any], process_data: Dict[str, Any]) -> str:
        """
        Infer what the user is doing based on screen and process data
        
        Args:
            screen_data: Processed screen data with LLaVA analysis
            process_data: Processed process data with classifications
            
        Returns:
            Action description
        """
        try:
            # Try to get action from LLaVA analysis first (most accurate)
            if "application" in screen_data and isinstance(screen_data["application"], dict):
                workflow = screen_data["application"].get("workflow_stage")
                if workflow:
                    return workflow
            
            # Extract screen description and window title
            description = ""
            if "llava_description" in screen_data:
                description = screen_data["llava_description"].lower()
            elif "visual_context" in screen_data:
                description = screen_data["visual_context"].lower()
                
            window_title = screen_data.get("active_window", "").lower()
            
            # Get app name from process data
            app_name = ""
            if "process_classification" in screen_data:
                classification = screen_data["process_classification"]
                if "active_app" in classification and classification["active_app"] != "Unknown Application":
                    app_name = classification["active_app"].lower()
            elif "active_app" in process_data:
                app_name = process_data["active_app"].lower()
            
            # Determine action based on application and content
            if "browser" in app_name or app_name in ["safari", "google chrome", "firefox", "chrome"]:
                if any(term in description for term in ["search", "query", "searching"]):
                    return "web_searching"
                elif any(term in description for term in ["read", "reading", "article", "news"]):
                    return "web_reading"
                elif any(term in description for term in ["video", "watching", "youtube"]):
                    return "video_watching"
                elif any(term in description for term in ["email", "gmail", "mail", "compose"]):
                    return "email_in_browser"
                return "web_browsing"
                
            elif "code" in app_name or app_name in ["vscode", "cursor", "intellij", "pycharm", "visual studio"]:
                if any(term in description for term in ["write", "writing", "edit", "editing"]):
                    return "code_writing"
                elif any(term in description for term in ["debug", "debugging"]):
                    return "code_debugging"
                return "coding"
                
            elif "document" in app_name or app_name in ["word", "pages", "docs", "text edit", "google doc"]:
                if any(term in description for term in ["edit", "editing", "writing", "write"]):
                    return "document_editing"
                return "document_viewing"
                
            elif "email" in app_name or app_name in ["outlook", "mail", "gmail"]:
                if "compose" in description:
                    return "composing_email"
                elif "read" in description:
                    return "reading_email"
                return "email_usage"
                
            elif "terminal" in app_name or app_name in ["iterm", "bash", "console", "cmd"]:
                return "command_line_usage"
                
            elif "chat" in app_name or app_name in ["slack", "teams", "discord", "messages"]:
                return "messaging"
            
            # Default fallback
            return "computer_usage"
            
        except Exception as e:
            logger.error(f"Error inferring user action: {e}")
            return "computer_usage"
    
    def _calculate_importance(self, screen_data: Dict[str, Any], process_data: Dict[str, Any]) -> float:
        """
        Calculate importance score (0-1) for this activity
        
        Args:
            screen_data: Processed screen data
            process_data: Processed process data
            
        Returns:
            Importance score between 0 and 1
        """
        importance = 0.5  # Default medium importance
        
        try:
            # Increase importance if:
            
            # 1. We have workflow stage from LLaVA
            if "application" in screen_data and isinstance(screen_data["application"], dict):
                if screen_data["application"].get("workflow_stage"):
                    importance += 0.2
            
            # 2. We have email data
            if "email_data" in screen_data:
                importance += 0.15
                
            # 3. We have form data
            if "form_data" in screen_data:
                importance += 0.1
                
            # 4. We have UI elements
            if screen_data.get("screen_elements") and len(screen_data["screen_elements"]) > 0:
                importance += 0.05
                
            # 5. We have an explicit significant action flag
            if screen_data.get("is_significant_action", False):
                importance += 0.2
        
        except Exception as e:
            logger.error(f"Error calculating importance: {e}")
            
        # Ensure importance is between 0 and 1
        return min(1.0, max(0.0, importance))
    
    async def add_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> bool:
        """
        Add and process sensor data
        
        Args:
            sensor_type: Type of sensor data (screen, process, file)
            data: Sensor data
            
        Returns:
            Success flag
        """
        try:
            # Skip processing invalid data
            if not data:
                return False
                
            # Process based on sensor type
            if sensor_type == "screen":
                # Enhance with LLaVA visual understanding
                enhanced_data = await self.process_screen_with_llava(data)
                
                # Add to recent screens
                self._update_recent_items("recent_screens", enhanced_data)
                
                # If we have recent process data, update context relationships
                if self.context_memory["recent_processes"]:
                    recent_process = self.context_memory["recent_processes"][0]
                    await self.update_context_memory(enhanced_data, recent_process)
                    
                # Forward to memory system if provided
                if self.memory_system:
                    await self.memory_system.add_sensor_data(sensor_type, enhanced_data)
                    
                return True
                
            elif sensor_type == "process":
                # Classify processes
                if "active_apps" in data:
                    process_classification = self.classify_processes(data)
                    data["process_classification"] = process_classification
                
                # Add to recent processes
                self._update_recent_items("recent_processes", data)
                
                # If we have recent screen data, update context relationships
                if self.context_memory["recent_screens"]:
                    recent_screen = self.context_memory["recent_screens"][0]
                    await self.update_context_memory(recent_screen, data)
                    
                # Forward to memory system if provided
                if self.memory_system:
                    await self.memory_system.add_sensor_data(sensor_type, data)
                    
                return True
                
            elif sensor_type == "file":
                # Add to recent files
                self._update_recent_items("recent_files", data)
                
                # Forward to memory system if provided
                if self.memory_system:
                    await self.memory_system.add_sensor_data(sensor_type, data)
                    
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error adding sensor data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def get_current_context(self) -> Dict[str, Any]:
        """
        Get the current context for LLM consumption
        
        Returns:
            Dict with current context organized by relevance
        """
        try:
            # Prepare the most relevant context information
            context = {
                "current_application": None,
                "current_activity": None,
                "screen_context": None,
                "recent_activities": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Get current application
            if self.context_memory["recent_processes"]:
                recent_process = self.context_memory["recent_processes"][0]
                if "process_classification" in recent_process:
                    classification = recent_process["process_classification"]
                    if "active_app" in classification:
                        context["current_application"] = {
                            "name": classification["active_app"],
                            "window": classification.get("active_window", ""),
                            "foreground_apps": classification.get("foreground", []),
                            "supporting_apps": classification.get("supporting", [])[:5]  # Limit to 5
                        }
            
            # Get current screen context
            if self.context_memory["recent_screens"]:
                recent_screen = self.context_memory["recent_screens"][0]
                
                # Add application context from LLaVA
                if "application" in recent_screen and isinstance(recent_screen["application"], dict):
                    app_context = recent_screen["application"]
                    if app_context.get("name") and app_context.get("name") != "unknown":
                        if not context["current_application"]:
                            context["current_application"] = {}
                        context["current_application"]["name"] = app_context["name"]
                        context["current_application"]["view"] = app_context.get("view", "")
                        context["current_application"]["workflow"] = app_context.get("workflow_stage", "")
                
                # Add visual context
                if recent_screen.get("visual_context") or recent_screen.get("llava_description"):
                    context["screen_context"] = {
                        "visual_description": recent_screen.get("visual_context") or recent_screen.get("llava_description", ""),
                        "ui_elements": recent_screen.get("screen_elements", [])[:5]  # Limit to 5 elements
                    }
                
                # Add email context if available
                if "email_data" in recent_screen:
                    context["email_context"] = recent_screen["email_data"]
                    
                # Add form context if available
                if "form_data" in recent_screen:
                    context["form_context"] = recent_screen["form_data"]
            
            # Add recent activities
            for activity in self.context_memory["activities"][:5]:  # Last 5 activities
                context["recent_activities"].append({
                    "timestamp": activity["timestamp"],
                    "application": activity["application"],
                    "window": activity["window"],
                    "action": activity["action"],
                    "content_summary": activity["content_summary"]
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting current context: {e}")
            logger.error(traceback.format_exc())
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Main function for testing
async def main():
    """Test the enhanced context memory system"""
    from llava_visual_processor import LLaVAVisualProcessor
    
    # Create LLaVA processor
    llava_processor = LLaVAVisualProcessor()
    
    # Create enhanced context memory
    context_memory = EnhancedContextMemory(llava_processor=llava_processor)
    
    # Test with dummy data
    dummy_screen = {
        "timestamp": time.time(),
        "active_window": "Visual Studio Code - project.py",
        "image": "sample.png" if os.path.exists("sample.png") else None
    }
    
    dummy_processes = {
        "timestamp": time.time(),
        "active_apps": [
            {"name": "Visual Studio Code", "pid": 1234},
            {"name": "Chrome", "pid": 2345},
            {"name": "Terminal", "pid": 3456},
            {"name": "Finder", "pid": 4567}
        ],
        "active_window": "Visual Studio Code - project.py"
    }
    
    # Add sensor data
    if dummy_screen["image"]:
        print("Processing screen data with image")
        await context_memory.add_sensor_data("screen", dummy_screen)
    
    print("Processing process data")
    await context_memory.add_sensor_data("process", dummy_processes)
    
    # Get current context
    context = await context_memory.get_current_context()
    print("\nCurrent context:")
    print(json.dumps(context, indent=2))

if __name__ == "__main__":
    asyncio.run(main())