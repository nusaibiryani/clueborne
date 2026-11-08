# Outbreakle
Run `python3 room_server.py` and open http://localhost:8000.
On Render use build command `python -m py_compile room_server.py` and start command `python room_server.py`.

Upload all five project files to replace the earlier version.
The HTML and server must be deployed together because the room API has changed.
Rooms are held in server memory. Restarting or redeploying the service expires active rooms.
Completed history and personal progress are stored in each browser. Clearing site data removes them.
Head-to-head leaderboards are saved when all room members have finished and the player's browser receives the result.
Team clocks continue while one member pauses. Solo and race clocks count active time.
Names are display names, without accounts or cross-device synchronization.
Only Case 001 is currently playable.

## Data
The 12 guest records are synthetic. Run `python3 build_case.py` after editing potluck_guests.csv.
The script produces guest details and the exposure counts used by the debrief.
Review narrative clues manually after changing records.
The client-side answer is inspectable. Competition is informal and based on trust.

## Validation
Python and JavaScript syntax checks passed. Server logic checks covered shared evidence deduplication,
host-only team guesses, proposals, race joins and separate player results.
A full browser playthrough, mobile visual audit and live multiplayer test are still required.
