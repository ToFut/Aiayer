#!/usr/bin/env python3
"""
Run Application Detection System

This script runs a standalone application detection system that logs all detected applications
with their views and UI elements to a log file.
"""
import os
import sys
import time
import asyncio
import logging
import json
from datetime import datetime
import argparse

# Add script directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Configure logging
os.makedirs('logs/perception', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/perception/app_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("perception.app_detection")

# Import required modules
try:
    from fast_app_detection import FastAppDetector
    use_fast_detector = True
    logger.info("Using fast application detector")
except ImportError:
    use_fast_detector = False
    logger.info("Fast detector not available, falling back to unified detector")

try:
    from unified_app_detection import UnifiedAppDetectionSystem
    use_unified_detector = True
except ImportError:
    use_unified_detector = False
    logger.error("Unified app detection system not available")
    if not use_fast_detector:
        logger.error("No application detection system available. Exiting.")
        sys.exit(1)

class AppDetectionRunner:
    """Runs continuous application detection and logs results"""
    
    def __init__(self, args):
        self.args = args
        self.output_dir = args.output_dir
        self.interval = args.interval
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize detection system
        if use_fast_detector and args.fast:
            self.detector = FastAppDetector()
            self.detector.detection_interval = self.interval
            self.detector.use_ocr = not args.no_ocr
            self.detector.use_ui_detection = not args.no_ui
            self.detector.use_color_profiles = not args.no_color
            logger.info(f"Initialized fast detector (OCR: {self.detector.use_ocr}, UI: {self.detector.use_ui_detection})")
        elif use_unified_detector:
            self.detector = UnifiedAppDetectionSystem(llava_url=args.llava_url)
            self.detector.detection_interval = self.interval
            logger.info(f"Initialized unified detector with LLaVA URL: {args.llava_url}")
        else:
            logger.error("No compatible detection system available")
            sys.exit(1)
        
        # Setup logging
        self.detection_log = os.path.join(self.output_dir, "detection_log.jsonl")
        logger.info(f"Detection results will be logged to {self.detection_log}")
        
        # Statistics
        self.stats = {
            "start_time": time.time(),
            "detections": 0,
            "unique_apps": set(),
            "unique_views": set(),
            "errors": 0
        }
    
    def start(self):
        """Start the detection system"""
        logger.info(f"Starting application detection with interval {self.interval} seconds")
        self.detector.start()
        
        # Log startup
        with open(self.detection_log, 'a') as f:
            startup_entry = {
                "type": "system",
                "event": "startup",
                "timestamp": time.time(),
                "config": {
                    "interval": self.interval,
                    "detector_type": "fast" if hasattr(self.detector, "use_ocr") else "unified",
                    "ocr_enabled": getattr(self.detector, "use_ocr", "n/a"),
                    "ui_detection_enabled": getattr(self.detector, "use_ui_detection", "n/a"),
                }
            }
            f.write(json.dumps(startup_entry) + "\n")
    
    def stop(self):
        """Stop the detection system"""
        logger.info("Stopping application detection")
        self.detector.stop()
        
        # Log shutdown
        with open(self.detection_log, 'a') as f:
            runtime = time.time() - self.stats["start_time"]
            shutdown_entry = {
                "type": "system",
                "event": "shutdown",
                "timestamp": time.time(),
                "stats": {
                    "runtime": runtime,
                    "detections": self.stats["detections"],
                    "unique_apps": list(self.stats["unique_apps"]),
                    "unique_views": list(self.stats["unique_views"]),
                    "errors": self.stats["errors"],
                    "detections_per_minute": (self.stats["detections"] / runtime) * 60 if runtime > 0 else 0
                }
            }
            f.write(json.dumps(shutdown_entry) + "\n")
        
        # Print summary
        print("\n===== APPLICATION DETECTION SUMMARY =====")
        print(f"Runtime: {runtime:.1f} seconds")
        print(f"Total detections: {self.stats['detections']}")
        print(f"Unique applications: {len(self.stats['unique_apps'])}")
        if self.stats["unique_apps"]:
            for app in sorted(self.stats["unique_apps"]):
                print(f"  - {app}")
        print(f"Detection rate: {(self.stats['detections'] / runtime) * 60:.1f} detections/minute")
        print("===========================================")
    
    async def run(self):
        """Run the detection loop"""
        self.start()
        
        try:
            while True:
                # Get latest detection
                if hasattr(self.detector, "get_current_detection"):
                    # Fast detector
                    detection = self.detector.get_current_detection()
                    if detection:
                        self._log_detection(detection)
                elif hasattr(self.detector, "get_current_application_context"):
                    # Unified detector
                    context = self.detector.get_current_application_context()
                    if context:
                        self._log_context(context)
                
                # Wait for interval
                await asyncio.sleep(self.interval)
                
                # Update UI occasionally
                if self.stats["detections"] % 5 == 0:
                    self._print_status()
                
        except KeyboardInterrupt:
            print("\nDetection interrupted by user")
        except Exception as e:
            logger.error(f"Error in detection loop: {e}")
            self.stats["errors"] += 1
        finally:
            self.stop()
    
    def _log_detection(self, detection):
        """Log a detection from fast detector"""
        if not detection:
            return
            
        # Create log entry
        entry = {
            "type": "detection",
            "timestamp": time.time(),
            "app_name": detection.app_name,
            "view_name": detection.view_name,
            "category": detection.category,
            "window_title": detection.window_title,
            "confidence": detection.confidence,
            "ui_elements_count": len(detection.ui_elements) if hasattr(detection, "ui_elements") else 0
        }
        
        # Write to log
        with open(self.detection_log, 'a') as f:
            f.write(json.dumps(entry) + "\n")
        
        # Update stats
        self.stats["detections"] += 1
        self.stats["unique_apps"].add(detection.app_name)
        if detection.view_name:
            self.stats["unique_views"].add(f"{detection.app_name}:{detection.view_name}")
    
    def _log_context(self, context):
        """Log a context from unified detector"""
        if not context:
            return
            
        # Create log entry
        entry = {
            "type": "context",
            "timestamp": time.time(),
            "app_name": context.app_name,
            "app_category": context.app_category,
            "view_name": context.view_name,
            "workflow": context.workflow,
            "confidence": context.confidence,
            "session_duration": context.session_duration if hasattr(context, "session_duration") else 0,
            "ui_elements_count": len(context.ui_elements) if hasattr(context, "ui_elements") else 0
        }
        
        # Write to log
        with open(self.detection_log, 'a') as f:
            f.write(json.dumps(entry) + "\n")
        
        # Update stats
        self.stats["detections"] += 1
        self.stats["unique_apps"].add(context.app_name)
        if context.view_name:
            self.stats["unique_views"].add(f"{context.app_name}:{context.view_name}")
    
    def _print_status(self):
        """Print current detection status"""
        if hasattr(self.detector, "get_current_detection"):
            # Fast detector
            detection = self.detector.get_current_detection()
            if detection:
                print(f"Current app: {detection.app_name} (view: {detection.view_name}, confidence: {detection.confidence:.2f})")
        elif hasattr(self.detector, "get_current_application_context"):
            # Unified detector
            context = self.detector.get_current_application_context()
            if context:
                print(f"Current app: {context.app_name} (view: {context.view_name}, workflow: {context.workflow})")

async def main():
    parser = argparse.ArgumentParser(description="Run Application Detection System")
    parser.add_argument("--fast", action="store_true", help="Use fast detector (default if available)")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR for faster performance (fast detector only)")
    parser.add_argument("--no-ui", action="store_true", help="Disable UI element detection (fast detector only)")
    parser.add_argument("--no-color", action="store_true", help="Disable color profile analysis (fast detector only)")
    parser.add_argument("--interval", type=float, default=5.0, help="Detection interval in seconds (default: 5.0)")
    parser.add_argument("--llava-url", default="http://localhost:11434", help="LLaVA API URL (unified detector only)")
    parser.add_argument("--output-dir", default="results/app_detection", help="Directory for output files")
    parser.add_argument("--duration", type=int, help="Run duration in seconds (default: run until interrupted)")
    
    args = parser.parse_args()
    
    # Create runner
    runner = AppDetectionRunner(args)
    
    if args.duration:
        # Run for specified duration
        logger.info(f"Running for {args.duration} seconds")
        try:
            runner.start()
            await asyncio.sleep(args.duration)
        finally:
            runner.stop()
    else:
        # Run until interrupted
        await runner.run()

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