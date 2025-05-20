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
file_handler.setLevel(logging.WARNING)  # Only log warnings and above
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Configure console handler with reduced output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)  # Only show errors in console
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(logging.WARNING)  # Set base level to WARNING

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
        self.max_buffer_size = 10  # Maximum number of entries per sensor type
        self.processing_interval = 30  # Process every 30 seconds
        self.last_processing_time = time.time()
        
        # Initialize processing task
        self.processing_task = None
        self.running = False
        
        self.logger.info("[ConsciousMemory] Initialized as middle layer for memory system")
    
    async def add_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> bool:
        """Add sensor data to the buffer for processing."""
        try:
            if not sensor_type or not data:
                self.logger.error("Invalid sensor data: type=%s, data=%s", sensor_type, data)
                return False
            
            if not isinstance(data, dict):
                self.logger.error("Invalid data type: expected dict, got %s", type(data))
                return False
                
            self.logger.info("[ConsciousMemory] Adding %s sensor data to buffer", sensor_type)
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = time.time()
            
            # Add to appropriate buffer
            if sensor_type in self.sensor_buffer:
                # Add new data to the beginning of the list
                self.sensor_buffer[sensor_type].insert(0, data)
                
                # Keep only the most recent entries
                self.sensor_buffer[sensor_type] = self.sensor_buffer[sensor_type][:self.max_buffer_size]
                
                # Process the data before feeding to memory
                processed_data = await self._process_sensor_data(sensor_type, data)
                if processed_data:
                    # Feed processed data to memory system
                    await self._feed_to_memory(processed_data)
                    self.logger.info("[ConsciousMemory] Added %s sensor data to buffer and fed to memory system", sensor_type)
                    return True
                else:
                    self.logger.warning("[ConsciousMemory] Failed to process %s sensor data", sensor_type)
                    return False
            else:
                self.logger.warning("[ConsciousMemory] Unknown sensor type: %s", sensor_type)
                return False
                
        except Exception as e:
            self.logger.error("[ConsciousMemory] Error adding sensor data: %s", str(e), exc_info=True)
            return False
    
    async def _feed_to_memory(self, processed_data: Dict[str, Any]) -> None:
        """Feed processed data to memory system."""
        try:
            # Debug logging
            self.logger.info(f"Processing data type: {type(processed_data)}")
            if 'active_apps' in processed_data:
                self.logger.info(f"Active apps type: {type(processed_data['active_apps'])}")
                self.logger.info(f"Active apps content: {processed_data['active_apps']}")
            
            # Handle active apps if present
            if 'active_apps' in processed_data:
                apps = processed_data['active_apps']
                if isinstance(apps, list):
                    # Simple string conversion
                    processed_data['active_apps'] = [str(app) for app in apps]
                elif isinstance(apps, str):
                    # Handle case where active_apps is a single string
                    processed_data['active_apps'] = [apps]
                else:
                    # Handle other cases
                    processed_data['active_apps'] = [str(apps)]
            
            # Add to short-term memory
            await self.memory_system.add_to_short_term_memory(processed_data)
            
            # Add to context memory
            await self.memory_system.add_to_context_memory(processed_data)
            
            # If significant, add to long-term memory
            if processed_data.get('is_significant', False):
                await self.memory_system.add_to_long_term_memory(processed_data)
                
            self.logger.info(f"Fed {len(processed_data)} items to memory")
            
        except Exception as e:
            self.logger.error(f"Error feeding data to memory: {e}")
            self.logger.error(traceback.format_exc())
    
    async def _process_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data before feeding to memory system.
        Extracts only necessary information without storing raw data."""
        try:
            # Ensure data is a dictionary
            if not isinstance(data, dict):
                self.logger.error(f"Invalid data type for {sensor_type}: {type(data)}")
                return None
                
            # Create base processed data without raw data
            processed_data = {
                "timestamp": datetime.now().isoformat(),
                "sensor_type": sensor_type,
                "is_significant": False
                # Raw data removed to reduce memory usage
            }
            
            # Process based on sensor type - extract only needed fields
            if sensor_type == "screen":
                processed_data.update({
                    "window_title": data.get("window_title", ""),
                    "screen_content": data.get("screen_content", ""),
                    "is_significant": data.get("is_significant", False)
                    # No raw image data stored
                })
            elif sensor_type == "process":
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
                    
                processed_data["is_significant"] = data.get("is_significant", False)
            elif sensor_type == "file":
                processed_data.update({
                    "file_path": data.get("file_path", ""),
                    "file_type": data.get("file_type", ""),
                    "is_significant": data.get("is_significant", False)
                    # No additional file content stored
                })
            
            # Validate processed data
            if not all(key in processed_data for key in ["timestamp", "sensor_type"]):
                self.logger.error(f"Missing required fields in processed data for {sensor_type}")
                return None
                
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing {sensor_type} data: {e}")
            self.logger.error(traceback.format_exc())
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
        """Generate prompt for LLM analysis."""
        try:
            prompt = "Analyze the following system state and provide insights:\n\n"
            
            # Add screen content
            if context.get('screen_data'):
                prompt += "Screen Content:\n"
                for data in context['screen_data'][:3]:  # Use last 3 screen captures
                    if 'text_content' in data:
                        prompt += f"- {data['text_content']}\n"
            
            # Add active processes
            if context.get('process_data'):
                prompt += "\nActive Processes:\n"
                for data in context['process_data'][:3]:  # Use last 3 process states
                    if 'active_apps' in data:
                        prompt += f"- {', '.join(data['active_apps'])}\n"
            
            # Add file changes
            if context.get('file_data'):
                prompt += "\nFile Changes:\n"
                for data in context['file_data'][:3]:  # Use last 3 file states
                    if 'current_file' in data:
                        prompt += f"- {data['current_file']}\n"
            
            prompt += "\nPlease provide insights about:\n"
            prompt += "1. What the user is currently working on\n"
            prompt += "2. Any patterns or trends in their activity\n"
            prompt += "3. Important context that should be remembered\n"
            
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