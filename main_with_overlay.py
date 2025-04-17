#!/usr/bin/env python3
"""
Local AI Assistant - Main Entry Point with Overlay Support
"""
import os
import logging
import threading
import asyncio
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from agent.overlay_bridge import OverlayBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app 
app = Flask(__name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'ui', 'static'),
    static_url_path='/static',
    template_folder=os.path.join(os.path.dirname(__file__), 'ui', 'templates')
)
CORS(app)

# Initialize the overlay bridge
overlay_bridge = OverlayBridge(port=8765)
bridge_thread = None

@app.route('/')
def index():
    """Render the main page."""
    return "Welcome to Local AI Assistant with Overlay Support!"

@app.route('/chat')
def chat():
    """Render the chat interface."""
    try:
        logger.info("Rendering chat page")
        return render_template('chat.html', 
                             conversation=[],
                             version={"assistant": "Local AI Assistant v0.1.0"})
    except Exception as e:
        logger.error(f"Error rendering chat: {str(e)}")
        return "Error loading chat interface", 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '0.1.0',
        'overlay_connected': len(overlay_bridge.clients) > 0
    })

@app.route('/overlay/status')
def overlay_status():
    """Check overlay status"""
    return jsonify({
        'active': True,
        'clients': len(overlay_bridge.clients),
        'server_running': overlay_bridge.server is not None
    })

@app.route('/test')
def test():
    return "Test route is working!"

if __name__ == "__main__":
    logger.info("Starting application with overlay support...")
    
    # Start the overlay bridge in a background thread
    bridge_thread = overlay_bridge.start()
    logger.info(f"Overlay bridge started on port {overlay_bridge.port}")
    
    # Start the Flask application
    app.run(host='127.0.0.1', port=5002, debug=True)
