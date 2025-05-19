#!/usr/bin/env python3
"""
Integrated Demo of Local Assistant
Combines sensors, LLM, and overlay in a single application
"""
import os
import asyncio
import logging
import json
import time
import sys
import threading
import http.server
import socketserver
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Dynamically add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
try:
    from agent.overlay_bridge import OverlayBridge
    # Mock classes for testing when real ones aren't available
    try:
        from llm.model import LocalLLM
    except ImportError:
        logger.warning("LLM module not available, using mock")
        class LocalLLM:
            def __init__(self, *args, **kwargs):
                self.logger = logger
            
            async def generate_response(self, messages):
                return f"This is a mock response to: {messages[-1]['content']}"
            
            async def start(self):
                return True
    
    try:
        from sensors.screen_sensor import ScreenSensor
        from sensors.process_sensor import ProcessSensor
    except ImportError:
        logger.warning("Sensor modules not available, using mocks")
        class ScreenSensor:
            def __init__(self, *args, **kwargs):
                self.latest_text = "Mock screen text"
            
            def start(self):
                return True
                
        class ProcessSensor:
            def __init__(self, *args, **kwargs):
                self.active_app = "Mock App"
                self.active_window_title = "Mock Window"
            
            def start(self):
                return True
                
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP server for serving overlay files"""
    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fix-overlay')
        super().__init__(*args, directory=directory, **kwargs)
        
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

class IntegratedDemo:
    """Integrated demo that combines all components"""
    def __init__(self):
        self.overlay_bridge = OverlayBridge(port=8765)
        self.llm = LocalLLM(model_name="ollam3.2:latest")
        self.sensors = {
            'screen': ScreenSensor(),
            'process': ProcessSensor()
        }
        self.web_server = None
        self.web_server_thread = None
        self.bridge_thread = None
        self.running = False
        
    async def start(self):
        """Start all components"""
        try:
            logger.info("Starting integrated demo...")
            
            # Start LLM
            logger.info("Starting LLM...")
            await self.llm.start()
            
            # Start sensors
            logger.info("Starting sensors...")
            for name, sensor in self.sensors.items():
                sensor.start()
                logger.info(f"Started {name} sensor")
            
            # Start overlay bridge
            logger.info("Starting overlay bridge...")
            self.bridge_thread = self.overlay_bridge.start()
            
            # Register message handlers
            self.overlay_bridge.register_callback('user_interaction', self.handle_user_interaction)
            self.overlay_bridge.register_callback('transform_request', self.handle_transform_request)
            
            # Start web server in another thread
            logger.info("Starting web server...")
            self.web_server_thread = threading.Thread(
                target=self.run_web_server,
                daemon=True
            )
            self.web_server_thread.start()
            
            self.running = True
            logger.info("Integrated demo started!")
            
            # Keep the main thread alive
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting integrated demo: {e}")
            self.stop()
            
    def run_web_server(self):
        """Run the web server for the overlay"""
        try:
            # Determine the directory where our overlay HTML is located
            directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fix-overlay')
            
            # Create a custom handler that serves from that directory
            handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(
                *args, directory=directory, **kwargs
            )
            
            # Start the server
            with socketserver.TCPServer(("", 8080), handler) as httpd:
                logger.info("Web server running at http://localhost:8080")
                httpd.serve_forever()
        except Exception as e:
            logger.error(f"Error running web server: {e}")
            
    def stop(self):
        """Stop all components"""
        logger.info("Stopping integrated demo...")
        self.running = False
        
    async def handle_user_interaction(self, data):
        """Handle user interaction from overlay"""
        try:
            if data.get('type') == 'query':
                query = data.get('query', '')
                logger.info(f"Received query: {query}")
                
                # Get context
                context = {
                    'screen_text': self.sensors['screen'].latest_text if hasattr(self.sensors['screen'], 'latest_text') else "No screen data",
                    'active_app': self.sensors['process'].active_app if hasattr(self.sensors['process'], 'active_app') else "Unknown app",
                    'active_window': self.sensors['process'].active_window_title if hasattr(self.sensors['process'], 'active_window_title') else "Unknown window"
                }
                
                # Prepare messages for LLM
                messages = [
                    {"role": "system", "content": f"""You are a helpful AI assistant with context awareness.
                    
