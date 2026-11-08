"""Serve Outbreakle and temporary co-op rooms using Python's standard library."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import re
import secrets
from threading import Lock
from time import monotonic, time

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
        match = re.fullmatch(r"/api/rooms(?:/([a-f0-9]{24}))?", self.path)
        if not match:
            return self.reply(404, {"error": "Room not found."})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 20000:
                raise ValueError()
            data = json.loads(self.rfile.read(size)) if size else {}
        except (ValueError, json.JSONDecodeError):
            return self.reply(400, {"error": "Invalid request."})
        player = str(data.get("player", ""))[:80]
        action = data.get("action")
        code = match.group(1)
        with LOCK:
            if action == "create" and not code:
                code = secrets.token_hex(12)
                ROOMS[code] = dict(code=code, mode=data.get("mode", "team"), team=str(data.get("team", "Detectives"))[:40],
                    host=player, players={}, opened=[], hints=[], guesses=0, started=None, result=None)
            room = ROOMS.get(code)
            if not room:
                return self.reply(404, {"error": "This room has expired. Your saved results remain in case history."})
            if action in ("create", "join"):
                if room["started"] and player not in room["players"] and room["mode"] == "race":
                    return self.reply(409, {"error": "This race has already started."})
                room["players"].setdefault(player, {"name": str(data.get("name", "Detective"))[:40], "result": None})
            if player not in room["players"]:
                return self.reply(403, {"error": "Join the room first."})
            if action == "start" and player == room["host"] and not room["started"]:
                room["started"] = int(time() * 1000)
            if action in ("card", "hint") and room["started"] and not room["result"]:
                index = data.get("index")
                if isinstance(index, int) and 0 <= index < 5:
                    target = room["opened" if action == "card" else "hints"]
                    if index not in target:
                        target.append(index)
            if action == "propose":
                room["proposal"] = room["players"][player]["name"] + " suggests " + str(data.get("answer", ""))[:120]
            if action == "guess":
                if player != room["host"]:
                    return self.reply(403, {"error": "Discuss your theory with the host, who submits the team guess."})
                if room["started"] and not room["result"]:
                    room["guesses"] += 1
                    correct = data.get("answer") in ['ice','the ice','ice bag','the ice bag','bag of ice','the bag of ice','shared ice','the shared ice','added ice','contaminated ice','ice cubes','the ice cubes','the ice from the shared bag','ice from the shared bag','shared bag of ice','the shared bag of ice']
                    if correct or room["guesses"] == 3:
                        room["result"] = dict(correct=correct, guesses=room["guesses"], opened=len(room["opened"]),
                            hints=len(room["hints"]), elapsed=int(time()*1000)-room["started"])
                    room["message"] = "That theory didn’t hold up." if not correct else ""
            if action == "result" and room["mode"] == "race":
                result = data.get("result")
                if isinstance(result, dict) and not room["players"][player]["result"]:
                    room["players"][player]["result"] = result
            payload = json.loads(json.dumps(room))
        self.reply(200, payload)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Outbreakle is running on port {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
