"""Validate fictional records and regenerate all evidence totals in the game."""
import csv
import json
import re
from pathlib import Path

root = Path(__file__).parent
with (root / "potluck_guests.csv").open() as source:
    guests = list(csv.DictReader(source))
for guest in guests:
    for key in ("sick", "chicken", "lemonade", "coffee", "ice"):
        guest[key] = int(guest[key])
        if guest[key] not in (0, 1):
            raise ValueError("Exposure and illness values must be 0 or 1.")
if len({g["guest"] for g in guests}) != len(guests):
    raise ValueError("Guest names must be unique.")
survey = []
for key, label in (("chicken", "Chicken skewers"), ("lemonade", "Lemonade"), ("coffee", "Iced coffee"), ("ice", "Added ice")):
    exposed = [g for g in guests if g[key]]
    unexposed = [g for g in guests if not g[key]]
    survey.append([label, sum(g["sick"] for g in exposed), len(exposed), sum(g["sick"] for g in unexposed), len(unexposed)])
data = dict(total=len(guests), sick=sum(g["sick"] for g in guests), survey=survey)
path = root / "clueborne.html"
html = path.read_text()
html = re.sub(r"// BEGIN GENERATED POTLUCK DATA.*?// END GENERATED POTLUCK DATA",
    "// BEGIN GENERATED POTLUCK DATA\nconst potluck = " + json.dumps(data) + ";\n// END GENERATED POTLUCK DATA", html, flags=re.S)
html = re.sub(r"// BEGIN GUEST RECORDS.*?// END GUEST RECORDS",
    "// BEGIN GUEST RECORDS\nconst guests = " + json.dumps(guests) + ";\n// END GUEST RECORDS", html, flags=re.S)
path.write_text(html)
print("Updated guest records and exposure counts. Review narrative clues after changing records.")
