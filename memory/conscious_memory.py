"""
Conscious Memory Module
Processes sensor data and generates meaningful insights using LLM.
"""
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
import traceback

# Configure logging with optimized settings
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure file handler with rotation
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    'logs/aiayer.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)  # Changed from WARNING to INFO
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Configure console handler with reduced output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Changed from ERROR to INFO
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)  # Changed from WARNING to INFO

class ConsciousMemory:
    """Acts as a middle layer to process sensor data and feed it to the main memory system."""
    
    def __init__(self, llm_provider, memory_system):
        self.llm_provider = llm_provider
        self.memory_system = memory_system
        self.logger = logger  # Use the configured logger
        
        # Buffer for sensor data
        self.sensor_buffer = {
            'screen': [],
            'process': [],
            'file': []
        }
        self.max_buffer_size = 15  # Maximum number of entries per sensor type (increased)
        self.processing_interval = 15  # Process every 15 seconds (faster response)
        self.last_processing_time = time.time()
        
        # Initialize processing task
        self.processing_task = None
        self.running = False
        
        self.logger.info("[ConsciousMemory] Initialized as middle layer for memory system")
    
    async def add_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> bool:
        """Add sensor data to the buffer and process it."""
        try:
            self.logger.info(f"[ConsciousMemory] Adding {sensor_type} sensor data")
            
            # Validate input
            if not isinstance(data, dict):
                self.logger.error(f"[ConsciousMemory] Invalid data type: {type(data)}")
                return False
                
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
                
            # Add to buffer
            if sensor_type not in self.sensor_buffer:
                self.sensor_buffer[sensor_type] = []
                
            # Add new data to buffer
            self.sensor_buffer[sensor_type].append(data)
            
            # Keep buffer size within limits
            if len(self.sensor_buffer[sensor_type]) > self.max_buffer_size:
                self.sensor_buffer[sensor_type] = self.sensor_buffer[sensor_type][-self.max_buffer_size:]
                
            self.logger.info(f"[ConsciousMemory] Added {sensor_type} data to buffer. Buffer size: {len(self.sensor_buffer[sensor_type])}")
            
            # Process the data
            try:
                processed_data = await self._process_sensor_data(sensor_type, data)
                if processed_data:
                    # Feed to memory system
                    await self._feed_to_memory(processed_data)
                    self.logger.info(f"[ConsciousMemory] Successfully processed and stored {sensor_type} data")
                    return True
                else:
                    self.logger.warning(f"[ConsciousMemory] Failed to process {sensor_type} data")
                    return False
            except Exception as e:
                self.logger.error(f"[ConsciousMemory] Error processing {sensor_type} data: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"[ConsciousMemory] Error adding sensor data: {e}")
            return False
    
    async def _feed_to_memory(self, data: Dict[str, Any]) -> bool:
        """Feed processed data to the memory system."""
        try:
            if not data:
                return False
                
            self.logger.info("[ConsciousMemory] Feeding data to memory system")
            
            # Determine memory type based on data characteristics
            memory_type = self._determine_memory_type(data)
            
            # Add to appropriate memory
            if memory_type == 'short_term':
                await self.memory_system.add_to_short_term_memory(data)
                self.logger.info("[ConsciousMemory] Added to short-term memory")
            elif memory_type == 'context':
                await self.memory_system.add_to_context_memory(data)
                self.logger.info("[ConsciousMemory] Added to context memory")
            elif memory_type == 'long_term':
                await self.memory_system.add_to_long_term_memory(data)
                self.logger.info("[ConsciousMemory] Added to long-term memory")
                
            return True
            
        except Exception as e:
            self.logger.error(f"[ConsciousMemory] Error feeding to memory: {e}")
            return False
    
    def _determine_memory_type(self, data: Dict[str, Any]) -> str:
        """Determine which memory type to use based on data characteristics."""
        try:
            # Check for high significance
            if data.get('significance', 0) >= 0.8:
                return 'long_term'
                
            # Check for context relevance
            if data.get('sensor_type') in ['screen', 'process']:
                return 'context'
                
            # Default to short-term memory
            return 'short_term'
            
        except Exception as e:
            self.logger.error(f"[ConsciousMemory] Error determining memory type: {e}")
            return 'short_term'  # Default to short-term on error
    
    async def _process_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sensor data before feeding to memory system with enhanced insight extraction.
        Performs deeper analysis to extract meaningful information including context, 
        application-specific understanding, and relationships between items.
        """
        try:
            self.logger.info(f"[ConsciousMemory] Starting _process_sensor_data for {sensor_type}")
            
            # Ensure data is a dictionary
            if not isinstance(data, dict):
                self.logger.error(f"[ConsciousMemory] Invalid data type for {sensor_type}: {type(data)}")
                return None
                
            # Create base processed data with enhanced structure
            processed_data = {
                "timestamp": datetime.now().isoformat(),
                "sensor_type": sensor_type,
                "is_significant": data.get("is_significant_action", False),  # Use action significance flag
                "processed_by": "conscious_memory",  # Mark as processed by conscious memory
                "memory_relationships": [],  # New field to track relationships between memory items
                "insights": []  # New field for extracted insights
            }
            
            # Process based on sensor type with enhanced meaning extraction
            if sensor_type == "screen":
                # Extract standard screen data and ensure it's not empty
                window_title = data.get("active_window", data.get("window_title", "Unknown Window"))
                screen_content = data.get("text", data.get("screen_content", ""))
                
                processed_data.update({
                    "window_title": window_title,
                    "screen_content": screen_content,
                    # Extract active app from window title if not present
                    "active_app": data.get("active_app", window_title.split(" - ")[0] if " - " in window_title else window_title)
                })
                
                # Add basic window insight regardless of other data
                window_insight = f"Active window: {window_title}"
                processed_data["insights"].append({
                    "type": "window",
                    "content": window_insight
                })
                
                # Add screen content insight if available
                if screen_content:
                    # Truncate to prevent excessively large context
                    content_preview = screen_content[:200] + ("..." if len(screen_content) > 200 else "")
                    processed_data["insights"].append({
                        "type": "screen_content",
                        "content": f"Screen content: {content_preview}"
                    })
                
                # Enhanced application context extraction
                if data.get("application"):
                    self.logger.info("Adding enhanced application context to conscious memory")
                    app_data = data.get("application")
                    
                    # Store original application data
                    processed_data["application"] = app_data
                    
                    # Extract additional context understanding
                    if isinstance(app_data, dict):
                        # Create a meaningful summary of what the user is doing
                        activity_context = []
                        
                        # Application name and view
                        if app_data.get("name"):
                            activity_context.append(f"Using {app_data['name']}")
                            # Ensure active_app is set
                            processed_data["active_app"] = app_data["name"]
                        if app_data.get("view"):
                            activity_context.append(f"in {app_data['view']} view")
                            
                        # User workflow/task (most important for understanding)
                        if app_data.get("workflow_stage"):
                            activity_context.append(app_data["workflow_stage"])
                            # Mark as significant if we have workflow information
                            processed_data["is_significant"] = True
                            
                        # Create a meaningful activity summary
                        if activity_context:
                            processed_data["activity_summary"] = " ".join(activity_context)
                            # Add as an insight
                            processed_data["insights"].append({
                                "type": "activity",
                                "content": processed_data["activity_summary"]
                            })
                
                # Enhanced email context extraction
                if data.get("email_data"):
                    self.logger.info("Adding enriched email context to conscious memory")
                    email_data = data.get("email_data")
                    processed_data["email_data"] = email_data
                    processed_data["is_significant"] = True  # Email data is always significant
                    
                    # Create meaningful email insights
                    if isinstance(email_data, dict):
                        email_context = []
                        if email_data.get("from"):
                            email_context.append(f"From: {email_data['from']}")
                        if email_data.get("to"):
                            email_context.append(f"To: {email_data['to']}")
                        if email_data.get("subject"):
                            email_context.append(f"Subject: {email_data['subject']}")
                            
                        if email_context:
                            email_summary = "Email: " + " | ".join(email_context)
                            processed_data["email_summary"] = email_summary
                            processed_data["insights"].append({
                                "type": "email",
                                "content": email_summary
                            })
                
                # Enhanced form interaction understanding
                if data.get("form_data"):
                    self.logger.info("Adding enriched form interaction context to conscious memory")
                    form_data = data.get("form_data")
                    processed_data["form_data"] = form_data
                    processed_data["is_significant"] = True  # Form interaction is always significant
                    
                    # Create meaningful form insights
                    if isinstance(form_data, dict) and form_data.get("form_fields"):
                        form_fields = form_data["form_fields"]
                        if isinstance(form_fields, list) and form_fields:
                            form_summary = f"Interacting with form fields: {', '.join(form_fields[:5])}"
                            if len(form_fields) > 5:
                                form_summary += f" and {len(form_fields) - 5} more"
                            processed_data["form_summary"] = form_summary
                            processed_data["insights"].append({
                                "type": "form_interaction",
                                "content": form_summary
                            })
                
                # Enhanced LLaVA analysis processing - This is critical for "what am I seeing" queries
                if data.get("llava_description") or data.get("visual_context"):
                    self.logger.info("Adding enhanced LLaVA analysis to conscious memory")
                    
                    # Store original LLaVA data
                    visual_context = data.get("visual_context", "")
                    llava_description = data.get("llava_description", "")
                    
                    processed_data.update({
                        "llava_description": llava_description,
                        "visual_context": visual_context,
                        "has_llava_data": True
                    })
                    
                    # Extract meaningful insights from LLaVA analysis
                    if visual_context:
                        # Mark as significant if LLaVA detected meaningful content
                        processed_data["is_significant"] = True
                        
                        # Add as an insight - prioritize this for "what am I seeing" queries
                        processed_data["insights"].append({
                            "type": "visual_understanding",
                            "content": f"Visual content: {visual_context[:250]}" + ("..." if len(visual_context) > 250 else "")
                        })
                    
                    # Add LLaVA description as a separate insight if available
                    if llava_description:
                        processed_data["insights"].append({
                            "type": "llava_description",
                            "content": f"LLaVA description: {llava_description[:250]}" + ("..." if len(llava_description) > 250 else "")
                        })
                    
                    # Process UI elements with enhanced understanding
                    screen_elements = data.get("screen_elements", [])
                    if screen_elements and isinstance(screen_elements, list):
                        # Filter to keep only meaningful elements (max 20)
                        important_elements = screen_elements[:20]
                        processed_data["screen_elements"] = important_elements
                        
                        # Extract interactive elements for better understanding of activity
                        interactive_elements = []
                        for element in important_elements:
                            if isinstance(element, dict):
                                element_type = element.get("type", "")
                                element_name = element.get("name", "")
                                
                                # Focus on interactive UI elements
                                if element_type in ["button", "input_field", "dropdown", "checkbox", "link"] and element_name:
                                    interactive_elements.append(f"{element_name} ({element_type})")
                        
                        # Add interactive elements summary if found
                        if interactive_elements:
                            interactive_summary = "Interactive elements: " + ", ".join(interactive_elements[:5])
                            if len(interactive_elements) > 5:
                                interactive_summary += f" and {len(interactive_elements) - 5} more"
                            processed_data["interactive_elements_summary"] = interactive_summary
                            processed_data["insights"].append({
                                "type": "interactive_elements",
                                "content": interactive_summary
                            })
                
                # Combine various insights into a unified context understanding
                if processed_data.get("insights"):
                    # Create a consolidated understanding of what the user is doing
                    context_parts = []
                    
                    # Add activity summary if available (highest priority)
                    if processed_data.get("activity_summary"):
                        context_parts.append(processed_data["activity_summary"])
                    
                    # Add email context if available
                    if processed_data.get("email_summary"):
                        context_parts.append(processed_data["email_summary"])
                    
                    # Add form context if available
                    if processed_data.get("form_summary"):
                        context_parts.append(processed_data["form_summary"])
                    
                    # Add interactive elements context if available
                    if processed_data.get("interactive_elements_summary"):
                        context_parts.append(processed_data["interactive_elements_summary"])
                    
                    # Create the unified context understanding
                    if context_parts:
                        processed_data["context_understanding"] = " | ".join(context_parts)
                        self.logger.info(f"Created unified context understanding: {processed_data['context_understanding']}")
                
            elif sensor_type == "process":
                # Enhanced process data extraction
                active_processes = data.get("active_processes", [])
                if isinstance(active_processes, list):
                    # Extract minimal required process information
                    processed_processes = []
                    for proc in active_processes:
                        if isinstance(proc, dict):
                            processed_processes.append({
                                "name": proc.get("name", ""),
                                "pid": proc.get("pid", 0)
                                # Removed detailed metrics to save memory
                            })
                    processed_data["active_processes"] = processed_processes
                    
                # Enhanced active apps categorization and understanding
                active_apps = data.get("active_apps", [])
                if isinstance(active_apps, list):
                    # Process each app entry - just keep names
                    processed_apps = []
                    for app in active_apps:
                        if isinstance(app, dict):
                            # Extract name from dictionary
                            name = app.get("name", "")
                            if name:  # Only add if name exists
                                processed_apps.append(name)
                        elif isinstance(app, str):
                            # Use string directly
                            processed_apps.append(app)
                        else:
                            self.logger.warning(f"Skipping invalid app entry type: {type(app)}")
                    processed_data["active_apps"] = processed_apps
                    
                    # Generate insights about application patterns
                    if len(processed_apps) > 0:
                        # Categorize apps for better understanding
                        app_categories = {
                            "browsers": [],
                            "productivity": [],
                            "development": [],
                            "communication": [],
                            "media": [],
                            "system": []
                        }
                        
                        # Simple categorization logic
                        for app in processed_apps:
                            app_lower = app.lower()
                            if any(browser in app_lower for browser in ["chrome", "firefox", "safari", "edge", "opera", "brave"]):
                                app_categories["browsers"].append(app)
                            elif any(dev in app_lower for dev in ["code", "vscode", "studio", "intellij", "pycharm", "compiler", "terminal"]):
                                app_categories["development"].append(app)
                            elif any(comm in app_lower for comm in ["slack", "teams", "zoom", "meet", "discord", "mail", "outlook"]):
                                app_categories["communication"].append(app)
                            elif any(prod in app_lower for prod in ["office", "word", "excel", "powerpoint", "docs", "sheets", "notion"]):
                                app_categories["productivity"].append(app)
                            elif any(media in app_lower for media in ["spotify", "netflix", "youtube", "player", "vlc", "music", "photo"]):
                                app_categories["media"].append(app)
                            else:
                                app_categories["system"].append(app)
                        
                        # Generate insights based on app categories
                        category_insights = []
                        for category, apps in app_categories.items():
                            if apps:
                                category_insights.append(f"{len(apps)} {category} apps")
                                
                        if category_insights:
                            app_insight = "Running " + ", ".join(category_insights)
                            processed_data["app_category_insight"] = app_insight
                            processed_data["insights"].append({
                                "type": "application_pattern",
                                "content": app_insight
                            })
                    
                # Mark process data as significant if it contains interesting patterns
                if processed_data.get("insights"):
                    processed_data["is_significant"] = True
                else:
                    processed_data["is_significant"] = data.get("is_significant", False)
                    
            elif sensor_type == "file":
                # Enhanced file event understanding
                processed_data.update({
                    "file_path": data.get("file_path", ""),
                    "file_type": data.get("file_type", ""),
                    "file_event": data.get("file_event", "")
                })
                
                # Generate insights about file interactions
                file_path = data.get("file_path", "")
                file_event = data.get("file_event", "")
                
                if file_path and file_event:
                    # Extract filename and extension
                    import os
                    filename = os.path.basename(file_path) if file_path else "Unknown file"
                    file_ext = os.path.splitext(filename)[1].lower() if filename else ""
                    
                    # Categorize file type
                    file_category = "unknown"
                    if file_ext:
                        if file_ext in [".py", ".js", ".java", ".cpp", ".c", ".h", ".ts", ".go", ".rb", ".php"]:
                            file_category = "code"
                        elif file_ext in [".doc", ".docx", ".pdf", ".txt", ".md", ".rtf"]:
                            file_category = "document"
                        elif file_ext in [".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp"]:
                            file_category = "image"
                        elif file_ext in [".mp3", ".wav", ".ogg", ".flac", ".aac"]:
                            file_category = "audio"
                        elif file_ext in [".mp4", ".avi", ".mov", ".mkv", ".wmv"]:
                            file_category = "video"
                        elif file_ext in [".xls", ".xlsx", ".csv", ".tsv"]:
                            file_category = "spreadsheet"
                        elif file_ext in [".json", ".xml", ".yaml", ".yml", ".toml"]:
                            file_category = "data"
                    
                    # Create meaningful file insight
                    file_insight = f"{file_event} {file_category} file: {filename}"
                    processed_data["file_insight"] = file_insight
                    processed_data["insights"].append({
                        "type": "file_interaction",
                        "content": file_insight
                    })
                    
                    # Mark as significant based on file event type
                    if file_event.lower() in ["created", "modified", "edited", "deleted"]:
                        processed_data["is_significant"] = True
                
            # Create a content field for search based on insights
            if processed_data.get("insights"):
                content_parts = [insight["content"] for insight in processed_data["insights"]]
                processed_data["content"] = " | ".join(content_parts)
            else:
                # Fallback content field if no insights generated
                if sensor_type == "screen":
                    processed_data["content"] = processed_data.get("screen_content", "")[:200]
                elif sensor_type == "process":
                    app_names = ", ".join(processed_data.get("active_apps", [])[:5])
                    processed_data["content"] = f"Active window: {processed_data.get('window_title', 'Unknown')} | Apps: {app_names}"
                elif sensor_type == "file":
                    processed_data["content"] = f"File event: {processed_data.get('file_event', '')} on {processed_data.get('file_path', '')}"
            
            # Validate processed data
            if not all(key in processed_data for key in ["timestamp", "sensor_type", "content"]):
                self.logger.error(f"Missing required fields in processed data for {sensor_type}")
                return None
                
            # Log the size of processed data for monitoring
            self.logger.debug(f"Enhanced processed {sensor_type} data size: {len(str(processed_data))} chars")
            self.logger.info(f"Generated {len(processed_data.get('insights', []))} insights from {sensor_type} data")
            
            self.logger.info(f"[ConsciousMemory] Completed processing {sensor_type} sensor data")
            return processed_data
            
        except Exception as e:
            self.logger.error(f"[ConsciousMemory] Error processing sensor data: {str(e)}", exc_info=True)
            return None
    
    async def process_data(self) -> bool:
        """Process buffered sensor data using LLM for insights."""
        try:
            current_time = time.time()
            if current_time - self.last_processing_time < self.processing_interval:
                return False
                
            self.logger.info("[ConsciousMemory] Starting periodic processing of buffered data...")
            
            # Prepare context for LLM
            context = await self._prepare_context()
            if not context:
                self.logger.warning("[ConsciousMemory] No context available for processing")
                return False
            
            # Generate prompt for LLM
            prompt = self._generate_analysis_prompt(context)
            if not prompt:
                self.logger.warning("[ConsciousMemory] Failed to generate analysis prompt")
                return False
            
            # Log the prompt
            self.logger.info("[ConsciousMemory] Generated LLM prompt:\n%s", prompt)
            
            # Get LLM analysis
            self.logger.info("[ConsciousMemory] Requesting LLM analysis...")
            response = await self.llm_provider.generate_response(prompt)
            if not response or 'response' not in response:
                self.logger.warning("[ConsciousMemory] No response from LLM")
                return False
            
            # Log the LLM response
            self.logger.info("[ConsciousMemory] Received LLM response:\n%s", response['response'])
            
            # Create insight data
            insight_data = {
                'type': 'insight',
                'content': response['response'],
                'timestamp': time.time(),
                'context': {
                    'screen_data': context.get('screen_data', []),
                    'process_data': context.get('process_data', []),
                    'file_data': context.get('file_data', [])
                }
            }
            
            # Store insights in both long-term and contextual memory
            self.logger.info("[LongTermMemory] Storing LLM insights with context:")
            self.logger.info("[LongTermMemory] - Screen data: %d entries", len(insight_data['context']['screen_data']))
            self.logger.info("[LongTermMemory] - Process data: %d entries", len(insight_data['context']['process_data']))
            self.logger.info("[LongTermMemory] - File data: %d entries", len(insight_data['context']['file_data']))
            await self.memory_system.add_to_long_term_memory(insight_data)
            
            self.logger.info("[ContextMemory] Storing LLM insights with context:")
            self.logger.info("[ContextMemory] - Screen data: %d entries", len(insight_data['context']['screen_data']))
            self.logger.info("[ContextMemory] - Process data: %d entries", len(insight_data['context']['process_data']))
            self.logger.info("[ContextMemory] - File data: %d entries", len(insight_data['context']['file_data']))
            await self.memory_system.add_to_context_memory(insight_data)
            
            self.logger.info("[ConsciousMemory] Successfully stored insights in both long-term and contextual memory")
            
            # Clear the buffer to make room for new data
            self._clear_processed_data()
            self.logger.info("[ConsciousMemory] Cleared buffer to prepare for next processing cycle")
            
            self.last_processing_time = current_time
            self.logger.info("[ConsciousMemory] Completed processing cycle. Next cycle in %d seconds", self.processing_interval)
            return True
            
        except Exception as e:
            self.logger.error("[ConsciousMemory] Error processing data: %s", str(e), exc_info=True)
            return False
    
    async def _prepare_context(self) -> Dict[str, Any]:
        """Prepare context from buffered sensor data."""
        try:
            context = {
                'timestamp': time.time(),
                'screen_data': [],
                'process_data': [],
                'file_data': []
            }
            
            # Add screen data
            if self.sensor_buffer['screen']:
                context['screen_data'] = self.sensor_buffer['screen']
            
            # Add process data
            if self.sensor_buffer['process']:
                context['process_data'] = self.sensor_buffer['process']
            
            # Add file data
            if self.sensor_buffer['file']:
                context['file_data'] = self.sensor_buffer['file']
            
            return context
            
        except Exception as e:
            self.logger.error("Error preparing context: %s", str(e), exc_info=True)
            return {}
    
    def _generate_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """
        Generate enhanced prompt for LLM analysis with application-specific context understanding.
        This prompt provides much more detailed information about what the user is doing in specific applications.
        """
        try:
            prompt = "# System State Analysis - Application-Aware\n\n"
            prompt += "You are an AI assistant that provides precise insights about the user's current activities with special focus on application-specific contexts.\n\n"
            
            # Add application-specific data with highest priority
            if context.get('screen_data'):
                # Check for application data in any of the recent screen captures
                screen_with_app_data = [data for data in context['screen_data'][:3] 
                                       if data.get('application') or data.get('email_data') or data.get('form_data')]
                
                if screen_with_app_data:
                    prompt += "## Application Context\n"
                    
                    # Add application context information
                    app_contexts = []
                    for data in screen_with_app_data:
                        app_context = []
                        
                        # Get application name, view and workflow stage
                        if data.get('application'):
                            app = data['application']
                            if app.get('name'):
                                app_context.append(f"Application: {app['name']}")
                            if app.get('view'):
                                app_context.append(f"View/Mode: {app['view']}")
                            if app.get('workflow_stage'):
                                app_context.append(f"User Task: {app['workflow_stage']}")
                        
                        # Get email-specific data
                        if data.get('email_data'):
                            email = data['email_data']
                            email_parts = []
                            if email.get('from'):
                                email_parts.append(f"From: {email['from']}")
                            if email.get('to'):
                                email_parts.append(f"To: {email['to']}")
                            if email.get('subject'):
                                email_parts.append(f"Subject: {email['subject']}")
                            
                            if email_parts:
                                app_context.append("Email: " + ", ".join(email_parts))
                        
                        # Get form data
                        if data.get('form_data') and data['form_data'].get('form_fields'):
                            form_fields = data['form_data']['form_fields']
                            app_context.append(f"Form fields: {', '.join(form_fields[:5])}")
                            
                        if app_context:
                            app_contexts.append(" | ".join(app_context))
                    
                    if app_contexts:
                        prompt += "User's application context:\n"
                        for i, context_text in enumerate(app_contexts):
                            prompt += f"{i+1}. {context_text}\n"
                    
                    # Add UI elements with enhanced type information
                    typed_ui_elements = []
                    for data in screen_with_app_data:
                        if data.get('screen_elements') and isinstance(data['screen_elements'], list):
                            for element in data['screen_elements'][:10]:
                                if isinstance(element, dict):
                                    element_type = element.get('type', 'unknown')
                                    element_name = element.get('name', element.get('element', ''))
                                    element_state = element.get('state', '')
                                    
                                    element_desc = f"{element_type}: {element_name}"
                                    if element_state:
                                        element_desc += f" ({element_state})"
                                    
                                    typed_ui_elements.append(element_desc)
                    
                    if typed_ui_elements:
                        prompt += "\nUI elements visible on screen:\n"
                        for element in typed_ui_elements[:10]:
                            prompt += f"- {element}\n"
                
                # Add LLaVA visual understanding
                screen_with_llava = [data for data in context['screen_data'][:3] 
                                    if data.get('llava_description') or data.get('visual_context')]
                
                if screen_with_llava:
                    prompt += "\n## Visual Context (from LLaVA)\n"
                    
                    # Add visual contexts from LLaVA (more useful than raw descriptions)
                    visual_contexts = []
                    for data in screen_with_llava:
                        if data.get('visual_context'):
                            visual_contexts.append(data['visual_context'])
                    
                    if visual_contexts:
                        prompt += "User's screen visual context:\n"
                        for i, context_text in enumerate(visual_contexts):
                            prompt += f"{i+1}. {context_text}\n"
                
                # Include OCR text as backup, but less prominent
                prompt += "\n## Screen Text Content (OCR)\n"
                for i, data in enumerate(context['screen_data'][:2]):
                    if 'screen_content' in data and data['screen_content']:
                        # Trim very long text to avoid prompt bloat
                        text = data['screen_content']
                        if len(text) > 500:
                            text = text[:500] + "... (truncated)"
                        prompt += f"Screen {i+1}: {text}\n\n"
                
                # Add window titles
                window_titles = [data.get('window_title') for data in context['screen_data'][:3] 
                                if data.get('window_title')]
                if window_titles:
                    prompt += "Active windows:\n"
                    for title in window_titles:
                        prompt += f"- {title}\n"
            
            # Add active processes with better formatting
            if context.get('process_data'):
                prompt += "\n## Active Applications\n"
                # Get the most recent process data
                recent_process = context['process_data'][0] if context['process_data'] else None
                if recent_process and 'active_apps' in recent_process:
                    active_apps = recent_process['active_apps']
                    # Group by app type for better analysis
                    app_categories = {
                        "Browsers": [],
                        "Editors/IDEs": [],
                        "Communication": [],
                        "Productivity": [],
                        "Media": [],
                        "Other": []
                    }
                    
                    browser_keywords = ["chrome", "firefox", "safari", "edge", "opera", "brave"]
                    editor_keywords = ["vscode", "intellij", "idea", "pycharm", "webstorm", "eclipse", "sublime", "vim", "emacs", "atom", "notepad", "code", "xcode"]
                    comm_keywords = ["slack", "discord", "teams", "zoom", "skype", "telegram", "whatsapp", "signal", "messenger"]
                    prod_keywords = ["office", "word", "excel", "powerpoint", "sheets", "docs", "notion", "evernote", "onenote"]
                    media_keywords = ["spotify", "itunes", "netflix", "youtube", "vlc", "quicktime", "photos", "gimp", "photoshop"]
                    
                    for app in active_apps:
                        app_lower = app.lower()
                        if any(kw in app_lower for kw in browser_keywords):
                            app_categories["Browsers"].append(app)
                        elif any(kw in app_lower for kw in editor_keywords):
                            app_categories["Editors/IDEs"].append(app)
                        elif any(kw in app_lower for kw in comm_keywords):
                            app_categories["Communication"].append(app)
                        elif any(kw in app_lower for kw in prod_keywords):
                            app_categories["Productivity"].append(app)
                        elif any(kw in app_lower for kw in media_keywords):
                            app_categories["Media"].append(app)
                        else:
                            app_categories["Other"].append(app)
                    
                    # Add categorized apps to prompt
                    for category, apps in app_categories.items():
                        if apps:
                            prompt += f"{category}: {', '.join(apps)}\n"
            
            # Add file changes with better organization
            if context.get('file_data'):
                prompt += "\n## File Activity\n"
                # Group files by extension/type
                file_extensions = {}
                
                for data in context['file_data'][:3]:
                    if 'events' in data and isinstance(data['events'], list):
                        for event in data['events']:
                            if isinstance(event, dict) and 'path' in event:
                                path = event['path']
                                # Get extension
                                ext = path.split('.')[-1] if '.' in path else 'unknown'
                                if ext not in file_extensions:
                                    file_extensions[ext] = []
                                file_extensions[ext].append(path)
                
                # Add files by type
                for ext, files in file_extensions.items():
                    prompt += f"{ext.upper()} Files: {', '.join(files[:3])}"
                    if len(files) > 3:
                        prompt += f" and {len(files) - 3} more"
                    prompt += "\n"
            
            # Enhanced analysis request
            prompt += "\n## Analysis Request\n"
            prompt += "Based on all the information above, please provide detailed insights about:\n\n"
            prompt += "1. What the user is currently working on (be specific about project, task, and context)\n"
            prompt += "2. What tools/applications they're using and how they're using them\n"
            prompt += "3. Key content they're interacting with (documents, websites, applications, code)\n"
            prompt += "4. Important context that should be remembered for future interactions\n"
            prompt += "5. User's workflow patterns or preferences\n\n"
            prompt += "Make your analysis detailed, insightful, and directly connected to the specific evidence provided above."
            
            return prompt
            
        except Exception as e:
            self.logger.error("Error generating analysis prompt: %s", str(e), exc_info=True)
            return ""
    
    def _clear_processed_data(self):
        """Clear processed data from buffers."""
        try:
            for sensor_type in self.sensor_buffer:
                self.sensor_buffer[sensor_type] = []
        except Exception as e:
            self.logger.error("Error clearing processed data: %s", str(e), exc_info=True)
    
    async def start(self):
        """Start the conscious memory processing loop."""
        try:
            self.running = True
            self.processing_task = asyncio.create_task(self._processing_loop())
            self.logger.info("[ConsciousMemory] Started processing loop")
            return True
        except Exception as e:
            self.logger.error("[ConsciousMemory] Error starting processing loop: %s", str(e), exc_info=True)
            return False
    
    async def stop(self):
        """Stop the conscious memory processing loop."""
        try:
            self.running = False
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
            self.logger.info("[ConsciousMemory] Stopped processing loop")
            return True
        except Exception as e:
            self.logger.error("[ConsciousMemory] Error stopping processing loop: %s", str(e), exc_info=True)
            return False
    
    async def _processing_loop(self):
        """Main processing loop for conscious memory."""
        try:
            while self.running:
                await self.process_data()
                await asyncio.sleep(self.processing_interval)
        except asyncio.CancelledError:
            self.logger.info("[ConsciousMemory] Processing loop cancelled")
        except Exception as e:
            self.logger.error("[ConsciousMemory] Error in processing loop: %s", str(e), exc_info=True)
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current state of conscious memory."""
        try:
            return {
                'sensor_buffer': self.sensor_buffer,
                'last_processing_time': self.last_processing_time,
                'running': self.running
            }
        except Exception as e:
            self.logger.error("Error getting conscious memory state: %s", str(e), exc_info=True)
            return {}
    
    def clear(self):
        """Clear all conscious memory data."""
        try:
            self._clear_processed_data()
            self.last_processing_time = time.time()
            self.logger.info("[ConsciousMemory] Cleared all data")
        except Exception as e:
            self.logger.error("[ConsciousMemory] Error clearing data: %s", str(e), exc_info=True)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state of conscious memory for testing and monitoring."""
        try:
            return {
                'sensor_buffer_size': len(self.sensor_buffer),
                'last_processing_time': self.last_processing_time,
                'running': self.running,
                'processed_items': getattr(self, '_processed_count', 0),
                'memory_system_connected': self.memory_system is not None,
                'llm_provider_connected': self.llm_provider is not None
            }
        except Exception as e:
            self.logger.error("Error getting current state: %s", str(e))
            return {}
    
    def get_context_awareness(self) -> Dict[str, Any]:
        """Get context awareness information from conscious memory."""
        try:
            # Get recent processing patterns
            context_awareness = {
                'active_contexts': [],
                'processing_patterns': {},
                'memory_connections': {},
                'awareness_level': 'active' if self.running else 'inactive'
            }
            
            # Analyze recent sensor buffer for active contexts
            if self.sensor_buffer:
                recent_data = list(self.sensor_buffer)[-5:]  # Last 5 items
                
                # Extract context types
                for data in recent_data:
                    if isinstance(data, dict):
                        for sensor_type in ['screen', 'process', 'file']:
                            if sensor_type in data:
                                context_awareness['active_contexts'].append(sensor_type)
                
                # Remove duplicates
                context_awareness['active_contexts'] = list(set(context_awareness['active_contexts']))
            
            # Check memory system integration
            if self.memory_system:
                try:
                    context_awareness['memory_connections'] = {
                        'short_term_available': hasattr(self.memory_system, 'short_term_memory'),
                        'long_term_available': hasattr(self.memory_system, 'long_term_memory'),
                        'context_available': hasattr(self.memory_system, 'context_memory'),
                        'enhanced_understanding': hasattr(self.memory_system, '_analyze_user_intent')
                    }
                except Exception as e:
                    self.logger.warning("Error checking memory connections: %s", str(e))
                    context_awareness['memory_connections'] = {'error': str(e)}
            
            return context_awareness
        except Exception as e:
            self.logger.error("Error getting context awareness: %s", str(e))
            return {'error': str(e), 'awareness_level': 'error'} 