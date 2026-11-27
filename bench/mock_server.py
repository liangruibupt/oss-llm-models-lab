#!/usr/bin/env python3
"""Tiny OpenAI-compatible streaming mock server for testing the harness.

It answers ``POST /v1/chat/completions`` and ``POST /v1/completions`` with an SSE
stream of ``max_tokens`` one-word chunks: it waits ``--ttft`` seconds before the
first chunk and ``--itl`` seconds between chunks, then sends a ``usage`` event and
``[DONE]``. No model, no GPU. Binds to 127.0.0.1 only.

    python bench/mock_server.py --port 8000 --ttft 0.05 --itl 0.01
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class MockHandler(BaseHTTPRequestHandler):
    ttft = 0.02
    itl = 0.005
    fail_every = 0  # if > 0, every Nth request returns HTTP 500
    _count = 0
    _lock = threading.Lock()
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep test output quiet
        pass

    def _send_json(self, code: int, obj: dict) -> None:
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/") == "/v1/models":
            self._send_json(200, {"object": "list", "data": [{"id": "mock", "object": "model"}]})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        chat = self.path.rstrip("/") == "/v1/chat/completions"
        if not chat and self.path.rstrip("/") != "/v1/completions":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        with MockHandler._lock:
            MockHandler._count += 1
            n = MockHandler._count
        if self.fail_every and n % self.fail_every == 0:
            self._send_json(500, {"error": "injected failure"})
            return
        max_tokens = int(body.get("max_tokens", 16))
        prompt = body.get("prompt") or " ".join(m.get("content", "") for m in body.get("messages", []))
        prompt_tokens = len(str(prompt).split())

        if not body.get("stream"):
            text = " ".join(["tok"] * max_tokens)
            self._send_json(200, {
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "length"}],
                "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": max_tokens},
            })
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def emit(obj) -> None:
            payload = obj if isinstance(obj, str) else json.dumps(obj)
            self.wfile.write(f"data: {payload}\n\n".encode())
            self.wfile.flush()

        time.sleep(self.ttft)
        for i in range(max_tokens):
            if i:
                time.sleep(self.itl)
            choice = {"index": 0, "delta": {"content": "tok "}} if chat else {"index": 0, "text": "tok "}
            emit({"object": "chat.completion.chunk" if chat else "text_completion", "choices": [choice]})
        if (body.get("stream_options") or {}).get("include_usage"):
            emit({"choices": [], "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": max_tokens}})
        emit("[DONE]")
        self.close_connection = True


def make_server(port: int = 0, ttft: float = 0.02, itl: float = 0.005, fail_every: int = 0) -> ThreadingHTTPServer:
    handler = type("ConfiguredMockHandler", (MockHandler,), {"ttft": ttft, "itl": itl, "fail_every": fail_every})
    # The stdlib default listen backlog (5) resets connections at concurrency 64.
    server_cls = type("MockHTTPServer", (ThreadingHTTPServer,), {"request_queue_size": 256})
    server = server_cls(("127.0.0.1", port), handler)
    server.daemon_threads = True
    return server


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--ttft", type=float, default=0.02, help="seconds before the first token")
    p.add_argument("--itl", type=float, default=0.005, help="seconds between tokens")
    a = p.parse_args()
    srv = make_server(a.port, a.ttft, a.itl)
    print(f"mock OpenAI server on http://127.0.0.1:{srv.server_address[1]}/v1")
    srv.serve_forever()


if __name__ == "__main__":
    main()
