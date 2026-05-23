from os import name

from .Options import IdleLoopsOptions, Goal
from .Actions import all_actions, all_locations, all_items, journeyRules, location_to_id, item_to_id, IdleLoopsLocation, IdleLoopsItem
from typing import Dict, Any
from BaseClasses import CollectionState, Region, Item, Tutorial, ItemClassification
from worlds.AutoWorld import World, WebWorld

# Based this file off Inscryption's world (since it was next alphabetically when i created the folder)
# And poking around a few other worlds, most are closer to this than to APQuest

class IdleLoopsWeb(WebWorld):
    theme = "dirt"

    guide_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up the Idle Loops Archipelago Multiworld",
        "English",
        "setup_en.md",
        "setup/en",
        ["Neffy"]
    )

    tutorials = [guide_en]

    bug_report_page = "https://github.com/Neffy/IdleLoops_Archipelago/issues"


class IdleLoopsWorld(World):
    """
    Idle Loops is an incremental game with light optimisation elements.
    You're stuck in a time loop and explore the world around you,
    getting a little bit stronger and doing a little more each loop.
    """
    game = "Idle Loops"
    web = IdleLoopsWeb()
    options_dataclass = IdleLoopsOptions
    options: IdleLoopsOptions
    item_name_to_id = item_to_id
    location_name_to_id = location_to_id

    def generate_early(self) -> None:
        self.all_items = [item.copy() for item in all_items]
        self.all_items[self.item_name_to_id["Z1 - Wander"] - 1]["count"] = 0
        self.multiworld.push_precollected(self.create_item("Z1 - Wander"))
        # I tried with only Wander and there just wasn't enough early checks
        self.multiworld.push_precollected(self.create_item("Z1 - Pots - Search"))
        # Handle Options
        pass

    def get_filler_item_name(self) -> str:
        return "Z1 - Pots"
        return self.random.choice(filler_items)["name"]

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        item_data = self.all_items[item_id - 1]
        return IdleLoopsItem(name, item_data["classification"], item_id, self.player)

    def create_items(self) -> None:
        items_added = 0

        for item in self.all_items:
            for _ in range(item["count"]):
                new_item = self.create_item(item["name"])
                self.multiworld.itempool.append(new_item)
                items_added += 1

        filler_count = len(all_locations) - items_added

        for _ in range(filler_count):
            new_item = self.create_item(self.get_filler_item_name())
            self.multiworld.itempool.append(new_item)

    def create_regions(self) -> None:
        used_regions = {
            "Menu": ["Z1"],
            "Z1": []
        }

        for region_name in used_regions:
            self.multiworld.regions.append(Region(region_name, self.player, self.multiworld))

        for region_name, region_connections in used_regions.items():
            region = self.get_region(region_name)
            region.add_exits(region_connections)
            region.add_locations({
                location: self.location_name_to_id[location] for location in all_locations if location.startswith(region_name)
            })

    def set_rules(self) -> None:
        rules = {}
        for action in all_actions:
            rules.update(action.rules(self.multiworld, self.player))
        multiworld = self.multiworld
        for region in multiworld.get_regions(self.player):
            for loc in region.locations:
                if loc.name in rules:
                    loc.access_rule = rules[loc.name]
        multiworld.completion_condition[self.player] = rules["Z1 - StartJourney"]

    def fill_slot_data(self) -> Dict[str, Any]:
        return self.options.as_dict(
            "goal"
        )
