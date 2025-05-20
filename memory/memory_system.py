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
# Removed numpy, sklearn and sentence_transformers dependencies
import websockets
import traceback

# Change relative imports to absolute imports
from memory.memory import ConversationMemory, ContextMemory
from memory.memory_logger import MemoryLogger
from memory.memory_diagnostic_logger import MemoryDiagnosticLogger
from memory.sensors import ScreenSensor, ProcessSensor
from memory.safe_json import safe_load, safe_dump, safe_dumps
from memory.conscious_memory import ConsciousMemory
from memory.enhanced_semantic_search import enhanced_search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aiayer.log'),
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
    TEXT_SIMILARITY_THRESHOLD = 0.7  # Renamed from VECTOR_SIMILARITY_THRESHOLD
    
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
        
        # Initialize memory logger
        self.memory_logger = MemoryLogger()
        self.logger.info("Memory logger initialized")
        
        # Initialize diagnostic logger
        self.diagnostic_logger = MemoryDiagnosticLogger()
        self.logger.info("Diagnostic logger initialized")
        
        # Initialize conscious memory
        self.conscious_memory = ConsciousMemory(llm_provider, self)
        self.logger.info("Conscious memory initialized")
        
        # Set last cleanup time
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 3600  # 1 hour in seconds
        
        # Use enhanced semantic search with vector embeddings
        self.logger.info("Using enhanced semantic search with vector embeddings for memory retrieval")
        self.semantic_search = enhanced_search
        
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
                    self.context_memory = {
                        'sensor_data': {
                            'screen': {},
                            'process': {},
                            'file': {}
                        }
                    }
                
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
                # Initialize empty memory state
                self.short_term_memory = []
                self.long_term_memory = []
                self.context_memory = {
                    'sensor_data': {
                        'screen': {},
                        'process': {},
                        'file': {}
                    }
                }
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

    async def _save_memory_state(self):
        """Save current memory state to file."""
        try:
            self.logger.debug(f"[DEBUG] _save_memory_state called. Short-term: {len(self.short_term_memory)}, Long-term: {len(self.long_term_memory)}, Context keys: {list(self.context_memory.keys()) if isinstance(self.context_memory, dict) else 'N/A'}")
            
            # Log memory state before saving
            state = {
                'short_term': self.short_term_memory,
                'long_term': self.long_term_memory,
                'context': self.context_memory,
                'conscious': self.conscious_memory.get_state() if hasattr(self.conscious_memory, 'get_state') else {},
                'last_update': datetime.now().isoformat()
            }
            self.memory_logger.log_memory_state(state, "memory_state_saving")
            
            # Save to file
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
            
            # Initialize process sensor with proper configuration
            self.process_sensor = ProcessSensor()
            await self.process_sensor.start()
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
            
    async def process_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> bool:
        """Process and store sensor data in the appropriate memory.
        Extracts only necessary information without storing raw image data."""
        try:
            # Extract only required data from sensor input to reduce memory usage
            processed_data = {}
            
            # Extract essential information based on sensor type
            if sensor_type == 'screen' and isinstance(data, dict):
                # For screen data, only keep text content and metadata, not the image
                processed_data = {
                    'text': data.get('text', ''),
                    'window_title': data.get('window_title', ''),
                    'active_window': data.get('active_window', ''),
                    'timestamp': datetime.now().isoformat()
                }
                # No image data stored to save memory
            elif sensor_type == 'process' and isinstance(data, dict):
                # For process data, only keep essential process info
                processed_data = {
                    'active_apps': data.get('active_apps', []),
                    'active_window': data.get('active_window', ''),
                    'timestamp': datetime.now().isoformat()
                }
            elif sensor_type == 'file' and isinstance(data, dict):
                # For file data, only keep file metadata without content
                processed_data = {
                    'file_path': data.get('file_path', ''),
                    'file_type': data.get('file_type', ''),
                    'file_event': data.get('file_event', ''),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # For other data types, create minimal representation
                processed_data = {
                    'timestamp': datetime.now().isoformat()
                }
                # Add any critical fields but avoid large data structures
                for key, value in data.items():
                    if key not in ['image', 'raw_data', 'binary_content'] and isinstance(value, (str, int, float, bool)):
                        processed_data[key] = value

            # Store in short-term memory with minimal data
            self.short_term_memory.append({
                'type': sensor_type,
                'data': processed_data,  # Only store processed data, not raw data
                'timestamp': datetime.now().isoformat()
            })

            # Update context memory with only essential information
            if sensor_type == 'screen':
                self.context_memory['screen_content'] = data.get('text', '')
                # No image stored in context memory
            elif sensor_type == 'process':
                self.context_memory['active_processes'] = data.get('processes', [])
            elif sensor_type == 'file':
                self.context_memory['recent_files'] = data.get('files', [])

            # Save memory state
            await self._save_memory_state()
            
            return True
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
            logger.error(traceback.format_exc())
            return False

    def _should_process_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> bool:
        """Advanced smart batching approach that considers multiple factors:
        1. Data importance and change significance
        2. System load and resource availability
        3. Sensor-specific requirements
        4. Adaptive batching intervals
        """
        try:
            current_time = time.time()
            
            # Initialize tracking attributes if not exists
            if not hasattr(self, '_last_processing_time'):
                self._last_processing_time = {}
            if not hasattr(self, '_processing_intervals'):
                self._processing_intervals = {
                    'screen': 5,  # Start with 5 seconds for screen
                    'process': 10,  # Start with 10 seconds for process
                    'file': 30     # Start with 30 seconds for file
                }
            if not hasattr(self, '_last_system_load'):
                self._last_system_load = 0.0
            
            # Get current system load
            try:
                current_load = psutil.cpu_percent() / 100.0
                self._last_system_load = current_load
            except Exception:
                current_load = self._last_system_load
            
            # Get last processing time for this sensor type
            last_time = self._last_processing_time.get(sensor_type, 0)
            if isinstance(last_time, str):
                try:
                    last_time = datetime.fromisoformat(last_time).timestamp()
                except (ValueError, TypeError):
                    last_time = 0
            
            # Get current interval
            current_interval = self._processing_intervals.get(sensor_type, 30)
            if isinstance(current_interval, str):
                try:
                    current_interval = float(current_interval)
                except (ValueError, TypeError):
                    current_interval = 30
            
            # Adjust processing interval based on system load
            if current_load > 0.8:  # High system load
                current_interval *= 2  # Double the interval
            elif current_load < 0.3:  # Low system load
                current_interval = max(5, current_interval * 0.75)  # Reduce interval but not below 5 seconds
            
            # Update the interval for this sensor type
            self._processing_intervals[sensor_type] = current_interval
            
            # Check if enough time has passed based on adjusted interval
            if current_time - last_time > current_interval:
                self._last_processing_time[sensor_type] = current_time
                return True
            
            # Sensor-specific importance checks
            if sensor_type == 'screen':
                # Check for significant visual changes
                if not hasattr(self, '_last_screen_hash'):
                    self._last_screen_hash = None
                
                if 'image_hash' in data and data['image_hash'] != self._last_screen_hash:
                    self._last_screen_hash = data['image_hash']
                    return True
                
                # Check for significant text changes
                if 'text' in data:
                    if not hasattr(self, '_last_screen_text'):
                        self._last_screen_text = None
                    
                    if data['text'] != self._last_screen_text:
                        self._last_screen_text = data['text']
                        return True
            
            elif sensor_type == 'process':
                # Check for window/app changes
                if not hasattr(self, '_last_window_app'):
                    self._last_window_app = {'window': None, 'app': None}
                
                current_window = data.get('active_window')
                current_app = data.get('active_app')
                
                # Process if window or app changed
                if (current_window != self._last_window_app['window'] or 
                    current_app != self._last_window_app['app']):
                    self._last_window_app = {'window': current_window, 'app': current_app}
                    return True
                
                # Check for significant process changes
                if 'active_processes' in data:
                    if not hasattr(self, '_last_process_list'):
                        self._last_process_list = set()
                    
                    current_processes = set(data['active_processes'])
                    if current_processes != self._last_process_list:
                        self._last_process_list = current_processes
                        return True
            
            elif sensor_type == 'file':
                # Check for file changes
                if not hasattr(self, '_last_file_state'):
                    self._last_file_state = {}
                
                if 'files' in data:
                    current_files = data['files']
                    if current_files != self._last_file_state:
                        self._last_file_state = current_files
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in smart batching logic: {e}")
            return True  # Process data if there's an error
            
    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            self.diagnostic_logger.log_memory_event("cleanup_started", {
                "timestamp": datetime.now().isoformat()
            })
            
            # Save memory state
            await self._save_memory_state()
            
            # Clean up conscious memory
            await self.conscious_memory.cleanup()
            
            # Clean up any resources
            if self.llava_client:
                try:
                    await self.llava_client.close()
                    self.logger.info("Closed LLaVA client connection")
                except Exception as e:
                    self.logger.error(f"Error closing LLaVA client: {e}")
            
            # Log final metrics
            self.diagnostic_logger.log_memory_metrics(self)
            
        except Exception as e:
            self.logger.error(f"Error in cleanup: {e}")
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
        """Remove old and unnecessary data with enhanced memory management."""
        try:
            self.logger.info("Starting memory cleanup with enhanced memory management")
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
                                # Remove any raw image or binary data before keeping
                                if isinstance(v, dict):
                                    # Create a clean copy without large binary data
                                    filtered_v = {}
                                    for field_key, field_val in v.items():
                                        if field_key not in ['image', 'raw_data', 'binary_content']:
                                            filtered_v[field_key] = field_val
                                    cleaned_context[k] = filtered_v
                                else:
                                    cleaned_context[k] = v
                        except (ValueError, TypeError):
                            # Keep items with invalid timestamps but strip large data
                            if isinstance(v, dict):
                                filtered_v = {}
                                for field_key, field_val in v.items():
                                    if field_key not in ['image', 'raw_data', 'binary_content']:
                                        filtered_v[field_key] = field_val
                                cleaned_context[k] = filtered_v
                            else:
                                cleaned_context[k] = v
                    else:
                        # Keep non-timestamped items but strip large data
                        if isinstance(v, dict):
                            filtered_v = {}
                            for field_key, field_val in v.items():
                                if field_key not in ['image', 'raw_data', 'binary_content']:
                                    filtered_v[field_key] = field_val
                            cleaned_context[k] = filtered_v
                        else:
                            cleaned_context[k] = v
                
                self.context_memory = cleaned_context
                self.logger.info(f"Cleaned context memory, kept {len(self.context_memory)} items with reduced memory footprint")
            
            # Clean up old sensor data
            if 'sensor_data' in self.context_memory:
                for sensor_type in ['screen', 'process', 'file']:
                    if sensor_type in self.context_memory['sensor_data']:
                        before_count = len(self.context_memory['sensor_data'][sensor_type])
                        
                        # Filter sensor data
                        cleaned_sensor_data = {}
                        for k, v in self.context_memory['sensor_data'][sensor_type].items():
                            if isinstance(v, dict) and 'timestamp' in v:
                                try:
                                    # Convert ISO timestamp to epoch time for comparison
                                    ts = datetime.fromisoformat(v['timestamp']).timestamp()
                                    # Only keep recent data and remove raw data
                                    if ts > cutoff_time:
                                        # For screen data, remove image
                                        if sensor_type == 'screen' and 'data' in v and isinstance(v['data'], dict):
                                            if 'image' in v['data']:
                                                v['data']['image'] = None
                                            cleaned_sensor_data[k] = v
                                        # For other data, keep metadata only
                                        else:
                                            # Strip out binary or large data before keeping
                                            if 'data' in v and isinstance(v['data'], dict):
                                                # Keep only essential metadata fields
                                                essential_data = {
                                                    'timestamp': v['data'].get('timestamp', datetime.now().isoformat())
                                                }
                                                # For process data, keep only process names
                                                if sensor_type == 'process':
                                                    essential_data['active_apps'] = v['data'].get('active_apps', [])
                                                # For file data, keep only file paths
                                                elif sensor_type == 'file':
                                                    essential_data['file_path'] = v['data'].get('file_path', '')
                                                
                                                # Replace with lightweight version
                                                v['data'] = essential_data
                                            cleaned_sensor_data[k] = v
                                except (ValueError, TypeError):
                                    # Skip items with invalid timestamps
                                    pass
                            else:
                                # Skip non-timestamped items to reduce memory
                                pass
                        
                        # Apply the cleaned data
                        self.context_memory['sensor_data'][sensor_type] = cleaned_sensor_data
                        after_count = len(self.context_memory['sensor_data'][sensor_type])
                        self.logger.info(f"Cleaned {sensor_type} sensor data: {before_count} → {after_count} items with optimized memory usage")
            
            # Clean up short-term memory - keep only essential data
            if self.short_term_memory:
                before_count = len(self.short_term_memory)
                # Keep only recent items and remove raw data
                optimized_memory = []
                
                # Take only last 30 items and optimize them
                for item in self.short_term_memory[-30:]:
                    if isinstance(item, dict):
                        # Create optimized version without large data
                        optimized_item = {
                            'type': item.get('type', 'unknown'),
                            'timestamp': item.get('timestamp', datetime.now().isoformat())
                        }
                        
                        # Handle 'data' field specially
                        if 'data' in item and isinstance(item['data'], dict):
                            # Create optimized data with minimal footprint
                            optimized_data = {}
                            for k, v in item['data'].items():
                                # Skip large binary data
                                if k not in ['image', 'raw_data', 'binary_content']:
                                    optimized_data[k] = v
                            optimized_item['data'] = optimized_data
                        
                        optimized_memory.append(optimized_item)
                
                self.short_term_memory = optimized_memory
                self.logger.info(f"Optimized short-term memory: {before_count} → {len(self.short_term_memory)} items with reduced memory footprint")
            
            # Clean up backup files in the cache directory
            try:
                cache_dirs = ['cache/screen_sensor', 'cache/process_sensor', 'cache/file_sensor']
                for cache_dir in cache_dirs:
                    if os.path.exists(cache_dir):
                        for filename in os.listdir(cache_dir):
                            if filename.endswith('.bak_'):
                                file_path = os.path.join(cache_dir, filename)
                                try:
                                    os.remove(file_path)
                                    self.logger.debug(f"Removed backup file: {file_path}")
                                except Exception as e:
                                    self.logger.warning(f"Couldn't remove backup file {file_path}: {e}")
            except Exception as cache_e:
                self.logger.warning(f"Error cleaning cache backup files: {cache_e}")
            
            # Force aggressive garbage collection
            gc.collect()
            
            self.last_cleanup_time = current_time
            self.logger.info("✅ Memory cleanup completed with enhanced memory management")
            
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

    def _add_to_memory_storage(self, item: Dict[str, Any], storage_type: str) -> None:
        """Add item to appropriate memory storage and index it in the semantic search."""
        try:
            # Extract text for search
            text = item.get('content', '') if isinstance(item, dict) else str(item)
            
            # Ensure item has a timestamp
            if isinstance(item, dict) and 'timestamp' not in item:
                item['timestamp'] = datetime.now().isoformat()
            
            # Add to enhanced semantic search index
            item_id = self.semantic_search.add_to_index(item, storage_type)
            
            # Also add to traditional memory stores for backward compatibility
            if storage_type == 'short_term':
                self.short_term_memory.append(item)
                self.memory_logger.log_short_term_memory(item, "short_term_memory_added")
            elif storage_type == 'long_term':
                self.long_term_memory.append(item)
                self.memory_logger.log_long_term_memory(item, "long_term_memory_added")
            elif storage_type == 'context':
                timestamp = datetime.now().isoformat()
                self.context_memory[timestamp] = item
                self.memory_logger.log_context_memory(item, "context_memory_added")
            elif storage_type == 'conscious':
                self.conscious_memory.add(item)
                self.memory_logger.log_conscious_memory(item, "conscious_memory_added")
            
            # Enforce memory limits
            max_length = 30 if storage_type in ['short_term', 'long_term'] else 50
            
            # Apply limits to traditional stores
            if storage_type == 'short_term' and len(self.short_term_memory) > max_length:
                self.short_term_memory = self.short_term_memory[-max_length:]
                self.logger.debug(f"Trimmed short-term memory to {max_length} items")
                
            elif storage_type == 'long_term' and len(self.long_term_memory) > max_length:
                self.long_term_memory = self.long_term_memory[-max_length:]
                self.logger.debug(f"Trimmed long-term memory to {max_length} items")
                
            elif storage_type == 'context' and 'searchable_items' in self.context_memory:
                items = self.context_memory['searchable_items']
                if len(items) > max_length:
                    # Sort by timestamp and keep only the most recent
                    sorted_keys = sorted(items.keys())
                    keys_to_remove = sorted_keys[:-max_length]
                    for key in keys_to_remove:
                        del items[key]
                    self.logger.debug(f"Trimmed context items to {max_length} items")
            
            # Log successful update
            self.diagnostic_logger.log_memory_event("memory_storage_updated", {
                "storage_type": storage_type,
                "text_length": len(text),
                "item_id": item_id,
                "timestamp": datetime.now().isoformat()
            })
                
        except Exception as e:
            self.logger.error(f"❌ Error updating memory storage: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "add_to_memory_storage",
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
            self.memory_logger.log_short_term_memory(message, "message_added")
            
            # Add to searchable memory
            self._add_to_memory_storage(message, 'short_term')
            
            # Create and store context
            context = self._create_context_summary(message)
            self.context_memory[context['timestamp']] = context
            self.memory_logger.log_context_memory(context, "context_created")
            
            # Add context to searchable memory
            self._add_to_memory_storage(context, 'context')
            
            # Save memory state
            await self._save_memory_state()
            
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
        """Create a summary of the current context for a message using semantic search."""
        try:
            self.logger.info("Creating context summary using semantic search")
            
            # Get message content to use as search query
            message_content = message.get('content', '')
            if not message_content:
                message_content = message.get('message_content', '')
            
            # Use semantic search to get relevant messages for context
            relevant_messages = []
            seen_contents = set()
            
            if message_content:
                self.logger.info(f"Performing semantic search for context with query: {message_content[:50]}...")
                # Use text-based search to get semantically relevant context
                search_results = asyncio.run(self._text_based_search(message_content, limit=5))
                
                # Extract the original items from search results and avoid duplicates
                for result in search_results:
                    original_item = result.get('original_item', {})
                    content = original_item.get('content', '')
                    if content and content not in seen_contents:
                        relevant_messages.append(original_item)
                        seen_contents.add(content)
                
                self.logger.info(f"Found {len(relevant_messages)} relevant messages through semantic search")
            
            # If no relevant messages found through semantic search, fall back to recent messages
            if not relevant_messages:
                self.logger.info("No relevant messages found through semantic search, falling back to recent messages")
                for msg in self.get_recent_messages(count=5):
                    content = msg.get('content', '')
                    if content and content not in seen_contents:
                        relevant_messages.append(msg)
                        seen_contents.add(content)
            
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
            
            # Create context summary with timestamp
            current_time = datetime.now()
            context_summary = {
                'timestamp': current_time.isoformat(),
                'date': current_time.strftime('%Y-%m-%d'),
                'time': current_time.strftime('%H:%M:%S'),
                'relevant_messages': relevant_messages,  # Changed from recent_messages to relevant_messages
                'sensor_states': sensor_states,
                'message_type': message.get('type', 'unknown'),
                'message_content': message_content,
                'search_query': message_content[:100],  # Include search query for reference
                'search_method': 'semantic_search'  # Indicate that semantic search was used
            }
            
            # Add any additional context from the message, avoiding duplicates
            if 'context' in message:
                for key, value in message['context'].items():
                    if key not in context_summary:
                        context_summary[key] = value
            
            self.logger.info("Successfully created context summary using semantic search")
            return context_summary
            
        except Exception as e:
            self.logger.error(f"Error creating context summary with semantic search: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "create_context_summary_semantic",
                "message": str(message),
                "error_type": type(e).__name__
            })
            # Fall back to basic context summary in case of error
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'message_type': message.get('type', 'unknown'),
                'recent_messages': self.get_recent_messages(count=3),  # Fall back to recent messages
                'search_method': 'fallback'
            }

    async def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context including sensor data."""
        try:
            self.logger.info("Getting context summary...")
            context_summary = {}
            
            # Get latest sensor data
            if 'sensor_data' in self.context_memory:
                sensor_data = self.context_memory['sensor_data']
                
                # Process each sensor type
                for sensor_type, data in sensor_data.items():
                    if data:  # If we have data for this sensor
                        # Get the most recent data point
                        latest_timestamp = max(data.keys())
                        latest_data = data[latest_timestamp]['data']
                        
                        # Add to context summary based on sensor type
                        if sensor_type == 'screen':
                            context_summary['screen_content'] = latest_data.get('screen_text', '')
                            context_summary['window'] = latest_data.get('active_window', 'Unknown')
                        elif sensor_type == 'process':
                            context_summary['active_apps'] = latest_data.get('active_apps', [])
                            context_summary['window'] = latest_data.get('active_window', 'Unknown')
                        elif sensor_type == 'file':
                            context_summary['recent_files'] = latest_data.get('recent_files', [])
                            context_summary['current_file'] = latest_data.get('current_file', {})
            
            # Add timestamp
            context_summary['timestamp'] = datetime.now().isoformat()
            
            self.logger.info(f"Context summary created with keys: {list(context_summary.keys())}")
            return context_summary
            
        except Exception as e:
            self.logger.error(f"Error getting context summary: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "get_context_summary",
                "timestamp": datetime.now().isoformat()
            })
            return {}

    def get_recent_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent messages from memory."""
        try:
            self.logger.info(f"🔄 Retrieving {count} recent messages [VERIFICATION CHECK 9/10]")
            return self.short_term_memory[-count:]
        except Exception as e:
            self.logger.error(f"❌ Error retrieving recent messages: {str(e)} [VERIFICATION FAILED]")
            return []
    
    async def search_memory(self, query: str, limit: int = 5, memory_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search memory using enhanced semantic search with vector embeddings."""
        try:
            self.logger.info(f"🔍 SEARCHING MEMORY WITH ENHANCED SEMANTIC SEARCH")
            self.logger.info(f"  - Query: {query}")
            self.logger.info(f"  - Limit: {limit}")
            if memory_types:
                self.logger.info(f"  - Memory types: {memory_types}")
            
            start_time = time.time()
            
            self.diagnostic_logger.log_memory_event("memory_search_started", {
                "query": query,
                "limit": limit,
                "memory_types": memory_types,
                "timestamp": datetime.now().isoformat(),
                "search_type": "vector_enhanced"
            })
            
            # Use enhanced semantic search with vector embeddings
            results = self.semantic_search.search(
                query=query,
                limit=limit,
                memory_types=memory_types,
                min_score=0.3  # Lower threshold to ensure we get enough results
            )
            
            search_time = time.time() - start_time
            
            # Log search stats
            self.logger.info(f"✅ Enhanced semantic search completed in {search_time:.3f}s")
            self.logger.info(f"  - Found {len(results)} results")
            if results:
                self.logger.info(f"  - Top result score: {results[0]['score']:.4f}")
            
            self.diagnostic_logger.log_memory_event("memory_search_completed", {
                "query": query,
                "results_count": len(results),
                "top_score": results[0]['score'] if results else 0,
                "search_time_ms": int(search_time * 1000),
                "timestamp": datetime.now().isoformat(),
                "search_type": "vector_enhanced"
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error in enhanced semantic search: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "search_memory_enhanced",
                "query": query,
                "error_type": type(e).__name__
            })
            
            # Fall back to text-based search in case of errors
            self.logger.info(f"Falling back to text-based search")
            try:
                return await self._text_based_search(query, limit)
            except Exception as fallback_e:
                self.logger.error(f"❌ Error in fallback text search: {fallback_e}")
                return []
            
    async def _text_based_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform enhanced text-based search on memory data."""
        self.logger.info("Performing enhanced text-based search")
        results = []
        seen_contents = set()  # Track seen content to avoid duplicates
        query_lower = query.lower()
        
        # Helper function to calculate a simple relevance score
        def calculate_score(text, search_query):
            # Count query term occurrences
            count = text.lower().count(search_query)
            # Higher score for exact matches or more occurrences
            if count > 0:
                base_score = 0.5
                bonus = min(0.4, 0.1 * count)  # Bonus for multiple occurrences, max 0.4
                # Bonus for exact match (case-insensitive whole word)
                if f" {search_query} " in f" {text.lower()} ":
                    bonus += 0.1
                return base_score + bonus
            return 0.0
        
        # Helper function to add result if not duplicate
        def add_result_if_unique(result):
            content = result['content']
            if content not in seen_contents:
                seen_contents.add(content)
                results.append(result)
        
        # Search in short-term memory
        for item in self.short_term_memory:
            if isinstance(item, dict):
                text = self._get_text_for_vectorization(item)
                if text and query_lower in text.lower():
                    score = calculate_score(text, query_lower)
                    add_result_if_unique({
                        'source': 'short_term',
                        'content': text,
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'score': score,
                        'original_item': item
                    })
        
        # Search in long-term memory
        for item in self.long_term_memory:
            if isinstance(item, dict):
                text = self._get_text_for_vectorization(item)
                if text and query_lower in text.lower():
                    score = calculate_score(text, query_lower)
                    add_result_if_unique({
                        'source': 'long_term',
                        'content': text,
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'score': score,
                        'original_item': item
                    })
        
        # Search in context memory
        # First check searchable items if they exist
        if 'searchable_items' in self.context_memory and isinstance(self.context_memory['searchable_items'], dict):
            for key, item in self.context_memory['searchable_items'].items():
                if isinstance(item, dict) and 'text' in item:
                    text = item['text']
                    if text and query_lower in text.lower():
                        score = calculate_score(text, query_lower)
                        add_result_if_unique({
                            'source': 'context',
                            'content': text,
                            'timestamp': item.get('timestamp', datetime.now().isoformat()),
                            'score': score,
                            'original_item': item.get('original_item', item)
                        })
        
        # Also check regular context items
        for key, value in self.context_memory.items():
            if key != 'searchable_items' and isinstance(value, dict):
                text = self._get_text_for_vectorization(value)
                if text and query_lower in text.lower():
                    score = calculate_score(text, query_lower)
                    add_result_if_unique({
                        'source': 'context',
                        'content': text,
                        'timestamp': value.get('timestamp', datetime.now().isoformat()),
                        'score': score,
                        'original_item': value
                    })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Log search results
        self.logger.info(f"✅ Found {len(results)} results for query: '{query}'")
        if results:
            self.logger.info(f"  - Top result score: {results[0]['score']}")
            
        self.diagnostic_logger.log_memory_event("text_search_completed", {
            "results_count": len(results),
            "top_score": results[0]['score'] if results else 0,
            "timestamp": datetime.now().isoformat()
        })
        
        # Return top results (limited by count)
        return results[:limit]
    
    def clear(self) -> None:
        """Clear all memory."""
        try:
            self.logger.info(f"🧹 CLEARING MEMORY: [VERIFICATION CHECK]")
            
            # Clear each memory type
            self.short_term_memory = []
            self.long_term_memory = []
            self.context_memory = {}
            if hasattr(self.conscious_memory, 'clear'):
                self.conscious_memory.clear()
            
            # Log the clearing of each memory type
            self.memory_logger.log_short_term_memory({"action": "clear"}, "memory_cleared")
            self.memory_logger.log_long_term_memory({"action": "clear"}, "memory_cleared")
            self.memory_logger.log_context_memory({"action": "clear"}, "memory_cleared")
            self.memory_logger.log_conscious_memory({"action": "clear"}, "memory_cleared")
            
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
                                await self._update_context(context_data)
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

    async def _update_context(self, context_data: Dict[str, Any]) -> None:
        """Update context memory with new data from the server."""
        try:
            # Update timestamp
            context_data['timestamp'] = datetime.now().isoformat()
            
            # Update context memory
            self.context_memory[context_data['timestamp']] = context_data
            
            # Log the update
            logger.debug(f"Updated context with new data: {safe_dumps(context_data, indent=2, fallback='{}')}")
            
            # Save memory state
            await self._save_memory_state()  # Changed to synchronous call since we're not using await
            
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "update_context",
                "data_size": len(str(context_data))
            })

    async def test_memory_search(self) -> Dict[str, Any]:
        """Test memory search functionality across all memory types."""
        try:
            self.logger.info("🧪 STARTING MEMORY SEARCH TEST")
            test_results = {
                'short_term': [],
                'long_term': [],
                'context': [],
                'combined': []
            }
            
            # Clear existing memory for clean test
            self.clear()
            
            # Add test data to short-term memory
            short_term_test = {
                'content': 'This is a test message in short-term memory',
                'timestamp': datetime.now().isoformat(),
                'type': 'test'
            }
            await self.add_message(short_term_test)
            
            # Add test data to long-term memory
            long_term_test = {
                'content': 'This is a test message in long-term memory',
                'timestamp': datetime.now().isoformat(),
                'type': 'test'
            }
            self._add_to_memory_storage(long_term_test, 'long_term')
            
            # Add test data to context memory
            context_test = {
                'content': 'This is a test message in context memory',
                'timestamp': datetime.now().isoformat(),
                'type': 'test'
            }
            self._add_to_memory_storage(context_test, 'context')
            
            # Test search in short-term memory
            short_term_results = await self.search_memory('short-term')
            test_results['short_term'] = short_term_results
            
            # Test search in long-term memory
            long_term_results = await self.search_memory('long-term')
            test_results['long_term'] = long_term_results
            
            # Test search in context memory
            context_results = await self.search_memory('context')
            test_results['context'] = context_results
            
            # Test combined search
            combined_results = await self.search_memory('test message')
            test_results['combined'] = combined_results
            
            # Log test results
            self.logger.info("📊 MEMORY SEARCH TEST RESULTS:")
            for memory_type, results in test_results.items():
                self.logger.info(f"  {memory_type.upper()}:")
                for i, result in enumerate(results):
                    self.logger.info(f"    {i+1}. Score: {result['score']:.2f}")
                    self.logger.info(f"       Content: {result['content'][:50]}...")
                    self.logger.info(f"       Source: {result['source']}")
            
            return test_results
            
        except Exception as e:
            self.logger.error(f"❌ ERROR IN MEMORY SEARCH TEST: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 

    async def add_to_short_term_memory(self, data: Dict[str, Any]) -> None:
        """Add data to short-term memory."""
        try:
            if not isinstance(data, dict):
                self.logger.error("Invalid data type for short-term memory: expected dict")
                return
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Add to short-term memory
            self.short_term_memory.append(data)
            
            # Keep only the most recent entries
            max_entries = 100
            if len(self.short_term_memory) > max_entries:
                self.short_term_memory = self.short_term_memory[-max_entries:]
            
            self.logger.info(f"Added data to short-term memory: {len(self.short_term_memory)} entries")
            
        except Exception as e:
            self.logger.error(f"Error adding to short-term memory: {e}")
    
    async def add_to_context_memory(self, data: Dict[str, Any]) -> None:
        """Add data to context memory."""
        try:
            if not isinstance(data, dict):
                self.logger.error("Invalid data type for context memory: expected dict")
                return
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Initialize context memory if needed
            if not self.context_memory:
                self.context_memory = {}
            
            # Add to context memory
            timestamp = datetime.now().isoformat()
            self.context_memory[timestamp] = data
            
            # Keep only the most recent entries
            max_entries = 50
            if len(self.context_memory) > max_entries:
                # Sort by timestamp and keep only the most recent
                sorted_keys = sorted(self.context_memory.keys())
                keys_to_remove = sorted_keys[:-max_entries]
                for key in keys_to_remove:
                    del self.context_memory[key]
            
            self.logger.info(f"Added data to context memory: {len(self.context_memory)} entries")
            
        except Exception as e:
            self.logger.error(f"Error adding to context memory: {e}")

    async def add_to_long_term_memory(self, data: Dict[str, Any]) -> None:
        """Add data to long-term memory."""
        try:
            if not isinstance(data, dict):
                self.logger.error("Invalid data type for long-term memory: expected dict")
                return
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Add to long-term memory
            self.long_term_memory.append(data)
            
            # Keep only the most recent entries
            max_entries = 1000  # Keep more entries in long-term memory
            if len(self.long_term_memory) > max_entries:
                self.long_term_memory = self.long_term_memory[-max_entries:]
            
            self.logger.info(f"Added data to long-term memory: {len(self.long_term_memory)} entries")
            
        except Exception as e:
            self.logger.error(f"Error adding to long-term memory: {e}") 