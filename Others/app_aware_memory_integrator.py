#!/usr/bin/env python3
"""
Application-Aware Memory Integrator

Integrates application detection with the memory system for enhanced context awareness.
Enables the system to understand when users are in specific applications and boosts
relevant memory entries based on application context.
"""
import os
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/app_aware_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("app_aware_memory")

# Add necessary paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import required modules
try:
    from unified_app_detection import UnifiedAppDetectionSystem, ApplicationContext
    from ui_element_detector import UIElementDetector, UIAnalysisResult
    logger.info("Successfully imported application detection modules")
except ImportError as e:
    logger.error(f"Error importing application detection modules: {e}")
    logger.error("Please ensure unified_app_detection.py and ui_element_detector.py are available")
    sys.exit(1)

# Try to import memory system modules
try:
    from memory.memory_system import MemorySystem
    from memory.conscious_memory import ConsciousMemory
    from memory.enhanced_semantic_search import EnhancedSemanticSearch
    logger.info("Successfully imported memory system modules")
except ImportError as e:
    logger.warning(f"Error importing memory system modules: {e}")
    logger.warning("Memory system integration may be limited")
    MemorySystem = None
    ConsciousMemory = None
    EnhancedSemanticSearch = None

@dataclass
class ApplicationMemoryContext:
    """Rich application context for memory integration"""
    timestamp: float
    app_name: str
    app_category: str = ""
    view_name: str = ""
    workflow: str = ""
    ui_elements: List[Dict[str, Any]] = field(default_factory=list)
    interaction_flows: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    screen_context: str = ""
    previous_app: str = ""
    session_duration: float = 0.0
    memory_references: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationMemoryContext':
        """Create from dictionary"""
        return cls(**data)

