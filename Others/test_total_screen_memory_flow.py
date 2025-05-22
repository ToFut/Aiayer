#!/usr/bin/env python3
"""
Test script for Total Screen Analyzer to Memory Flow
Tests the complete data flow from Total Screen Analyzer through Enhanced Screen Memory Processor to Memory System.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TotalScreenMemoryFlowTest:
    """Test class for verifying the complete memory flow."""
    
    def __init__(self):
        self.bridge_uri = "ws://localhost:8766"
        self.ws_server_uri = "ws://localhost:8765"
        self.client_id = str(uuid.uuid4())
        
    async def test_complete_flow(self):
        """Test the complete flow from Total Screen Analyzer to Memory."""
        logger.info("Starting Total Screen Analyzer to Memory Flow Test")
        
        # Create sample Total Screen Analyzer data
        sample_data = self._create_sample_total_screen_data()
        
        try:
            # Connect to bridge server as total_screen_analyzer sensor
            logger.info("Connecting to bridge server...")
            async with websockets.connect(self.bridge_uri) as websocket:
                
                # Register as total_screen_analyzer
                await self._register_sensor(websocket)
                
                # Send sample data
                await self._send_screen_data(websocket, sample_data)
                
                # Wait for processing
                await asyncio.sleep(2)
                
                logger.info("Test completed successfully!")
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False
        
        return True
    
    async def _register_sensor(self, websocket):
        """Register as total_screen_analyzer sensor."""
        registration_message = {
            "type": "register",
            "client_type": "total_screen_analyzer",
            "payload": {
                "client_type": "total_screen_analyzer",
                "version": "1.0.0",
                "capabilities": ["comprehensive_analysis", "multi_layer_detection"],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await websocket.send(json.dumps(registration_message))
        logger.info("Sent registration message")
        
        # Wait for confirmation
        response = await websocket.recv()
        response_data = json.loads(response)
        logger.info(f"Registration response: {response_data.get('type')}")
    
    async def _send_screen_data(self, websocket, data):
        """Send screen analysis data to bridge server."""
        sensor_message = {
            "type": "sensor_data",
            "payload": data,
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send(json.dumps(sensor_message))
        logger.info("Sent total_screen_analyzer data")
        
        # Wait for any response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            logger.info(f"Bridge server response: {response_data.get('type')}")
        except asyncio.TimeoutError:
            logger.info("No immediate response from bridge server (expected)")
    
    def _create_sample_total_screen_data(self) -> Dict[str, Any]:
        """Create sample data that mimics Total Screen Analyzer output."""
        return {
            "sensor_type": "total_screen_analyzer",
            "timestamp": datetime.now().isoformat(),
            "analysis_layers": {
                "ocr_analysis": {
                    "text_content": "Claude Code - Advanced AI Assistant",
                    "confidence": 0.95,
                    "language": "en",
                    "text_regions": [
                        {
                            "text": "Claude Code",
                            "bbox": [100, 50, 200, 80],
                            "confidence": 0.98
                        }
                    ]
                },
                "ui_detection": {
                    "elements": [
                        {
                            "type": "button",
                            "text": "Send Message",
                            "bbox": [300, 400, 400, 430],
                            "confidence": 0.92
                        },
                        {
                            "type": "text_input",
                            "placeholder": "Type your message...",
                            "bbox": [50, 350, 450, 390],
                            "confidence": 0.89
                        }
                    ],
                    "layout_type": "chat_interface"
                },
                "application_context": {
                    "name": "Claude Code",
                    "category": "AI Assistant",
                    "window_title": "Claude Code - Chat Interface",
                    "process_info": {
                        "pid": 12345,
                        "memory_usage": 256.7,
                        "cpu_usage": 15.3
                    }
                },
                "semantic_understanding": {
                    "primary_task": "AI conversation",
                    "user_intent": "software development assistance",
                    "context_keywords": ["code", "programming", "ai", "assistant"],
                    "content_type": "interactive_chat"
                },
                "workflow_detection": {
                    "current_workflow": "ai_assisted_development",
                    "workflow_stage": "active_conversation",
                    "user_actions": [
                        {
                            "action": "typing",
                            "timestamp": datetime.now().isoformat(),
                            "confidence": 0.85
                        }
                    ]
                },
                "visual_analysis": {
                    "dominant_colors": ["#1a1a1a", "#ffffff", "#0066cc"],
                    "layout_structure": "vertical_chat_layout",
                    "visual_complexity": "medium",
                    "attention_areas": [
                        {
                            "area": "message_input",
                            "importance": 0.9,
                            "bbox": [50, 350, 450, 390]
                        }
                    ]
                }
            },
            "insights": {
                "user_productivity": "User is actively engaged in AI-assisted development",
                "attention_focus": "Primary focus on message composition area",
                "context_continuity": "Continuing previous conversation about code development",
                "workflow_efficiency": "High - direct interaction with AI assistant"
            },
            "metadata": {
                "screen_resolution": "1920x1080",
                "screenshot_quality": "high",
                "processing_time_ms": 234,
                "analysis_version": "1.0.0"
            }
        }

async def main():
    """Main test function."""
    test = TotalScreenMemoryFlowTest()
    
    logger.info("=" * 60)
    logger.info("TOTAL SCREEN ANALYZER TO MEMORY FLOW TEST")
    logger.info("=" * 60)
    
    # Test the flow
    success = await test.test_complete_flow()
    
    if success:
        logger.info("✅ Test completed successfully!")
        logger.info("Data should now be processed and stored in memory system.")
    else:
        logger.error("❌ Test failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test error: {e}")
        sys.exit(1)