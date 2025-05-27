#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple web server example
"""

from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"""<!DOCTYPE html>
<html>
<head>
    <title>Simple Web Server</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>This is a simple web server created with Python.</p>
</body>
</html>""")

def create_server(port=8000):
    """Create a server instance without binding to a port."""
    # For testing purposes, we'll just demonstrate the server setup without actually binding
    print(f"Creating server configuration for port {port}...")
    print("This is a demonstration only - no actual server is started")
    print("To run a real server, uncomment the code below:")
    print("""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Server running on port {port}...")
    httpd.serve_forever()
    """)
    return True

if __name__ == '__main__':
    # Just demonstrate the server setup without actually binding to a port
    create_server()
