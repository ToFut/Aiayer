#!/usr/bin/env python3
"""
Enhanced App Detection Module
Detects and analyzes applications using LLaVA for visual understanding.
"""
import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional
from PIL import Image

# Configure logging
os.makedirs('logs/app_detection', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app_detection/app_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('app_detection')

def main():
    parser = argparse.ArgumentParser(description='Enhanced App Detection')
    parser.add_argument('--llava-url', default='http://localhost:11434', help='LLaVA service URL')
    parser.add_argument('--save-dir', default='results', help='Directory to save results')
    parser.add_argument('image_path', nargs='?', default='sample.png', help='Path to image for analysis')
    
    args = parser.parse_args()
    
    # Create save directory if it doesn't exist
    os.makedirs(args.save_dir, exist_ok=True)
    
    # Check if image exists, if not create a sample
    if not os.path.exists(args.image_path):
        logger.info(f"Creating sample image at {args.image_path}")
        Image.new('RGB', (100, 100), color='white').save(args.image_path)
    
    # Initialize app detection
    from llava_visual_processor import LLaVAVisualProcessor
    processor = LLaVAVisualProcessor(args.llava_url)
    
    # Process image
    try:
        image = Image.open(args.image_path)
        result = processor.analyze_screen(image)
        logger.info(f"Analysis result: {result}")
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()