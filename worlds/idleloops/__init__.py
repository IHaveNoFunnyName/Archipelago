from functools import reduce
import itertools

from Options import OptionError
from logging import warning


from .Options import IdleLoopsOptions, option_groups
from .Actions import IdleLoopsLocation, all_actions, all_items, location_name_to_id, item_to_id, IdleLoopsItem
from typing import Dict, Any, List
from BaseClasses import ItemClassification, MultiWorld, Region, Item, Tutorial
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
    option_groups = option_groups

    bug_report_page = "https://github.com/IHaveNoFunnyName/IdleLoopsAP/issues?q=is%3Aissue%20state%3Aopen%20label%3Abug%2C%22Minor%20bug%22"


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
    glitches_item_name = "Hard"

    def handle_options(self) -> None:
        if self.options.item_pots and (self.options.filler_nothing == 100 or (not self.options.filler_extra_mana_pot and not self.options.filler_starting_mana and not self.options.filler_starting_gold)):
            raise OptionError(f"Idle Loops Player {self.player_name} Error: All basic sources of mana (Mana Pots, Starting Mana, Starting Gold) disabled")
        if self.options.item_search and not self.options.location_progress:
            warning(f"Idle Loops Player {self.player_name} Recommendation: \"Items: Search\" is intended to break up the Progress Bar and Lootable rewards for each Progress action, without \"Locations: Progress Bars\" it doesn't need to do this and so can be disabled.")
        if self.options.logic_vanilla_all:
            warning(f"Idle Loops Player {self.player_name} Warning: \"Logic: Vanilla Requirements All\" enabled. This option works but is unsupported.")
        if self.options.goal < 3 and self.options.location_skill > IdleLoopsOptions.__annotations__["location_skill"].defaults[self.options.goal + 1]:
            warning(f"Idle Loops Player {self.player_name} Warning: \"Locations: Skill\" set above what is reasonable for a Z{self.options.goal + 1} goal.")
        if self.options.goal < 3 and self.options.location_fight > IdleLoopsOptions.__annotations__["location_fight"].defaults[self.options.goal + 1]:
            warning(f"Idle Loops Player {self.player_name} Warning: \"Locations: Fight\" set above what is reasonable for a Z{self.options.goal + 1} goal.")
        if self.options.goal < 3 and self.options.location_heal > IdleLoopsOptions.__annotations__["location_heal"].defaults[self.options.goal + 1]:
            warning(f"Idle Loops Player {self.player_name} Warning: \"Locations: Heal\" set above what is reasonable for a Z{self.options.goal + 1} goal.")
        if self.options.goal == 0 and self.options.logic_z2_mana > 0:
            self.options.logic_z2_mana.value = 0

        # Set defaults for -1 options
        for option in self.options.__annotations__:
            option_value = getattr(self.options, option)
            if option_value.value == -1:
                option_value.value = self.options.__annotations__[option].defaults[self.options.goal]

        # x10 the option - option is Nx total mult, items are +0.1x
        for option in ['item_game_speed', 'item_exp_mult']:
            option_value = getattr(self.options, option)
            option_value.value = max(option_value.value - 1, 0) * 10

        self.options.logic_fight_heal.value = 1 if self.multiworld.random.randint(0, 99) < self.options.logic_fight_heal.value else 0

    def generate_early(self) -> None:

        if self.options.logic_vanilla_all:
            self.options.logic_vanilla.value = 1

        self.options.local_items.value.add("Death")

        self.handle_options()
        self.goal = "Z" + str(self.options.goal + 1)

        self.rules = {}
        for action in all_actions:
            self.rules.update(action.rules(self.options))
        # Called "used_regions" because that's what it used to be
        # But I want to use "CanReachRegion" all over the place
        # so all regions need to exist all the time, just empty.
        self.used_regions = {
            "Menu": [("Z1", True_())],
            "Z1": [("Z2", self.rules["Z1 - Start Journey"])],
            "Z2": [("Z3", self.rules["Z2 - Continue On"])],
            "Z3": [("Z4", self.rules["Z3 - Start Trek"])],
            "Z4": []
        }
        base_regions = ["Z1", "Z2", "Z3", "Z4"]

        for action in all_actions:
            for new_region_name, region_data in action.regions(self.options).items():
                if not region_data["multi_region"]:
                    self.used_regions[new_region_name] = []
                    self.used_regions[action.region].append((new_region_name, region_data["rule"]))
                else:
                    for region in base_regions:
                        self.used_regions[region + " " + new_region_name] = []
                        self.used_regions[region].append((region + " " + new_region_name, region_data["rule"]))

        # This might not need to exist, it just did on the apworld i based this off.
        self.all_items = [item.copy() for item in all_items]

        self.multiworld.push_precollected(self.create_item("Z1 - Wander"))
        self.multiworld.push_precollected(self.create_item("Z1 - Mana Pot - Search"))

        # TODO: Refactor Actions.py to also export a list of limited actions to use here
        if not self.options.item_search:
            for action in ["Z1 - Lock", "Z1 - Short Quest", "Z1 - Long Quest", "Z2 - Wild Mana", "Z2 - Herb", "Z2 - Hunt", "Z3 - Gamble", "Z4 - Mana Geyser", "Z4 - Soulstone", "Z4 - Artifact"]:
                self.multiworld.push_precollected(self.create_item(f"{action} - Search"))

        if not self.options.item_shop:
            if self.options.location_z1_shop or self.options.location_z1_shop_expensive:
                self.multiworld.push_precollected(self.create_item("Z1 - AP Shop"))
            if self.options.location_z3_shop:
                self.multiworld.push_precollected(self.create_item("Z3 - AP Shop"))

        self.multiworld.local_early_items[self.player]["Z1 - Buy Mana"] = 1

        # Help the rando a bit, Meet People is the only item that gets you anything else in Z1.
        if self.options.logic_vanilla_all:
            self.multiworld.early_items[self.player]["Z1 - Meet People"] = 1
            self.multiworld.early_items[self.player]["Z1 - Mana Pot"] = 8

        self.used_locations = [(name, region) for action in all_actions for (name, region) in action.included_locations(self.options) if action.region[-1] <= self.goal[-1]]
        self.used_items = [name for action in all_actions for name in action.included_items(self.options) if action.region[-1] <= self.goal[-1]]

        item_count = reduce(lambda a, item: a + item["count"], self.used_items, 0)
        location_count = len(self.used_locations)

        if location_count < item_count:
            raise OptionError(f"Idle Loops Player {self.player_name} Error: More items than locations.")
        if location_count - item_count < (50 - ((1 - self.options.item_pots) * 50)) / ((1 - self.options.filler_nothing / 100) + 0.001):
            raise OptionError(f"Idle Loops Player {self.player_name} Error: Less than 50 Pots (+Starting Mana/Gold) in the item pool. Lower \"Filler: Nothing\", enabling more Locations or decreasing items like \"Item: Game Speed\".")

    def get_filler_item_names(self, count) -> List[str]:

        filler_weight = (100 - self.options.filler_nothing) / 100
        included_filler_count = self.options.filler_extra_mana_pot + self.options.filler_starting_mana + self.options.filler_starting_gold

        if included_filler_count == 0:
            if self.options.filler_nothing == 0:
                warning(f"You wanted to see what would happen, with 0 filler, huh? Well, I thought of it. To answer your question there was a division by 0.")
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

    def create_item(self, name: str, classification=False) -> Item:
        item_id = self.item_name_to_id[name]
        if not classification:
            item_data = self.all_items[item_id - 1]
            classification = item_data["classification"]
            # I don't understand why this is needed, we're not calling create_item without a classification
            # for an item with an iterable classification. idgi
            # i'm not happy with this implimentation for multi-classification items at all

            # Still confused at the above but this is needed by UT so
            # I think UT creates many many items so the iterator runs out, just make a progression one in that case
            try:
                if isinstance(classification, itertools.chain):
                    classification = classification.__next__()
            except Exception:
                classification = ItemClassification.progression
        return IdleLoopsItem(name, classification, item_id, self.player)

    def create_items(self) -> None:

        placed = {}
        placed_anywhere = {}
        # Run our own little rando just for Z1 required items
        # Helps with fill errors as the rando doesn't have to place all these items in early spheres
        # Also/mainly makes the game more fun
        # As running pure rando logic seems to *love* "get lots of gold and haggle 4 times" over Heal/Fight
        z1 = self.get_region("Z1")
        exits = [self.get_region(exit) for exit, _ in self.used_regions["Z1"] if not exit.startswith("Z2")]
        z1_regions: List[Region] = [z1] + exits
        z1_locations: List[IdleLoopsLocation] = [location for region in z1_regions for location in region.get_locations()]

        required_items = ["Z1 - Start Journey", "Z1 - Buy Supplies"]
        if self.goal != "Z1" and (self.options.logic_fight_heal or self.options.logic_vanilla):
            required_items += self.random.choice([["Z1 - Haggle", "Z1 - Heal The Sick", "Z1 - Mage Lessons"], ["Z1 - Fight Monsters", "Z1 - Warrior Lessons"]])
        if self.options.logic_haggle:
            # It doesn't matter if this is added twice, it ignores ones it already placed
            required_items.append("Z1 - Haggle")
        if self.options.logic_glasses:
            required_items.append("Z1 - Buy Glasses")

        meet_requirement = self.random.choice(["Z1 - Meet People", "Z1 - Throw Party"])

        # If an item name is in `placed`, future items cannot be placed in any location it unlocks. (This isn't perfect, it should be "any item it requires", but that would require recursion and brain hurty)
        # I say that but i'm sure the algorithm is quite elegant and easy to understand if i see it.
        # By default this is locations that start with its name,
        # this dict is for exceptions
        excluded_rules = {
            "Z1 - Mage Lessons": ["Magic", "Z1 - Heal The Sick", "Z1 - Small Dungeon"] if self.options.logic_vanilla else ["Magic", "Z1 - Heal The Sick"],
            "Z1 - Warrior Lessons": ["Combat", "Z1 - Fight Monsters", "Z1 - Small Dungeon", "Z1 - Haggle"] if self.options.logic_vanilla else ["Combat", "Z1 - Fight Monsters"],
            "Z1 - Buy Glasses": ["Z1 - Buy Glasses",
                                 "Z1 - Wander - 6", "Z1 - Wander - 7", "Z1 - Wander - 8", "Z1 - Wander - 9", "Z1 - Wander - 100",
                                 # Sorry mana pot 3 and 4, you will never have glasses
                                 "Z1 - Mana Pot - #3", "Z1 - Mana Pot - #4", "Z1 - Mana Pot - #50", "Z1 - Mana Pot - #26", "Z1 - Mana Pot - #27", "Z1 - Mana Pot - #28", "Z1 - Mana Pot - #29",
                                 "Z1 - Lock - #6", "Z1 - Lock - #7", "Z1 - Lock - #8", "Z1 - Lock - #9", "Z1 - Lock - #10"] if self.options.logic_glasses else ["Z1 - Buy Glasses"],
            "Z1 - Investigate": ["Z1 - Investigate", "Z1 - Long Quest"],
            "Z1 - Meet People": ["Z1 - Meet People", "Z1 - Short Quest"],
            "Z1 - Throw Party": ["Z1 - Throw Party", "Z1 - Meet People - ", "Z1 - Short Quest"],
            "Z1 - Lock - Search": ["Z1 - Lock"],
            "Z1 - Short Quest - Search": ["Z1 - Short Quest"],
            "Z1 - Long Quest - Search": ["Z1 - Long Quest"],
        }

        # Items to append to required_items when a location starting with it is locked.
        # Locations not in this dict have the same dependent as their name
        dependents = {
            "Z1 - Small Dungeon": "Z1 - Small Dungeon",
            "Z1 - Fight Monsters": ["Z1 - Fight Monsters", "Z1 - Warrior Lessons"],
            "Z1 - Heal The Sick": ["Z1 - Heal The Sick", "Z1 - Mage Lessons"],
            "Magic": "Z1 - Mage Lessons",
            "Combat": "Z1 - Warrior Lessons",
            "Z1 - AP Shop": "Z1 - AP Shop" if self.options.item_shop else [],
            "Z1 - Investigate": "Z1 - Investigate",
            "Z1 - Long Quest": ["Z1 - Investigate", "Z1 - Long Quest - Search"] if self.options.item_search else ["Z1 - Investigate"],
            "Z1 - Wander": [],
            "Z1 - Smash Pot": [],
        }
        if self.options.logic_glasses:
            dependents_glasses = {
                "Z1 - Wander - 6": "Z1 - Buy Glasses",
                "Z1 - Wander - 7": "Z1 - Buy Glasses",
                "Z1 - Wander - 8": "Z1 - Buy Glasses",
                "Z1 - Wander - 9": "Z1 - Buy Glasses",
                "Z1 - Wander - 100": "Z1 - Buy Glasses",
                "Z1 - Mana Pot - #3": "Z1 - Buy Glasses",
                "Z1 - Mana Pot - #4": "Z1 - Buy Glasses",
                "Z1 - Mana Pot - #50": "Z1 - Buy Glasses",
                "Z1 - Mana Pot - #26": "Z1 - Buy Glasses",
                "Z1 - Mana Pot - #27": "Z1 - Buy Glasses",
                "Z1 - Mana Pot - #28": "Z1 - Buy Glasses",
                "Z1 - Mana Pot - #29": "Z1 - Buy Glasses",
                "Z1 - Lock - #6": ["Z1 - Buy Glasses", "Z1 - Lock - Search"] if self.options.item_search else "Z1 - Buy Glasses",
                "Z1 - Lock - #7": ["Z1 - Buy Glasses", "Z1 - Lock - Search"] if self.options.item_search else "Z1 - Buy Glasses",
                "Z1 - Lock - #8": ["Z1 - Buy Glasses", "Z1 - Lock - Search"] if self.options.item_search else "Z1 - Buy Glasses",
                "Z1 - Lock - #9": ["Z1 - Buy Glasses", "Z1 - Lock - Search"] if self.options.item_search else "Z1 - Buy Glasses",
                "Z1 - Lock - #10": ["Z1 - Buy Glasses", "Z1 - Lock - Search"] if self.options.item_search else "Z1 - Buy Glasses",
            }
            dependents.update(dependents_glasses)

        if self.options.logic_party:
            dependents_party = {
                "Z1 - Wander - 6": "Z1 - Throw Party",
                "Z1 - Wander - 7": "Z1 - Throw Party",
                "Z1 - Wander - 8": "Z1 - Throw Party",
                "Z1 - Wander - 9": "Z1 - Throw Party",
                "Z1 - Wander - 100": "Z1 - Throw Party",
                "Z1 - Short Quest - #1": "Z1 - Throw Party",
                "Z1 - Short Quest - #20": "Z1 - Throw Party",
            }
            dependents.update(dependents_party)

        # These are checked in order, so this makes it see optional dependencies first
        dependents.update({
            "Z1 - Lock": "Z1 - Lock - Search" if self.options.item_search else [],
            "Z1 - Meet People": meet_requirement,
            "Z1 - Short Quest": [meet_requirement, "Z1 - Short Quest - Search"] if self.options.item_search else [meet_requirement],
        })

        while len(required_items):
            if required_items[0] not in placed_anywhere:
                # Equal chance to put it in any players world (Well, weighted by total locations).
                if self.random.random() < (len(self.used_locations) / len(self.multiworld.get_locations())):
                    # Local

                    while True:
                        location = self.random.choice(z1_locations)
                        if not location.locked and all([not location.name.startswith(y) for x in list(placed_anywhere.keys()) + [required_items[0]] for y in excluded_rules.get(x, [x])]):
                            break
                    placed[required_items[0]] = 1
                    placed_anywhere[required_items[0]] = 1
                    location.place_locked_item(self.create_item(required_items[0]))

                    # Our rando is way worse than the AP rando, so only place dependents too when the restrictive start doesn't need help
                    if self.goal != "Z1":
                        for dependent in dependents:
                            if location.name.startswith(dependent):
                                next = dependents[dependent]
                                required_items += next if isinstance(next, list) else [next]
                                break

                else:
                    # Non-local

                    # We will only place one of each item
                    self.multiworld.early_items[self.player][required_items[0]] = 1
                    placed_anywhere[required_items[0]] = 1
            required_items.pop(0)

        items_added = 0
        for item in self.used_items:
            count = item["count"] - 1 if item["name"] in placed else item["count"]
            classification = item["classification"]
            # Dumb code duplication
            if isinstance(classification, itertools.chain):
                classification = classification.__iter__()
                for _ in range(count):
                    next_class = classification.__next__()
                    new_item = self.create_item(item["name"], next_class)
                    self.multiworld.itempool.append(new_item)
                    items_added += 1
            else:
                for _ in range(count):
                    new_item = self.create_item(item["name"], classification)
                    self.multiworld.itempool.append(new_item)
                    items_added += 1
        filler_count = len(self.used_locations) - len(placed) - items_added

        names = self.get_filler_item_names(filler_count)
        for name in names:
            new_item = self.create_item(name)
            self.multiworld.itempool.append(new_item)

    # Stolen and modified from https://github.com/Mysteryem/Archipelago-TCS/blob/v1.4.4/lego_star_wars_tcs/__init__.py#L743-L781
    # (Actually I lied I stole the implimentation from sa2b after searching the code base for stage_fill_hook)
    # Found on Discord
    # Sort the Item Pool so the randomiser places progression items before fillers
    # ... At least that's what I thought, but according to the github link above, this would make it put filler items first.
    # But this way literally halves fill errors and the other doesn't, so, shrug? The lego star wars one is wrong?
    @classmethod
    def stage_fill_hook(cls, multiworld: MultiWorld, progitempool: list[Item], usefulitempool, filleritempool, fill_locations) -> None:
        if multiworld.get_game_players(cls.game):
            progitempool.sort(key=lambda item: 1 if item.game == cls.game and item.classification in (ItemClassification.progression_deprioritized, ItemClassification.progression_deprioritized_skip_balancing) else 0)

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
            for loc in region.get_locations():
                if loc.name in self.rules:
                    self.set_rule(loc, self.rules[loc.name])

        for region_name, region_data in self.used_regions.items():
            for connection, rule in region_data:
                self.create_entrance(self.get_region(region_name), self.get_region(connection), rule)
        completion_rule = self.rules["Z1 - Start Journey"]
        if self.goal != "Z1":
            completion_rule &= self.rules["Z2 - Continue On"]
            if self.goal != "Z2":
                completion_rule &= self.rules["Z3 - Start Trek"]
                if self.goal != "Z3":
                    completion_rule &= self.rules["Z4 - Face Judgement"]
        self.set_completion_rule(completion_rule)

    def fill_slot_data(self) -> Dict[str, Any]:
        data = self.options.as_dict(
            "death_link",
            "goal",
            "logic_vanilla",
            "logic_vanilla_all",
            "z1_shop_expensive_max",
            "game_speed",
            "stat_exp_mult",
            "skill_exp_mult",
            "bonus",
            # "soul_link",
            "mod_ui_crime",
            "mod_color"
        )
        data["version"] = self.world_version.as_simple_string()
        return data
