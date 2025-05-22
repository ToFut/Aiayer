#!/usr/bin/env python3
"""
Enhanced Perception System Runner
Runs the improved application detection with fast native window detection for all types of apps.
"""
import os
import sys
import time
import asyncio
import logging
import json
import argparse
from datetime import datetime

# Configure logging
os.makedirs('logs/perception', exist_ok=True)
os.makedirs('logs/sensors/screen_sensor', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/perception/perception.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("perception_system")

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import our fast detector first
try:
    from fast_app_detection import FastAppDetector
    has_fast_detector = True
    logger.info("Fast application detector available - will use for quick recognition")
except ImportError:
    has_fast_detector = False
    logger.info("Fast detector not available - will fallback to LLaVA")

# Import screen sensor and original app detection
try:
    from sensors.fixed_screen_sensor import FixedScreenSensor
    has_screen_sensor = True
except ImportError:
    has_screen_sensor = False
    logger.warning("Screen sensor not available - perception will be limited")

# Try to import unified detector
try:
    from unified_app_detection import UnifiedAppDetectionSystem, ApplicationContext
    has_unified_detector = True
    logger.info("Unified application detector available")
except ImportError:
    has_unified_detector = False
    logger.info("Unified application detector not available")

class EnhancedPerceptionSystem:
    """
    Enhanced perception system that combines multiple detection methods
    to recognize any application the user is interacting with.
    """
    
    def __init__(self, args):
        self.args = args
        self.screen_sensor = None
        self.fast_detector = None
        self.unified_detector = None
        self.running = False
        self.detection_log = []
        self.detected_applications = set()
        
        # Detection settings
        self.use_fast = args.fast
        self.use_llava = not args.no_llava
        self.use_screen_sensor = not args.no_screen
        self.llava_url = args.llava_url
        self.interval = args.interval
        
        # Make cache and results directories
        os.makedirs('cache/screen_sensor', exist_ok=True)
        os.makedirs('logs/perception', exist_ok=True)
        os.makedirs('results/app_detection', exist_ok=True)
        
        logger.info("Enhanced perception system initialized with settings:")
        logger.info(f"  Fast detection: {self.use_fast}")
        logger.info(f"  LLaVA detection: {self.use_llava}")
        logger.info(f"  Screen sensor: {self.use_screen_sensor}")
        logger.info(f"  LLaVA URL: {self.llava_url}")
        logger.info(f"  Detection interval: {self.interval}s")
    
    async def initialize(self):
        """Initialize detection components."""
        success = True
        
        # Initialize fast detector
        if has_fast_detector and self.use_fast:
            logger.info("Initializing fast application detector...")
            try:
                self.fast_detector = FastAppDetector()
                self.fast_detector.detection_interval = self.interval
                logger.info("Fast application detector initialized")
            except Exception as e:
                logger.error(f"Error initializing fast detector: {e}")
                success = False
        
        # Initialize unified detector
        if has_unified_detector and self.use_llava:
            logger.info(f"Initializing unified application detector with LLaVA at {self.llava_url}...")
            try:
                self.unified_detector = UnifiedAppDetectionSystem(llava_url=self.llava_url)
                self.unified_detector.detection_interval = self.interval
                logger.info("Unified application detector initialized")
            except Exception as e:
                logger.error(f"Error initializing unified detector: {e}")
                success = False
        
        # Initialize screen sensor
        if has_screen_sensor and self.use_screen_sensor:
            logger.info("Initializing enhanced screen sensor...")
            try:
                self.screen_sensor = FixedScreenSensor(llava_url=self.llava_url)
                sensor_initialized = await self.screen_sensor.initialize()
                if sensor_initialized:
                    logger.info("Enhanced screen sensor initialized")
                else:
                    logger.error("Screen sensor initialization failed")
                    success = False
            except Exception as e:
                logger.error(f"Error initializing screen sensor: {e}")
                success = False
        
        return success
    
    async def start(self):
        """Start all detection systems."""
        logger.info("Starting enhanced perception system...")
        
        # Start fast detector
        if self.fast_detector:
            logger.info("Starting fast application detector")
            self.fast_detector.start()
        
        # Start unified detector
        if self.unified_detector:
            logger.info("Starting unified application detector")
            self.unified_detector.start()
        
        self.running = True
        logger.info("Enhanced perception system started")
    
    async def run(self):
        """Run the perception system with all available detection methods."""
        # Start all components
        await self.start()
        
        try:
            while self.running:
                try:
                    # Log current application using the best available detector
                    detection_info = await self._get_current_application()
                    
                    if detection_info and detection_info.get('application'):
                        # Check if this is a new detection
                        app_name = detection_info['application']
                        view_name = detection_info.get('view', '')
                        detection_key = f"{app_name}:{view_name}"
                        is_new_detection = detection_key not in self.detected_applications
                        
                        if is_new_detection:
                            self.detected_applications.add(detection_key)
                            logger.info(f"NEW APPLICATION DETECTED: {app_name}")
                            logger.info(f"DETAILS: {json.dumps(detection_info, indent=2)}")
                        
                        # Store detection data
                        self.detection_log.append(detection_info)
                        # Keep only last 20 entries
                        self.detection_log = self.detection_log[-20:]
                        
                        # Save latest detection for easy verification
                        with open('logs/perception/latest_detection.json', 'w') as f:
                            json.dump(detection_info, f, indent=2)
                        
                        # Save full detection log
                        with open('logs/perception/detection_log.json', 'w') as f:
                            json.dump(self.detection_log, f, indent=2)
                    
                    # Wait for next detection
                    logger.info("Waiting for next detection...")
                    await asyncio.sleep(self.interval)
                    
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            logger.info("Perception system task cancelled")
        finally:
            await self.stop()
    
    async def _get_current_application(self):
        """Get current application info using all available detectors."""
        current_time = datetime.now().isoformat()
        detection_info = {
            'timestamp': current_time,
            'sources_used': []
        }
        
        # Try fast detector first (fastest, but less detail)
        if self.fast_detector:
            try:
                fast_result = self.fast_detector.get_current_detection()
                if fast_result and fast_result.app_name != "Unknown":
                    detection_info['application'] = fast_result.app_name
                    detection_info['view'] = fast_result.view_name
                    detection_info['category'] = fast_result.category
                    detection_info['window_title'] = fast_result.window_title
                    detection_info['confidence'] = fast_result.confidence
                    detection_info['sources_used'].append('fast_detector')
                    detection_info['detection_time'] = fast_result.timestamp if hasattr(fast_result, 'timestamp') else time.time()
            except Exception as e:
                logger.error(f"Error getting fast detection: {e}")
        
        # Try unified detector (good balance of speed and detail)
        if self.unified_detector and (not detection_info.get('application') or detection_info.get('confidence', 0) < 0.7):
            try:
                context = self.unified_detector.get_current_application_context()
                if context and context.app_name != "Unknown":
                    detection_info['application'] = context.app_name
                    detection_info['category'] = context.app_category
                    detection_info['view'] = context.view_name
                    detection_info['workflow'] = context.workflow
                    detection_info['confidence'] = context.confidence
                    detection_info['ui_elements'] = [asdict(elem) for elem in context.ui_elements] if hasattr(context, 'ui_elements') else []
                    detection_info['sources_used'].append('unified_detector')
            except Exception as e:
                logger.error(f"Error getting unified detection: {e}")
        
        # Try screen sensor with LLaVA as last resort (slowest but most detailed)
        if self.screen_sensor and self.use_llava and (not detection_info.get('application') or detection_info.get('confidence', 0) < 0.6):
            try:
                state = await self.screen_sensor.get_current_state()
                if state and 'application' in state:
                    app_data = state['application']
                    app_name = app_data.get('name', 'Unknown')
                    
                    if app_name != "Unknown":
                        detection_info['application'] = app_name
                        detection_info['view'] = app_data.get('view', '')
                        detection_info['workflow'] = app_data.get('workflow_stage', '')
                        detection_info['elements_detected'] = len(state.get('screen_elements', []))
                        detection_info['is_significant'] = state.get('is_significant_action', False)
                        detection_info['sources_used'].append('screen_sensor')
                        
                        # Add email or form data if present
                        if 'email_data' in state:
                            detection_info['email_data'] = state['email_data']
                        if 'form_data' in state:
                            detection_info['form_data'] = state['form_data']
            except Exception as e:
                logger.error(f"Error getting screen state: {e}")
        
        return detection_info
    
    async def stop(self):
        """Stop all detection systems."""
        self.running = False
        
        # Stop all detectors
        if self.fast_detector:
            try:
                logger.info("Stopping fast detector")
                self.fast_detector.stop()
            except Exception as e:
                logger.error(f"Error stopping fast detector: {e}")
        
        if self.unified_detector:
            try:
                logger.info("Stopping unified detector")
                self.unified_detector.stop()
            except Exception as e:
                logger.error(f"Error stopping unified detector: {e}")
        
        if self.screen_sensor:
            try:
                logger.info("Stopping screen sensor")
                await self.screen_sensor.cleanup()
            except Exception as e:
                logger.error(f"Error stopping screen sensor: {e}")
        
        logger.info("Enhanced perception system stopped")

async def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Enhanced Perception System")
    parser.add_argument("--fast", action="store_true", help="Use fast detector (default if available)")
    parser.add_argument("--no-llava", action="store_true", help="Disable LLaVA detection")
    parser.add_argument("--no-screen", action="store_true", help="Disable screen sensor")
    parser.add_argument("--interval", type=float, default=5.0, help="Detection interval in seconds (default: 5.0)")
    parser.add_argument("--llava-url", default="http://localhost:11434", help="LLaVA URL (default: http://localhost:11434)")
    parser.add_argument("--duration", type=int, help="Run duration in seconds (default: run until interrupted)")
    args = parser.parse_args()
    
    # Create and initialize perception system
    perception_system = EnhancedPerceptionSystem(args)
    
    if not await perception_system.initialize():
        logger.error("Failed to initialize perception system")
        return
    
    try:
        logger.info("Running enhanced perception system...")
        logger.info("INSTRUCTIONS:")
        logger.info("1. Open any application in your system (browser, editor, email client, etc.)")
        logger.info("2. Wait for a few seconds for the system to detect the application")
        logger.info("3. Check logs/perception/latest_detection.json for latest results")
        logger.info("4. Check logs/perception/detection_log.json for all detections")
        
        # Start the perception system
        start_time = time.time()
        
        # Run the perception system
        if args.duration:
            logger.info(f"Running for {args.duration} seconds")
            
            # Start the system
            await perception_system.start()
            
            # Wait for specified duration
            try:
                while time.time() - start_time < args.duration:
                    # Check current application periodically
                    if int(time.time() - start_time) % args.interval == 0:
                        detection_info = await perception_system._get_current_application()
                        if detection_info and detection_info.get('application'):
                            print(f"Current app: {detection_info['application']} - {detection_info.get('view', '')}")
                    await asyncio.sleep(1)
            finally:
                await perception_system.stop()
        else:
            # Run until interrupted
            await perception_system.run()
    except KeyboardInterrupt:
        logger.info("Perception system stopped by user")
    finally:
        # Clean up resources
        await perception_system.stop()
        
if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript terminated by user")
    except Exception as e:
        print(f"Error: {e}")