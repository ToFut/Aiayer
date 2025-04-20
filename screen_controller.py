"""Screen controller for LLaVA-based analysis"""

import asyncio
import logging
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime
import time
import json
import os

# Import our components
from sensors.screen_sensor import ScreenSensor
from sensors.llm_analyzer import LocalLLMAnalyzer

logger = logging.getLogger(__name__)

class ScreenController:
    """Controller for managing screen capture and LLaVA analysis."""
    
    def __init__(self, screen_sensor: Optional[ScreenSensor] = None, 
                 llm_analyzer: Optional[LocalLLMAnalyzer] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the screen controller with optional existing components."""
        self.config = config or self._default_config()
        
        # Use provided components or create new ones
        self.sensor = screen_sensor or ScreenSensor(self.config.get('sensor_config', {}))
        self.analyzer = llm_analyzer or LocalLLMAnalyzer(self.config.get('analyzer_config', {}))
        
        self.event_handlers = {
            'screen_capture': [],
            'llm_analysis': [],
            'error': []
        }
        self.is_running = False
        self.monitor_task = None
        self.last_analysis_time = 0
        self.min_analysis_interval = self.config.get('min_analysis_interval', 1.0)
        logger.info("Screen controller initialized")
        
        # Get capture interval
        self.capture_interval = self.config.get('capture_interval', 2.0)
        
        # Analysis results storage
        self.analyses = []
        self.max_stored_analyses = self.config.get('max_stored_analyses', 100)
        
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'sensor_config': {
                'min_interval': 0.5,
                'optimization_level': 2,
                'max_width': 1920,
                'jpeg_quality': 60
            },
            'analyzer_config': {
                'model_name': 'llava:latest',
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 5,
                'cache_size': 100,
                'cache_ttl': 300,
                'disk_cache_enabled': True,
                'disk_cache_dir': '.llava_cache',
                'thread_workers': 4,
                'process_workers': 2,
                'max_queue_size': 10,
                'max_concurrent_requests': 2,
                'min_request_interval': 0.5
            },
            'capture_interval': 2.0,
            'min_analysis_interval': 1.0,
            'max_stored_analyses': 100,
            'output_dir': 'output'
        }
        
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Added handler for event type: {event_type}")
        
    async def _trigger_event(self, event_type: str, data: Any) -> None:
        """Trigger event handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        await asyncio.get_event_loop().run_in_executor(None, handler, data)
                except Exception as e:
                    logger.error(f"Error in {event_type} handler: {e}")
                    await self._trigger_event('error', {
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e),
                        'type': f'handler_error_{event_type}'
                    })
                    
    async def start(self) -> None:
        """Start the controller."""
        if self.is_running:
            return
            
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Screen controller started")
        
    async def stop(self) -> None:
        """Stop the controller."""
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Screen controller stopped")
        
    async def _monitor_loop(self) -> None:
        """Main monitoring loop with rate limiting."""
        while self.is_running:
            try:
                # Capture screen
                screen_data = await self.sensor.capture()
                if screen_data:
                    await self._trigger_event('screen_capture', screen_data)
                    
                    # Check if enough time has passed since last analysis
                    current_time = time.time()
                    time_since_last = current_time - self.last_analysis_time
                    
                    if time_since_last >= self.min_analysis_interval:
                        # Analyze screen content
                        try:
                            analysis = await self.analyzer.analyze({
                                'image': screen_data['image'],
                                'timestamp': screen_data['timestamp'],
                                'screen_size': screen_data['screen_size']
                            })
                            
                            if analysis:
                                self._store_analysis(analysis)
                                await self._trigger_event('llm_analysis', analysis)
                                self.last_analysis_time = current_time
                                
                        except Exception as e:
                            logger.error(f"Analysis failed: {e}")
                            await self._trigger_event('error', {
                                'timestamp': datetime.now().isoformat(),
                                'error': str(e),
                                'type': 'analysis_error'
                            })
                
                # Wait for next capture
                await asyncio.sleep(self.capture_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await self._trigger_event('error', {
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'type': 'monitor_error'
                })
                await asyncio.sleep(1)  # Prevent tight error loop
                
    def _store_analysis(self, analysis: Dict[str, Any]) -> None:
        """Store analysis results."""
        self.analyses.append(analysis)
        
        # Keep only the most recent analyses
        if len(self.analyses) > self.max_stored_analyses:
            self.analyses = self.analyses[-self.max_stored_analyses:]
            
    def get_status(self) -> Dict[str, Any]:
        """Get current controller status."""
        return {
            'running': self.is_running,
            'analyses_count': len(self.analyses),
            'last_analysis_time': self.last_analysis_time,
            'cache_stats': self.analyzer.get_cache_stats()
        }
        
    def save_results(self, filename: str = None) -> str:
        """Save analysis results to file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analysis_{timestamp}.json"
            
        output_dir = self.config.get('output_dir', 'output')
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'analyses': self.analyses,
                'config': self.config
            }, f, indent=2)
            
        return filepath
        
    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the most recent analysis."""
        return self.analyses[-1] if self.analyses else None

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def screen_change_handler(data):
        print(f"Screen changed at {datetime.fromtimestamp(data['timestamp']).strftime('%H:%M:%S')}")
        print(f"Screen size: {data['screen_size']['width']}x{data['screen_size']['height']}")
    
    async def llm_analysis_handler(analysis):
        print("\nLLM Analysis Results:")
        print(f"Summary: {analysis.get('summary', 'No summary available')}")
        print("UI Elements:")
        for element in analysis.get('ui_elements', []):
            print(f"- {element}")
        print("Important Text:")
        for text in analysis.get('important_text', []):
            print(f"- {text}")
        print("Suggested Actions:")
        for action in analysis.get('suggested_actions', []):
            print(f"- {action}")
    
    async def error_handler(error):
        print(f"Error occurred: {error['message']}")
    
    async def main():
        # Create and configure the controller
        controller = ScreenController()
        
        # Register event handlers
        controller.add_event_handler('screen_capture', screen_change_handler)
        controller.add_event_handler('llm_analysis', llm_analysis_handler)
        controller.add_event_handler('error', error_handler)
        
        # Start the controller
        await controller.start()
        
        try:
            # Run for 30 seconds
            print("Running screen analysis for 30 seconds...")
            await asyncio.sleep(30)
            
            # Stop the controller
            await controller.stop()
            
            # Save the results
            filepath = controller.save_results()
            if filepath:
                print(f"Analysis results saved to {filepath}")
            
        except KeyboardInterrupt:
            # Stop the controller on Ctrl+C
            await controller.stop()
            print("Screen analysis stopped by user")
    