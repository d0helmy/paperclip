#!/usr/bin/env python3
"""
Smart Ollama proxy v2:
- Handles both /api/chat (Ollama native) and /v1/chat/completions (OpenAI-compatible)
- Collects streaming responses (SSE), detecting text-format tool calls
- Converts text-format tool calls to proper tool_calls format
"""
import http.server
import urllib.request
import urllib.error
import json
import re
import threading
import socketserver
import sys

OLLAMA_URL = "http://localhost:11434"
PROXY_PORT = 11435

def fix_json(s):
    """Fix invalid JSON escape sequences like \\$ -> $"""
    valid_escapes = set('"\\bfnrtu/')
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s) and s[i+1] not in valid_escapes:
            result.append(s[i+1])
            i += 2
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)


def extract_tool_call(content):
    """Try to parse content as a tool call JSON. Returns tool_call dict or None."""
    if not content or not content.strip():
        return None
    
    content = content.strip()
    # Remove markdown code blocks if present
    if content.startswith('```'):
        lines = content.split('\n')
        lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        content = '\n'.join(lines).strip()
    
    # Try to parse as standard JSON: {"name": "bash", "parameters": {...}}
    for attempt in [content, fix_json(content)]:
        try:
            data = json.loads(attempt)
            if isinstance(data, dict) and 'name' in data and 'parameters' in data:
                return {
                    "id": "call_proxy_001",
                    "type": "function",
                    "function": {
                        "name": data['name'],
                        "arguments": data['parameters']
                    }
                }
        except (json.JSONDecodeError, KeyError, ValueError):
            pass
    
    # Try to detect OpenCode's text format: {function <nil> {bash command="..." description:"..."}}
    # or function-call style: bash(command="...", description="...")
    # Pattern: {function ... {TOOLNAME command="CMD"...}}
    m = re.match(r'\{function\s+\S+\s+\{(\w+)\s+(.*)\}\}', content, re.DOTALL)
    if m:
        tool_name = m.group(1)
        args_str = m.group(2)
        # Parse key=value or key:"value" pairs
        params = {}
        for kv in re.finditer(r'(\w+)[=:]\s*"((?:[^"\\]|\\.)*)"', args_str):
            params[kv.group(1)] = kv.group(2).replace('\\"', '"')
        if tool_name and params:
            return {
                "id": "call_proxy_001",
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": params
                }
            }
    
    # Try to detect bash(command="...", description="...") style
    # or bash(command="...", description:"...")
    m2 = re.match(r'(\w+)\s*\(\s*(.*)\)\s*$', content, re.DOTALL)
    if m2:
        tool_name = m2.group(1)
        args_str = m2.group(2)
        if tool_name in ('bash', 'shell', 'run'):
            params = {}
            for kv in re.finditer(r'(\w+)\s*[=:]\s*"((?:[^"\\]|\\.)*)"', args_str):
                params[kv.group(1)] = kv.group(2).replace('\\"', '"')
            if params.get('command'):
                return {
                    "id": "call_proxy_001",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": params
                    }
                }
    
    return None


def build_sse_tool_call_response(original_chunk_json, tool_call):
    """Build SSE streaming chunks for a tool_call response."""
    # Parse the first chunk to get id, model, etc.
    base = original_chunk_json.copy()
    
    # Chunk 1: tool call begins (send the function name and start of args)
    tool_args = json.dumps(tool_call['function']['arguments'])
    
    chunks = []
    
    # First chunk: role
    c1 = {
        "id": base.get("id", "chatcmpl-proxy"),
        "object": "chat.completion.chunk",
        "created": base.get("created", 0),
        "model": base.get("model", ""),
        "system_fingerprint": base.get("system_fingerprint", "fp_proxy"),
        "choices": [{
            "index": 0,
            "delta": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "index": 0,
                    "id": tool_call["id"],
                    "type": "function",
                    "function": {
                        "name": tool_call["function"]["name"],
                        "arguments": ""
                    }
                }]
            },
            "finish_reason": None
        }]
    }
    chunks.append(c1)
    
    # Second chunk: arguments
    c2 = {
        "id": base.get("id", "chatcmpl-proxy"),
        "object": "chat.completion.chunk",
        "created": base.get("created", 0),
        "model": base.get("model", ""),
        "system_fingerprint": base.get("system_fingerprint", "fp_proxy"),
        "choices": [{
            "index": 0,
            "delta": {
                "tool_calls": [{
                    "index": 0,
                    "function": {
                        "arguments": tool_args
                    }
                }]
            },
            "finish_reason": None
        }]
    }
    chunks.append(c2)
    
    # Third chunk: finish
    c3 = {
        "id": base.get("id", "chatcmpl-proxy"),
        "object": "chat.completion.chunk",
        "created": base.get("created", 0),
        "model": base.get("model", ""),
        "system_fingerprint": base.get("system_fingerprint", "fp_proxy"),
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "tool_calls"
        }]
    }
    chunks.append(c3)
    
    # Build SSE bytes
    sse_bytes = b""
    for c in chunks:
        sse_bytes += f"data: {json.dumps(c)}\n\n".encode()
    sse_bytes += b"data: [DONE]\n\n"
    return sse_bytes


