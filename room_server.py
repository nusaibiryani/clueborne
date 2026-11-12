"""Serve Clueborne and temporary co-op rooms using Python's standard library."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import re
import secrets
from threading import Lock
from time import time

HTML = Path(__file__).with_name("clueborne.html")
ROOMS = {}
LOCK = Lock()
REASONS = ['hypothesis', 'exposures', 'shared', 'comparison', 'timing']
ANSWERS = {'ice','the ice','ice bag','the ice bag','bag of ice','the bag of ice','shared ice','the shared ice','added ice','contaminated ice','ice cubes','the ice cubes','the ice from the shared bag','ice from the shared bag','shared bag of ice','the shared bag of ice'}


def progress_stats(data):
    source = data.get('progress', {})
    if not isinstance(source, dict):
        source = {}
    result = {}
    for field, maximum in [('guesses', 3), ('opened', 5), ('hints', 5), ('elapsed', 86400000)]:
        value = source.get(field, 0)
        result[field] = max(0, min(maximum, value)) if type(value) is int else 0
    return result


def finalize_racer(member, status):
    if member['result'] is None:
        member['result'] = dict(member.get('progress', {}), correct=False, **{status: True})



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
                    host=player, players={}, opened=[], hints=[], guesses=0, started=None, result=None, race_ended=False)
            room = ROOMS.get(code)
            if not room:
                return self.reply(404, {"error": "This room has expired. Your saved results remain in case history."})
            if action in ("create", "join"):
                if room["started"] and player not in room["players"] and room["mode"] == "race":
                    return self.reply(409, {"error": "This race has already started."})
                room["players"].setdefault(player, {"name": str(data.get("name", "Detective"))[:40], "result": None, "left": False, "progress": {"guesses": 0, "opened": 0, "hints": 0, "elapsed": 0}})
                if room["host"] not in room["players"]:
                    room["host"] = player
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
            member = room["players"][player]
            if room["mode"] == "race" and member["result"] is None and "progress" in data:
                member["progress"] = progress_stats(data)
            if action == "propose":
                room["message"] = ""
                room["proposal"] = member["name"] + " suggests " + str(data.get("answer", ""))[:120] + " · " + str(data.get("reason", ""))[:40]
            if action == "guess":
                if room["mode"] != "team" or player != room["host"]:
                    return self.reply(403, {"error": "The host submits the team theory."})
                evidence = data.get("evidence")
                reason = data.get("reason")
                if type(evidence) is not int or evidence not in room["opened"] or reason not in REASONS:
                    return self.reply(400, {"error": "Choose an opened clue and supporting reasoning."})
                if room["started"] and not room["result"]:
                    room["proposal"] = ""
                    room["guesses"] += 1
                    answer_correct = data.get("answer") in ANSWERS
                    reasoning_correct = REASONS[evidence] == reason
                    correct = answer_correct and reasoning_correct
                    if correct or room["guesses"] == 3:
                        room["result"] = dict(correct=correct, guesses=room["guesses"], opened=len(room["opened"]),
                            hints=len(room["hints"]), elapsed=int(time()*1000)-room["started"], evidence=evidence,
                            reason=reason, answerCorrect=answer_correct, reasoningCorrect=reasoning_correct)
                    room["message"] = "That theory and supporting reasoning didn’t hold up. " + str(3-room["guesses"]) + " guesses remaining." if not correct else ""
            if action == "result" and room["mode"] == "race":
                result = data.get("result")
                if not room["started"]:
                    return self.reply(409, {"error": "The race has not started."})
                if isinstance(result, dict) and member["result"] is None and not room["race_ended"]:
                    member["result"] = result
            if action == "end" and room["mode"] == "race":
                if player != room["host"]:
                    return self.reply(403, {"error": "Only the host can end the race."})
                if not room["started"]:
                    return self.reply(409, {"error": "The race has not started."})
                room["race_ended"] = True
                for racer in room["players"].values():
                    finalize_racer(racer, "ended")
            if action == "leave":
                if room["mode"] == "race" and room["started"]:
                    finalize_racer(member, "withdrawn")
                    member["left"] = True
                else:
                    del room["players"][player]
                if player == room["host"]:
                    candidates = [key for key, value in room["players"].items() if not value.get("left")]
                    if candidates:
                        room["host"] = candidates[0]
            room["race_complete"] = bool(room["started"] and room["players"] and all(p["result"] is not None for p in room["players"].values()))
            payload = json.loads(json.dumps(room))
        self.reply(200, payload)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Clueborne is running on port {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
