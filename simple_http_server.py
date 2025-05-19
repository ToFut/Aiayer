#!/usr/bin/env python3
"""
Simple HTTP Server

A minimal HTTP server to serve static files.
"""
import http.server
import socketserver
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/http_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('http_server')

# Create directories
os.makedirs('pids', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Save PID
with open('pids/http_server.pid', 'w') as f:
    f.write(str(os.getpid()))

# Configuration
PORT = 8080
DIRECTORY = "."

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler with logging."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(format % args)
    
    def do_GET(self):
        """Handle GET requests with CORS headers."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        return super().do_GET()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    """Run the HTTP server."""
    try:
        # Create server
        handler = CustomHandler
        httpd = socketserver.TCPServer(("", PORT), handler)
        
        logger.info(f"HTTP server running on port {PORT}")
        logger.info(f"Serving files from directory: {os.path.abspath(DIRECTORY)}")
        
        # Serve forever
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.server_close()
    except Exception as e:
        logger.error(f"Error in HTTP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()