Current user context:
- Active application: {context['active_app']}
- Window title: {context['active_window']}
- Screen contains information about: {context['screen_text'][:100]}...

Provide helpful responses based on this context. If the user is looking at an application,
you can suggest actions or provide information about it. Be concise and helpful."""},
                    {"role": "user", "content": query}
                ]
                
                # Generate response
                response = await self.llm.generate_response(messages)
                
                # Send response back to overlay
                await self.overlay_bridge.send_message('query_response', {
                    'query': query,
                    'response': response,
                    'context': context
                })
                
                logger.info(f"Sent response for query: {query}")
                
        except Exception as e:
            logger.error(f"Error handling user interaction: {e}")
            await self.overlay_bridge.send_message('query_response', {
                'query': data.get('query', ''),
                'response': f"Error processing your request: {str(e)}",
                'error': True
            })
            
    async def handle_transform_request(self, data):
        """Handle transform request from overlay"""
        try:
            logger.info(f"Received transform request: {data}")
            
            # Get information about active application
            active_app = self.sensors['process'].active_app if hasattr(self.sensors['process'], 'active_app') else "Unknown"
            window_title = self.sensors['process'].active_window_title if hasattr(self.sensors['process'], 'active_window_title') else "Unknown"
            screen_text = self.sensors['screen'].latest_text if hasattr(self.sensors['screen'], 'latest_text') else "No screen data available"
            
            # Generate a mock transformation (in a real system, this would be processed by the LLM)
            transformation = {
                "layout": {
                    "elements": [
                        {
                            "id": "header",
                            "type": "rectangle",
                            "bounds": {"x": 0, "y": 0, "width": 800, "height": 60},
                            "style": {
                                "backgroundColor": "rgba(33, 150, 243, 0.8)",
                                "color": "#fff"
                            }
                        },
                        {
                            "id": "title",
                            "type": "text",
                            "bounds": {"x": 20, "y": 20, "width": 400, "height": 30},
                            "content": f"Simplified {active_app}",
                            "style": {
                                "color": "#fff",
                                "font": "bold 18px sans-serif"
                            }
                        },
                        {
                            "id": "main_action",
                            "type": "button",
                            "bounds": {"x": 20, "y": 80, "width": 200, "height": 40},
                            "content": "Main Action",
                            "style": {
                                "backgroundColor": "rgba(76, 175, 80, 0.9)",
                                "color": "#fff",
                                "borderRadius": "4px"
                            }
                        }
                    ]
                },
                "interactionMap": {
                    "main_action": {
                        "action": "click",
                        "target": "primary_button"
                    }
                },
                "metadata": {
                    "purpose": f"Simplify {active_app} interface",
                    "originalElements": 15,
                    "transformedElements": 3
                }
            }
            
            # Send the transformation to the overlay
            await self.overlay_bridge.send_message('transform-interface', {
                'layout': transformation['layout'],
                'interactionMap': transformation['interactionMap'],
                'metadata': transformation['metadata'],
                'screen_data': {
                    'text': screen_text[:1000] + "..." if len(screen_text) > 1000 else screen_text,
                    'active_app': active_app,
                    'window_title': window_title
                },
                'timestamp': time.time()
            })
            
            logger.info(f"Sent transformation for {active_app}")
            
        except Exception as e:
            logger.error(f"Error handling transform request: {e}")
            await self.overlay_bridge.send_message('transform-error', {
                'error': 'Internal error',
                'message': str(e)
            })

def main():
    """Main entry point"""
    demo = IntegratedDemo()
    
    try:
        # Run the demo in the event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(demo.start())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        demo.stop()
        logger.info("Demo stopped")

if __name__ == "__main__":
    main()