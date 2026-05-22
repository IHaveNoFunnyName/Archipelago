from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification

class IdleLoopsItem(Item):
    game = "Idle Loops"

Z1_items = [
    {
        "name": "Z1 - Wander",
        # Count 0 because starting item
        "count": 0,
        "classification": ItemClassification.useful
    },
    {
        "name": "Z1 - Pots",
        "count": 50,
        "classification": ItemClassification.useful | ItemClassification.filler
    },
    {
        "name": "Z1 - Locks",
        "count": 10,
        "classification": ItemClassification.useful | ItemClassification.filler
    },
]