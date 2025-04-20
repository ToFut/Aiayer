"""High-performance LLaVA analyzer with enhanced caching and parallel processing."""

import asyncio
import logging
from typing import Dict, Any, Optional, Union, List, Tuple
import json
import os
from datetime import datetime
import aiohttp
import requests
import base64
from PIL import Image
import io
import numpy as np
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache
import threading
import queue
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import aiofiles
import signal
import contextlib

# Configure logging
logger = logging.getLogger(__name__)

class AnalysisCache:
    """Advanced caching system for LLaVA analysis results."""
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size  # Maximum cache size
        self.ttl = ttl  # Time to live in seconds
        self._cache = {}  # Main cache dictionary
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._access_times = {}  # Track last access time for each key
        self._cleanup_timer = None  # Timer for periodic cleanup
        self._start_cleanup_timer()
        self._hit_count = 0
        self._miss_count = 0
        self._disk_cache_enabled = False
        self._disk_cache_dir = None
    
    def enable_disk_cache(self, cache_dir: str = ".llava_cache"):
        """Enable disk-based caching for persistence."""
        self._disk_cache_enabled = True
        self._disk_cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        # Load existing disk cache into memory
        self._load_from_disk()
        logger.info(f"Disk cache enabled in {cache_dir}")
    
    def _start_cleanup_timer(self):
        """Start periodic cleanup timer."""
        self._cleanup_timer = threading.Timer(60.0, self._cleanup_expired)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
    
    def _cleanup_expired(self):
        """Clean up expired cache entries."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, access_time in self._access_times.items()
                if (current_time - access_time) > self.ttl
            ]
            
            for key in expired_keys:
                if key in self._cache:
                    del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
            
            logger.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries")
        
        # Schedule next cleanup
        self._start_cleanup_timer()
    
    def _enforce_size_limit(self):
        """Enforce the maximum cache size by removing least recently used items."""
        if len(self._cache) <= self.max_size:
            return
            
        # Sort by access time (oldest first)
        sorted_keys = sorted(self._access_times.items(), key=lambda x: x[1])
        
        # Calculate how many items to remove
        excess = len(self._cache) - self.max_size
        
        # Remove oldest items
        for i in range(excess):
            key = sorted_keys[i][0]
            if key in self._cache:
                del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]
    
    async def _save_to_disk_async(self, key: str, value: Dict[str, Any]):
        """Save cache entry to disk asynchronously."""
        if not self._disk_cache_enabled:
            return
            
        try:
            file_path = os.path.join(self._disk_cache_dir, f"{key}.json")
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps({
                    'value': value,
                    'timestamp': self._access_times.get(key, time.time())
                }))
        except Exception as e:
            logger.warning(f"Failed to save cache to disk: {e}")
    
    def _save_to_disk(self, key: str, value: Dict[str, Any]):
        """Save cache entry to disk."""
        if not self._disk_cache_enabled:
            return
            
        try:
            file_path = os.path.join(self._disk_cache_dir, f"{key}.json")
            with open(file_path, 'w') as f:
                json.dump({
                    'value': value,
                    'timestamp': self._access_times.get(key, time.time())
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save cache to disk: {e}")
    
    def _load_from_disk(self):
        """Load cache entries from disk."""
        if not self._disk_cache_enabled:
            return
            
        try:
            files = [f for f in os.listdir(self._disk_cache_dir) if f.endswith('.json')]
            loaded_count = 0
            
            for file_name in files:
                try:
                    file_path = os.path.join(self._disk_cache_dir, file_name)
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        key = file_name[:-5]  # Remove .json extension
                        
                        # Check if entry is expired
                        if (time.time() - data.get('timestamp', 0)) <= self.ttl:
                            self._cache[key] = data['value']
                            self._access_times[key] = data['timestamp']
                            loaded_count += 1
                except Exception as e:
                    logger.warning(f"Failed to load cache file {file_name}: {e}")
            
            logger.info(f"Loaded {loaded_count} entries from disk cache")
        except Exception as e:
            logger.warning(f"Failed to load cache from disk: {e}")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from the cache."""
        with self._lock:
            value = self._cache.get(key)
            
            if value is not None:
                # Update access time
                self._access_times[key] = time.time()
                self._hit_count += 1
                return value
                
            self._miss_count += 1
            return None
    
    def set(self, key: str, value: Dict[str, Any]):
        """Set a value in the cache."""
        with self._lock:
            self._cache[key] = value
            self._access_times[key] = time.time()
            self._enforce_size_limit()
            
        # Save to disk if enabled (outside of lock to avoid blocking)
        if self._disk_cache_enabled:
            self._save_to_disk(key, value)
    
    async def set_async(self, key: str, value: Dict[str, Any]):
        """Set a value in the cache asynchronously."""
        with self._lock:
            self._cache[key] = value
            self._access_times[key] = time.time()
            self._enforce_size_limit()
            
        # Save to disk if enabled (outside of lock to avoid blocking)
        if self._disk_cache_enabled:
            await self._save_to_disk_async(key, value)
    
    def clear(self):
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._hit_count = 0
            self._miss_count = 0
            
        # Clear disk cache if enabled
        if self._disk_cache_enabled:
            try:
                for file_name in os.listdir(self._disk_cache_dir):
                    if file_name.endswith('.json'):
                        os.remove(os.path.join(self._disk_cache_dir, file_name))
            except Exception as e:
                logger.warning(f"Failed to clear disk cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_ratio = self._hit_count / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'ttl': self.ttl,
                'hit_count': self._hit_count,
                'miss_count': self._miss_count,
                'hit_ratio': hit_ratio,
                'disk_cache_enabled': self._disk_cache_enabled
            }