def handle_openai_streaming(resp_body_bytes, first_chunk_json):
    """
    Parse full streaming SSE response, reassemble content, 
    and if it's a text tool call, return converted SSE bytes.
    Returns (new_body_bytes, was_converted) tuple.
    """
    raw = resp_body_bytes.decode('utf-8', errors='replace')
    lines = raw.split('\n')
    
    full_content = []
    last_chunk_json = first_chunk_json
    
    for line in lines:
        line = line.strip()
        if not line or line == 'data: [DONE]':
            continue
        if line.startswith('data: '):
            json_str = line[6:]
            try:
                chunk = json.loads(json_str)
                last_chunk_json = chunk
                choices = chunk.get('choices', [])
                if choices:
                    delta = choices[0].get('delta', {})
                    # If already has tool_calls, don't convert
                    if delta.get('tool_calls'):
                        return resp_body_bytes, False
                    content = delta.get('content', '')
                    if content:
                        full_content.append(content)
            except (json.JSONDecodeError, Exception):
                pass
    
    assembled = ''.join(full_content)
    sys.stderr.write(f"[proxy] Assembled content: {repr(assembled[:200])}\n")
    sys.stderr.flush()
    
    tool_call = extract_tool_call(assembled)
    if tool_call:
        sys.stderr.write(f"[proxy] Converted tool call: {tool_call['function']['name']}\n")
        sys.stderr.flush()
        sse = build_sse_tool_call_response(last_chunk_json, tool_call)
        return sse, True
    
    return resp_body_bytes, False


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Log request info for debugging
        try:
            req_data = json.loads(body)
            has_tools = bool(req_data.get('tools'))
            model = req_data.get('model', 'unknown')
            msg_count = len(req_data.get('messages', []))
            sys.stderr.write(f"[proxy] {self.path} model={model} msgs={msg_count} tools={has_tools}\n")
            sys.stderr.flush()
        except:
            pass
        
        # Forward to real Ollama
        target_url = f"{OLLAMA_URL}{self.path}"
        forward_headers = {k: v for k, v in self.headers.items()
                          if k.lower() not in ('host', 'content-length')}
        
        req = urllib.request.Request(target_url, data=body, 
                                      headers=forward_headers, method='POST')
        
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                resp_body = resp.read()
                resp_headers = dict(resp.headers)
                resp_status = resp.status
                
                # Handle /api/chat (Ollama native format, non-streaming)
                if self.path == '/api/chat':
                    try:
                        resp_data = json.loads(resp_body)
                        msg = resp_data.get('message', {})
                        if not msg.get('tool_calls') and msg.get('content'):
                            tool_call = extract_tool_call(msg['content'])
                            if tool_call:
                                msg['tool_calls'] = [tool_call]
                                msg['content'] = ''
                                resp_data['message'] = msg
                                resp_body = json.dumps(resp_data).encode()
                    except Exception as e:
                        sys.stderr.write(f"[proxy] /api/chat error: {e}\n")
                
                # Handle /v1/chat/completions (OpenAI-compatible format)
                elif self.path == '/v1/chat/completions':
                    try:
                        content_type = resp_headers.get('Content-Type', '').lower()
                        is_streaming = b'data:' in resp_body[:100] or 'text/event-stream' in content_type
                        
                        if is_streaming:
                            # Parse first chunk to get base info
                            first_chunk = {}
                            for line in resp_body.decode('utf-8', errors='replace').split('\n'):
                                line = line.strip()
                                if line.startswith('data: ') and line != 'data: [DONE]':
                                    try:
                                        first_chunk = json.loads(line[6:])
                                        break
                                    except:
                                        pass
                            
                            new_body, converted = handle_openai_streaming(resp_body, first_chunk)
                            if converted:
                                resp_body = new_body
                        else:
                            # Non-streaming response
                            resp_data = json.loads(resp_body)
                            choices = resp_data.get('choices', [])
                            if choices:
                                msg = choices[0].get('message', {})
                                if not msg.get('tool_calls') and msg.get('content'):
                                    tool_call = extract_tool_call(msg['content'])
                                    if tool_call:
                                        msg['tool_calls'] = [tool_call]
                                        msg['content'] = ''
                                        choices[0]['message'] = msg
                                        choices[0]['finish_reason'] = 'tool_calls'
                                        resp_data['choices'] = choices
                                        resp_body = json.dumps(resp_data).encode()
                    except Exception as e:
                        sys.stderr.write(f"[proxy] /v1/chat/completions error: {e}\n")
                
                self.send_response(resp_status)
                for k, v in resp_headers.items():
                    if k.lower() not in ('transfer-encoding', 'content-length'):
                        self.send_header(k, v)
                self.send_header('Content-Length', len(resp_body))
                self.end_headers()
                self.wfile.write(resp_body)
                
        except Exception as e:
            sys.stderr.write(f"[proxy] Error: {e}\n")
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())
    
    def do_GET(self):
        target_url = f"{OLLAMA_URL}{self.path}"
        req = urllib.request.Request(target_url)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ('transfer-encoding', 'content-length'):
                        self.send_header(k, v)
                self.send_header('Content-Length', len(resp_body))
                self.end_headers()
                self.wfile.write(resp_body)
        except Exception as e:
            sys.stderr.write(f"[proxy] GET error: {e}\n")
            self.send_response(502)
            self.end_headers()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


if __name__ == '__main__':
    server = ThreadedHTTPServer(('127.0.0.1', PROXY_PORT), ProxyHandler)
    sys.stderr.write(f"Ollama proxy v2 running on port {PROXY_PORT}\n")
    sys.stderr.write(f"Forwarding to {OLLAMA_URL}\n")
    server.serve_forever()
