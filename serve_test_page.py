#!/usr/bin/env python3
"""
Simple HTTP server to serve test notification pages
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time

# Set up the server
PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """A quieter HTTP handler that doesn't log every request"""
    def log_message(self, format, *args):
        # Only log errors, not regular requests
        if args and args[1] >= 400:
            super().log_message(format, *args)

def open_browser():
    """Open the browser after a short delay"""
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}/test_overlay_notification.html')

# Create and start the server
with socketserver.TCPServer(("127.0.0.1", PORT), QuietHTTPHandler) as httpd:
    print(f"Serving test page at http://localhost:{PORT}/test_overlay_notification.html")
    
    # Open browser in a separate thread
    threading.Thread(target=open_browser).start()
    
    try:
        # Serve until interrupted
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")