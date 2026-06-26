from .Options import IdleLoopsOptions, Goal
from .Actions import all_actions, all_locations, all_items, location_name_to_id, item_to_id, IdleLoopsLocation, IdleLoopsItem, filler_item_names, Tags
from typing import Dict, Any
from BaseClasses import CollectionState, Region, Item, Tutorial, ItemClassification
from worlds.AutoWorld import World, WebWorld
from rule_builder.rules import True_

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
    location_name_to_id = location_name_to_id

    def generate_early(self) -> None:
        self.all_items = [item.copy() for item in all_items]

        self.rules = {}
        for action in all_actions:
            self.rules.update(action.rules())

        self.multiworld.push_precollected(self.create_item("Z1 - Wander"))
        # I tried with only Wander and it still was too restrictive a start
        self.multiworld.push_precollected(self.create_item("Z1 - Mana Pot - Search"))
        # Handle Options
        self.excluded_tags = []
        if self.options.goal == Goal.option_z1:
            self.goal = "Z1"
            self.excluded_tags = self.excluded_tags + [Tags.Z2, Tags.Z3, Tags.Z4]
        elif self.options.goal == Goal.option_z2:
            self.goal = "Z2"
            self.excluded_tags = self.excluded_tags + [Tags.Z3, Tags.Z4]
        elif self.options.goal == Goal.option_z3:
            self.goal = "Z3"
            self.excluded_tags = self.excluded_tags + [Tags.Z4]
        elif self.options.goal == Goal.option_z4:
            self.goal = "Z4"

        self.used_regions = {
            "Menu": (["Z1"], {"Z1": True_()}),
            "Z1": ([], {})
        }

        if self.goal != "Z1":
            self.used_regions["Z1"] = (["Z2"], {"Z2": self.rules["Z1 - Start Journey"]})
            self.used_regions["Z2"] = ([], {})
            if self.goal != "Z2":
                self.used_regions["Z2"] = (["Z3"], {"Z3": self.rules["Z2 - Continue On"]})
                self.used_regions["Z3"] = ([], {})
                if self.goal != "Z3":
                    self.used_regions["Z3"] = (["Z4"], {"Z4": self.rules["Z3 - Start Trek"]})
                    self.used_regions["Z4"] = ([], {})

        # Enough guaranteed pots to Meet People/Investigate, and buy mana to be able to get mana from locks/quests
        # Should be enough
        self.multiworld.local_early_items[self.player]["Z1 - Buy Mana"] = 1
        self.multiworld.local_early_items[self.player]["Z1 - Mana Pot"] = 15
        if self.goal != "Z1":
            pass
        #     self.multiworld.early_items[self.player]["Z1 - Meet People"] = 1
        #     self.multiworld.early_items[self.player]["Z1 - Investigate"] = 1

    # I'm quite worried about Z2+ items diluting the pool and making Z1 impossible without a loooong wait for checks, so I think all filler should help Z1
    def get_filler_item_name(self) -> str:
        return self.random.choice(filler_item_names)

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        item_data = self.all_items[item_id - 1]
        return IdleLoopsItem(name, item_data["classification"], item_id, self.player)

    def create_items(self) -> None:
        items_added = 0
        # Wander and Smash Pots are precollected so should are skipped here with [2::]
        # There's a better way to do this
        for item in self.all_items[2::]:

            if (not item["name"][0] ==  "F") and (int(item["name"][1]) > int(self.goal[1])):
                continue

            for _ in range(item["count"]):
                new_item = self.create_item(item["name"])
                self.multiworld.itempool.append(new_item)
                items_added += 1
        
        # Temporary, rewrite to use tags later
        if self.options.proggressive_lootable:
            for _ in range(20):
                new_item = self.create_item("Filler - Progressive Lootable")
                self.multiworld.itempool.append(new_item)
                items_added += 1
        
        used_locations = []
        for location in all_locations:
            if all(tag not in self.excluded_tags for tag in location[1]):
                used_locations.append(location)

        filler_count = len(used_locations) - items_added

        for _ in range(filler_count):
            new_item = self.create_item(self.get_filler_item_name())
            self.multiworld.itempool.append(new_item)

    def create_regions(self) -> None:
        dumb = {
            "Menu": "_",
            "Z1": Tags.Z1,
            "Z2": Tags.Z2,
            "Z3": Tags.Z3,
            "Z4": Tags.Z4
        }

        for region_name in self.used_regions:
            self.multiworld.regions.append(Region(region_name, self.player, self.multiworld))
            region = self.get_region(region_name)
            region.add_locations({
                location[0]: self.location_name_to_id[location[0]] for location in all_locations if all(tag not in self.excluded_tags for tag in location[1]) and dumb[region_name] in location[1]
            })

    def set_rules(self) -> None:
        
        multiworld = self.multiworld
        for region in multiworld.get_regions(self.player):
            for loc in region.locations:
                if loc.name in self.rules:
                    self.set_rule(loc, self.rules[loc.name])
        
        for region_name, region_data in self.used_regions.items():
            region_connections, region_rules = region_data
            for connection in region_connections:
                self.create_entrance(self.get_region(region_name), self.get_region(connection), region_rules[connection])

        if self.goal == "Z1":
            self.set_completion_rule(self.rules["Z1 - Start Journey"])
        elif self.goal == "Z2":
            self.set_completion_rule(self.rules["Z2 - Continue On"])
        elif self.goal == "Z3":
            self.set_completion_rule(self.rules["Z3 - Start Trek"])
        elif self.goal == "Z4":
            self.set_completion_rule(self.rules["Z4 - Face Judgement"])

    def fill_slot_data(self) -> Dict[str, Any]:
        return self.options.as_dict(
            "goal",
            "bonus"
        )
