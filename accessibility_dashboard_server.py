#!/usr/bin/env python3
"""
Accessibility Dashboard Server

This server provides a web interface for the Accessibility UI Detector
and exposes API endpoints to interact with the detector.
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes
import tempfile

# Import the accessibility detector
from accessibility_ui_detector import AccessibilityAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('dashboard_server')

# Initialize the API
accessibility_api = AccessibilityAPI()

class DashboardRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the accessibility dashboard.
    """
    
    def _set_headers(self, status_code=200, content_type='text/html'):
        """Set response headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _json_response(self, data, status_code=200):
        """Send a JSON response."""
        self._set_headers(status_code, 'application/json')
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        try:
            # API endpoints
            if path == '/api/accessibility/scan':
                # Trigger a new scan
                result = accessibility_api.detect_ui_elements()
                self._json_response(result)
                return
            
            elif path == '/api/accessibility/latest':
                # Get the latest scan results
                result = accessibility_api.get_latest_scan()
                self._json_response(result)
                return
            
            elif path == '/api/accessibility/accuracy':
                # Calculate accuracy
                query = parse_qs(parsed_path.query)
                ground_truth_file = query.get('ground_truth', [None])[0]
                result = accessibility_api.calculate_accuracy(ground_truth_file)
                self._json_response(result)
                return
            
            # Serve static files
            if path == '/':
                path = '/accessibility_dashboard.html'
            
            file_path = os.path.join(os.getcwd(), path.lstrip('/'))
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # Determine content type
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                # Serve the file
                with open(file_path, 'rb') as file:
                    self._set_headers(200, content_type)
                    self.wfile.write(file.read())
            else:
                # File not found
                self._set_headers(404)
                self.wfile.write(b'404 - File not found')
                
        except Exception as e:
            logger.error(f"Error handling GET request: {str(e)}")
            self._set_headers(500)
            self.wfile.write(str(e).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            if self.path == '/api/save-ground-truth':
                # Get request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # Parse JSON data
                ground_truth = json.loads(post_data)
                
                # Save to a temporary file
                fd, temp_path = tempfile.mkstemp(prefix='ground_truth_', suffix='.json')
                with os.fdopen(fd, 'w') as f:
                    json.dump(ground_truth, f, indent=2)
                
                # Return the path to the temporary file
                self._json_response({
                    'success': True,
                    'file_path': temp_path
                })
                
            else:
                self._set_headers(404)
                self.wfile.write(b'404 - Endpoint not found')
                
        except Exception as e:
            logger.error(f"Error handling POST request: {str(e)}")
            self._set_headers(500)
            self.wfile.write(str(e).encode())

def run_server(host='localhost', port=8080):
    """Run the dashboard server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    logger.info(f"Starting dashboard server at http://{host}:{port}")
    print(f"Accessibility Dashboard is running at http://{host}:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()