class AppAwareMemoryIntegrator:
    """
    Integrates application detection with the memory system for enhanced context.
    
    This class connects the application detection system with the memory system,
    enabling application-aware memory processing and retrieval.
    """
    
    def __init__(self, memory_system=None, llava_url="http://localhost:11434"):
        self.llava_url = llava_url
        self.memory_system = memory_system
        
        # Initialize application detection
        self.app_detector = UnifiedAppDetectionSystem(llava_url=llava_url)
        self.ui_detector = UIElementDetector(llava_url=llava_url)
        
        # Memory context tracking
        self.current_app_context = None
        self.app_context_history = []
        self.max_history_size = 50
        
        # App session tracking
        self.app_sessions = {}  # app_name -> {start_time, duration, count, etc.}
        
        # Memory integration settings
        self.context_integration_interval = 15  # seconds
        self.ui_analysis_interval = 30  # seconds
        self.memory_boost_factor = 1.5  # boost factor for app-relevant memories
        
        # Path settings
        self.output_dir = "results/app_memory"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Thread management
        self.running = False
        self.integration_thread = None
        self._stop_event = threading.Event()
        
        # Try to connect to memory system if not provided
        if not self.memory_system and MemorySystem:
            try:
                self.memory_system = MemorySystem()
                logger.info("Connected to memory system")
            except Exception as e:
                logger.warning(f"Could not connect to memory system: {e}")
        
        # Load application context history
        self._load_context_history()
    
    def _load_context_history(self):
        """Load application context history from file"""
        try:
            history_file = f"{self.output_dir}/app_context_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    
                    # Convert to ApplicationMemoryContext objects
                    self.app_context_history = [
                        ApplicationMemoryContext.from_dict(item) for item in history_data
                    ]
                    
                    logger.info(f"Loaded {len(self.app_context_history)} application context history entries")
        except Exception as e:
            logger.warning(f"Error loading application context history: {e}")
    
    def _save_context_history(self):
        """Save application context history to file"""
        try:
            history_file = f"{self.output_dir}/app_context_history.json"
            
            # Convert to serializable format
            history_data = [item.to_dict() for item in self.app_context_history]
            
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
            logger.info(f"Saved {len(self.app_context_history)} application context history entries")
        except Exception as e:
            logger.warning(f"Error saving application context history: {e}")
    
    def start(self):
        """Start the application-aware memory integration"""
        if self.running:
            logger.warning("Application-aware memory integration is already running")
            return
            
        self.running = True
        self._stop_event.clear()
        
        # Start application detection
        self.app_detector.start()
        logger.info("Started application detection system")
        
        # Start integration thread
        logger.info("Starting application-aware memory integration")
        self.integration_thread = threading.Thread(target=self._integration_loop)
        self.integration_thread.daemon = True
        self.integration_thread.start()
        
        logger.info("Application-aware memory integration started")
    
    def stop(self):
        """Stop the application-aware memory integration"""
        if not self.running:
            logger.warning("Application-aware memory integration is not running")
            return
            
        logger.info("Stopping application-aware memory integration")
        self._stop_event.set()
        self.running = False
        
        # Stop application detection
        self.app_detector.stop()
        logger.info("Stopped application detection system")
        
        if self.integration_thread:
            self.integration_thread.join(timeout=10)
            if self.integration_thread.is_alive():
                logger.warning("Integration thread did not terminate cleanly")
        
        # Save final state
        self._save_context_history()
        
        logger.info("Application-aware memory integration stopped")
    
    def _integration_loop(self):
        """Main integration loop running in a background thread"""
        last_context_integration = 0
        last_ui_analysis = 0
        
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # Check if it's time for context integration
                if current_time - last_context_integration >= self.context_integration_interval:
                    self._integrate_app_context()
                    last_context_integration = current_time
                
                # Check if it's time for UI analysis
                if current_time - last_ui_analysis >= self.ui_analysis_interval and self.current_app_context:
                    # UI analysis requires a separate async call
                    # Start a separate thread for UI analysis
                    asyncio.run(self._perform_ui_analysis())
                    last_ui_analysis = current_time
                
            except Exception as e:
                logger.error(f"Error in integration loop: {e}")
                
            # Sleep to avoid excessive CPU usage
            time.sleep(1)
    
    def _integrate_app_context(self):
        """Integrate application context with memory system"""
        try:
            # Get current application context
            app_context = self.app_detector.get_current_application_context()
            
            if not app_context:
                logger.debug("No application context available")
                return
                
            # Check if application has changed
            app_changed = False
            if not self.current_app_context or app_context.app_name != self.current_app_context.app_name:
                app_changed = True
                logger.info(f"Application changed: {app_context.app_name} (previous: {self.current_app_context.app_name if self.current_app_context else 'None'})")
            
            # Create memory context
            memory_context = ApplicationMemoryContext(
                timestamp=time.time(),
                app_name=app_context.app_name,
                app_category=app_context.app_category,
                view_name=app_context.view_name,
                workflow=app_context.workflow,
                ui_elements=app_context.ui_elements,
                confidence=app_context.confidence,
                previous_app=self.current_app_context.app_name if self.current_app_context else ""
            )
            
            # Update session tracking
            self._update_app_session(memory_context)
            
            # Add session duration
            if memory_context.app_name in self.app_sessions:
                memory_context.session_duration = self.app_sessions[memory_context.app_name].get("current_duration", 0)
            
            # Add to history
            self.app_context_history.append(memory_context)
            
            # Trim history if needed
            if len(self.app_context_history) > self.max_history_size:
                self.app_context_history = self.app_context_history[-self.max_history_size:]
            
            # Update current context
            self.current_app_context = memory_context
            
            # If we have a memory system, integrate the context
            if self.memory_system:
                self._integrate_with_memory_system(memory_context, app_changed)
            
            # Save to file
            self._save_current_context(memory_context)
            
            logger.info(f"Integrated application context: {memory_context.app_name} (view: {memory_context.view_name})")
            
        except Exception as e:
            logger.error(f"Error integrating application context: {e}")
    
    def _update_app_session(self, context: ApplicationMemoryContext):
        """Update app session tracking data"""
        app_name = context.app_name
        current_time = time.time()
        
        # Initialize if first time seeing this app
        if app_name not in self.app_sessions:
            self.app_sessions[app_name] = {
                "first_seen": current_time,
                "last_seen": current_time,
                "total_duration": 0,
                "current_start": current_time,
                "current_duration": 0,
                "session_count": 1,
                "views": {context.view_name: 1} if context.view_name else {}
            }
            return
        
        # Update existing app session
        session = self.app_sessions[app_name]
        session["last_seen"] = current_time
        
        # If previous context was different app, this is a new session
        if self.current_app_context and self.current_app_context.app_name != app_name:
            # Close previous session
            prev_app = self.current_app_context.app_name
            if prev_app in self.app_sessions:
                prev_session = self.app_sessions[prev_app]
                session_duration = current_time - prev_session["current_start"]
                prev_session["total_duration"] += session_duration
                prev_session["current_duration"] = 0
            
            # Start new session
            session["current_start"] = current_time
            session["current_duration"] = 0
            session["session_count"] += 1
        else:
            # Update current session duration
            session["current_duration"] = current_time - session["current_start"]
        
        # Update view count
        if context.view_name:
            session["views"][context.view_name] = session["views"].get(context.view_name, 0) + 1
    
    def _integrate_with_memory_system(self, context: ApplicationMemoryContext, app_changed: bool):
        """Integrate application context with memory system"""
        try:
            if not self.memory_system:
                return
                
            # Create memory data for storage
            memory_data = {
                "type": "application_context",
                "timestamp": context.timestamp,
                "application": {
                    "name": context.app_name,
                    "category": context.app_category,
                    "view": context.view_name,
                    "workflow": context.workflow,
                    "confidence": context.confidence
                },
                "session_info": {
                    "duration": context.session_duration,
                    "previous_app": context.previous_app
                },
                "ui_elements": context.ui_elements[:5]  # Store first 5 elements for brevity
            }
            
            # Add to memory system if available
            if hasattr(self.memory_system, "add_memory_item"):
                # Store in memory system
                memory_id = self.memory_system.add_memory_item(memory_data)
                logger.info(f"Added application context to memory system with ID: {memory_id}")
                
                # Store memory reference
                if memory_id:
                    context.memory_references.append(memory_id)
            
            # If application changed, update conscious memory
            if app_changed and hasattr(self.memory_system, "conscious_memory"):
                app_switch_event = {
                    "type": "application_switch",
                    "timestamp": context.timestamp,
                    "from_app": context.previous_app,
                    "to_app": context.app_name,
                    "importance": 0.7  # App switches are moderately important
                }
                
                # Add to conscious buffer
                self.memory_system.conscious_memory.add_to_buffer("app_switches", app_switch_event)
                logger.info(f"Added application switch event to conscious memory: {context.previous_app} -> {context.app_name}")
            
            # Update search context with application info
            if hasattr(self.memory_system, "set_search_context"):
                search_context = {
                    "application": context.app_name,
                    "app_category": context.app_category,
                    "view": context.view_name
                }
                
                self.memory_system.set_search_context(search_context)
                logger.info(f"Updated memory search context with application: {context.app_name}")
            
        except Exception as e:
            logger.error(f"Error integrating with memory system: {e}")
    
    async def _perform_ui_analysis(self):
        """Perform detailed UI analysis asynchronously"""
        try:
            # Skip if no context
            if not self.current_app_context:
                return
                
            # Capture screenshot
            screenshot_path = f"{self.output_dir}/temp_screenshot.jpg"
            
            # Use app detector's screenshot function
            screenshot = self.app_detector._capture_screenshot()
            if not screenshot:
                logger.warning("Failed to capture screenshot for UI analysis")
                return
                
            # Save screenshot
            screenshot.save(screenshot_path)
            
            # Prepare app context
            app_context = {
                "app_name": self.current_app_context.app_name,
                "view_name": self.current_app_context.view_name
            }
            
            # Perform UI analysis
            ui_result = await self.ui_detector.detect_ui_elements(screenshot_path, app_context)
            
            # Update memory context with UI elements
            if ui_result and ui_result.elements:
                ui_elements = [asdict(elem) for elem in ui_result.elements]
                
                # Update current context
                self.current_app_context.ui_elements = ui_elements
                self.current_app_context.interaction_flows = ui_result.interaction_flows
                
                # Generate screen context description
                screen_context = self._generate_screen_context(ui_result, self.current_app_context.app_name)
                self.current_app_context.screen_context = screen_context
                
                # Integrate with memory if available
                if self.memory_system:
                    ui_memory_data = {
                        "type": "ui_analysis",
                        "timestamp": time.time(),
                        "application": self.current_app_context.app_name,
                        "view": self.current_app_context.view_name,
                        "ui_elements": ui_elements[:10],  # Store first 10 elements for brevity
                        "screen_context": screen_context
                    }
                    
                    # Add to memory system
                    if hasattr(self.memory_system, "add_memory_item"):
                        memory_id = self.memory_system.add_memory_item(ui_memory_data)
                        logger.info(f"Added UI analysis to memory system with ID: {memory_id}")
                        
                        # Store memory reference
                        if memory_id:
                            self.current_app_context.memory_references.append(memory_id)
                
                logger.info(f"UI analysis complete: {len(ui_elements)} elements detected")
                
            else:
                logger.warning("UI analysis did not detect any elements")
            
        except Exception as e:
            logger.error(f"Error performing UI analysis: {e}")
    
    def _generate_screen_context(self, ui_result: UIAnalysisResult, app_name: str) -> str:
        """Generate a text description of the screen context based on UI analysis"""
        try:
            # Start with basic info
            context_lines = [
                f"Application: {app_name}",
                f"View: {ui_result.view_name}",
                f"Elements: {len(ui_result.elements)} UI components detected"
            ]
            
            # Add top 5 most important elements
            important_elements = self._find_important_elements(ui_result.elements, app_name)
            if important_elements:
                context_lines.append("\nKey interface elements:")
                for i, elem in enumerate(important_elements[:5]):
                    context_lines.append(f"- {elem.element_type}: {elem.element_text}")
            
            # Add interaction flows if available
            if ui_result.interaction_flows:
                context_lines.append("\nPossible user workflows:")
                for i, flow in enumerate(ui_result.interaction_flows[:3]):
                    context_lines.append(f"- {flow.get('description', '')}")
            
            # Add application patterns if available
            if ui_result.app_specific_patterns:
                patterns = ui_result.app_specific_patterns.get("raw_text", "")
                if patterns:
                    # Extract first 200 chars max
                    pattern_summary = patterns[:200] + ("..." if len(patterns) > 200 else "")
                    context_lines.append(f"\nInterface patterns: {pattern_summary}")
            
            return "\n".join(context_lines)
        
        except Exception as e:
            logger.error(f"Error generating screen context: {e}")
            return f"Application: {app_name}"
    
    def _find_important_elements(self, elements, app_name: str):
        """Find the most important UI elements based on application type and element properties"""
        try:
            # Create scoring function based on app type
            def score_element(element):
                base_score = 0
                
                # Buttons are generally important
                if element.element_type.lower() == "button":
                    base_score += 5
                
                # Active input fields are important
                if element.element_type.lower() in ["textfield", "input"]:
                    base_score += 4
                
                # Main content areas are important
                if element.element_type.lower() in ["content", "main", "panel"]:
                    base_score += 4
                
                # Headers and titles are important for context
                if element.element_type.lower() in ["header", "title", "heading"]:
                    base_score += 3
                
                # App-specific scoring
                if "gmail" in app_name.lower():
                    email_terms = ["compose", "inbox", "send", "reply", "forward", "attach"]
                    if any(term in (element.element_text or "").lower() for term in email_terms):
                        base_score += 3
                elif "word" in app_name.lower() or "document" in app_name.lower():
                    doc_terms = ["save", "format", "style", "paragraph", "font", "edit"]
                    if any(term in (element.element_text or "").lower() for term in doc_terms):
                        base_score += 3
                elif "code" in app_name.lower() or "vscode" in app_name.lower():
                    code_terms = ["file", "edit", "debug", "terminal", "run", "search"]
                    if any(term in (element.element_text or "").lower() for term in code_terms):
                        base_score += 3
                
                # Prioritize elements with text
                if element.element_text:
                    base_score += 2
                
                # Prioritize interactive elements
                if element.interaction_hints:
                    base_score += 2
                
                # Elements with app-specific data are important
                if element.app_specific:
                    base_score += 3
                
                return base_score
            
            # Score and sort elements
            scored_elements = [(element, score_element(element)) for element in elements]
            scored_elements.sort(key=lambda x: x[1], reverse=True)
            
            # Return sorted elements
            return [element for element, score in scored_elements]
            
        except Exception as e:
            logger.error(f"Error finding important elements: {e}")
            return elements
    
    def _save_current_context(self, context: ApplicationMemoryContext):
        """Save current context to file"""
        try:
            context_file = f"{self.output_dir}/current_context.json"
            
            with open(context_file, 'w') as f:
                json.dump(context.to_dict(), f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving current context: {e}")
    
    def get_current_context(self) -> Optional[ApplicationMemoryContext]:
        """Get the current application context"""
        return self.current_app_context
    
    def get_context_history(self) -> List[ApplicationMemoryContext]:
        """Get the application context history"""
        return self.app_context_history
    
    def get_app_usage_statistics(self) -> Dict[str, Any]:
        """Get application usage statistics"""
        stats = {
            "total_apps": len(self.app_sessions),
            "apps": {}
        }
        
        # Collect stats for each app
        for app_name, session in self.app_sessions.items():
            # Calculate total time
            total_time = session["total_duration"]
            if session["current_duration"] > 0:
                total_time += session["current_duration"]
            
            # Add app stats
            stats["apps"][app_name] = {
                "total_time": total_time,
                "session_count": session["session_count"],
                "first_seen": session["first_seen"],
                "last_seen": session["last_seen"],
                "top_views": sorted(session["views"].items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
        return stats
    
    def boost_relevant_memories(self, query: str) -> float:
        """
        Boost relevance of app-related memories for a given query
        
        Args:
            query: The search query
            
        Returns:
            The boost factor applied
        """
        if not self.current_app_context or not self.memory_system:
            return 1.0
        
        # Only boost if we have a high-confidence app detection
        if self.current_app_context.confidence < 0.7:
            return 1.0
        
        try:
            # Set application context in memory search
            boost_factor = self.memory_boost_factor
            
            if hasattr(self.memory_system, "set_search_context"):
                context = {
                    "application": self.current_app_context.app_name,
                    "boost_factor": boost_factor,
                    "view": self.current_app_context.view_name,
                    "workflow": self.current_app_context.workflow
                }
                
                self.memory_system.set_search_context(context)
                logger.info(f"Boosted relevant memories for application: {self.current_app_context.app_name} with factor {boost_factor}")
            
            return boost_factor
            
        except Exception as e:
            logger.error(f"Error boosting relevant memories: {e}")
            return 1.0
    
    def integrate_llm_request(self, query: str, response: str) -> None:
        """
        Integrate an LLM request with application context
        
        Args:
            query: The user query
            response: The LLM response
        """
        if not self.current_app_context:
            return
            
        try:
            # Create memory entry for LLM interaction
            memory_data = {
                "type": "llm_interaction",
                "timestamp": time.time(),
                "application": {
                    "name": self.current_app_context.app_name,
                    "view": self.current_app_context.view_name,
                    "workflow": self.current_app_context.workflow
                },
                "query": query,
                "response_length": len(response),
                "application_relevant": self._is_query_app_relevant(query, self.current_app_context.app_name)
            }
            
            # Add to memory system if available
            if self.memory_system and hasattr(self.memory_system, "add_memory_item"):
                memory_id = self.memory_system.add_memory_item(memory_data)
                logger.info(f"Added LLM interaction to memory system with ID: {memory_id}")
                
                # Store memory reference
                if memory_id and self.current_app_context:
                    self.current_app_context.memory_references.append(memory_id)
            
        except Exception as e:
            logger.error(f"Error integrating LLM request: {e}")
    
    def _is_query_app_relevant(self, query: str, app_name: str) -> bool:
        """Check if a query is relevant to the current application"""
        if not query or not app_name:
            return False
            
        query = query.lower()
        app_name = app_name.lower()
        
        # Check for app name in query
        if app_name in query:
            return True
            
        # Check for app-specific terms
        app_specific_terms = {
            "gmail": ["email", "message", "inbox", "compose", "send", "unread"],
            "word": ["document", "paragraph", "format", "edit", "text", "write"],
            "excel": ["spreadsheet", "cell", "formula", "row", "column", "calculate"],
            "powerpoint": ["slide", "presentation", "deck", "animate", "transition"],
            "code": ["file", "code", "debug", "function", "class", "method", "compile"],
            "chrome": ["website", "webpage", "browser", "tab", "bookmark", "history"],
            "slack": ["message", "channel", "direct", "team", "workspace", "chat"]
        }
        
        # Find the most relevant app key
        app_key = None
        for key in app_specific_terms:
            if key in app_name:
                app_key = key
                break
                
        # Check terms for the app
        if app_key and app_key in app_specific_terms:
            terms = app_specific_terms[app_key]
            if any(term in query for term in terms):
                return True
                
        return False

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Application-Aware Memory Integration")
    parser.add_argument("--show-context", action="store_true", help="Show current application context")
    parser.add_argument("--show-stats", action="store_true", help="Show application usage statistics")
    parser.add_argument("--run", action="store_true", help="Run the memory integration service")
    parser.add_argument("--time", type=int, default=300, help="Run time in seconds for service (default: 300)")
    parser.add_argument("--llava-url", default="http://localhost:11434", help="URL for Ollama API (default: http://localhost:11434)")
    parser.add_argument("--boost-query", help="Test memory boosting with a query")
    
    args = parser.parse_args()
    
    # Create memory integration system
    integrator = AppAwareMemoryIntegrator(llava_url=args.llava_url)
    
    # Show current context if requested
    if args.show_context:
        context = integrator.get_current_context()
        if context:
            print("\n===== CURRENT APPLICATION CONTEXT =====")
            print(f"Application: {context.app_name}")
            print(f"Category: {context.app_category}")
            print(f"View: {context.view_name}")
            print(f"Workflow: {context.workflow}")
            print(f"Session duration: {context.session_duration:.2f} seconds")
            print(f"Confidence: {context.confidence:.2f}")
            
            if context.ui_elements:
                print(f"\nUI Elements: {len(context.ui_elements)} detected")
                for i, elem in enumerate(context.ui_elements[:5]):
                    print(f"  {i+1}. {elem.get('element_type', 'Unknown')}: {elem.get('element_text', '')}")
            
            print("=======================================")
        else:
            print("No current application context available")
    
    # Show application statistics if requested
    if args.show_stats:
        stats = integrator.get_app_usage_statistics()
        
        print("\n===== APPLICATION USAGE STATISTICS =====")
        print(f"Total applications detected: {stats['total_apps']}")
        
        for app_name, app_stats in sorted(stats["apps"].items(), 
                                         key=lambda x: x[1]["total_time"], 
                                         reverse=True):
            total_time_mins = app_stats["total_time"] / 60
            print(f"\n{app_name}:")
            print(f"  Total time: {total_time_mins:.2f} minutes")
            print(f"  Sessions: {app_stats['session_count']}")
            print("  Top views:")
            for view, count in app_stats["top_views"]:
                print(f"    - {view}: {count} times")
        
        print("=======================================")
    
    # Test memory boosting if requested
    if args.boost_query:
        boost_factor = integrator.boost_relevant_memories(args.boost_query)
        
        print(f"\nQuery: {args.boost_query}")
        print(f"Memory boost factor: {boost_factor}")
        
        context = integrator.get_current_context()
        if context:
            print(f"Current application: {context.app_name}")
            print(f"Is query app-relevant: {integrator._is_query_app_relevant(args.boost_query, context.app_name)}")
    
    # Run service if requested
    if args.run:
        print(f"Starting application-aware memory integration for {args.time} seconds")
        
        # Start integration
        integrator.start()
        
        # Run for specified time
        try:
            for i in range(args.time):
                await asyncio.sleep(1)
                if i % 10 == 0:  # Status every 10 seconds
                    context = integrator.get_current_context()
                    if context:
                        print(f"Current app: {context.app_name} (view: {context.view_name}, workflow: {context.workflow})")
        except KeyboardInterrupt:
            print("\nStopping integration due to user interrupt")
        finally:
            # Stop integration
            integrator.stop()
        
        # Final summary
        context_history = integrator.get_context_history()
        print(f"\nDetected {len(context_history)} application context changes")
        
        # Show top applications
        app_counts = {}
        for context in context_history:
            app_counts[context.app_name] = app_counts.get(context.app_name, 0) + 1
            
        print("\nTop applications:")
        for app, count in sorted(app_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {app}: {count} times")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nScript terminated by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)