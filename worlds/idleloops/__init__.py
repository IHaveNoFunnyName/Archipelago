from os import name

from .Options import IdleLoopsOptions, Goal
from .Actions import all_actions, all_locations, all_items, journeyRules, location_to_id, item_to_id, IdleLoopsLocation, IdleLoopsItem, filler_item_names, Tags
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

        # Enough guaranteed pots to Meet People/Investigate, and buy mana to be able to get mana from locks/quests
        # Should be enough
        if self.goal != "Z1":
        #     self.multiworld.early_items[self.player]["Z1 - Met"] = 1
        #     self.multiworld.early_items[self.player]["Z1 - Secrets"] = 1
        #     self.multiworld.early_items[self.player]["Z1 - BuySupplies"] = 1
            self.multiworld.local_early_items[self.player]["Z1 - BuyManaZ1"] = 1
            self.multiworld.local_early_items[self.player]["Z1 - Pots"] = 15
        #     self.multiworld.early_items[self.player]["Z1 - Haggle"] = 1
        #     self.multiworld.early_items[self.player]["Z1 - StartJourney"] = 1

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

            if (not item["name"][0] ==  "F") and int(item["name"][1]) > int(self.goal[1]):
                pass

            for _ in range(item["count"]):
                new_item = self.create_item(item["name"])
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
            
        def z2rule(state: CollectionState) -> bool:
            return state.has_all_counts({
                "Z1 - BuySupplies": 1,
                "Z1 - BuyManaZ1": 1,
                "Z1 - Haggle": 1,
                "Z1 - StartJourney": 1
            }, self.player)
        def z3rule(state: CollectionState) -> bool:
            return state.has_all_counts({
                "Z2 - ContinueOn": 1
            }, self.player)
        def z4rule(state: CollectionState) -> bool:
            return state.has_all_counts({
                "Z3 - StartTrek": 1
            }, self.player)
        
        dumb = {
            "Menu": "_",
            "Z1": Tags.Z1,
            "Z2": Tags.Z2,
            "Z3": Tags.Z3,
            "Z4": Tags.Z4
        }

        used_regions = {
            "Menu": (["Z1"], {}),
            "Z1": ([], {})
        }

        if self.goal != "Z1":
            used_regions["Z1"] = (["Z2"], {"Z2": z2rule})
            used_regions["Z2"] = ([], {})
            if self.goal != "Z2":
                used_regions["Z2"] = (["Z3"], {"Z3": z3rule})
                used_regions["Z3"] = ([], {})
                if self.goal != "Z3":
                    used_regions["Z3"] = (["Z4"], {"Z4": z4rule})
                    used_regions["Z4"] = ([], {})

        for region_name in used_regions:
            self.multiworld.regions.append(Region(region_name, self.player, self.multiworld))

        for region_name, region_data in used_regions.items():
            region_connections, region_rules = region_data
            region = self.get_region(region_name)
            region.add_exits(region_connections, region_rules)
            region.add_locations({
                location[0]: self.location_name_to_id[location[0]] for location in all_locations if all(tag not in self.excluded_tags for tag in location[1]) and dumb[region_name] in location[1]
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
        
        # def z2rule(state: CollectionState) -> bool:
        #     return state.has_all_counts({
        #         "Z1 - BuySupplies": 1,
        #         "Z1 - BuyManaZ1": 1,
        #         "Z1 - Haggle": 1,
        #         "Z1 - StartJourney": 1
        #     }, self.player)
        # def z3rule(state: CollectionState) -> bool:
        #     return state.has_all_counts({
        #         "Z2 - ContinueOn": 1
        #     }, self.player)
        # def z4rule(state: CollectionState) -> bool:
        #     return state.has_all_counts({
        #         "Z3 - StartTrek": 1
        #     }, self.player)
        # def z5rule(state: CollectionState) -> bool:
        #     return state.has_all_counts({
        #         "Z4 - FaceJudgement": 1
        #     }, self.player)

        # # These broke generation? I feel it should be equivalent to the existing rules on the regions, whatever

        # if self.goal == "Z1":
        #     multiworld.completion_condition[self.player] = z2rule
        # elif self.goal == "Z2":
        #     multiworld.completion_condition[self.player] = z3rule
        # elif self.goal == "Z3":
        #     multiworld.completion_condition[self.player] = z4rule
        # elif self.goal == "Z4":
        #     multiworld.completion_condition[self.player] = z5rule

    def fill_slot_data(self) -> Dict[str, Any]:
        return self.options.as_dict(
            "goal",
            "bonus"
        )
