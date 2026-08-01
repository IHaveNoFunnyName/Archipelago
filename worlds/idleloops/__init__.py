from functools import reduce

from Options import OptionError
from logging import warning

from rule_builder.cached_world import CachedRuleBuilderWorld

from .Options import IdleLoopsOptions, Goal
from .Actions import all_actions, all_locations, all_items, location_name_to_id, item_to_id, IdleLoopsItem
from typing import Dict, Any, List
from BaseClasses import Region, Item, Tutorial
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


def error_during_fuzz(message: str) -> None:
    # I'm not sure how to check how it's being run. Comment out the one you don't want.
    # raise OptionError(message)
    warning(message)


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

    def check_options(self) -> None:
        if self.options.goal >= 2 and not (self.options.location_progress and self.options.logic_big_sphere1):
            error_during_fuzz(f"Idle Loops Player {self.player_name} Warning: Goals beyond Z2 are known to need \"Locations: Progress Bars\" and \"Logic: Force Early Meet People/Investigate\" to generate consistently.")
        if self.options.logic_vanilla_all:
            error_during_fuzz(f"Idle Loops Player {self.player_name} Warning: \"Logic: Vanilla Requirements All\" causes generation problems.")
        if self.options.goal == 0 and self.options.z1_shop_max > 200:
            raise OptionError(f"Idle Loops Player {self.player_name} Warning: \"Locations: Z1 Shop Max\" requires more gold than is availible in Z1")
        if self.options.goal < 3 and self.options.location_skill > IdleLoopsOptions.__annotations__["location_skill"].defaults[self.options.goal + 1]:
            warning(f"Idle Loops Player {self.player_name} Warning: \"Locations: Skill\" set above what is reasonable for a Z{self.options.goal + 1} goal.")
        if self.options.goal < 3 and self.options.location_fight > IdleLoopsOptions.__annotations__["location_fight"].defaults[self.options.goal + 1]:
            warning(f"Idle Loops Player {self.player_name} Warning: \"Locations: Fight\" set above what is reasonable for a Z{self.options.goal + 1} goal.")
        if self.options.goal < 3 and self.options.location_heal > IdleLoopsOptions.__annotations__["location_heal"].defaults[self.options.goal + 1]:
            warning(f"Idle Loops Player {self.player_name} Warning: \"Locations: Heal\" set above what is reasonable for a Z{self.options.goal + 1} goal.")

    def generate_early(self) -> None:

        if self.options.logic_vanilla_all:
            self.options.logic_vanilla.value = 1

        self.check_options()
        self.goal = "Z" + str(self.options.goal + 1)
        self.rules = {}
        self.used_regions = {
            "Menu": [("Z1", True_())],
            "Z1": []
        }
        base_regions = ["Z1"]

        for action in all_actions:
            self.rules.update(action.rules(self.options))

        if self.goal != "Z1":
            self.used_regions["Z1"] = [("Z2", self.rules["Z1 - Start Journey"])]
            self.used_regions["Z2"] = []
            base_regions.append("Z2")
            if self.goal != "Z2":
                self.used_regions["Z2"] = [("Z3", self.rules["Z2 - Continue On"])]
                self.used_regions["Z3"] = []
                base_regions.append("Z3")
                if self.goal != "Z3":
                    self.used_regions["Z3"] = [("Z4", self.rules["Z3 - Start Trek"])]
                    self.used_regions["Z4"] = []
                    base_regions.append("Z4")

        for action in all_actions:
            if action.region[-1] <= self.goal[-1]:
                for new_region_name, region_data in action.regions(self.options).items():
                    if not region_data["multi_region"]:
                        self.used_regions[new_region_name] = []
                        self.used_regions[action.region].append((new_region_name, region_data["rule"]))
                    else:
                        for region in base_regions:
                            self.used_regions[region + "_" + new_region_name] = []
                            self.used_regions[region].append((region + "_" + new_region_name, region_data["rule"]))

        for option in self.options.__annotations__:
            option_value = getattr(self.options, option)
            if option_value.value == -1:
                option_value.value = self.options.__annotations__[option].defaults[self.options.goal]

        # This might not need to exist, it just did on the apworld i based this off.
        self.all_items = [item.copy() for item in all_items]

        self.multiworld.push_precollected(self.create_item("Z1 - Wander"))
        self.multiworld.push_precollected(self.create_item("Z1 - Mana Pot - Search"))

        # TODO: Refactor Actions.py to also export a list of limited actions to use here
        if not self.options.item_search:
            for action in ["Z1 - Lock", "Z1 - Short Quest", "Z1 - Long Quest", "Z2 - Wild Mana", "Z2 - Herb", "Z2 - Hunt", "Z3 - Gamble", "Z4 - Mana Geyser", "Z4 - Soulstone", "Z4 - Artifact"]:
                self.multiworld.push_precollected(self.create_item(f"{action} - Search"))

        if not self.options.item_shop:
            if self.options.location_z1_shop > 0:
                self.multiworld.push_precollected(self.create_item("Z1 - AP Shop"))
            if self.options.location_z3_shop > 0:
                self.multiworld.push_precollected(self.create_item("Z3 - AP Shop"))

        self.multiworld.local_early_items[self.player]["Z1 - Buy Mana"] = 1
        if self.options.logic_big_sphere1:
            self.multiworld.early_items[self.player]["Z1 - Meet People"] = 1
            self.multiworld.early_items[self.player]["Z1 - Investigate"] = 1
        # Help the rando a bit, Meet People is the only item that gets you anything else in Z1.
        if self.options.logic_vanilla > 1:
            self.multiworld.early_items[self.player]["Z1 - Meet People"] = 1
            self.multiworld.early_items[self.player]["Z1 - Mana Pot"] = 8

        self.used_locations = [(name, region) for action in all_actions for (name, region) in action.included_locations(self.options) if region in self.used_regions]
        self.used_items = [name for action in all_actions for name in action.included_items(self.options) if action.region[-1] <= self.goal[-1]]
        item_count = reduce(lambda a, item: a + item["count"], self.used_items, 0)

        if len(self.used_locations) < item_count:
            raise OptionError(f"Idle Loops Player {self.player_name} Error: More items than locations.")

    def get_filler_item_names(self, count) -> List[str]:

        filler_weight = (100 - self.options.filler_nothing) / 100
        included_filler_count = self.options.filler_extra_mana_pot + self.options.filler_starting_mana + self.options.filler_starting_gold

        if included_filler_count == 0:
            if self.options.filler_nothing == 0:
                error_during_fuzz(f"You wanted to see what would happen, with 0 filler, huh? Well, I thought of it. To answer your question there was a division by 0.")
            filler_weights = [0, 0, 0, 1]
        else:
            filler_weights = [
                self.options.filler_extra_mana_pot * filler_weight / included_filler_count,
                self.options.filler_starting_mana * filler_weight / included_filler_count,
                self.options.filler_starting_gold * filler_weight / included_filler_count,
                self.options.filler_nothing / 100
            ]

        return self.random.choices(
            ["Z1 - Mana Pot", "Filler - 50 Starting Mana", "Filler - 1 Starting Gold", "Filler - Nothing"],
            weights=filler_weights,
            k=count
        )

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        item_data = self.all_items[item_id - 1]
        return IdleLoopsItem(name, item_data["classification"], item_id, self.player)

    def create_items(self) -> None:
        items_added = 0
        # Wander and Smash Pots are precollected so should are skipped here with [2::]
        # There's a better way to do this
        for item in self.used_items:
            for _ in range(item["count"]):
                new_item = self.create_item(item["name"])
                self.multiworld.itempool.append(new_item)
                items_added += 1
        filler_count = len(self.used_locations) - items_added
        names = self.get_filler_item_names(filler_count)
        for name in names:
            new_item = self.create_item(name)
            self.multiworld.itempool.append(new_item)

    def create_regions(self) -> None:
        regions = {}
        for region_name in self.used_regions:
            region = Region(region_name, self.player, self.multiworld)
            self.multiworld.regions.append(region)
            regions[region_name] = region

        for location, region_name in self.used_locations:
            regions[region_name].add_locations({location: location_name_to_id[location]})

    def set_rules(self) -> None:
        multiworld = self.multiworld
        for region in multiworld.get_regions(self.player):
            for loc in region.locations:
                if loc.name in self.rules:
                    self.set_rule(loc, self.rules[loc.name])

        for region_name, region_data in self.used_regions.items():
            for connection, rule in region_data:
                self.create_entrance(self.get_region(region_name), self.get_region(connection), rule)

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
            "location_z1_shop",
            "z1_shop_min",
            "z1_shop_max",
            "location_z3_shop",
            "z3_shop_min",
            "z3_shop_max",
            "game_speed",
            "stat_exp_mult",
            "skill_exp_mult",
            "bonus",
            # "soul_link",
            "mod_ui_crime"
        )
