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
ASSETS = Path(__file__).with_name("assets")
PUBLIC_ASSETS = {
    "clueborne-favicon.ico": "image/x-icon",
    "clueborne-glossy.webp": "image/webp",
    "clueborne-glossy-32.png": "image/png",
    "clueborne-glossy-48.png": "image/png",
    "clueborne-glossy-180.png": "image/png",
    "clueborne-share-glossy.png": "image/png",
    "clueborne-mark.svg": "image/svg+xml",
    "favicon.svg": "image/svg+xml",
    "favicon-32.png": "image/png",
    "apple-touch-icon.png": "image/png",
    "clueborne-share.png": "image/png",
}
ROOT_ICONS = {
    "/favicon.ico": ("clueborne-favicon.ico", "image/x-icon"),
    "/apple-touch-icon.png": ("clueborne-glossy-180.png", "image/png"),
    "/apple-touch-icon-precomposed.png": ("clueborne-glossy-180.png", "image/png"),
}
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
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ROOT_ICONS:
            filename, content_type = ROOT_ICONS[path]
            return self.reply(200, (ASSETS / filename).read_bytes(), content_type)
        if path.startswith("/assets/"):
            filename = path.removeprefix("/assets/")
            if filename in PUBLIC_ASSETS:
                return self.reply(200, (ASSETS / filename).read_bytes(), PUBLIC_ASSETS[filename])
            return self.reply(404, {"error": "Asset not found."})
        if path == "/":
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
                    host=player, players={}, proposals={}, opened=[], hints=[], guesses=0, started=None, result=None, race_ended=False)
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
            if action in ("propose", "remove_proposal", "guess"):
                if room["mode"] != "team":
                    return self.reply(400, {"error": "Proposals are only available in Team Investigation."})
                if not room["started"] or room["result"]:
                    return self.reply(409, {"error": "The team investigation is not accepting theories."})
                proposals = room.setdefault("proposals", {})
            if action == "propose":
                evidence, reason = data.get("evidence"), data.get("reason")
                answer = str(data.get("answer", "")).strip()[:120]
                if not answer or type(evidence) is not int or evidence not in room["opened"] or reason not in REASONS:
                    return self.reply(400, {"error": "Enter a source, choose an opened clue, and select supporting reasoning."})
                proposals[player] = dict(id=secrets.token_hex(12), player=player, name=member["name"],
                    answer=answer, evidence=evidence, reason=reason, submissions=0)
            if action == "remove_proposal":
                owner = next((key for key, proposal in proposals.items() if proposal["id"] == data.get("proposalId")), None)
                if owner is None:
                    return self.reply(409, {"error": "That theory was removed or replaced. Choose a current theory."})
                if player not in (owner, room["host"]):
                    return self.reply(403, {"error": "You can only remove your own theory. The host can remove any theory."})
                del proposals[owner]
            if action == "guess":
                if player != room["host"]:
                    return self.reply(403, {"error": "The host submits the team theory."})
                proposal = next((item for item in proposals.values() if item["id"] == data.get("proposalId")), None)
                if proposal is None:
                    return self.reply(409, {"error": "That theory was removed or replaced. Choose a current theory."})
                if type(data.get("expectedGuesses")) is not int or data["expectedGuesses"] != room["guesses"]:
                    return self.reply(409, {"error": "The team guess count changed. Review the latest result before submitting again."})
                evidence, reason = proposal["evidence"], proposal["reason"]
                room["guesses"] += 1
                proposal["submissions"] += 1
                answer = re.sub(r"[^a-z0-9]+", " ", proposal["answer"].lower()).strip()
                answer_correct = answer in ANSWERS
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
                room.get("proposals", {}).pop(player, None)
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
