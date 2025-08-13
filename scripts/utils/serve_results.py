#!/usr/bin/env python3
"""
Simple HTTP server to serve Hendrix pipeline results
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path
import argparse

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Custom handling for root path
        if self.path == '/':
            # List available results
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Hendrix Pipeline Results</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333; }
                    .result-link { 
                        display: block; 
                        padding: 10px; 
                        margin: 5px 0; 
                        background: #f0f0f0; 
                        text-decoration: none; 
                        color: #333;
                        border-radius: 5px;
                    }
                    .result-link:hover { background: #e0e0e0; }
                </style>
            </head>
            <body>
                <h1>Hendrix Pipeline Results</h1>
                <h2>Available Results:</h2>
            """
            
            # Find all comprehensive_captions.html files
            base_dir = Path(self.directory)
            for html_file in base_dir.rglob("comprehensive_captions.html"):
                relative_path = html_file.relative_to(base_dir)
                session_name = html_file.parent.parent.name
                html += f'<a class="result-link" href="/{relative_path}">{session_name}</a>\n'
            
            html += """
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        else:
            super().do_GET()

def main():
    parser = argparse.ArgumentParser(description='Serve Hendrix pipeline results')
    parser.add_argument('--port', type=int, default=3000, help='Port to serve on')
    parser.add_argument('--directory', default='hendrix_output', help='Directory to serve')
    args = parser.parse_args()
    
    # Change to the directory
    os.chdir('/dev-work/hendrix_12aug')
    
    Handler = lambda *args, **kwargs: CustomHTTPRequestHandler(*args, directory=args.directory, **kwargs)
    
    with socketserver.TCPServer(("", args.port), Handler) as httpd:
        print(f"Server running at http://localhost:{args.port}")
        print(f"Serving directory: {os.path.abspath(args.directory)}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    main()