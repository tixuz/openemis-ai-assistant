#!/usr/bin/env python3
"""
Mock LLM Server - Returns instant hardcoded responses for testing
Run this instead of the slow llama-server for development/testing
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Mock responses for different tasks
MOCK_RESPONSES = {
    "navigate": {
        "commands": [
            {"type": "navigate", "url": "https://demo.openemis.org/core"}
        ]
    },
    "login": {
        "commands": [
            {"type": "navigate", "url": "https://demo.openemis.org/core"},
            {"type": "fill", "selector": "#username", "value": "admin"},
            {"type": "fill", "selector": "#password", "value": "demo"},
            {"type": "click", "selector": "button[type='submit']"},
            {"type": "wait_for_navigation", "timeout": 5000}
        ]
    },
    "default": {
        "commands": [
            {"type": "navigate", "url": "https://demo.openemis.org/core"}
        ]
    }
}

class MockLLMHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/v1/chat/completions':
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)

            user_message = data.get('messages', [{}])[-1].get('content', '').lower()

            # Determine which mock response to return
            if 'login' in user_message or 'password' in user_message:
                response_data = MOCK_RESPONSES['login']
            elif 'navigate' in user_message or 'open' in user_message or 'go to' in user_message:
                response_data = MOCK_RESPONSES['navigate']
            else:
                response_data = MOCK_RESPONSES['default']

            # Return OpenAI-compatible format
            response = {
                "id": "mock-1",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "mock-llm",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(response_data)
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/v1/models':
            response = {
                "data": [{"id": "mock-llm", "object": "model"}],
                "object": "list"
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/health':
            response = {"status": "ok"}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), MockLLMHandler)
    print("🚀 Mock LLM Server running on http://localhost:8080")
    print("   Returns INSTANT responses for testing!")
    print("   Press Ctrl+C to stop")
    server.serve_forever()
