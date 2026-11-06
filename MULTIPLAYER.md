# Outbreakle multiplayer

Solo play works by opening outbreakle.html. For co-op, run python3 room_server.py
and visit http://localhost:8000. Choose Play with friends and copy the invite.
Use two browser tabs to test. Everyone uses their own screen, notes and guesses.
Evidence opened in one browser appears as Team found on the other board.

For friends on other networks, deploy this folder to a host that runs a Python
web service, with python3 room_server.py as the start command. Use a single
server instance and open the deployed HTTPS URL before creating an invite.
A localhost link only works on your own device. GitHub Pages can serve solo
play but cannot run the room server. Rooms are stored in memory and disappear
when the server restarts or after six hours without activity.
