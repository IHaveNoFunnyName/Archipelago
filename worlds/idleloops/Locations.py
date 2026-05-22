from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from BaseClasses import Location


class IdleLoopsLocation(Location):
    game = "Idle Loops"

Z1_locations = []

bar_locations = ["1", "10", "25", "50", "75", "90", "95", "99", "100"]

Z1_bars = ["Wander"]
Z1_limited = [("Pots", 50)]

# I had these as list comprehension form, but if i have to mirror them on the client
# then foor loops keeps things similar

for bar in Z1_bars:
    for location in bar_locations:
        Z1_locations.append("Z1 - " + bar + " - " + location + "%")

for limited in Z1_limited:
    for n in range(1, limited[1] + 1):
        Z1_locations.append("Z1 - " + limited[0] + " - #" + str(n))

regions_to_locations: Dict[str, List[str]] = {
    "Menu": [],
    "Z1": Z1_locations
}