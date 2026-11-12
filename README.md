# Clueborne

A cozy outbreak mystery game. Investigate the outbreak, connect evidence to your reasoning, and identify the most likely source in three guesses.

## Run locally

Requires Python 3; no third-party packages or build step.

```sh
python3 room_server.py
```

Open [localhost:8000](http://localhost:8000). Use the server for multiplayer; opening the HTML file directly does not provide the room API.

## Play

- **Solo:** investigate at your own pace, with browser-saved progress and case history.
- **Team Investigation:** share discoveries and three guesses; the host submits the team's theory.
- **Head-to-Head:** two or more players investigate independently. Solved players rank by fewer hints, then active completion time. Cards opened do not affect ranking.

Each guess requires an opened clue and a matching reasoning choice. Hints are optional. Every distinct card hint counts once. Players can withdraw from races, and hosts can end them without discarding completed results.

Only **Case 001: The Midnight Potluck** is currently playable. Guest records are fictional. Answers are inspectable in the client, so competition is informal and based on trust.

## Files

- `clueborne.html`: game interface, illustration, logic, styles, and embedded soundtrack.
- `room_server.py`: Python standard-library web server and in-memory multiplayer rooms.
- `potluck_guests.csv`: synthetic guest records.
- `build_case.py`: validates guest records and updates generated data in the HTML.
- [MULTIPLAYER.md](MULTIPLAYER.md): hosting, persistence, rules, validation, and music notes.

After editing the CSV, run `python3 build_case.py` and review narrative clues for consistency.

## Hosting

Set `PORT` if needed (default `8000`). On Render, use build command `python -m py_compile room_server.py` and start command `python room_server.py`. Deploy the HTML and server together. Rooms live in server memory and expire when the service restarts. Progress and case history live in each browser; there are no accounts or cross-device sync.

## Music credit

“I Knew a Guy” by **Kevin MacLeod** ([incompetech.com](https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100199)). Licensed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

Adaptations: re-encoded at 192 kbps, short opening and closing fades, looped for gameplay. Music is embedded locally in the game.

## Previous name

Clueborne was previously called Outbreakle. Existing browser saves are migrated automatically. The entry file is now `clueborne.html`.
