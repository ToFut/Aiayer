#!/usr/bin/env python3
"""
Simple HTTP server to serve the memory dashboard
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="web/dashboard/templates", **kwargs)

def run(server_class=HTTPServer, handler_class=DashboardHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting dashboard server on http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run() 