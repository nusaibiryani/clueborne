"""Serve Outbreakle and temporary co-op rooms using Python's standard library."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import re
import secrets
from threading import Lock
from time import monotonic

HTML = Path(__file__).with_name("outbreakle.html")
ROOMS = {}
LOCK = Lock()
LIFETIME = 6 * 60 * 60


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, content_type="application/json"):
        body = json.dumps(data).encode() if content_type == "application/json" else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/":
            return self.reply(200, HTML.read_bytes(), "text/html; charset=utf-8")
        self.room_request()

    def do_POST(self):
        self.room_request()

    def room_request(self):
        match = re.fullmatch(r"/api/rooms(?:/([a-f0-9]{24})(?:/evidence/([0-4]))?)?", self.path)
        if not match:
            return self.reply(404, {"error": "Room not found."})
        code, card = match.groups()
        with LOCK:
            now = monotonic()
            for expired in [key for key, room in ROOMS.items() if now - room["touched"] > LIFETIME]:
                del ROOMS[expired]
            if self.command == "POST" and code is None:
                code = secrets.token_hex(12)
                ROOMS[code] = {"touched": now, "opened": set()}
            room = ROOMS.get(code)
            if room is None:
                status, payload = 404, {"error": "This room is missing or has expired."}
            else:
                if self.command == "POST" and card is not None:
                    room["opened"].add(int(card))
                room["touched"] = now
                status, payload = 200, {"code": code, "opened": sorted(room["opened"])}
        self.reply(status, payload)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Outbreakle is running on port {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
