#!/usr/bin/env python3
"""
Local AI Assistant - Main Entry Point
Simple version for testing
"""
import os
import logging
from flask import Flask, jsonify, render_template
from flask_cors import CORS

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

@app.route('/')
def index():
    """Render the main page."""
    return "Welcome to Local AI Assistant!"

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
        'version': '0.1.0'
    })

@app.route('/test')
def test():
    return "Test route is working!"

if __name__ == "__main__":
    logger.info("Starting application...")
    app.run(host='127.0.0.1', port=5001, debug=True)