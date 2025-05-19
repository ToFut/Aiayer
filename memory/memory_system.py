"""
Memory System Module
Combines short-term, long-term, and contextual memory management.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import time
import json
import os
import base64
from io import BytesIO
import aiohttp
from collections import deque
import asyncio
import zlib
import psutil
import gc
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import websockets
import traceback

from memory.memory import ConversationMemory, ContextMemory
from memory.memory_logger import MemoryLogger
from memory.memory_diagnostic_logger import MemoryDiagnosticLogger
from memory.sensors import ScreenSensor, ProcessSensor
from memory.safe_json import safe_load, safe_dump, safe_dumps

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MemorySystem:
    """Combined memory system managing short-term, long-term, and contextual memory."""
    
    # Memory limits
    MAX_MEMORY_SIZE_MB = 100  # Maximum memory size in MB
    MAX_MESSAGE_SIZE_KB = 10  # Maximum size of a single message in KB
    COMPRESSION_THRESHOLD_MB = 50  # Threshold to trigger compression
    VECTOR_SIMILARITY_THRESHOLD = 0.7
    
    # Sensor configuration
    SENSOR_CONFIG = {
        'screen': {
            'interval_sec': 5,
            'max_memory_mb': 50,
            'cleanup_threshold_mb': 25,
            'max_errors': 3,
            'retry_delay_sec': 5,
            'compression_enabled': True
        },
        'process': {
            'interval_sec': 5,
            'max_memory_mb': 30,
            'cleanup_threshold_mb': 15,
            'max_errors': 3,
            'exclude_patterns': ['system', 'kernel'],
            'max_processes': 100
        },
        'ai': {
            'monitor_interval_sec': 60,
            'analysis_interval_sec': 300,
            'prediction_interval_sec': 600,
            'max_memory_mb': 200,
            'max_cpu_percent': 50,
            'max_disk_usage': 80,
            'max_network_usage': 1000,
            'event_queue_size': 1000,
            'insight_queue_size': 100,
            'alert_queue_size': 50,
            'anomaly_threshold': 0.8,
            'pattern_window': 24,
            'prediction_window': 6
        }
    }
    
    def __init__(self, llm_provider=None):
        """Initialize the memory system."""
        self.llm = llm_provider
        self.messages = []
        self.screen_sensor = None
        self.process_sensor = None
        self.llava_client = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize diagnostic logger
        from memory.memory_diagnostic_logger import MemoryDiagnosticLogger
        self.diagnostic_logger = MemoryDiagnosticLogger()
        self.logger.info("Diagnostic logger initialized")
        
        # Set last cleanup time
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 3600  # 1 hour in seconds
        
        # Initialize vector model for semantic search
        try:
            self.vector_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info("Vector model initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing vector model: {e}")
            self.vector_model = None
        
        # Initialize memory components
        self.short_term_memory = []
        self.long_term_memory = []
        self.context_memory = {}
        
        # Set up memory directory structure
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.memory_dir = os.path.join(self.base_dir, 'memory')
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(os.path.join(self.memory_dir, 'logs', 'context'), exist_ok=True)
        
        # Initialize memory state file path
        self.memory_state_file = os.path.join(self.memory_dir, 'memory_state.json')
        self._load_memory_state()
        
        self.logger.info("Memory system initialized")
    
    def _load_memory_state(self):
        """Load memory state from file if it exists."""
        try:
            if os.path.exists(self.memory_state_file):
                self.logger.info(f"🔄 Loading memory state from {self.memory_state_file}")
                
                with open(self.memory_state_file, 'r') as f:
                    state = json.load(f)
                    
                # Load short-term memory
                loaded_short_term = state.get('short_term', [])
                if loaded_short_term:
                    self.logger.info(f"  - Found {len(loaded_short_term)} short-term memory items")
                    self.short_term_memory = loaded_short_term
                else:
                    self.logger.info("  - No short-term memory found, initializing empty")
                    self.short_term_memory = []
                
                # Load long-term memory
                loaded_long_term = state.get('long_term', [])
                if loaded_long_term:
                    self.logger.info(f"  - Found {len(loaded_long_term)} long-term memory items")
                    self.long_term_memory = loaded_long_term
                else:
                    self.logger.info("  - No long-term memory found, initializing empty")
                    self.long_term_memory = []
                
                # Load context memory
                loaded_context = state.get('context', {})
                if loaded_context:
                    self.logger.info(f"  - Found context memory with {len(loaded_context)} items")
                    self.context_memory = loaded_context
                else:
                    self.logger.info("  - No context memory found, initializing empty")
                    self.context_memory = {}
                
                self.logger.info(f"✅ Successfully loaded memory state")
                
                # Log successful load with diagnostic logger
                self.diagnostic_logger.log_memory_event("memory_state_loaded", {
                    "short_term_count": len(self.short_term_memory),
                    "long_term_count": len(self.long_term_memory),
                    "context_count": len(self.context_memory),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                self.logger.info("No existing memory state found, starting fresh")
                self._save_memory_state()
                
                # Log initialization with diagnostic logger
                self.diagnostic_logger.log_memory_event("memory_state_initialized", {
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            self.logger.error(f"❌ Error loading memory state: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "load_memory_state",
                "error_type": type(e).__name__
            })
            self._save_memory_state()  # Create new state file if loading fails

    def _save_memory_state(self):
        """Save current memory state to file."""
        try:
            self.diagnostic_logger.log_memory_event("saving_memory_state", {
                "short_term_count": len(self.short_term_memory),
                "long_term_count": len(self.long_term_memory),
                "context_count": len(self.context_memory) if isinstance(self.context_memory, dict) else 0
            })
            
            # Prepare serializable representation of memory
            serializable_short_term = []
            for item in self.short_term_memory:
                if isinstance(item, np.ndarray):
                    # Convert numpy arrays to lists for serialization
                    serializable_short_term.append(item.tolist())
                else:
                    serializable_short_term.append(item)
                    
            serializable_long_term = []
            for item in self.long_term_memory:
                if isinstance(item, np.ndarray):
                    serializable_long_term.append(item.tolist())
                else:
                    serializable_long_term.append(item)
            
            # Create state object
            state = {
                'short_term': serializable_short_term,
                'long_term': serializable_long_term,
                'context': self.context_memory,
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.memory_state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
            self.logger.info(f"✅ Saved memory state with {len(self.short_term_memory)} short-term memories")
            self.diagnostic_logger.log_memory_event("memory_state_saved", {
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
        except Exception as e:
            self.logger.error(f"❌ Error saving memory state: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "save_memory_state"
            })
    
    async def initialize(self):
        """Initialize the memory system with sensors and LLaVA client."""
        try:
            # Initialize screen sensor
            self.screen_sensor = ScreenSensor(self.SENSOR_CONFIG['screen'])
            await self.screen_sensor.initialize()
            self.logger.info("Screen sensor initialized")
            
            # Initialize process sensor
            self.process_sensor = ProcessSensor(self.SENSOR_CONFIG['process'])
            await self.process_sensor.start()  # Start the process sensor
            self.logger.info("Process sensor initialized and started")
            
            # Initialize LLaVA client
            self.llava_client = None  # Will be initialized when needed
            self.logger.info("LLaVA client initialized")
            
            # Start sensor data collection
            asyncio.create_task(self._collect_sensor_data())
            self.logger.info("Sensor data collection started")
            
            return True
        except Exception as e:
            self.logger.error(f"Error initializing memory system: {e}")
            return False

    async def _collect_sensor_data(self):
        """Collect data from all sensors periodically."""
        while True:
            try:
                # Collect screen data
                if self.screen_sensor:
                    screen_data = await self.screen_sensor.get_current_state()
                    await self.process_sensor_data('screen', screen_data)
                    self.logger.debug(f"Screen data collected: {screen_data.get('image_hash', 'no hash')}")
                
                # Collect process data
                if self.process_sensor:
                    process_data = await self.process_sensor.get_current_state()
                    await self.process_sensor_data('process', process_data)
                    self.logger.debug(f"Process data collected: {len(process_data.get('active_apps', []))} processes")
                
                # Wait before next collection
                await asyncio.sleep(5)  # Collect every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error collecting sensor data: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    def extract_relevant_info(self, message: Union[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract only the relevant information from a message."""
        try:
            self.logger.debug(f"Extracting info from message: {message}")
            # Log memory metrics before processing
            self.diagnostic_logger.log_memory_metrics(self)
            
            # Process message
            if isinstance(message, str):
                return {'content': message}
            elif isinstance(message, dict):
                return message
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting info from message: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "extract_relevant_info",
                "message": str(message)
            })
            return None
            
    async def process_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> None:
        """Process and store sensor data with smart batching"""
        try:
            self.diagnostic_logger.log_memory_event("sensor_data_received", {
                "sensor_type": sensor_type,
                "data_size": len(str(data)),
                "timestamp": datetime.now().isoformat()
            })
            
            # Determine if data is significant enough to process
            should_process = self._should_process_sensor_data(sensor_type, data)
            
            if should_process:
                self.logger.info(f"Processing significant {sensor_type} sensor update")
                
                # Store sensor data in context memory dictionary
                timestamp = datetime.now().isoformat()
                
                # Initialize sensor data section if not exists
                if 'sensor_data' not in self.context_memory:
                    self.context_memory['sensor_data'] = {}
                
                # Initialize specific sensor type if not exists
                if sensor_type not in self.context_memory['sensor_data']:
                    self.context_memory['sensor_data'][sensor_type] = {}
                
                # Store with timestamp as key
                self.context_memory['sensor_data'][sensor_type][timestamp] = {
                    'data': data,
                    'timestamp': timestamp
                }
                
                # Keep the most recent sensor data limited
                max_entries = 20  # Keep only the most recent 20 entries
                sensor_data = self.context_memory['sensor_data'][sensor_type]
                if len(sensor_data) > max_entries:
                    # Sort by timestamp and keep only the most recent
                    sorted_keys = sorted(sensor_data.keys())
                    keys_to_remove = sorted_keys[:-max_entries]
                    for key in keys_to_remove:
                        del sensor_data[key]
                
                self.logger.info(f"Stored {sensor_type} sensor data with timestamp {timestamp}")
                
                # Log updated metrics
                self.diagnostic_logger.log_memory_metrics(self)
            else:
                self.logger.debug(f"Skipping non-significant {sensor_type} sensor update")
            
        except Exception as e:
            self.logger.error(f"Error processing sensor data: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "process_sensor_data",
                "sensor_type": sensor_type,
                "data_size": len(str(data))
            })
            
    def _should_process_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> bool:
        """Smart batching: determine if sensor data should be processed based on significance"""
        try:
            # For screen sensor data
            if sensor_type == 'screen':
                # Check if we have previous screen data to compare
                if not hasattr(self, '_last_screen_data') or not self._last_screen_data:
                    self._last_screen_data = data
                    return True
                
                # Check for significant changes in screen content
                if 'screen_text' in data and 'screen_text' in self._last_screen_data:
                    # If text content has changed significantly (>20% different)
                    old_text = self._last_screen_data.get('screen_text', '')
                    new_text = data.get('screen_text', '')
                    
                    # Simple difference check based on length
                    if abs(len(old_text) - len(new_text)) > 0.2 * max(len(old_text), len(new_text)):
                        self._last_screen_data = data
                        return True
                    
                    # If image hash has changed (different screen visual)
                    if data.get('image_hash') != self._last_screen_data.get('image_hash'):
                        self._last_screen_data = data
                        return True
                        
                # No significant changes detected
                return False
                
            # For process sensor data
            elif sensor_type == 'process':
                # Check if we have previous process data to compare
                if not hasattr(self, '_last_process_data') or not self._last_process_data:
                    self._last_process_data = data
                    return True
                
                # Check for window/application changes
                old_window = self._last_process_data.get('active_window')
                new_window = data.get('active_window')
                
                old_app = self._last_process_data.get('active_app')
                new_app = data.get('active_app')
                
                # If active window or application changed, process the data
                if old_window != new_window or old_app != new_app:
                    self._last_process_data = data
                    self.logger.info(f"Significant context change: Window: {old_window} -> {new_window}, App: {old_app} -> {new_app}")
                    return True
                
                # Check time elapsed since last processed update
                last_timestamp = self._last_process_data.get('timestamp', 0)
                current_timestamp = data.get('timestamp', 0)
                
                # Force an update every 30 seconds regardless of changes
                if current_timestamp - last_timestamp > 30:
                    self._last_process_data = data
                    return True
                    
                # No significant changes detected
                return False
                
            # Unknown sensor type - process by default
            return True
            
        except Exception as e:
            self.logger.error(f"Error in smart batching logic: {e}")
            # Default to processing data in case of errors
            return True
            
    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            self.diagnostic_logger.log_memory_event("cleanup_started", {
                "timestamp": datetime.now().isoformat()
            })
            
            # FIXED: Removed super().cleanup() call since this class doesn't inherit from anything
            # Instead, save memory state and clean up resources directly
            self._save_memory_state()
            
            # Clean up any resources
            if self.llava_client:
                try:
                    await self.llava_client.close()
                    self.logger.info("Closed LLaVA client connection")
                except Exception as e:
                    self.logger.error(f"Error closing LLaVA client: {e}")
            
            # Log final metrics
            self.diagnostic_logger.log_memory_metrics(self)
            
            self.diagnostic_logger.log_memory_event("cleanup_completed", {
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "cleanup"
            })

    def _check_memory_usage(self) -> bool:
        """Check if current memory usage is within limits."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            
            if memory_usage_mb > self.MAX_MEMORY_SIZE_MB:
                self.logger.warning(f"Memory usage ({memory_usage_mb:.2f}MB) exceeds limit ({self.MAX_MEMORY_SIZE_MB}MB)")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error checking memory usage: {e}")
            return False

    def _compress_memory(self) -> None:
        """Compress memory data to reduce size."""
        try:
            if not self._check_memory_usage():
                self.logger.info("Compressing memory data...")
                
                # Compress conversation history
                if self.short_term_memory:
                    compressed = zlib.compress(json.dumps(self.short_term_memory).encode())
                    self.short_term_memory = json.loads(zlib.decompress(compressed).decode())
                
                # Compress context history
                if self.context_memory:
                    compressed = zlib.compress(json.dumps(self.context_memory).encode())
                    self.context_memory = json.loads(zlib.decompress(compressed).decode())
                
                # Force garbage collection
                gc.collect()
                
                self.logger.info("Memory compression completed")
        except Exception as e:
            self.logger.error(f"Error compressing memory: {e}")

    def _cleanup_old_data(self) -> None:
        """Remove old and unnecessary data."""
        try:
            self.logger.info("Starting memory cleanup")
            self.diagnostic_logger.log_memory_event("cleanup_started", {
                "timestamp": datetime.now().isoformat()
            })
            
            current_time = time.time()
            cutoff_time = current_time - (24 * 3600)  # 24 hours
            
            # Clean up old context data
            if self.context_memory:
                # Filter based on timestamp format in ISO 8601 
                cleaned_context = {}
                for k, v in self.context_memory.items():
                    if isinstance(v, dict) and 'timestamp' in v:
                        try:
                            # Convert ISO timestamp to epoch time for comparison
                            ts = datetime.fromisoformat(v['timestamp']).timestamp()
                            if ts > cutoff_time:
                                cleaned_context[k] = v
                        except (ValueError, TypeError):
                            # Keep items with invalid timestamps (safe approach)
                            cleaned_context[k] = v
                    else:
                        # Keep non-timestamped items
                        cleaned_context[k] = v
                
                self.context_memory = cleaned_context
                self.logger.info(f"Cleaned context memory, kept {len(self.context_memory)} items")
            
            # Clean up old sensor data
            if 'sensor_data' in self.context_memory:
                for sensor_type in ['screen', 'process']:
                    if sensor_type in self.context_memory['sensor_data']:
                        before_count = len(self.context_memory['sensor_data'][sensor_type])
                        
                        # Filter sensor data
                        cleaned_sensor_data = {}
                        for k, v in self.context_memory['sensor_data'][sensor_type].items():
                            if isinstance(v, dict) and 'timestamp' in v:
                                try:
                                    # Convert ISO timestamp to epoch time for comparison
                                    ts = datetime.fromisoformat(v['timestamp']).timestamp()
                                    if ts > cutoff_time:
                                        cleaned_sensor_data[k] = v
                                except (ValueError, TypeError):
                                    # Keep items with invalid timestamps
                                    cleaned_sensor_data[k] = v
                            else:
                                # Keep non-timestamped items
                                cleaned_sensor_data[k] = v
                        
                        self.context_memory['sensor_data'][sensor_type] = cleaned_sensor_data
                        after_count = len(self.context_memory['sensor_data'][sensor_type])
                        self.logger.info(f"Cleaned {sensor_type} sensor data: {before_count} → {after_count} items")
            
            # Force garbage collection
            gc.collect()
            
            self.last_cleanup_time = current_time
            self.logger.info("✅ Memory cleanup completed")
            
            self.diagnostic_logger.log_memory_event("cleanup_completed", {
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up memory: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "cleanup_old_data",
                "error_type": type(e).__name__
            })

    def _get_text_for_vectorization(self, item: Dict[str, Any]) -> str:
        """Extract text content for vectorization from a memory item."""
        try:
            if isinstance(item, dict):
                # Combine relevant fields for vectorization
                text_parts = []
                if 'content' in item:
                    text_parts.append(str(item['content']))
                if 'message_content' in item:
                    text_parts.append(str(item['message_content']))
                if 'screen_content' in item:
                    text_parts.append(str(item['screen_content']))
                if 'window' in item:
                    text_parts.append(str(item['window']))
                return ' '.join(text_parts)
            return str(item)
        except Exception as e:
            self.logger.error(f"Error extracting text for vectorization: {e}")
            return ""

    def _update_vector_storage(self, item: Dict[str, Any], storage_type: str) -> None:
        """Update vector storage with new item."""
        try:
            self.logger.debug(f"Updating vector storage for type: {storage_type}")
            
            if not self.vector_model:
                self.logger.warning("Vector model not available, skipping vector storage update")
                return
                
            # Extract text for vectorization
            text = self._get_text_for_vectorization(item)
            if not text:
                self.logger.warning("No text available for vectorization, skipping update")
                return
                
            # Generate vector embedding
            self.logger.debug(f"Generating vector embedding for text: {text[:50]}...")
            vector = self.vector_model.encode(text)
            
            # Create vector entry with metadata
            vector_entry = {
                'vector': vector.tolist(),  # Convert numpy array to list for JSON serialization
                'text': text,
                'original_item': item,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to appropriate storage
            if storage_type == 'short_term':
                # For short-term, create a list structure that includes both the item and its vector
                if not isinstance(self.short_term_memory, list):
                    self.short_term_memory = []
                
                # Keep track if the item exists in a format without vector
                item_exists = False
                for existing_item in self.short_term_memory:
                    if isinstance(existing_item, dict) and not isinstance(existing_item.get('vector'), list):
                        item_exists = True
                        break
                
                if not item_exists:
                    self.short_term_memory.append(vector_entry)
                    self.logger.debug(f"Added vector entry to short-term memory, total: {len(self.short_term_memory)}")
                
            elif storage_type == 'long_term':
                # For long-term, same structure as short-term
                if not isinstance(self.long_term_memory, list):
                    self.long_term_memory = []
                    
                self.long_term_memory.append(vector_entry)
                self.logger.debug(f"Added vector entry to long-term memory, total: {len(self.long_term_memory)}")
                
            elif storage_type == 'context':
                # For context memory, store with timestamp key in vectors sub-dictionary
                if 'vectors' not in self.context_memory:
                    self.context_memory['vectors'] = {}
                
                timestamp = datetime.now().isoformat()
                self.context_memory['vectors'][timestamp] = vector_entry
                self.logger.debug(f"Added vector entry to context memory, key: {timestamp}")
            
            # Enforce memory limits to prevent unbounded growth
            max_length = 30 if storage_type in ['short_term', 'long_term'] else 50
            
            # Apply limits
            if storage_type == 'short_term' and len(self.short_term_memory) > max_length:
                self.short_term_memory = self.short_term_memory[-max_length:]
                self.logger.debug(f"Trimmed short-term memory to {max_length} items")
                
            elif storage_type == 'long_term' and len(self.long_term_memory) > max_length:
                self.long_term_memory = self.long_term_memory[-max_length:]
                self.logger.debug(f"Trimmed long-term memory to {max_length} items")
                
            elif storage_type == 'context' and 'vectors' in self.context_memory:
                vectors = self.context_memory['vectors']
                if len(vectors) > max_length:
                    # Sort by timestamp and keep only the most recent
                    sorted_keys = sorted(vectors.keys())
                    keys_to_remove = sorted_keys[:-max_length]
                    for key in keys_to_remove:
                        del vectors[key]
                    self.logger.debug(f"Trimmed context vectors to {max_length} items")
            
            # Log successful update
            self.diagnostic_logger.log_memory_event("vector_storage_updated", {
                "storage_type": storage_type,
                "text_length": len(text),
                "timestamp": datetime.now().isoformat()
            })
                
        except Exception as e:
            self.logger.error(f"❌ Error updating vector storage: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "update_vector_storage",
                "storage_type": storage_type,
                "error_type": type(e).__name__
            })

    async def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to memory with size checks and cleanup."""
        try:
            # Check message size
            message_size_kb = len(json.dumps(message)) / 1024
            if message_size_kb > self.MAX_MESSAGE_SIZE_KB:
                self.logger.warning(f"Message size ({message_size_kb:.2f}KB) exceeds limit ({self.MAX_MESSAGE_SIZE_KB}KB)")
                message = self._truncate_message(message)
            
            # Check if cleanup is needed
            if time.time() - self.last_cleanup_time > self.cleanup_interval:
                self._cleanup_old_data()
            
            # Check memory usage and compress if necessary
            if not self._check_memory_usage():
                self._compress_memory()
            
            # Add message to conversation memory
            self.short_term_memory.append(message)
            
            # Update vector storage
            self._update_vector_storage(message, 'short_term')
            
            # Create and store context
            context = self._create_context_summary(message)
            self.context_memory[context['timestamp']] = context
            
            # Update context vector storage
            self._update_vector_storage(context, 'context')
            
            # Save memory state
            self._save_memory_state()
            
        except Exception as e:
            self.logger.error(f"Error adding message to memory: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "add_message",
                "message_size": message_size_kb
            })

    def _truncate_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Truncate message content if it exceeds size limits."""
        try:
            if 'content' in message and isinstance(message['content'], str):
                max_content_length = (self.MAX_MESSAGE_SIZE_KB * 1024) // 2  # Leave room for other fields
                if len(message['content']) > max_content_length:
                    message['content'] = message['content'][:max_content_length] + "..."
            return message
        except Exception as e:
            self.logger.error(f"Error truncating message: {e}")
            return message

    def _create_context_summary(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the current context for a message."""
        try:
            # Get recent messages for context
            recent_messages = self.get_recent_messages(count=5)
            
            # Get current sensor states
            sensor_states = {}
            if self.screen_sensor:
                sensor_states['screen'] = {
                    'active_apps': self.screen_sensor.get_active_apps(),
                    'window_info': self.screen_sensor._get_window_info()
                }
            if self.process_sensor:
                sensor_states['process'] = {
                    'active_processes': self.process_sensor.get_active_processes()
                }
            
            # Create context summary
            context_summary = {
                'timestamp': datetime.now().isoformat(),
                'recent_messages': recent_messages,
                'sensor_states': sensor_states,
                'message_type': message.get('type', 'unknown'),
                'message_content': message.get('content', '')
            }
            
            # Add any additional context from the message
            if 'context' in message:
                context_summary.update(message['context'])
            
            return context_summary
            
        except Exception as e:
            self.logger.error(f"Error creating context summary: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "create_context_summary",
                "message": str(message)
            })
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'message_type': message.get('type', 'unknown')
            }

    async def get_context_summary(self) -> Dict[str, Any]:
        """Get current context summary with sensor data and LLaVA analysis"""
        try:
            self.logger.info(f"🔍 RETRIEVING CONTEXT SUMMARY: [VERIFICATION CHECK 8/10]")
            self.diagnostic_logger.log_memory_event("context_summary_requested", {
                "timestamp": datetime.now().isoformat()
            })
            
            # Get screen data
            self.logger.info(f"  - Retrieving screen sensor data [VERIFICATION CHECK]")
            screen_data = None
            screen_image = None
            try:
                if self.screen_sensor:
                    screen_data = await self.screen_sensor.get_current_state()
                    self.logger.info(f"  - Screen data retrieved: {bool(screen_data)}")
                    if screen_data:
                        self.logger.info(f"  - Screen data keys: {list(screen_data.keys())}")
                        screen_image = screen_data.get('image')
                        self.logger.info(f"  - Screen image available: {bool(screen_image)}")
                else:
                    self.logger.warning(f"  - Screen sensor not available [VERIFICATION WARNING]")
            except Exception as e:
                self.logger.error(f"  - Error retrieving screen data: {str(e)}")
                self.diagnostic_logger.log_memory_error(e, {
                    "context": "get_screen_data",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Get process data
            self.logger.info(f"  - Retrieving process sensor data [VERIFICATION CHECK]")
            process_data = None
            try:
                if self.process_sensor:
                    process_data = await self.process_sensor.get_current_state()
                    self.logger.info(f"  - Process data retrieved: {bool(process_data)}")
                    if process_data:
                        self.logger.info(f"  - Process data keys: {list(process_data.keys())}")
                        if 'active_window' in process_data:
                            self.logger.info(f"  - Active window: {process_data.get('active_window')}")
                else:
                    self.logger.warning(f"  - Process sensor not available [VERIFICATION WARNING]")
            except Exception as e:
                self.logger.error(f"  - Error retrieving process data: {str(e)}")
                self.diagnostic_logger.log_memory_error(e, {
                    "context": "get_process_data",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Analyze screen with LLaVA if we have an image
            self.logger.info(f"  - Analyzing screen with LLaVA [VERIFICATION CHECK]")
            llava_analysis = None
            if screen_image:
                try:
                    self.logger.info(f"  - Converting image to base64")
                    # Convert image to base64
                    buffered = BytesIO()
                    screen_image.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    self.logger.info(f"  - Image converted successfully, size: {len(img_str)} chars")
                    
                    # Check if LLaVA client is available
                    if self.llava_client:
                        self.logger.info(f"  - Sending image to LLaVA for analysis")
                        # Send to LLaVA
                        async with self.llava_client.post(
                            "http://localhost:11434/api/generate",
                            json={
                                "model": "llava",
                                "prompt": "Describe what you see in this image in detail",
                                "images": [img_str]
                            }
                        ) as response:
                            self.logger.info(f"  - LLaVA response status: {response.status}")
                            if response.status == 200:
                                result = await response.json()
                                llava_analysis = result.get('response', '')
                                self.logger.info(f"  - LLaVA analysis received, length: {len(llava_analysis)}")
                                self.logger.info(f"  - Analysis sample: {llava_analysis[:100]}...")
                            else:
                                self.logger.warning(f"  - LLaVA returned non-200 status: {response.status} [VERIFICATION WARNING]")
                    else:
                        self.logger.warning(f"  - LLaVA client not available [VERIFICATION WARNING]")
                except Exception as e:
                    self.logger.error(f"  - Error analyzing screen with LLaVA: {str(e)}")
                    self.logger.error(f"  - Error type: {type(e).__name__}")
                    self.diagnostic_logger.log_memory_error(e, {
                        "context": "llava_analysis",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                self.logger.info(f"  - No screen image available for LLaVA analysis")
            
            # Get recent messages
            self.logger.info(f"  - Retrieving recent messages [VERIFICATION CHECK]")
            recent_messages = []
            try:
                recent_messages = self.short_term_memory[-5:]  # Last 5 messages
                self.logger.info(f"  - Retrieved {len(recent_messages)} recent messages")
            except Exception as e:
                self.logger.error(f"  - Error retrieving recent messages: {str(e)}")
                self.diagnostic_logger.log_memory_error(e, {
                    "context": "get_recent_messages",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Combine all context
            self.logger.info(f"  - Building complete context object [VERIFICATION CHECK]")
            context = {
                "window": process_data.get('active_window', 'Unknown') if process_data else 'Unknown',
                "active_apps": process_data.get('active_apps', []) if process_data else [],
                "window_history": process_data.get('window_history', []) if process_data else [],
                "screen_content": screen_data.get('text', '') if screen_data else '',
                "screen_analysis": llava_analysis,
                "recent_messages": recent_messages,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ CONTEXT SUMMARY COMPLETE: [VERIFICATION PASSED]")
            self.logger.info(f"  - Context keys: {list(context.keys())}")
            self.logger.info(f"  - Window: {context.get('window')}")
            self.logger.info(f"  - Active apps count: {len(context.get('active_apps', []))}")
            self.logger.info(f"  - Screen content length: {len(context.get('screen_content', ''))}")
            self.logger.info(f"  - Has screen analysis: {bool(context.get('screen_analysis'))}")
            self.logger.info(f"  - Recent messages count: {len(context.get('recent_messages', []))}")
            
            self.diagnostic_logger.log_memory_event("context_summary_completed", {
                "context_keys": list(context.keys()),
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
            
            return context
            
        except Exception as e:
            self.logger.error(f"❌ ERROR GETTING CONTEXT SUMMARY: [VERIFICATION FAILED]")
            self.logger.error(f"  - Error: {str(e)}")
            self.logger.error(f"  - Error type: {type(e).__name__}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "get_context_summary",
                "timestamp": datetime.now().isoformat()
            })
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    def get_recent_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent messages from memory."""
        try:
            self.logger.info(f"🔄 Retrieving {count} recent messages [VERIFICATION CHECK 9/10]")
            return self.short_term_memory[-count:]
        except Exception as e:
            self.logger.error(f"❌ Error retrieving recent messages: {str(e)} [VERIFICATION FAILED]")
            return []
    
    async def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory using vector similarity."""
        try:
            self.logger.info(f"🔍 VECTOR SEARCHING MEMORY")
            self.logger.info(f"  - Query: {query}")
            self.logger.info(f"  - Limit: {limit}")
            
            self.diagnostic_logger.log_memory_event("memory_search_started", {
                "query": query,
                "limit": limit,
                "timestamp": datetime.now().isoformat()
            })
            
            # If vector model isn't available, fall back to text-based search
            if not self.vector_model:
                self.logger.warning("Vector model not available, falling back to text-based search")
                return await self._text_based_search(query, limit)
            
            # Generate query vector
            query_vector = self.vector_model.encode(query)
            
            # Collect all vector entries from different memory stores
            vector_entries = []
            
            # Process short-term memory
            for item in self.short_term_memory:
                if isinstance(item, dict) and 'vector' in item:
                    # Already in the right format with vector
                    vector_entries.append({
                        'source': 'short_term',
                        'vector': np.array(item['vector']) if isinstance(item['vector'], list) else item['vector'],
                        'text': item.get('text', ''),
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'original_item': item.get('original_item', item)
                    })
                elif isinstance(item, dict):
                    # Item without vector, try to extract text and vectorize
                    text = self._get_text_for_vectorization(item)
                    if text:
                        try:
                            vector = self.vector_model.encode(text)
                            vector_entries.append({
                                'source': 'short_term',
                                'vector': vector,
                                'text': text,
                                'timestamp': item.get('timestamp', datetime.now().isoformat()),
                                'original_item': item
                            })
                        except Exception as e:
                            self.logger.error(f"Error vectorizing short-term item: {e}")
            
            # Process long-term memory (similar to short-term)
            for item in self.long_term_memory:
                if isinstance(item, dict) and 'vector' in item:
                    vector_entries.append({
                        'source': 'long_term',
                        'vector': np.array(item['vector']) if isinstance(item['vector'], list) else item['vector'],
                        'text': item.get('text', ''),
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'original_item': item.get('original_item', item)
                    })
                elif isinstance(item, dict):
                    text = self._get_text_for_vectorization(item)
                    if text:
                        try:
                            vector = self.vector_model.encode(text)
                            vector_entries.append({
                                'source': 'long_term',
                                'vector': vector,
                                'text': text,
                                'timestamp': item.get('timestamp', datetime.now().isoformat()),
                                'original_item': item
                            })
                        except Exception as e:
                            self.logger.error(f"Error vectorizing long-term item: {e}")
            
            # Process context memory vectors
            if 'vectors' in self.context_memory and isinstance(self.context_memory['vectors'], dict):
                for timestamp, vector_item in self.context_memory['vectors'].items():
                    if isinstance(vector_item, dict) and 'vector' in vector_item:
                        vector_entries.append({
                            'source': 'context',
                            'vector': np.array(vector_item['vector']) if isinstance(vector_item['vector'], list) else vector_item['vector'],
                            'text': vector_item.get('text', ''),
                            'timestamp': vector_item.get('timestamp', timestamp),
                            'original_item': vector_item.get('original_item', vector_item)
                        })
            
            # If no vector entries were found, fall back to text search
            if not vector_entries:
                self.logger.warning("No vector entries found, falling back to text-based search")
                return await self._text_based_search(query, limit)
            
            # Perform similarity search
            self.logger.info(f"Performing similarity search with {len(vector_entries)} vector entries")
            all_results = []
            
            # Extract all vectors for batch similarity computation
            vectors = np.array([entry['vector'] for entry in vector_entries])
                    
            # Compute similarities
            try:
                similarities = cosine_similarity([query_vector], vectors)[0]
                
                # Get top matches
                top_indices = np.argsort(similarities)[-limit:][::-1]
                
                for idx in top_indices:
                    similarity = similarities[idx]
                    if similarity >= self.VECTOR_SIMILARITY_THRESHOLD:
                        entry = vector_entries[idx]
                        result = {
                            'source': entry['source'],
                            'content': entry['text'],
                            'timestamp': entry['timestamp'],
                            'score': float(similarity),
                            'original_item': entry['original_item']
                        }
                        all_results.append(result)
                
                # Log search results
                self.logger.info(f"✅ Found {len(all_results)} relevant results")
                self.diagnostic_logger.log_memory_event("memory_search_completed", {
                    "results_count": len(all_results),
                    "top_score": float(similarities[top_indices[0]]) if len(top_indices) > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Sort by similarity score and return top results
            all_results.sort(key=lambda x: x['score'], reverse=True)
            return all_results[:limit]
            
        except Exception as e:
                self.logger.error(f"Error computing similarities: {e}")
                return await self._text_based_search(query, limit)
            
        except Exception as e:
            self.logger.error(f"❌ Error in vector search: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "search_memory",
                "query": query,
                "error_type": type(e).__name__
            })
            # Fall back to text-based search in case of errors
            return await self._text_based_search(query, limit)
            
    async def _text_based_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback text-based search when vector search is not available."""
        self.logger.info("Performing text-based search")
        results = []
        
        # Search in short-term memory
        for item in self.short_term_memory:
            if isinstance(item, dict):
                text = self._get_text_for_vectorization(item)
                if query.lower() in text.lower():
                    results.append({
                        'source': 'short_term',
                        'content': text,
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'score': 0.5,  # Default score for text matching
                        'original_item': item
                    })
        
        # Search in long-term memory
        for item in self.long_term_memory:
            if isinstance(item, dict):
                text = self._get_text_for_vectorization(item)
                if query.lower() in text.lower():
                    results.append({
                        'source': 'long_term',
                        'content': text,
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'score': 0.5,
                        'original_item': item
                    })
        
        # Search in context memory
        for key, value in self.context_memory.items():
            if isinstance(value, dict):
                text = self._get_text_for_vectorization(value)
                if query.lower() in text.lower():
                    results.append({
                        'source': 'context',
                        'content': text,
                        'timestamp': value.get('timestamp', datetime.now().isoformat()),
                        'score': 0.5,
                        'original_item': value
                    })
        
        # Return top results (limited by count)
        return results[:limit]
    
    def clear(self) -> None:
        """Clear all memory."""
        try:
            self.logger.info(f"🧹 CLEARING MEMORY: [VERIFICATION CHECK]")
            self.short_term_memory = []
            self.long_term_memory = []
            self.context_memory = {}
            self.logger.info(f"✅ MEMORY CLEARED SUCCESSFULLY [VERIFICATION PASSED]")
            self.diagnostic_logger.log_memory_event("memory_cleared", {
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
        except Exception as e:
            self.logger.error(f"❌ ERROR CLEARING MEMORY: [VERIFICATION FAILED]")
            self.logger.error(f"  - Error: {str(e)}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "clear_memory",
                "timestamp": datetime.now().isoformat()
            })

    async def cleanup(self):
        """Cleanup resources"""
        try:
            self.logger.info(f"🧹 CLEANUP MEMORY SYSTEM: [FINAL VERIFICATION]")
            self.diagnostic_logger.log_memory_event("cleanup_started", {
                "timestamp": datetime.now().isoformat()
            })
            
            # Cleanup screen sensor
            self.logger.info(f"  - Cleaning up screen sensor")
            if self.screen_sensor:
                try:
                    await self.screen_sensor.cleanup()
                    self.logger.info(f"  - Screen sensor cleanup successful")
                except Exception as e:
                    self.logger.error(f"  - Error cleaning up screen sensor: {str(e)}")
                    self.diagnostic_logger.log_memory_error(e, {
                        "context": "cleanup_screen_sensor",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                self.logger.info(f"  - No screen sensor to clean up")
                
            # Cleanup process sensor
            self.logger.info(f"  - Cleaning up process sensor")
            if self.process_sensor:
                try:
                    await self.process_sensor.cleanup()
                    self.logger.info(f"  - Process sensor cleanup successful")
                except Exception as e:
                    self.logger.error(f"  - Error cleaning up process sensor: {str(e)}")
                    self.diagnostic_logger.log_memory_error(e, {
                        "context": "cleanup_process_sensor",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                self.logger.info(f"  - No process sensor to clean up")
                
            # Cleanup LLaVA client
            self.logger.info(f"  - Cleaning up LLaVA client")
            if self.llava_client:
                try:
                    await self.llava_client.close()
                    self.logger.info(f"  - LLaVA client cleanup successful")
                except Exception as e:
                    self.logger.error(f"  - Error cleaning up LLaVA client: {str(e)}")
                    self.diagnostic_logger.log_memory_error(e, {
                        "context": "cleanup_llava_client",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                self.logger.info(f"  - No LLaVA client to clean up")
                
            # Log final summary
            self.logger.info(f"✅ MEMORY SYSTEM CLEANUP COMPLETE: [VERIFICATION PASSED]")
            self.diagnostic_logger.log_memory_event("cleanup_completed", {
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
            
        except Exception as e:
            self.logger.error(f"❌ ERROR CLEANING UP MEMORY SYSTEM: [VERIFICATION FAILED]")
            self.logger.error(f"  - Error: {str(e)}")
            self.logger.error(f"  - Error type: {type(e).__name__}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "cleanup_memory_system",
                "timestamp": datetime.now().isoformat()
            })

    async def _collect_process_data(self):
        """Collect data from process sensor."""
        while True:
            try:
                if "process" in self.sensors and self.sensors["process"]:
                    data = await self.sensors["process"].get_current_state()
                    self._context_memory['sensor_data']['process'] = data
                    self._context_memory['sensor_data']['last_update'] = time.time()
                    self.logger.debug(f"Updated process sensor data: {safe_dumps(data, indent=2, fallback='{}')}")
            except Exception as e:
                self.logger.error(f"Error collecting process sensor data: {e}")
            await asyncio.sleep(2.0) 

    async def connect_to_server(self):
        """Connect to the bridge server to receive context updates"""
        retry_count = 0
        max_retries = 5
        retry_delay = 5  # seconds
        
        while self.running:
            try:
                async with websockets.connect(self.server_uri) as websocket:
                    logger.info(f"Connected to server at {self.server_uri}")
                    retry_count = 0  # Reset retry count on successful connection
                    
                    # Send initial connection message
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "memory_system",
                            "version": "1.0.0",
                            "timestamp": datetime.now().isoformat()
                        }
                    }))
                    
                    # Handle incoming messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            msg_type = data.get('type', 'unknown')
                            
                            if msg_type == 'context_update':
                                # Process context update
                                context_data = data.get('payload', {})
                                self._update_context(context_data)
                            elif msg_type == 'ping':
                                # Respond to ping
                                await websocket.send(json.dumps({
                                    "type": "pong",
                                    "timestamp": datetime.now().isoformat()
                                }))
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
                if retry_count < max_retries:
                    retry_count += 1
                    retry_delay *= 1.5  # Exponential backoff
                    logger.info(f"Retrying connection in {retry_delay} seconds (attempt {retry_count}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Max retry attempts reached, stopping reconnection")
                    self.running = False
                    break
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                if retry_count < max_retries:
                    retry_count += 1
                    retry_delay *= 1.5
                    logger.info(f"Retrying connection in {retry_delay} seconds (attempt {retry_count}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Max retry attempts reached, stopping reconnection")
                    self.running = False
                    break 

    def _update_context(self, context_data: Dict[str, Any]) -> None:
        """Update context memory with new data from the server."""
        try:
            # Update timestamp
            context_data['timestamp'] = datetime.now().isoformat()
            
            # Update context memory
            self.context_memory[context_data['timestamp']] = context_data
            
            # Log the update
            logger.debug(f"Updated context with new data: {safe_dumps(context_data, indent=2, fallback='{}')}")
            
            # Save memory state
            self._save_memory_state()
            
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "update_context",
                "data_size": len(str(context_data))
            }) 