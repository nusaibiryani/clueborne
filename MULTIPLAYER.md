# Clueborne
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
Browser checks cover solo reasoning, two-player race withdrawal and host ending, and shared team guesses. Responsive layout checks cover phone, tablet and laptop widths.

## Music
“I Knew a Guy” Kevin MacLeod (incompetech.com).
Licensed under Creative Commons: By Attribution 4.0 License
https://creativecommons.org/licenses/by/4.0/
Official source and download: https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100199
Adaptations: re-encoded at 192 kbps, added a 0.2-second opening fade and 1-second closing fade, looped for gameplay.
The track is embedded in clueborne.html, with music volume set to 28%.

## Investigation rules
Every guess requires an opened evidence card and a choice explaining what that clue supports. Both the item and the reasoning must be correct. Failed attempts give neutral feedback; reasoning explanations appear in the final debrief.
Solved Head-to-Head players rank by fewer hints first, then active completion time. Equal hint counts and exact times share a place. Guesses provide context, and opened cards remain a personal statistic. Each distinct card hint counts once. One supporting clue and its reasoning are required; there is no second supporting clue field. Withdrawn and host-ended unfinished players are unranked.
Players can withdraw; the host can end a started race. Completed results remain intact. If the host leaves, control transfers to a remaining player. Closing a tab does not automatically withdraw a player: the host can end the race if someone disappears.

## Multiplayer screens
Choose a multiplayer mode (and a team name for Team Investigation), then choose a case. Selecting the case creates a dedicated invitation lobby. Invitees enter that lobby directly. The host starts the introduction for everyone; each player chooses when to open the evidence board. During the introduction, investigation, and debrief, the header’s Room button opens invitation, leave/withdraw, and host end-race controls. Refresh restores the lobby or personal investigation stage instead of skipping the introduction.
