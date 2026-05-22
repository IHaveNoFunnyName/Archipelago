from .Options import IdleLoopsOptions, Goal
from .Items import Z1_items, IdleLoopsItem
from .Locations import Z1_locations, IdleLoopsLocation, regions_to_locations
from .Regions import idle_loops_regions_z1
from typing import Dict, Any
from . import Rules
from BaseClasses import Region, Item, Tutorial, ItemClassification
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
    all_items = Z1_items
    item_name_to_id = {item["name"]: i + 1 for i, item in enumerate(all_items)}
    all_locations = Z1_locations
    location_name_to_id = {location: i + 1 for i, location in enumerate(all_locations)}

    def generate_early(self) -> None:
        self.all_items = [item.copy() for item in self.all_items]
        self.multiworld.push_precollected(self.create_item("Z1 - Wander"))
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
        useful_items = self.all_items.copy()

        for item in useful_items:
            for _ in range(item["count"]):
                new_item = self.create_item(item["name"])
                self.multiworld.itempool.append(new_item)
                items_added += 1

        filler_count = len(self.all_locations) - items_added

        for i in range(filler_count):
            new_item = self.create_item(self.get_filler_item_name())
            self.multiworld.itempool.append(new_item)

    def create_regions(self) -> None:
        used_regions = idle_loops_regions_z1
        for region_name in used_regions.keys():
            self.multiworld.regions.append(Region(region_name, self.player, self.multiworld))

        for region_name, region_connections in used_regions.items():
            region = self.get_region(region_name)
            region.add_exits(region_connections)
            region.add_locations({
                location: self.location_name_to_id[location] for location in regions_to_locations[region_name]
            })

    def set_rules(self) -> None:
        Rules.IdleLoopsRules(self).set_all_rules()

    def fill_slot_data(self) -> Dict[str, Any]:
        return self.options.as_dict()