# Image preprocessing pool
def preprocess_image(image_data: Union[bytes, np.ndarray, Image.Image], max_width: int = 800, quality: int = 60) -> bytes:
    """Preprocess image for LLaVA analysis."""
    try:
        # Convert to PIL Image based on input type
        if isinstance(image_data, np.ndarray):
            img = Image.fromarray(image_data)
        elif isinstance(image_data, Image.Image):
            img = image_data
        else:
            img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if necessary
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Optimize and compress
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Image preprocessing error: {e}")
        raise

class LocalLLMAnalyzer:
    """Enhanced high-performance analyzer for screen content using Ollama local LLM."""
    
    def __init__(self, cache_dir=".llava_cache", max_cache_size=100):
        """Initialize the LocalLLMAnalyzer with caching and connection management."""
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size
        self.cache = {}
        self.cache_hits = 0
        self.total_requests = 0
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize thread and process pools
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.process_pool = ProcessPoolExecutor(max_workers=2)
        
        # Initialize model parameters
        self.model_params = {
            "model": "llava",
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        }
        
        # Initialize session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Initialize cache
        self._init_cache()
        
        # Initialize request processing
        self.request_queue = asyncio.Queue()
        self.request_semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        self.processor_task = None
        
        # Set up additional parameters
        self.base_url = 'http://localhost:11434'
        self.model_name = 'llava:latest'
        self.timeout = 30
        self.min_request_interval = 0.5
        self.last_request_time = 0
        self.running = True
        
        # Check server availability
        self._check_server()

    def _init_cache(self):
        """Initialize the cache system."""
        try:
            # Create cache directory if it doesn't exist
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Initialize AnalysisCache with disk caching enabled
            self.cache = AnalysisCache(max_size=self.max_cache_size)
            self.cache.enable_disk_cache(self.cache_dir)
            
            logger.info(f"Cache initialized with size {self.max_cache_size} in directory {self.cache_dir}")
            
        except Exception as e:
            logger.error(f"Error initializing cache: {e}")
            # Fall back to in-memory cache only
            self.cache = AnalysisCache(max_size=self.max_cache_size)
            logger.info("Fallback to in-memory cache only")

    def _check_server(self):
        """Check if Ollama server is running and model is available."""
        try:
            response = self.session.get('http://localhost:11434/api/tags')
            response.raise_for_status()
            models = response.json().get('models', [])
            if not any(m.get('name', '').startswith('llava:') for m in models):
                logging.warning("LLaVA model not found in available models")
        except Exception as e:
            logging.error(f"Failed to check server: {e}")
            raise RuntimeError("Ollama server not available") from e

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'thread_pool'):
            self.thread_pool.shutdown(wait=False)
        if hasattr(self, 'process_pool'):
            self.process_pool.shutdown(wait=False)

    async def analyze(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze screen content using LLaVA."""
        try:
            # Extract image data and metadata
            image_data = content.get('image')
            if image_data is None:
                self.logger.error("No image data provided")
                return self._get_default_analysis(
                    timestamp=content.get('timestamp', time.time()),
                    screen_size=content.get('screen_size', {'width': 0, 'height': 0}),
                    error="No image data provided"
                )
            
            timestamp = content.get('timestamp', time.time())
            screen_size = content.get('screen_size', {'width': 0, 'height': 0})
            
            # Generate cache key
            cache_key = self._get_cache_key(image_data)
            
            # Check cache
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                self.logger.debug(f"Cache hit for key {cache_key}")
                cached_result['timestamp'] = timestamp
                return cached_result
            
            # Process image
            try:
                preprocessed_image = await self._preprocess_image(image_data)
            except Exception as e:
                self.logger.error(f"Image preprocessing failed: {e}")
                return self._get_default_analysis(
                    timestamp=timestamp,
                    screen_size=screen_size,
                    error=f"Image preprocessing failed: {str(e)}"
                )
            
            # Prepare analysis request
            try:
                response = await self._request_llava_analysis(
                    preprocessed_image,
                    self._prepare_prompt(screen_size)
                )
                
                # Add metadata to response
                response['timestamp'] = timestamp
                response['screen_size'] = screen_size
                
                # Cache the result
                await self.cache.set_async(cache_key, response)
                
                return response
                
            except Exception as e:
                self.logger.error(f"LLaVA analysis failed: {e}")
                return self._get_default_analysis(
                    timestamp=timestamp,
                    screen_size=screen_size,
                    error=f"Analysis failed: {str(e)}"
                )
            
        except asyncio.CancelledError:
            self.logger.warning("Analysis request was cancelled")
            raise
        except Exception as e:
            self.logger.error(f"Error in analyze: {str(e)}")
            return self._get_default_analysis(
                timestamp=time.time(),
                screen_size={'width': 0, 'height': 0},
                error=str(e)
            )

    def _get_cache_key(self, image_data: bytes) -> str:
        """Generate a cache key for the image."""
        return hashlib.md5(image_data).hexdigest()

    async def _preprocess_image(self, image_data: bytes) -> str:
        """Preprocess image data."""
        try:
            loop = asyncio.get_event_loop()
            if hasattr(self, 'process_pool') and self.process_pool:
                processed = await loop.run_in_executor(
                    self.process_pool,
                    preprocess_image,
                    image_data,
                    800,  # max_width
                    60   # quality
                )
            else:
                # Fallback to synchronous processing if no process pool
                processed = preprocess_image(
                    image_data,
                    max_width=800,
                    quality=60
                )
            return base64.b64encode(processed).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            raise

    def _prepare_prompt(self, screen_size: Dict[str, int]) -> str:
        """Prepare analysis prompt."""
        return f"""Analyze this screen capture and provide:
1. Main content summary (1-2 sentences)
2. Key UI elements (max 5)
3. Important text (max 3)
4. Next actions (max 2)

Screen size: {screen_size.get('width', 0)}x{screen_size.get('height', 0)}

Format as JSON:
{{
    "summary": "Brief summary",
    "ui_elements": ["max 5 elements"],
    "important_text": ["max 3 items"],
    "suggested_actions": ["max 2 actions"],
    "primary_activity": "Main activity or context",
    "confidence": 0.0-1.0
}}"""

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for the LLM analyzer."""
        return {
            'model_name': 'llava:latest',
            'base_url': 'http://localhost:11434',
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 5,
            'thread_workers': 4,
            'process_workers': 2,
            'cache_size': 100,
            'cache_ttl': 300,
            'disk_cache_enabled': True,
            'disk_cache_dir': '.llava_cache',
            'max_queue_size': 10,
            'max_concurrent_requests': 2,
            'min_request_interval': 0.5,
            'temperature': 0.2,
            'top_p': 0.9,
            'top_k': 40,
            'num_gpu': 1,
            'num_thread': 4,
            'repeat_last_n': 64,
            'max_tokens': 512,
            'analysis_prompt': """
            Analyze this screenshot and provide:
            1. Main content summary (1-2 sentences)
            2. Key UI elements (max 5)
            3. Important text (max 3)
            4. Next actions (max 2)
            
            Format as JSON:
            {
                "summary": "Brief summary",
                "ui_elements": ["max 5 elements"],
                "important_text": ["max 3 items"],
                "suggested_actions": ["max 2 actions"],
                "primary_activity": "Main activity or context",
                "confidence": 0.0-1.0
            }
            """
        }
    
    def shutdown(self):
        """Shutdown the analyzer and clean up resources."""
        self.running = False
        self.thread_pool.shutdown(wait=False)
        self.process_pool.shutdown(wait=False)
        
        # Cancel request processor task
        if hasattr(self, 'request_processor_task') and self.request_processor_task:
            self.request_processor_task.cancel()
    
    async def _process_request_queue(self):
        """Process the request queue."""
        while self.running:
            try:
                # Get next request from queue
                image_base64, prompt, future, cache_key, timestamp = await self.request_queue.get()
                
                # Process request with throttling and concurrency control
                async with self.request_semaphore:
                    # Enforce minimum time between requests
                    current_time = time.time()
                    time_since_last = current_time - self.last_request_time
                    if time_since_last < self.min_request_interval:
                        await asyncio.sleep(self.min_request_interval - time_since_last)
                    
                    # Send request to LLaVA
                    try:
                        analysis = await self._request_llava_analysis(image_base64, prompt)
                        
                        # Add metadata
                        analysis['timestamp'] = timestamp
                        
                        # Cache the result
                        await self.cache.set_async(cache_key, analysis)
                        
                        # Resolve future with result
                        if not future.done():
                            future.set_result(analysis)
                    except Exception as e:
                        logger.error(f"Error processing request: {e}")
                        if not future.done():
                            future.set_exception(e)
                
                # Mark task as done
                self.request_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Request processor task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in request processor: {e}")
                # Continue processing queue even if there's an error
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _request_llava_analysis(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """Make the LLaVA analysis request with error handling and retries."""
        async with aiohttp.ClientSession() as session:
            # Update last request time
            self.last_request_time = time.time()
            
            # Create a more robust request with timeout
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": self.model_params
            }
            
            # Include image if not empty
            if image_base64:
                request_data["images"] = [image_base64]
            
            # Log request size for debugging
            request_size = len(json.dumps(request_data))
            logger.debug(f"Request size: {request_size / 1024:.2f} KB")
            
            # Use timeout context manager
            try:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=request_data,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"LLaVA request failed with status {response.status}: {error_text}")
                    
                    # Parse response as it comes
                    result = await response.json()
                    return await self._process_response(result)
                    
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error during LLaVA request: {e}")
                raise
            except asyncio.TimeoutError:
                logger.error(f"LLaVA request timed out after {self.timeout} seconds")
                raise
            except Exception as e:
                logger.error(f"Error during LLaVA request: {e}")
                raise
    
    async def _process_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate the LLaVA response."""
        try:
            response_text = result.get('response', '')
            
            # Extract JSON from response (robust parsing)
            try:
                # First attempt: try to parse the full response as JSON
                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                # Second attempt: extract JSON portion
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    try:
                        analysis = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Third attempt: try to repair JSON
                        repaired_json = self._repair_json(json_str)
                        analysis = json.loads(repaired_json)
                else:
                    raise ValueError("No JSON object found in response")
            
            # Validate and ensure required fields
            required_fields = {
                'summary': str,
                'ui_elements': list,
                'important_text': list,
                'suggested_actions': list,
                'primary_activity': str,
                'confidence': float
            }
            
            # Fill in missing fields with defaults
            for field, field_type in required_fields.items():
                if field not in analysis:
                    if field_type == str:
                        analysis[field] = ""
                    elif field_type == list:
                        analysis[field] = []
                    elif field_type == float:
                        analysis[field] = 0.0
                elif not isinstance(analysis[field], field_type):
                    # Convert to the expected type if possible
                    try:
                        if field_type == float and isinstance(analysis[field], (int, str)):
                            analysis[field] = float(analysis[field])
                        elif field_type == list and isinstance(analysis[field], str):
                            analysis[field] = [analysis[field]]
                        elif field_type == str and not isinstance(analysis[field], (list, dict)):
                            analysis[field] = str(analysis[field])
                    except (ValueError, TypeError):
                        # If conversion fails, use default
                        if field_type == str:
                            analysis[field] = ""
                        elif field_type == list:
                            analysis[field] = []
                        elif field_type == float:
                            analysis[field] = 0.0
            
            # Ensure confidence is between 0 and 1
            if 'confidence' in analysis:
                analysis['confidence'] = max(0.0, min(1.0, float(analysis['confidence'])))
            
            # Add processing metadata
            analysis['model'] = self.model_name
            analysis['processing_time'] = result.get('total_duration', 0)
            
            return analysis
                
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            raise ValueError(f"Failed to process response: {e}")
    
    def _repair_json(self, json_str: str) -> str:
        """Attempt to repair malformed JSON."""
        # Common JSON issues that can be fixed
        repairs = [
            (r'(\w+):', r'"\1":'),  # Add quotes to keys without quotes
            (r':\s*([a-zA-Z][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2'),  # Add quotes to string values
            (r',\s*}', r'}'),  # Remove trailing commas
            (r'}\s*{', r'},{'),  # Add comma between objects
            (r'"\s*\n\s*"', r'" "'),  # Fix multiline strings
        ]
        
        result = json_str
        for pattern, replacement in repairs:
            import re
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def _get_default_analysis(self, timestamp=None, screen_size=None, error=None) -> Dict[str, Any]:
        """Return default analysis structure for error cases."""
        return {
            'summary': 'Analysis failed',
            'ui_elements': [],
            'important_text': [],
            'suggested_actions': [],
            'primary_activity': 'Unknown',
            'confidence': 0.0,
            'timestamp': timestamp or time.time(),
            'screen_size': screen_size or {'width': 0, 'height': 0},
            'error': error
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()
    
    async def batch_analyze(self, image_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple images in batch."""
        tasks = [self.analyze(image_data) for image_data in image_list]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Context manager for the analyzer
@contextlib.contextmanager
def analyzer_context(config=None):
    """Context manager for the LocalLLMAnalyzer."""
    analyzer = LocalLLMAnalyzer(config)
    try:
        yield analyzer
    finally:
        analyzer.shutdown()

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_analyzer():
        # Create analyzer with default configuration
        async with analyzer_context() as analyzer:
            # Load a test image
            image_path = "test_screenshot.png"
            if not os.path.exists(image_path):
                print(f"Test image not found: {image_path}")
                return
                
            with open(image_path, "rb") as f:
                image_data = f.read()
                
            # Analyze the image
            result = await analyzer.analyze({
                'image': image_data,
                'timestamp': time.time(),
                'screen_size': {'width': 1920, 'height': 1080}
            })
            
            # Print the result
            print(json.dumps(result, indent=2))
            
            # Print cache stats
            print("\nCache stats:")
            print(json.dumps(analyzer.get_cache_stats(), indent=2))
    
    # Run the test
    asyncio.run(test_analyzer())