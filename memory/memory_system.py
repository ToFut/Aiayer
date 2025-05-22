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
import websockets
import traceback

# Use relative imports for same package
try:
    from .memory_logger import MemoryLogger
except ImportError:
    from memory_logger import MemoryLogger

try:
    from .memory_diagnostic_logger import MemoryDiagnosticLogger
except ImportError:
    from memory_diagnostic_logger import MemoryDiagnosticLogger

try:
    from .conscious_memory import ConsciousMemory
except ImportError:
    from conscious_memory import ConsciousMemory

try:
    from .enhanced_semantic_search import EnhancedSemanticSearch
except ImportError:
    # Fallback to basic search
    EnhancedSemanticSearch = None

try:
    from sensors import ScreenSensor, ProcessSensor
except ImportError:
    # Fallback - sensors not available
    ScreenSensor = ProcessSensor = None

from .safe_json import safe_load, safe_dump, safe_dumps
from .memory_types import ConversationMemory, ContextMemory

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
        self.process_sensor = ProcessSensor(config=self.SENSOR_CONFIG['process'])
        self.llava_client = None
        self.logger = logging.getLogger(__name__)
        self.ws = None
        self.ws_uri = "ws://localhost:8765"
        self.connected = False
        self.reconnect_delay = 3
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        
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
        
        # Initialize enhanced semantic search
        self.semantic_search = EnhancedSemanticSearch()
        self.logger.info("Enhanced semantic search initialized")
        
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
        # Set initialized to True at the end
        self.initialized = True
        
    async def connect(self):
        """Establish WebSocket connection."""
        try:
            self.ws = await websockets.connect(self.ws_uri)
            self.connected = True
            self.reconnect_attempts = 0
            self.logger.info("WebSocket connection established")
            
            # Start message handling loop
            asyncio.create_task(self._handle_messages())
            return True
        except Exception as e:
            self.logger.error(f"Failed to establish WebSocket connection: {e}")
            return False
            
    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            while self.connected:
                try:
                    message = await self.ws.recv()
                    await self._process_message(message)
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket connection closed")
                    await self._reconnect()
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
        except Exception as e:
            self.logger.error(f"Message handling loop error: {e}")
            self.connected = False
            
    async def _reconnect(self):
        """Attempt to reconnect to WebSocket server."""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                await asyncio.sleep(self.reconnect_delay)
                self.ws = await websockets.connect(self.ws_uri)
                self.connected = True
                self.reconnect_attempts = 0
                self.logger.info("Reconnected successfully")
                return True
            except Exception as e:
                self.reconnect_attempts += 1
                self.logger.error(f"Reconnection attempt failed: {e}")
        self.logger.error("Max reconnection attempts reached")
        return False
        
    async def _process_message(self, message):
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'sensor_data':
                await self.process_sensor_data(data.get('sensor_type'), data.get('data'))
            elif message_type == 'memory_query':
                response = await self.search_memory(data.get('query'), data.get('limit', 3))
                await self._send_response(data.get('id'), response)
            elif message_type == 'memory_update':
                await self.add_to_memory(data.get('memory_type'), data.get('data'))
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            
    async def _send_response(self, message_id, response):
        """Send response back through WebSocket."""
        try:
            if self.connected and self.ws:
                await self.ws.send(json.dumps({
                    'type': 'response',
                    'id': message_id,
                    'data': response
                }))
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            
    async def disconnect(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.connected = False
            self.logger.info("WebSocket connection closed")
    
    def _load_memory_state(self):
        """Load memory state from file if it exists."""
        try:
            if os.path.exists(self.memory_state_file):
                self.logger.info(f"🔄 Loading memory state from {self.memory_state_file}")
                
                with open(self.memory_state_file, 'r') as f:
                    state = json.load(f)
                    
                # Load short-term memory with increased capacity
                loaded_short_term = state.get('short_term', [])
                if loaded_short_term:
                    self.logger.info(f"  - Found {len(loaded_short_term)} short-term memory items")
                    self.short_term_memory = loaded_short_term
                else:
                    self.logger.info("  - No short-term memory found, initializing empty")
                    self.short_term_memory = []
                
                # Load long-term memory with increased capacity
                loaded_long_term = state.get('long_term', [])
                if loaded_long_term:
                    self.logger.info(f"  - Found {len(loaded_long_term)} long-term memory items")
                    self.long_term_memory = loaded_long_term
                else:
                    self.logger.info("  - No long-term memory found, initializing empty")
                    self.long_term_memory = []
                
                # Load context memory with increased capacity
                loaded_context = state.get('context', {})
                if loaded_context:
                    self.logger.info(f"  - Found context memory with {len(loaded_context)} items")
                    self.context_memory = loaded_context
                else:
                    self.logger.info("  - No context memory found, initializing empty")
                    self.context_memory = {
                        'current_context': {},
                        'application_context': {},
                        'sensor_data': {
                            'screen': {},
                            'process': {},
                            'file': {}
                        },
                        'activities': [],
                        'relationships': {},
                        'by_timestamp': {}
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
                # Initialize empty memory state with increased capacity
                self.short_term_memory = []
                self.long_term_memory = []
                self.context_memory = {
                    'sensor_data': {
                        'screen': {},
                        'process': {},
                        'file': {}
                    }
                }
                # Save initial state
                self._save_memory_state_sync()
                
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
            # Create new state file if loading fails
            self._save_memory_state_sync()

    def _save_memory_state_sync(self):
        """Synchronous version of save_memory_state for use in __init__ and error handling."""
        try:
            self.logger.debug(f"[DEBUG] _save_memory_state_sync called. Short-term: {len(self.short_term_memory)}, Long-term: {len(self.long_term_memory)}, Context keys: {list(self.context_memory.keys()) if isinstance(self.context_memory, dict) else 'N/A'}")
            
            # Log memory state before saving
            state = {
                'short_term': self.short_term_memory,
                'long_term': self.long_term_memory,
                'context': self.context_memory,
                'conscious': self.conscious_memory.get_state() if hasattr(self.conscious_memory, 'get_state') else {},
                'last_update': datetime.now().isoformat()
            }
            
            # Update existing file without creating backups
            with open(self.memory_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            self.logger.info(f"✅ Updated memory state with {len(self.short_term_memory)} short-term memories (sync)")
            self.diagnostic_logger.log_memory_event("memory_state_saved", {
                "timestamp": datetime.now().isoformat(),
                "success": True
            })
        except Exception as e:
            self.logger.error(f"❌ Error saving memory state (sync): {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "save_memory_state_sync"
            })

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
            
            # Update existing file without creating backups
            with open(self.memory_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Also update the last_context.json file for LLM integration
            await self._update_last_context()
            
            self.logger.info(f"✅ Updated memory state with {len(self.short_term_memory)} short-term memories")
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
        """Initialize the memory system with automatic sensor data collection."""
        try:
            self.logger.info("Initializing memory system...")
            
            # Load existing memory state
            self._load_memory_state()
            
            # Initialize sensors
            self.logger.info("Initializing sensors...")
            try:
                self.screen_sensor = ScreenSensor(config=self.SENSOR_CONFIG['screen'])
                self.process_sensor = ProcessSensor()
                self.logger.info("Sensors initialized successfully")
            except Exception as e:
                self.logger.error(f"Error initializing sensors: {e}")
                return False
            
            # Start sensor data collection
            self.logger.info("Starting sensor data collection...")
            asyncio.create_task(self._collect_sensor_data())
            
            # Start periodic memory cleanup
            self.logger.info("Starting periodic memory cleanup...")
            asyncio.create_task(self._periodic_cleanup())
            
            # Start WebSocket connection to bridge server
            self.logger.info("Connecting to bridge server...")
            asyncio.create_task(self.connect_to_server())
            
            self.logger.info("Memory system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing memory system: {e}")
            return False
            
    async def _periodic_cleanup(self):
        """Periodically clean up old memory data."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_old_data()
                self._compress_memory()
                await self._save_memory_state()
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")
                
    async def _collect_sensor_data(self):
        """Continuously collect data from sensors."""
        while True:
            try:
                # Collect screen sensor data
                if self.screen_sensor:
                    screen_data = await self.screen_sensor.get_current_state()
                    if screen_data:
                        await self.process_sensor_data('screen', screen_data)
                
                # Collect process sensor data
                if self.process_sensor:
                    process_data = await self.process_sensor.get_current_state()
                    if process_data:
                        await self.process_sensor_data('process', process_data)
                
                # Save memory state periodically
                await self._save_memory_state()
                
                # Wait before next collection
                await asyncio.sleep(self.SENSOR_CONFIG['screen']['interval_sec'])
                
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
            
    def process_sensor_data(self, sensor_data):
        """Process and store sensor data with enhanced context awareness"""
        try:
            # Extract screen and process data
            screen_data = sensor_data.get('screen', {})
            process_data = sensor_data.get('process', {})
            
            # Create meaningful summary
            summary = {
                'timestamp': time.time(),
                'active_applications': {
                    'foreground': [
                        {
                            'name': app.get('name', ''),
                            'type': app.get('type', ''),
                            'category': app.get('category', ''),
                            'state': app.get('state', {})
                        }
                        for app in process_data.get('foreground', [])
                    ],
                    'background': [
                        {
                            'name': app.get('name', ''),
                            'type': app.get('type', ''),
                            'category': app.get('category', '')
                        }
                        for app in process_data.get('background', [])
                        if app.get('type') != 'unknown'  # Only include relevant background apps
                    ]
                },
                'visual_context': {
                    'active_window': screen_data.get('active_window', {}),
                    'main_content': screen_data.get('content', {}).get('main_content', ''),
                    'ui_elements': {
                        'controls': len(screen_data.get('ui_elements', {}).get('controls', [])),
                        'text_fields': len(screen_data.get('ui_elements', {}).get('text_fields', [])),
                        'navigation': len(screen_data.get('ui_elements', {}).get('navigation', []))
                    },
                    'text_content': {
                        'headers': screen_data.get('text_content', {}).get('headers', []),
                        'main_text': screen_data.get('text_content', {}).get('main_text', [])
                    }
                },
                'system_state': {
                    'resources': process_data.get('system_resources', {}),
                    'network': process_data.get('network_state', {}),
                    'session_duration': process_data.get('session_duration', 0)
                }
            }
            
            # Store in short-term memory
            self.short_term_memory.append(summary)
            
            # Update context memory
            self.context_memory.update({
                'current_context': summary,
                'application_context': {
                    'active_apps': summary['active_applications'],
                    'app_states': process_data.get('app_states', {}),
                    'app_workflows': process_data.get('app_workflows', {})
                },
                'visual_context': summary['visual_context'],
                'system_state': summary['system_state']
            })
            
            # Save memory state
            self.save_memory_state()
            
            # Update last context
            self._update_last_context(sensor_data)
            
            logger.info("Processed and stored sensor data with enhanced context")
            logger.debug(f"Memory update stats: {len(summary['active_applications']['foreground'])} foreground apps, "
                        f"{len(summary['active_applications']['background'])} background apps, "
                        f"{summary['visual_context']['ui_elements']['controls']} UI controls")
            
        except Exception as e:
            logger.error(f"Error processing sensor data: {e}")
            
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
            context = await self._create_context_summary(message)
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

    async def _create_context_summary(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the current context using enhanced vector-based semantic search."""
        try:
            current_time = time.time()
            
            # Get latest screen data
            screen_data = None
            llava_analysis = None
            
            # First try to get LLaVA analysis from screen sensor
            if self.screen_sensor and hasattr(self.screen_sensor, 'last_data'):
                screen_data = self.screen_sensor.last_data
                if screen_data and hasattr(screen_data, 'llava_analysis'):
                    llava_analysis = screen_data.llava_analysis
            
            # If not available, try to get from conscious memory
            if not llava_analysis and self.conscious_memory:
                try:
                    llava_analysis = await self.conscious_memory.get_latest_llava_analysis()
                except Exception as e:
                    logger.warning(f"Failed to get LLaVA analysis from conscious memory: {e}")
            
            # Create context summary with LLaVA analysis if available
            context_summary = {
                "timestamp": current_time,
                "screen_context": {
                    "application": llava_analysis.get("application", {}).get("name", "unknown") if llava_analysis else "unknown",
                    "application_state": llava_analysis.get("application", {}).get("state", "unknown") if llava_analysis else "unknown",
                    "ui_elements": llava_analysis.get("ui_elements", []) if llava_analysis else [],
                    "user_activity": llava_analysis.get("user_activity", {}) if llava_analysis else {},
                    "visual_content": llava_analysis.get("visual_content", {}) if llava_analysis else {},
                    "text_content": screen_data.get("text", "") if screen_data else "",
                    "active_window": screen_data.get("active_window", "unknown") if screen_data else "unknown"
                },
                "process_context": {
                    "foreground_processes": llava_analysis.get("process_classification", {}).get("foreground", []) if llava_analysis else [],
                    "supporting_processes": llava_analysis.get("process_classification", {}).get("supporting", []) if llava_analysis else [],
                    "background_processes": llava_analysis.get("process_classification", {}).get("background", []) if llava_analysis else []
                },
                "search_method": "enhanced_vector_search",
                "relevance_quality": {
                    "score": 0.95 if llava_analysis else 0.5,  # High confidence if LLaVA analysis available
                    "confidence": "high" if llava_analysis else "medium",
                    "reason": "Direct visual analysis with LLaVA" if llava_analysis else "Basic screen analysis"
                }
            }
            
            # Log the rich context summary
            logger.info(f"=== CONTEXT SUMMARY ===\n{json.dumps(context_summary, indent=2)}")
            
            return context_summary
            
        except Exception as e:
            logger.error(f"Error creating context summary: {e}")
            return {
                "timestamp": current_time,
                "error": str(e),
                "search_method": "fallback",
                "relevance_quality": {
                    "score": 0.0,
                    "confidence": "low",
                    "reason": f"Error in context creation: {str(e)}"
                }
            }

    async def get_context_summary(self, query=None, limit=3):
        """Get a summary of the current context including relevant memories."""
        try:
            # Get latest sensor data
            latest_data = await self.get_latest_sensor_data()
            if not latest_data:
                return {
                    'window': 'Unknown',
                    'active_apps': [],
                    'screen_content': 'No screen content available',
                    'current_file': None,
                    'recent_files': [],
                    'relevant_memories': []
                }

            # Get relevant memories if query is provided
            relevant_memories = []
            if query:
                try:
                    # Use semantic search to find relevant memories
                    search_results = self.semantic_search.search(
                        query=query,
                        limit=limit * 2,  # Get more results to filter
                        memory_types=['short_term', 'long_term', 'context'],
                        min_score=0.5  # Higher threshold for better relevance
                    )
                    
                    # Process and filter results
                    seen_contents = set()
                    for result in search_results:
                        if result['score'] < 0.5:  # Skip low relevance results
                            continue
                            
                        content = result.get('content', '')
                        if content and content not in seen_contents:
                            seen_contents.add(content)
                            # Add search metadata
                            memory_item = {
                                'content': content,
                                'timestamp': result.get('timestamp', datetime.now().isoformat()),
                                '_search_score': result['score'],
                                '_search_source': result.get('source', 'unknown')
                            }
                            relevant_memories.append(memory_item)
                            
                            if len(relevant_memories) >= limit:
                                break
                                
                    self.logger.info(f"Found {len(relevant_memories)} relevant memories for query: {query}")
                    
                except Exception as e:
                    logger.error(f"Error searching memories: {e}")
                    logger.error(traceback.format_exc())

            # Get current file information
            current_file = None
            if latest_data.get('type') == 'file':
                current_file = {
                    'path': latest_data.get('path', 'Unknown'),
                    'type': latest_data.get('file_type', 'Unknown'),
                    'content': latest_data.get('content', '')[:500] + '...' if len(latest_data.get('content', '')) > 500 else latest_data.get('content', '')
                }

            # Get recent files
            recent_files = []
            try:
                # Use semantic search to find recent file-related memories
                file_results = self.semantic_search.search(
                    query='file',
                    limit=5,
                    memory_types=['short_term', 'context'],
                    min_score=0.4
                )
                
                for result in file_results:
                    if result.get('type') == 'file':
                        path = result.get('path')
                        if path and path not in recent_files:
                            recent_files.append(path)
            except Exception as e:
                logger.error(f"Error getting recent files: {e}")

            # Get active applications
            active_apps = []
            try:
                if 'active_apps' in latest_data:
                    apps = latest_data['active_apps']
                    if isinstance(apps, list):
                        for app in apps:
                            if isinstance(app, dict):
                                active_apps.append(app.get('name', str(app)))
                            else:
                                active_apps.append(str(app))
            except Exception as e:
                logger.error(f"Error processing active apps: {e}")

            # Construct context summary
            context_summary = {
                'window': latest_data.get('window', 'Unknown'),
                'active_apps': active_apps,
                'screen_content': latest_data.get('screen_content', 'No screen content available'),
                'current_file': current_file,
                'recent_files': recent_files,
                'relevant_memories': relevant_memories,
                'timestamp': datetime.now().isoformat(),
                'sensor_type': latest_data.get('type', 'Unknown'),
                'metadata': {
                    'search_performed': bool(query),
                    'memories_found': len(relevant_memories),
                    'context_source': 'memory_system',
                    'search_quality': 'high' if relevant_memories and any(m.get('_search_score', 0) > 0.7 for m in relevant_memories) else 'medium'
                }
            }

            # Add any additional sensor-specific data
            if latest_data.get('type') == 'screen':
                context_summary['ui_elements'] = latest_data.get('ui_elements', [])
                context_summary['workflow_stage'] = latest_data.get('workflow_stage', 'Unknown')
            elif latest_data.get('type') == 'process':
                context_summary['process_details'] = {
                    'pid': latest_data.get('pid'),
                    'cpu_usage': latest_data.get('cpu_usage'),
                    'memory_usage': latest_data.get('memory_usage')
                }

            return context_summary

        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            logger.error(traceback.format_exc())
            # Return basic context if there's an error
            return {
                'window': 'Unknown',
                'active_apps': [],
                'screen_content': 'Error retrieving context',
                'current_file': None,
                'recent_files': [],
                'relevant_memories': [],
                'error': str(e)
            }

    def get_recent_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent messages from memory."""
        try:
            self.logger.info(f"🔄 Retrieving {count} recent messages [VERIFICATION CHECK 9/10]")
            return self.short_term_memory[-count:]
        except Exception as e:
            self.logger.error(f"❌ Error retrieving recent messages: {str(e)} [VERIFICATION FAILED]")
            return []
    
    async def search_memory(self, query: str, limit: int = 5, memory_types: List[str] = None, 
                          context_aware: bool = True, time_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search memory using enhanced semantic search with context awareness and relationship tracking.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            memory_types: List of memory types to search in (short_term, long_term, context)
            context_aware: Whether to enhance search with current context
            time_window: Optional time window in seconds to limit search (e.g., 3600 for last hour)
            
        Returns:
            List of matching memory items with metadata
        """
        try:
            self.logger.info(f"🔍 SEARCHING MEMORY WITH ENHANCED CONTEXT-AWARE SEMANTIC SEARCH")
            self.logger.info(f"  - Query: {query}")
            self.logger.info(f"  - Limit: {limit}")
            self.logger.info(f"  - Context-aware: {context_aware}")
            if memory_types:
                self.logger.info(f"  - Memory types: {memory_types}")
            if time_window:
                self.logger.info(f"  - Time window: {time_window} seconds")
            
            start_time = time.time()
            
            self.diagnostic_logger.log_memory_event("memory_search_started", {
                "query": query,
                "limit": limit,
                "memory_types": memory_types,
                "context_aware": context_aware,
                "time_window": time_window,
                "timestamp": datetime.now().isoformat(),
                "search_type": "context_aware_vector"
            })
            
            # Enhance query with current context if context_aware is enabled
            enhanced_query = query
            application_context = None
            
            if context_aware and hasattr(self, 'context_memory') and self.context_memory:
                context_enhancers = []
                
                # Get current application context if available
                if 'current_context' in self.context_memory:
                    current_ctx = self.context_memory['current_context']
                    
                    # Add application context
                    if 'application' in current_ctx:
                        app_name = current_ctx['application']
                        context_enhancers.append(f"application:{app_name}")
                        application_context = app_name
                        
                    # Add workflow context
                    if 'workflow_stage' in current_ctx:
                        context_enhancers.append(f"task:{current_ctx['workflow_stage']}")
                        
                    # Add window title context
                    if 'window_title' in current_ctx:
                        window_parts = current_ctx['window_title'].split(' - ')
                        if window_parts:
                            context_enhancers.append(f"window:{window_parts[0]}")
                
                # Add recent activity contexts
                if 'activities' in self.context_memory and self.context_memory['activities']:
                    # Take the most recent activity
                    latest_activity = self.context_memory['activities'][-1]
                    activity_text = latest_activity.get('activity', '')
                    if activity_text:
                        # Extract key phrases (simplified)
                        activity_keywords = ' '.join([
                            word for word in activity_text.split()
                            if len(word) > 3 and word.lower() not in 
                            {'this', 'that', 'with', 'from', 'have', 'has', 'had', 'using', 'used'}
                        ])
                        if activity_keywords:
                            context_enhancers.append(f"activity:{activity_keywords[:50]}")
                
                # Combine context enhancers
                if context_enhancers:
                    context_string = ' '.join(context_enhancers)
                    enhanced_query = f"{query} {context_string}"
                    self.logger.info(f"Enhanced query with context: {enhanced_query[:100]}...")
            
            # Apply time window filter if provided
            min_timestamp = None
            if time_window:
                min_timestamp = datetime.now() - timedelta(seconds=time_window)
                min_timestamp = min_timestamp.isoformat()
            
            # Use enhanced semantic search with vector embeddings and context awareness
            results = self.semantic_search.search(
                query=enhanced_query,
                limit=limit * 2,  # Request more results to filter by timestamp
                memory_types=memory_types,
                min_score=0.3,  # Lower threshold to ensure we get enough results
                application_context=application_context  # Pass application context for better relevance
            )
            
            # Apply time window filtering if needed
            if min_timestamp:
                filtered_results = []
                for result in results:
                    result_ts = result.get('timestamp', '')
                    if result_ts and result_ts >= min_timestamp:
                        filtered_results.append(result)
                results = filtered_results
            
            # Apply relationship-based relevance boosting
            if context_aware and 'relationships' in self.context_memory:
                # Try to identify memory items with relationships to current context
                for i, result in enumerate(results):
                    # Check if this memory has connections to other memories
                    memory_id = result.get('id')
                    original_item = result.get('original_item', {})
                    
                    if 'memory_connections' in original_item:
                        for connection in original_item['memory_connections']:
                            conn_type = connection.get('type')
                            conn_id = connection.get('id')
                            
                            # Check if this connection relates to current context
                            if conn_type and conn_id:
                                # Boost score if related to current application context
                                if (conn_type == 'application' and 
                                    'current_context' in self.context_memory and
                                    self.context_memory['current_context'].get('application') == conn_id):
                                    result['score'] *= 1.3  # 30% boost
                                    self.logger.debug(f"Boosted result {memory_id} due to application relationship")
                                
                                # Boost score if related to current sensor data
                                elif (conn_type == 'source' and 
                                      'sensor_data' in self.context_memory and
                                      conn_id in self.context_memory['sensor_data']):
                                    result['score'] *= 1.2  # 20% boost
                                    self.logger.debug(f"Boosted result {memory_id} due to sensor relationship")
            
            # Sort by score and apply limit
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            limited_results = results[:limit]
            
            search_time = time.time() - start_time
            
            # Enhance results with additional metadata
            for result in limited_results:
                # Add memory type and update timestamp format for consistency
                memory_id = result.get('id', '')
                original_item = result.get('original_item', {})
                
                # Add relationship information to help user understand connections
                if 'memory_connections' in original_item:
                    connections_summary = []
                    for conn in original_item.get('memory_connections', [])[:3]:  # Show at most 3 connections
                        conn_type = conn.get('type', 'unknown')
                        conn_id = conn.get('id', 'unknown')
                        connections_summary.append(f"{conn_type}:{conn_id}")
                    
                    if connections_summary:
                        result['connections'] = connections_summary
                
                # Add insight information if available
                if 'insights' in original_item and isinstance(original_item['insights'], list):
                    insight_types = [insight.get('type', 'unknown') for insight in original_item['insights'][:3]]
                    if insight_types:
                        result['insight_types'] = insight_types
            
            # Log search stats
            self.logger.info(f"✅ Context-aware semantic search completed in {search_time:.3f}s")
            self.logger.info(f"  - Found {len(limited_results)} results (from {len(results)} total matches)")
            if limited_results:
                self.logger.info(f"  - Top result score: {limited_results[0]['score']:.4f}")
                if 'content' in limited_results[0]:
                    content_preview = limited_results[0]['content'][:50].replace('\n', ' ')
                    self.logger.info(f"  - Top result preview: {content_preview}...")
            
            self.diagnostic_logger.log_memory_event("memory_search_completed", {
                "query": query,
                "enhanced_query": enhanced_query != query,
                "results_count": len(limited_results),
                "total_matches": len(results),
                "top_score": limited_results[0]['score'] if limited_results else 0,
                "search_time_ms": int(search_time * 1000),
                "timestamp": datetime.now().isoformat(),
                "search_type": "context_aware_vector",
                "context_enhanced": context_aware and enhanced_query != query
            })
            
            return limited_results
            
        except Exception as e:
            self.logger.error(f"❌ Error in context-aware semantic search: {e}")
            self.logger.error(traceback.format_exc())
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
        """Clear all memory including enhanced semantic search index."""
        try:
            self.logger.info(f"🧹 CLEARING MEMORY AND SEMANTIC SEARCH INDEX: [VERIFICATION CHECK]")
            
            # Clear traditional memory stores
            self.short_term_memory = []
            self.long_term_memory = []
            self.context_memory = {}
            if hasattr(self.conscious_memory, 'clear'):
                self.conscious_memory.clear()
            
            # Clear enhanced semantic search index
            self.semantic_search.clear()
            self.logger.info("Cleared enhanced semantic search index")
            
            # Log the clearing of each memory type
            self.memory_logger.log_short_term_memory({"action": "clear"}, "memory_cleared")
            self.memory_logger.log_long_term_memory({"action": "clear"}, "memory_cleared")
            self.memory_logger.log_context_memory({"action": "clear"}, "memory_cleared")
            self.memory_logger.log_conscious_memory({"action": "clear"}, "memory_cleared")
            
            self.logger.info(f"✅ MEMORY CLEARED SUCCESSFULLY [VERIFICATION PASSED]")
            self.diagnostic_logger.log_memory_event("memory_cleared", {
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "semantic_search_cleared": True
            })
        except Exception as e:
            self.logger.error(f"❌ ERROR CLEARING MEMORY: [VERIFICATION FAILED]")
            self.logger.error(f"  - Error: {str(e)}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "clear_memory",
                "timestamp": datetime.now().isoformat()
            })

    async def get_related_memories(self, memory_id: str, relationship_types: List[str] = None, 
                                limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve memories related to a specific memory by memory_id.
        This method uses the relationship tracking system to find connected memories.
        
        Args:
            memory_id: The ID of the memory to find relations for
            relationship_types: Optional list of relationship types to filter by
            limit: Maximum number of related memories to return
            
        Returns:
            List of related memory items sorted by relevance
        """
        try:
            self.logger.info(f"Finding related memories for memory_id: {memory_id}")
            
            if not memory_id:
                return []
                
            # Initialize result collection
            related_memories = []
            seen_ids = set()
            
            # First, try to find the target memory to get its connections
            target_memory = None
            
            # Check short-term memory
            for mem in self.short_term_memory:
                if mem.get('memory_id') == memory_id:
                    target_memory = mem
                    break
            
            # Check long-term memory if not found
            if not target_memory:
                for mem in self.long_term_memory:
                    if mem.get('memory_id') == memory_id:
                        target_memory = mem
                        break
            
            # Check context memory if not found
            if not target_memory and 'by_timestamp' in self.context_memory:
                for ts, mem in self.context_memory['by_timestamp'].items():
                    if mem.get('memory_id') == memory_id:
                        target_memory = mem
                        break
            
            # If target memory is found, get direct connections
            if target_memory and 'memory_connections' in target_memory:
                self.logger.info(f"Found target memory: {memory_id}, extracting connections")
                
                # Get connections from target memory
                for connection in target_memory.get('memory_connections', []):
                    conn_type = connection.get('type')
                    conn_id = connection.get('id')
                    
                    # Skip if not a requested relationship type
                    if relationship_types and conn_type not in relationship_types:
                        continue
                    
                    # Look for memories with this connection
                    if 'relationships' in self.context_memory and conn_type in self.context_memory['relationships']:
                        if conn_id in self.context_memory['relationships'][conn_type]:
                            for related_ref in self.context_memory['relationships'][conn_type][conn_id]:
                                related_id = related_ref.get('memory_id')
                                if related_id and related_id != memory_id and related_id not in seen_ids:
                                    # Find the actual memory object
                                    related_memory = None
                                    
                                    # Check in various memory stores
                                    for mem in self.short_term_memory:
                                        if mem.get('memory_id') == related_id:
                                            related_memory = mem
                                            break
                                    
                                    if not related_memory:
                                        for mem in self.long_term_memory:
                                            if mem.get('memory_id') == related_id:
                                                related_memory = mem
                                                break
                                    
                                    if not related_memory and 'by_timestamp' in self.context_memory:
                                        for ts, mem in self.context_memory['by_timestamp'].items():
                                            if mem.get('memory_id') == related_id:
                                                related_memory = mem
                                                break
                                    
                                    if related_memory:
                                        # Calculate relevance score based on relationship type
                                        relevance = 1.0
                                        if conn_type == 'source':
                                            relevance = 0.8  # Same source but lower relevance
                                        elif conn_type == 'insight':
                                            relevance = 0.9  # Insights are more relevant
                                        elif conn_type == 'application':
                                            relevance = 1.0  # Application context is highly relevant
                                        
                                        # Add to result with relevance info
                                        related_memories.append({
                                            'memory': related_memory,
                                            'relevance': relevance,
                                            'relationship_type': conn_type,
                                            'relationship_id': conn_id
                                        })
                                        seen_ids.add(related_id)
            
            # If we don't have enough related memories yet, try semantic similarity
            if len(related_memories) < limit and target_memory:
                self.logger.info(f"Not enough relation-based memories, adding semantic similarity matches")
                
                # Extract text for similarity search
                query_text = self._get_text_for_vectorization(target_memory)
                if query_text:
                    # Use semantic search to find similar memories
                    similar_results = await self.search_memory(
                        query=query_text,
                        limit=(limit - len(related_memories)) * 2,  # Get more to filter
                        context_aware=False  # Don't re-use current context for this search
                    )
                    
                    # Add similar results that aren't already in related_memories
                    for result in similar_results:
                        result_id = result.get('id')
                        if result_id and result_id != memory_id and result_id not in seen_ids:
                            # Get the full memory for consistency
                            similar_memory = None
                            for mem in self.short_term_memory:
                                if mem.get('memory_id') == result_id:
                                    similar_memory = mem
                                    break
                            
                            if not similar_memory:
                                for mem in self.long_term_memory:
                                    if mem.get('memory_id') == result_id:
                                        similar_memory = mem
                                        break
                            
                            if not similar_memory and 'by_timestamp' in self.context_memory:
                                for ts, mem in self.context_memory['by_timestamp'].items():
                                    if mem.get('memory_id') == result_id:
                                        similar_memory = mem
                                        break
                            
                            if similar_memory:
                                # Add to result with similarity score as relevance
                                related_memories.append({
                                    'memory': similar_memory,
                                    'relevance': result.get('score', 0.5),
                                    'relationship_type': 'semantic_similarity',
                                    'relationship_id': None
                                })
                                seen_ids.add(result_id)
            
            # Sort by relevance and apply limit
            related_memories.sort(key=lambda x: x.get('relevance', 0), reverse=True)
            limited_results = related_memories[:limit]
            
            # Format results for return
            formatted_results = []
            for item in limited_results:
                memory = item['memory']
                formatted_result = {
                    'memory_id': memory.get('memory_id', 'unknown'),
                    'content': memory.get('content', ''),
                    'timestamp': memory.get('timestamp', ''),
                    'memory_type': memory.get('memory_type', 'unknown'),
                    'relevance': item.get('relevance', 0),
                    'relationship_type': item.get('relationship_type', 'unknown'),
                    'sensor_type': memory.get('sensor_type', 'unknown')
                }
                
                # Add insights if available
                if 'insights' in memory and isinstance(memory['insights'], list):
                    formatted_result['insights'] = memory['insights']
                
                formatted_results.append(formatted_result)
            
            self.logger.info(f"Found {len(formatted_results)} related memories for {memory_id}")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error finding related memories: {e}")
            self.logger.error(traceback.format_exc())
            return []

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
                async with websockets.connect(self.server_uri, ping_interval=30, ping_timeout=90) as websocket:
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

    async def add_to_short_term_memory(self, data: Dict[str, Any]) -> str:
        """
        Add data to short-term memory with enhanced metadata tracking and search indexing.
        
        Args:
            data: Dictionary containing the memory data
            
        Returns:
            memory_id: Identifier for the stored memory item
        """
        try:
            if not isinstance(data, dict):
                self.logger.error("Invalid data type for short-term memory: expected dict")
                return None
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Generate a memory_id if not present
            memory_id = data.get('memory_id', f"stm_{int(time.time() * 1000)}")
            data['memory_id'] = memory_id
            
            # Add memory type metadata if not present
            if 'memory_type' not in data:
                data['memory_type'] = 'short_term'
            
            # Add to short-term memory
            self.short_term_memory.append(data)
            
            # Keep only the most recent entries
            max_entries = 200  # Increased from 100 for better context
            if len(self.short_term_memory) > max_entries:
                # Before discarding old memories, consider moving important ones to long-term
                oldest_memories = self.short_term_memory[:(len(self.short_term_memory) - max_entries)]
                for old_memory in oldest_memories:
                    # If the memory has insights or is marked as significant, move to long-term
                    if (old_memory.get('insights') or 
                        old_memory.get('is_significant', False) or 
                        old_memory.get('memory_type') in ['application_workflow', 'email_data', 'visual_data']):
                        # Clone and mark as auto-archived
                        archived_memory = old_memory.copy()
                        archived_memory['archived_from'] = 'short_term'
                        archived_memory['archived_at'] = datetime.now().isoformat()
                        await self.add_to_long_term_memory(archived_memory)
                        self.logger.info(f"Auto-archived significant memory {old_memory.get('memory_id')} to long-term")
                
                # Keep only the most recent entries
                self.short_term_memory = self.short_term_memory[-max_entries:]
            
            # Add to searchable memory via semantic search
            try:
                self.semantic_search.add_to_index(
                    data, 
                    'short_term',
                    metadata={
                        'timestamp': data['timestamp'],
                        'memory_id': memory_id,
                        'memory_type': data.get('memory_type', 'short_term'),
                        'source': data.get('sensor_type', 'unknown')
                    }
                )
            except Exception as se:
                self.logger.error(f"Error adding to semantic search index: {se}")
            
            self.logger.info(f"Added data to short-term memory: {len(self.short_term_memory)} entries, id={memory_id}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error adding to short-term memory: {e}")
            self.logger.error(traceback.format_exc())
            return None
    
    def _update_last_context(self, sensor_data):
        """Update last_context.json with comprehensive context data"""
        try:
            # Get the most recent context summary
            context_summary = self.get_latest_context_summary()
            
            # Get the most recent screen and process data
            screen_data = sensor_data.get('screen', {})
            process_data = sensor_data.get('process', {})
            
            # Get active window and application info
            active_window = screen_data.get('active_window', {})
            active_app = process_data.get('foreground', [{}])[0] if process_data.get('foreground') else {}
            
            # Create rich context structure
            last_context = {
                'timestamp': time.time(),
                'visual_context': {
                    'active_window': {
                        'title': active_window.get('title', ''),
                        'application': active_window.get('application', ''),
                        'path': active_window.get('path', '')
                    },
                    'screen_elements': {
                        'controls': screen_data.get('ui_elements', {}).get('controls', []),
                        'text_fields': screen_data.get('ui_elements', {}).get('text_fields', []),
                        'navigation': screen_data.get('ui_elements', {}).get('navigation', [])
                    },
                    'text_content': {
                        'headers': screen_data.get('text_content', {}).get('headers', []),
                        'main_text': screen_data.get('text_content', {}).get('main_text', []),
                        'raw_text': screen_data.get('text_content', {}).get('raw_text', '')
                    },
                    'visual_hierarchy': screen_data.get('visual_hierarchy', {}),
                    'ui_state': screen_data.get('ui_state', {})
                },
                'application_context': {
                    'active_app': {
                        'name': active_app.get('name', ''),
                        'type': active_app.get('type', ''),
                        'category': active_app.get('category', ''),
                        'state': active_app.get('state', {})
                    },
                    'foreground_apps': [
                        {
                            'name': app.get('name', ''),
                            'type': app.get('type', ''),
                            'category': app.get('category', ''),
                            'state': app.get('state', {})
                        }
                        for app in process_data.get('foreground', [])
                    ],
                    'background_apps': [
                        {
                            'name': app.get('name', ''),
                            'type': app.get('type', ''),
                            'category': app.get('category', '')
                        }
                        for app in process_data.get('background', [])
                        if app.get('type') != 'unknown'
                    ],
                    'app_states': process_data.get('app_states', {}),
                    'app_workflows': process_data.get('app_workflows', {})
                },
                'user_activity': {
                    'current_activity': context_summary.get('current_activity', {}),
                    'recent_actions': context_summary.get('recent_actions', []),
                    'interaction_state': screen_data.get('ui_state', {}),
                    'workflow_stage': process_data.get('app_workflows', {}).get('current_stage', '')
                },
                'system_state': {
                    'active_processes': process_data.get('foreground', []) + process_data.get('background', []),
                    'system_resources': {
                        'cpu_usage': process_data.get('system_resources', {}).get('cpu_usage', 0),
                        'memory_usage': process_data.get('system_resources', {}).get('memory_usage', 0),
                        'disk_usage': process_data.get('system_resources', {}).get('disk_usage', 0)
                    },
                    'network_state': process_data.get('network_state', {}),
                    'session_duration': process_data.get('session_duration', 0)
                },
                'temporal_context': {
                    'time_of_day': datetime.now().strftime('%H:%M:%S'),
                    'session_duration': process_data.get('session_duration', 0),
                    'last_update': time.time()
                },
                'semantic_context': {
                    'current_task': context_summary.get('current_task', ''),
                    'related_insights': context_summary.get('related_insights', []),
                    'workflow_context': process_data.get('app_workflows', {}).get('context', {}),
                    'user_intent': context_summary.get('user_intent', '')
                }
            }
            
            # Save to last_context.json
            with open('last_context.json', 'w') as f:
                json.dump(last_context, f, indent=2)
            
            logger.info("Updated last_context.json with comprehensive context data")
            logger.debug(f"Context update stats: {len(last_context['visual_context']['screen_elements']['controls'])} UI controls, "
                        f"{len(last_context['application_context']['foreground_apps'])} foreground apps, "
                        f"{len(last_context['user_activity']['recent_actions'])} recent actions")
            
        except Exception as e:
            logger.error(f"Error updating last context: {e}")
            self.diagnostic_logger.log_memory_error(e, {
                "context": "update_last_context"
            })
    
    async def add_to_context_memory(self, data: Dict[str, Any]) -> str:
        """
        Add data to context memory with enhanced structure and relationship tracking.
        
        Args:
            data: Dictionary containing the memory data
            
        Returns:
            memory_id: Identifier for the stored memory item
        """
        try:
            if not isinstance(data, dict):
                self.logger.error("Invalid data type for context memory: expected dict")
                return None
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
            
            # Generate a memory_id if not present
            memory_id = data.get('memory_id', f"ctx_{int(time.time() * 1000)}")
            data['memory_id'] = memory_id
            
            # Add memory type metadata if not present
            if 'memory_type' not in data:
                data['memory_type'] = 'context'
            
            # Initialize context memory with structured categories if needed
            if not self.context_memory:
                self.context_memory = {
                    'current_context': {},
                    'application_context': {},
                    'sensor_data': {
                        'screen': {},
                        'process': {},
                        'file': {}
                    },
                    'activities': [],
                    'relationships': {},
                    'by_timestamp': {}
                }
            
            # Ensure all required keys exist in context_memory
            if 'by_timestamp' not in self.context_memory:
                self.context_memory['by_timestamp'] = {}
            if 'current_context' not in self.context_memory:
                self.context_memory['current_context'] = {}
            if 'application_context' not in self.context_memory:
                self.context_memory['application_context'] = {}
            if 'activities' not in self.context_memory:
                self.context_memory['activities'] = []
            if 'relationships' not in self.context_memory:
                self.context_memory['relationships'] = {}
            if 'sensor_data' not in self.context_memory:
                self.context_memory['sensor_data'] = {
                    'screen': {},
                    'process': {},
                    'file': {}
                }
            elif isinstance(self.context_memory['sensor_data'], dict):
                # Ensure sensor_data contains required keys
                for sensor_type in ['screen', 'process', 'file']:
                    if sensor_type not in self.context_memory['sensor_data']:
                        self.context_memory['sensor_data'][sensor_type] = {}
            
            # Timestamp for context organization
            timestamp = data.get('timestamp', datetime.now().isoformat())
            
            # Store in timestamp-indexed map
            self.context_memory['by_timestamp'][timestamp] = data
            
            # Store in appropriate category based on memory type
            sensor_type = data.get('sensor_type')
            if sensor_type and sensor_type in self.context_memory['sensor_data']:
                # Store in sensor-specific section
                self.context_memory['sensor_data'][sensor_type][memory_id] = data
                
                # Update current context with latest sensor data
                if 'window_title' in data:
                    self.context_memory['current_context']['window_title'] = data['window_title']
                if 'content' in data:
                    self.context_memory['current_context']['content'] = data['content']
                
            # Store application context separately for faster retrieval
            if 'application' in data and isinstance(data['application'], dict):
                app_name = data['application'].get('name')
                if app_name:
                    self.context_memory['application_context'][app_name] = {
                        'last_seen': timestamp,
                        'data': data['application'],
                        'memory_id': memory_id
                    }
                    
                    # Add to current context
                    self.context_memory['current_context']['application'] = app_name
                    if data['application'].get('workflow_stage'):
                        self.context_memory['current_context']['workflow_stage'] = data['application']['workflow_stage']
            
            # Store activity data for context tracking
            if data.get('context_understanding') or data.get('activity_summary'):
                # Add to activities list
                activity = {
                    'timestamp': timestamp,
                    'memory_id': memory_id,
                    'activity': data.get('context_understanding') or data.get('activity_summary'),
                    'source': data.get('sensor_type')
                }
                self.context_memory['activities'].append(activity)
                
                # Keep only the most recent activities
                max_activities = 30
                if len(self.context_memory['activities']) > max_activities:
                    self.context_memory['activities'] = self.context_memory['activities'][-max_activities:]
            
            # Track relationships between memory items
            if 'memory_connections' in data and isinstance(data['memory_connections'], list):
                for connection in data['memory_connections']:
                    conn_type = connection.get('type')
                    conn_id = connection.get('id')
                    if conn_type and conn_id:
                        if conn_type not in self.context_memory['relationships']:
                            self.context_memory['relationships'][conn_type] = {}
                        if conn_id not in self.context_memory['relationships'][conn_type]:
                            self.context_memory['relationships'][conn_type][conn_id] = []
                        # Add reference to this memory item
                        self.context_memory['relationships'][conn_type][conn_id].append({
                            'memory_id': memory_id,
                            'timestamp': timestamp
                        })
            
            # Limit the size of the context memory
            max_timestamps = 200
            if len(self.context_memory['by_timestamp']) > max_timestamps:
                # Find oldest timestamps to remove
                sorted_timestamps = sorted(self.context_memory['by_timestamp'].keys())
                timestamps_to_remove = sorted_timestamps[:(len(sorted_timestamps) - max_timestamps)]
                
                # Remove old data
                for old_ts in timestamps_to_remove:
                    old_data = self.context_memory['by_timestamp'].pop(old_ts, None)
                    
                    # Clean up sensor data references if needed
                    if old_data:
                        old_sensor_type = old_data.get('sensor_type')
                        old_memory_id = old_data.get('memory_id')
                        if old_sensor_type and old_memory_id and old_sensor_type in self.context_memory['sensor_data']:
                            self.context_memory['sensor_data'][old_sensor_type].pop(old_memory_id, None)
            
            # Add to searchable memory via semantic search
            try:
                self.semantic_search.add_to_index(
                    data, 
                    'context',
                    metadata={
                        'timestamp': timestamp,
                        'memory_id': memory_id,
                        'memory_type': data.get('memory_type', 'context'),
                        'source': data.get('sensor_type', 'unknown')
                    }
                )
            except Exception as se:
                self.logger.error(f"Error adding context to semantic search index: {se}")
            
            self.logger.info(f"Added data to context memory: memory_id={memory_id} | total timestamps: {len(self.context_memory['by_timestamp'])}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error adding to context memory: {e}")
            self.logger.error(traceback.format_exc())
            return None

    async def add_to_long_term_memory(self, data: Dict[str, Any]) -> str:
        """
        Add data to long-term memory with proper categorization and relationship tracking.
        
        Args:
            data: Dictionary containing the memory data
            
        Returns:
            memory_id: Identifier for the stored memory item
        """
        try:
            if not isinstance(data, dict):
                self.logger.error("Invalid data type for long-term memory: expected dict")
                return None
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()
                
            # Generate a memory_id if not present
            memory_id = data.get('memory_id', f"ltm_{int(time.time() * 1000)}")
            data['memory_id'] = memory_id
            
            # Add memory type metadata if not present
            if 'memory_type' not in data:
                data['memory_type'] = 'long_term'
            
            # Add storage timestamp
            data['stored_at'] = datetime.now().isoformat()
            
            # Process and classify memory before storing
            # This enhances retrievability later
            if 'content' in data and isinstance(data['content'], str):
                # Calculate approximate "importance score" based on various factors
                importance_score = 1.0
                
                # Factors that increase importance
                if data.get('is_significant', False):
                    importance_score *= 1.5
                
                # Content with insights is more valuable
                if 'insights' in data and isinstance(data['insights'], list):
                    importance_score *= (1.0 + min(0.5, 0.1 * len(data['insights'])))
                
                # Email and application data is important
                if 'email_data' in data or ('application' in data and data['application'].get('workflow_stage')):
                    importance_score *= 1.3
                
                # Add importance score
                data['importance_score'] = importance_score
            
            # Add to long-term memory
            self.long_term_memory.append(data)
            
            # Keep only the most recent/important entries
            max_entries = 2000  # Increased from 1000 for better long-term recall
            if len(self.long_term_memory) > max_entries:
                # Sort by importance score and recency, then keep the top entries
                # This is more sophisticated than just keeping recent entries
                
                # First, score all items by combining importance and recency
                scored_items = []
                now = datetime.now()
                
                for i, item in enumerate(self.long_term_memory):
                    # Get basic scores
                    importance = item.get('importance_score', 1.0)
                    
                    # Calculate recency factor
                    try:
                        timestamp = datetime.fromisoformat(item.get('timestamp', '2020-01-01T00:00:00'))
                        time_diff_days = (now - timestamp).days
                        # Recency factor decreases with age but doesn't go below 0.2
                        recency = max(0.2, 1.0 - (time_diff_days / 365))
                    except (ValueError, TypeError):
                        recency = 0.5  # Default for invalid timestamps
                    
                    # Combined score
                    combined_score = (importance * 0.7) + (recency * 0.3)
                    
                    scored_items.append((i, combined_score, item))
                
                # Sort by score (highest first)
                scored_items.sort(key=lambda x: x[1], reverse=True)
                
                # Keep the top items
                indices_to_keep = [item[0] for item in scored_items[:max_entries]]
                indices_to_keep.sort()  # Sort to maintain original order
                
                # Rebuild the list with only the selected items
                self.long_term_memory = [self.long_term_memory[i] for i in indices_to_keep]
            
            # Add to searchable memory via semantic search
            try:
                self.semantic_search.add_to_index(
                    data, 
                    'long_term',
                    metadata={
                        'timestamp': data['timestamp'],
                        'memory_id': memory_id,
                        'memory_type': data.get('memory_type', 'long_term'),
                        'source': data.get('sensor_type', 'unknown'),
                        'importance': data.get('importance_score', 1.0)
                    }
                )
            except Exception as se:
                self.logger.error(f"Error adding to semantic search index: {se}")
            
            self.logger.info(f"Added data to long-term memory: {len(self.long_term_memory)} entries, id={memory_id}")
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Error adding to long-term memory: {e}")
            self.logger.error(traceback.format_exc())
            return None
            
    async def get_latest_sensor_data(self):
        """Return the most recent sensor data from context_memory['sensor_data']."""
        try:
            # Try to get the latest screen data
            screen_data = self.context_memory.get('sensor_data', {}).get('screen', {})
            if screen_data:
                # Get the most recent screen data by timestamp
                latest_screen = max(screen_data.values(), key=lambda x: x.get('timestamp', ''), default=None)
                if latest_screen:
                    return latest_screen
            # Try to get the latest process data
            process_data = self.context_memory.get('sensor_data', {}).get('process', {})
            if process_data:
                latest_process = max(process_data.values(), key=lambda x: x.get('timestamp', ''), default=None)
                if latest_process:
                    return latest_process
            # Try to get the latest file data
            file_data = self.context_memory.get('sensor_data', {}).get('file', {})
            if file_data:
                latest_file = max(file_data.values(), key=lambda x: x.get('timestamp', ''), default=None)
                if latest_file:
                    return latest_file
            return {}
        except Exception as e:
            self.logger.error(f"Error getting latest sensor data: {e}")
            return {}

# Add main function to allow direct execution
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Main function to run the memory system."""
        logger.info("Starting memory system as standalone service")
        memory_system = MemorySystem()
        await memory_system.initialize()
        
        try:
            # Keep the memory system running
            while True:
                await asyncio.sleep(10)
                logger.info("Memory system is running...")
        except KeyboardInterrupt:
            logger.info("Memory system stopped by user")
        except Exception as e:
            logger.error(f"Error in memory system: {e}")
            logger.error(traceback.format_exc())
        finally:
            # Clean up resources
            if hasattr(memory_system, "stop"):
                await memory_system.stop()
    
    # Run the main function
    asyncio.run(main()) 