import asyncio
import logging
import os
from datetime import datetime
from screen_controller import ScreenController
from sensors.screen_sensor import ScreenSensor
from sensors.llm_analyzer import LocalLLMAnalyzer
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def screen_capture_handler(data: dict):
    """Handle screen capture events."""
    logger.info("Screen captured:")
    logger.info(f"Timestamp: {data.get('timestamp')}")
    logger.info(f"Screen size: {data.get('screen_size')}")
    logger.info(f"Image size: {len(data.get('image', ''))} bytes")

async def llm_analysis_handler(data: dict):
    """Handle LLM analysis events."""
    try:
        logger.info("\nLLM Analysis Results:")
        logger.info(f"Timestamp: {data.get('timestamp')}")
        logger.info(f"Summary: {data.get('summary', 'No summary')}")
        
        # Log UI Elements
        logger.info("\nUI Elements:")
        for element in data.get('ui_elements', []):
            logger.info(f"- {element}")
        
        # Log Important Text
        logger.info("\nImportant Text:")
        for text in data.get('important_text', []):
            logger.info(f"- {text}")
        
        # Log Suggested Actions
        logger.info("\nSuggested Actions:")
        for action in data.get('suggested_actions', []):
            logger.info(f"- {action}")
        
        # Log Primary Activity and Confidence
        logger.info(f"\nPrimary Activity: {data.get('primary_activity', 'Unknown')}")
        logger.info(f"Confidence: {data.get('confidence', 0.0)}")
        
        # Log processing metadata
        logger.info("\nProcessing Metadata:")
        logger.info(f"Model: {data.get('model', 'Unknown')}")
        logger.info(f"Processing Time: {data.get('processing_time', 0)}ms")
        if 'error' in data:
            logger.warning(f"Error: {data['error']}")
            
    except Exception as e:
        logger.error(f"Error in analysis handler: {e}")
        logger.error(f"Raw data: {data}")

async def main():
    try:
        # Initialize components
        logger.info("Initializing ScreenController...")
        controller = ScreenController()
        
        # Add event handlers
        logger.info("Adding event handlers...")
        controller.add_event_handler("screen_capture", screen_capture_handler)
        controller.add_event_handler("llm_analysis", llm_analysis_handler)
        
        # Start the controller
        logger.info("Starting ScreenController...")
        await controller.start()
        
        # Run for 60 seconds
        logger.info("Running for 60 seconds...")
        await asyncio.sleep(60)
        
        # Stop the controller
        logger.info("Stopping ScreenController...")
        await controller.stop()
        
        # Print cache statistics
        logger.info("\nCache Statistics:")
        stats = controller.analyzer.get_cache_stats()
        logger.info(f"Cache Size: {stats['size']}/{stats['max_size']}")
        logger.info(f"Hit Ratio: {stats['hit_ratio']:.2%}")
        logger.info(f"Total Requests: {stats.get('hit_count', 0) + stats.get('miss_count', 0)}")
        
        # Save results
        output_file = f"output/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("output", exist_ok=True)
        with open(output_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "analyses": controller.analyses,
                "config": controller.config
            }, f, indent=2)
        logger.info(f"\nResults saved to: {output_file}")
        
        logger.info("Test completed")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs(".llava_cache", exist_ok=True)
    
    # Run the test
    asyncio.run(main()) 