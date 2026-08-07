from __future__ import annotations
import json

from os import name
from typing import Dict, List, Literal, NamedTuple, Optional, TypedDict, Tuple
from bisect import bisect_left

from BaseClasses import ItemClassification, Location, Item
from rule_builder.rules import Has, HasAll, HasFromList, True_, Rule

from .Options import IdleLoopsOptions, LocationProgress
from .Rules import HasIfOptionManaReduction, IfOption, rules, HasIfOptionVanillaSkills, HasIfOptionVanillaAll, HasMana, JourneyRule

# This does nothing, just allows me to in code disambiguate when i'm using
# the class: for grabbing static max/min/etc values
# vs
# an instance: getting actual user option values
IdleLoopsOptionsClass = IdleLoopsOptions


class IdleLoopsLocation(Location):
    game = "Idle Loops"


class IdleLoopsItem(Item):
    game = "Idle Loops"


location_id = 1
location_name_to_id = {}
item_id = 1
item_to_id = {}

all_locations = []
all_items = []


# Considering how tightly coupled Loctaions, Items and Rules are in this game, it makes sense to see them as Actions that generate said Locations, Items and Rules.
class Action:
    """By default generates a single Location and Item, with a rule that requires the Item to complete the Location.
    And an option to add more Rules.

    This can be extended with Mixins, but if you're reading this you kinda already know that you have eyes."""

    # I don't know enough about python's type hinting to get this to return something that the IDE can pick up on all kwargs with
    # Or rather, i didn't even try, that's more accurate
    def __new__(self, *args: type) -> _Action:
        name = "_".join([x.__name__ for x in args])
        return type(name, args + (_Action,), {})


class RegionData(TypedDict):
    rule: Rule
    multi_region: bool


class _Action:
    def __init__(self, zone: str, name: str, internal_name: str = None, classification: ItemClassification = ItemClassification.progression, rule: Rule = None, full_rule: Rule = None, base_count: int = 1):
        self.zone = zone
        self.region = "Z1"
        self.name = name
        self.internal_name = name if internal_name is None else internal_name
        self.classification = classification
        self.rule = rule
        self.full_rule = full_rule
        self.base_count = base_count

    def base_location_list(self) -> List[str]:
        return [self.zone + " - " + self.name]

    def location_list(self) -> List[str]:
        return self.base_location_list()

    def all_locations(self, location_id, location_name_to_id) -> Tuple[List[str], int]:
        output = []
        for name in self.location_list():
            location_name_to_id[name] = location_id
            output.append(name)
            location_id += 1
        return (output, location_id)

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, str]]:
        """
        Returns a list of (location ID, region).
        """
        return [(name, self.region) for name in self.location_list()]

    def base_rule(self) -> Rule:
        return Has(self.unlock_item_name())

    def rules(self, options: IdleLoopsOptions) -> Dict[str, callable]:
        rule = self.base_rule()
        if self.full_rule is not None:
            rule = self.full_rule
        else:
            if self.rule is not None:
                rule = rule & self.rule
        return {name: rule for name in self.location_list()}

    def regions(self, options: IdleLoopsOptions) -> Dict[str, RegionData]:
        """Used in place of rules if the Action has multiple Locations (and the same rule applies to all), to not calculate the rule each location."""
        return {}

    def unlock_item_name(self) -> str:
        """
        I can't think of a better function name, i mean the name of the item that is required to complete the locations for this Action.
        This is a function and not a property solely so i can add this heredoc
        """
        return f"{self.zone} - {self.name}"

    def base_item_list(self) -> List[str]:
        return [{
            "name": self.unlock_item_name(),
            "classification": self.classification,
            "count": self.base_count
        }]

    def extra_items(self) -> List[str]:
        return []

    def item_list(self) -> List[str]:
        return self.base_item_list() + self.extra_items()

    def all_items(self, item_id, item_to_id) -> Tuple[List[str], int]:
        items = self.item_list()
        output = []
        for item in items:
            item_to_id[item["name"]] = item_id
            output.append(item)
            item_id += 1
        return (output, item_id)

    def included_items(self, options: IdleLoopsOptions) -> List[int]:
        return self.item_list()

    def name_map(self, action_map: Dict[str, str], skill_map: Dict[str, str]) -> None:
        action_map[self.name] = self.internal_name


class Start():
    """Mixin that removes the base rule and doesn't add it's unlock item to the pool (with the intention of it being precollected), basically "This is Sphere 1"."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_count = 0

    def base_rule(self) -> Rule:
        return True_()


class Region():
    """Mixin to put all its locations into a region, with one rule for the lot.

    Added kwargs:

    multi_region: bool = False: Creates one region branching off the Action's .region. True: Creates a region branching off each zone (for Actions that span locations across zones) (defaults to False)."""

    def __init__(self, multi_region: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.multi_region = multi_region

    def rules(self, options: IdleLoopsOptions) -> Dict[str, Rule]:
        return {}

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, str]]:
        return [(name, self.name) for name in self.location_list()]

    def regions(self, options: IdleLoopsOptions) -> Dict[str, RegionData]:
        output = {}
        rule = self.base_rule()
        if self.full_rule is not None:
            rule = self.full_rule
        else:
            if self.rule is not None:
                rule = rule & self.rule
        output[self.name] = {"rule": rule, "multi_region": self.multi_region}
        base_rule = rule
        if hasattr(self, "add_rules"):
            for add_rule in self.add_rules:
                if add_rule.type == 'and':
                    rule &= add_rule.rule
                elif add_rule.type == 'or':
                    rule |= add_rule.rule
                elif add_rule.type == 'full':
                    rule = add_rule.rule
                elif add_rule.type == 'full_add':
                    rule = base_rule & add_rule.rule
                output[self.name + "_" + add_rule.name] = {"rule": rule, "multi_region": self.multi_region}
        return output


class Progress(Region):
    """Mixin for Actions with a progress bar, adds locations throughout completion (if that option is enabled)."""
    progress_locations = ["1", "5", "10", "15", "20", "25", "30", "40", "50", "60", "70", "80", "90", "95", "99", "100"]

    def locations_progress_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - {progress}%" for progress in self.progress_locations]

    def location_list(self) -> List[str]:
        return self.base_location_list() + self.locations_progress_list()

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        list = self.locations_progress_list() if options.location_progress else self.base_location_list()
        output = []
        for i, name in enumerate(list):
            if hasattr(self, "add_rules"):
                region = ""
                for add_rule in self.add_rules:
                    if i >= add_rule.at:
                        region = "_" + add_rule.name
                        break
                output.append((name, self.name + region))
            else:
                output.append((name, self.name))
        return output


class LimitedLocations():
    """This Mixin was split off from Limited, as Shop worked like the locations part of Limited without the items.

    Added kwargs:

    count: int = The number of locations to add."""

    def __init__(self, count: int, **kwargs):
        super().__init__(**kwargs)
        self.count = count

    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - #{i}" for i in range(1, self.count + 1)]


class Limited(LimitedLocations, Region):
    """Mixin that adds #x locations and items for actions, and a required " - Search" item (if that option is enabled)

    Added kwargs:

    count: int = The max number of locations/items to add.

    items: int = The max number of items to add (defaults to count).

    option: str = An attr of the option class that controls how many locations/items to include in a game."""

    def __init__(self, count: int, items: int = None, option: str = None, lootable_classification: ItemClassification = ItemClassification.progression, **kwargs):
        super().__init__(count=count, **kwargs)
        self.lootable_classification = lootable_classification
        self.items = items if items is not None else count
        self.option = option

    def unlock_item_name(self) -> str:
        return f"{self.zone} - {self.name} - Search"

    def extra_items(self, options: IdleLoopsOptions = None) -> List[str]:
        # Bit unintuitive but at the time of writing the only is a toggle that removes the pots when true.
        option_value = getattr(options, "item_" + self.option) if self.option and options is not None else None
        if option_value:
            count = 0
        else:
            count = self.items
        return [{
            "name": f"{self.zone} - {self.name}",
            "classification": self.lootable_classification,
            "count": count
        }]

    def included_items(self, options: IdleLoopsOptions) -> List[int]:
        if options.item_search:
            return self.item_list()
        else:
            return self.extra_items(options)

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        output = []
        for i, name in enumerate(self.location_list(), 1):
            if hasattr(self, "add_rules"):
                region = ""
                for add_rule in self.add_rules:
                    if i >= add_rule.at:
                        region = "_" + add_rule.name
                        break
                output.append((name, self.name + region))
            else:
                output.append((name, self.name))
        return output


class Batched(Limited):
    """Mixin that works like Limited but can optionally batch its locations/items.

    Added kwargs:

    All the Limited kwargs

    batch_size: int = The batch size. What more do you want from me that name is the definition of self documenting code. (defaults to 10)."""

    def __init__(self, batch_size: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.batch_size = batch_size

    def batched_location_list(self) -> List[str]:
        return [f"{self.zone} - x{self.batch_size} {self.name} - #{i}" for i in range(1, ((self.count + self.batch_size - 1) // self.batch_size) + 1)]

    def location_list(self) -> List[str]:
        return super().location_list() + self.batched_location_list()

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        if options.batch_z2:
            output = []
            for i, name in enumerate(self.batched_location_list(), 1):
                if hasattr(self, "add_rules"):
                    region = ""
                    for add_rule in self.add_rules:
                        if i * self.batch_size >= add_rule.at:
                            region = "_" + add_rule.name
                            break
                    output.append((name, self.name + region))
                else:
                    output.append((name, self.name))
            return output
        else:
            return super().included_locations(options)

    def batched_items(self) -> List[str]:
        return [{
            "name": f"{self.zone} - x{self.batch_size} {self.name}",
            "classification": self.lootable_classification,
            "count": self.items // self.batch_size
        }]

    def extra_items(self) -> List[str]:
        return super().extra_items() + self.batched_items()

    def included_items(self, options: IdleLoopsOptions) -> List[int]:
        output = []
        if options.item_search:
            output += self.base_item_list()
        if options.batch_z2:
            output += self.batched_items()
        else:
            output += super().extra_items()
        return output


class Shop(LimitedLocations):
    """Mixin that adds #x locations with ramping costs with equal steps (rounded down) between min and max

    Added kwargs:

    option: str = An attr of the option class that controls how many locations to include in a game and min/max gold cost."""

    def __init__(self, min: int, option: str, after_z1: Rule = None, max: Optional[int] = None, **kwargs):
        self.option = option
        self.min = min
        self.max = max
        kwargs["count"] = 10
        super().__init__(**kwargs)
        self.after_z1 = True_() if after_z1 is None else after_z1

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        # Sort into regions based on reasonable value of PM, manually gathered
        if not getattr(options, "location_" + self.option):
            return []
        min_ = self.min
        if min_ <= 99:
            return [(f"{self.zone} - {self.name} - #{i}", self.region) for i in range(1, 11)]
        num = 10
        max_ = self.max if self.max else getattr(options, self.option + "_max")
        current = min_ + 1
        step = (max_ - min_) / (num - 1)
        output = []
        for i in range(1, 11):
            region = bisect_left([0, 0, 399, 599], int((current // 10) * 10))
            current += step
            if region > options.goal:
                region = int(options.goal) + 1
            if region < int(self.region[-1]):
                region = int(self.region[-1])
            output.append((f"{self.zone} - {self.name} - #{i}", "Z" + str(region)))
        return output

    def included_items(self, options: IdleLoopsOptions) -> List[int]:
        return [
            {
                "name": f"{self.zone} - {self.name}",
                "classification": self.classification,
                "count": 1
            }
        ] if options.item_shop and getattr(options, "location_" + self.option) else []

    def rules(self, options: IdleLoopsOptions) -> Dict[str, callable]:
        # No mana logic after Z1
        min_ = self.min
        if min_ > 99:
            return super().rules(options)
        num = 10
        max_ = self.max if self.max else getattr(options, self.option + "_max")
        current = min_ + 1
        step = (max_ - min_) / (num - 1)

        output = {}
        for name in self.location_list():
            rule = HasMana(int(((current // 10) * 500) + 200))
            current += step
            output[name] = self.base_rule() & rule & (self.rule if self.rule is not None else True_())
        return output


class Multipart():
    """Mixin for Actions that can be completed multiple times, with a location each completion.
    It's a bit of a misnomer but all of those actions (Well, up to Z4) are Multipart in game, so...

    Added kwargs:

    option: str = An attr of the option class that controls how many locations to include in a game."""

    def __init__(self, option: str = None, **kwargs):
        super().__init__(**kwargs)
        self.option = option
        self.location_numbers = list(range(1, IdleLoopsOptionsClass.__annotations__["location_" + self.option].range_end + 1)) if option else []

    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - Completion #{i}" for i in self.location_numbers]

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        if not self.option or not options.location_multipart_toggle:
            return []
        region = int(self.region[-1])
        locations = []
        for location in self.location_numbers:
            if location > getattr(options, "location_" + self.option):
                break
            if location > IdleLoopsOptionsClass.__annotations__["location_" + self.option].defaults[region - 1] and region <= options.goal:
                region += 1
            locations.append((f"{self.zone} - {self.name} - Completion #{location}", "Z" + str(region)))
        return locations


class AddRuleTuple(NamedTuple):
    name: str
    at: int
    rule: Rule
    type: Literal['and', 'or', 'full', 'full_add'] = 'and'


class AddRule():
    """Mixin that adds a second rule part way through its locations

    Properties of add_rules:

    name: str = The name of the rule, used to create a new region for it in a hacky way (i.e. Implemented in Region instead)

    at: int = The first location to add the rule to.

    rule: Rule = Self explanatory.

    type: Operation, self explanatory except 'full_add' which overwrites previous add_rules but *not* the base rule."""

    def __init__(self, add_rules: List[AddRuleTuple] | AddRuleTuple, **kwargs):
        super().__init__(**kwargs)
        self.add_rules = add_rules if isinstance(add_rules, list) else [add_rules]

    def rules(self, options: IdleLoopsOptions) -> Dict[str, callable]:
        output = {}
        for i, location in enumerate(self.location_list(), 1):
            rule = self.base_rule() & (self.rule if self.rule is not None else True_())
            base_rule = rule
            for add_rule in self.add_rules:
                if i >= add_rule.at:
                    if add_rule.type == 'and':
                        rule &= add_rule.rule
                    elif add_rule.type == 'or':
                        rule |= add_rule.rule
                    elif add_rule.type == 'full':
                        rule = add_rule.rule
                    elif add_rule.type == 'full_add':
                        rule = base_rule & add_rule.rule
            output.update({location: rule})
        return output


class Skill(Region):
    """Mixin that adds a bunch of locations for a Skill (Or Buff), and the action that unlocks it. It made less sense to keep them separate.
    Maybe swapping it so name is the action name like all other actions and then skill_name in addition makes more sense, but whatever.
    Oh wait, but then i'd have to rename them for buffs heh.

    Added kwargs:

    action_name: str = Like name normally

    internal_action_name: str = Like internal_name normally

    option: str = An attr of the option class that controls both the max locations and how many to include in a game.

    every: int = Put a location every x levels. Probably will replace this behaviour in later versions as in later zones you can get obscene levels
    So the gaps will have to increase over time."""

    def __init__(self, action_name: str = None, internal_action_name: str = None, option: str = "skill", every: int = 10, **kwargs):
        super().__init__(multi_region=True, **kwargs)
        self.action_name = action_name if action_name is not None else self.name
        self.internal_action_name = internal_action_name if internal_action_name is not None else self.action_name
        self.option = option
        self.option_toggle = "location_skill_toggle"
        self.location_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] + list(range(10 + every, IdleLoopsOptionsClass.__annotations__["location_" + self.option].range_end + 1, every))

    def unlock_item_name(self) -> str:
        return f"{self.zone} - {self.action_name}"

    def location_list(self) -> List[str]:
        return [self.unlock_item_name()] + [f"{self.name} - Level {n}" for n in self.location_numbers]

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        option_value = getattr(options, "location_" + self.option)
        if not getattr(options, self.option_toggle) or option_value == 0:
            return [(f"{self.zone} - {self.action_name}", self.region)]
        region = int(self.region[-1])

        locations = []
        for level in self.location_numbers:
            if level > option_value:
                break
            if level > IdleLoopsOptionsClass.__annotations__["location_" + self.option].defaults[region - 1] and region <= options.goal:
                region += 1
            locations.append((f"{self.name} - Level {level}", "Z" + str(region) + "_" + self.name))
        return locations

    def name_map(self, action_map: Dict[str, str], skill_map: Dict[str, str]) -> None:
        action_map[self.action_name] = self.internal_action_name
        skill_map[self.name] = self.internal_name


class Buff(Skill):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.option_toggle = "location_buff_toggle"

    def location_list(self) -> List[str]:
        return [self.unlock_item_name()] + [f"{self.name} {n}" for n in self.location_numbers]

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        option_value = getattr(options, "location_" + self.option)
        if not getattr(options, self.option_toggle) or option_value == 0:
            return [(f"{self.zone} - {self.action_name}", self.region)]
        region = int(self.region[-1])

        locations = []
        for level in self.location_numbers:
            if level > option_value:
                break
            if level > IdleLoopsOptionsClass.__annotations__["location_" + self.option].defaults[region - 1] and region <= options.goal:
                region += 1
            locations.append((f"{self.name} {level}", "Z" + str(region) + "_" + self.name))
        return locations


class Extra():
    def __init__(self, option: str = None, **kwargs):
        super().__init__(**kwargs)
        self.option = option

    def included_items(self, options: IdleLoopsOptions = None) -> List[str]:
        count = 2 if getattr(options, self.option) else 1
        return [{
            "name": self.unlock_item_name(),
            "classification": self.classification,
            "count": count
        }]


class Filler():
    """Mixin for filler items, they don't have any locations.

    Added kwargs:

    option: str = An attr of the option class that controls how many items to include in a game. Defaults to 0
    (the ones with 0 are intended to be added by the World to balance locations and items)"""

    def __init__(self, option: str = None, **kwargs):
        if "classification" not in kwargs:
            kwargs["classification"] = ItemClassification.filler
        super().__init__(zone="Filler", **kwargs)
        self.option = option

    def location_list(self) -> List[str]:
        return []

    def unlock_item_name(self) -> str:
        return f"{self.name}"

    def included_items(self, options: IdleLoopsOptions = None) -> List[str]:
        count = getattr(options, self.option) if self.option else 0
        return [{
            "name": self.name,
            "classification": self.classification,
            "count": count
        }]

    def name_map(self, action_map: Dict[str, str], skill_map: Dict[str, str]) -> None:
        pass


class Z2():
    """Puts locations into the Z2 region, requiring the rule put on the region and excluding it from games with an earlier goal."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = "Z2"


class Z3():
    """Puts locations into the Z3 region, requiring the rule put on the region and excluding it from games with an earlier goal."""

    def __init__(self, **kwargs):
        if "classification" not in kwargs:
            kwargs["classification"] = ItemClassification.progression_skip_balancing
        super().__init__(**kwargs)
        self.region = "Z3"


class Z4():
    """Puts locations into the Z4 region, requiring the rule put on the region and excluding it from games with an earlier goal."""

    def __init__(self, **kwargs):
        if "classification" not in kwargs:
            kwargs["classification"] = ItemClassification.progression_skip_balancing
        super().__init__(**kwargs)
        self.region = "Z4"


# ofc filler actions are only items but calling it actions makes it fit with the others
filler_actions = [
    Action(Filler)(name="Filler - 50 Starting Mana", classification=ItemClassification.progression_deprioritized_skip_balancing),
    Action(Filler)(name="Filler - 1 Starting Gold", classification=ItemClassification.progression_deprioritized_skip_balancing),
    # Progressive lootable acts as an extra count for limited actions, (up to their usual max, for when you don't have them capped) in rough order of usefullness/progression
    # Long Quests (up to 2) > Short Quests > Long Quests (Rest) > Locks > Wild Mana ... > n-1 > Mana Pot
    Action(Filler)(name="Progressive Lootable", option="item_progressive_lootable", classification=ItemClassification.progression),
    Action(Filler)(name="+0.1 Game Speed", option="item_game_speed", classification=ItemClassification.useful),
    Action(Filler)(name="+0.1 Exp Multiplier", option="item_exp_mult", classification=ItemClassification.useful),
    Action(Filler)(name="Filler - Nothing"),
]

# ZX Class means that action should be included if the goal is >=n, the zone arg only used for the name/display

# CanReachLocation would make a lot of these rules simpler, however as the locations would want to use most are optional
# I decided against it and just copy & pasted the relevant rules instead.
# I can't see how CanReachLocation would work, when the location exists in the id to name map
# but not in any region and without any rules set on it.
# I guess a potential answer is to use events? Register every unused location to regions as usual, but as events

all_actions: List[_Action] = [
    # Zone 1
    Action(Start, Progress, AddRule)(zone="Z1", name="Wander", add_rules=AddRuleTuple("glasses", 9, rules["Option Has Glasses"])),
    Action(Start, Limited, AddRule) (zone="Z1", name="Mana Pot", internal_name="Pots", count=50, option="pots", lootable_classification=ItemClassification.progression_deprioritized_skip_balancing, add_rules=AddRuleTuple("glasses", 26, rules["Option Has Glasses"])),
    Action(Limited, AddRule)        (zone="Z1", name="Lock", internal_name="Locks", count=10, lootable_classification=ItemClassification.progression_deprioritized_skip_balancing, add_rules=AddRuleTuple("glasses", 6, rules["Option Has Glasses"])),
    Action(Extra)                   (zone="Z1", name="Buy Glasses", internal_name="BuyGlasses", option="item_glasses",
                                     rule=(Has("Z1 - Lock") & HasMana(450) | Has("Z1 - Short Quest") & HasMana(650) | HasFromList("Z1 - Long Quest", "Progressive Lootable") & HasMana(1550)) | Has("Filler - 1 Starting Gold", 10)
                                     ),
    Action()                        (zone="Z1", name="Buy Mana", internal_name="BuyMana"),
    Action(Progress)                (zone="Z1", name="Meet People", internal_name="Met", full_rule=IfOption({"option": LocationProgress}, rules["Meet People Progress"], rules["Z1 - Meet People"])),
    Action()                        (zone="Z1", name="Train Strength", internal_name="TrainStrength", classification=ItemClassification.progression_skip_balancing, rule=HasMana(2000) & HasIfOptionVanillaAll(rules["Meet People Progress"])),
    Action(Limited)                 (zone="Z1", name="Short Quest", internal_name="SQuests", count=20, rule=rules["Meet People Progress"]),
    Action(Progress)                (zone="Z1", name="Investigate", internal_name="Secrets", full_rule=rules["Z1 - Investigate"]),
    Action(Limited)                 (zone="Z1", name="Long Quest", internal_name="LQuests", count=10, rule=rules["Z1 - Investigate"]),
    Action()                        (zone="Z1", name="Throw Party", internal_name="ThrowParty", full_rule=rules["Z1 - Throw Party"]),
    # JorneyRule works just about the same for Buy Supplies, minus the 1k mana for Start Journey but that can be left out
    # Just removed the check for Z1 - Start Journey and let the default & in rules() handle it

    Action()                        (zone="Z1", name="Buy Supplies", internal_name="BuySupplies", full_rule=JourneyRule() & HasIfOptionVanillaSkills(rules["Z1 Has Magic"] | rules["Z1 Has Combat"])),
    Action()                        (zone="Z1", name="Haggle", rule=HasFromList("Z1 - Long Quest", "Progressive Lootable", count=1) & HasIfOptionVanillaSkills(rules["Z1 Has Magic"] | rules["Z1 Has Combat"])),
    Action()                        (zone="Z1", name="Start Journey", internal_name="StartJourney", rule=JourneyRule() & HasIfOptionVanillaSkills(rules["Z1 Has Magic"] | rules["Z1 Has Combat"])),
    Action(Shop)                    (zone="Z1", name="AP Shop", internal_name="APShop", min=50, max=200, option="z1_shop"),
    Action(Z2, Shop, Start)         (zone="Z1", name="AP Shop (Expensive)", internal_name="APShopExpensive", min=300, option="z1_shop_expensive", rule=rules["Has Practical Magic"] & HasFromList("Z1 - Lock", "Z1 - Short Quest", "Z1 - Long Quest", "Progressive Lootable", count=40)),

    Action(Multipart)               (zone="Z1", name="Heal The Sick", internal_name="Heal", option="heal", rule=rules["Z1 Has Magic"] & HasMana(2500)),
    Action(AddRule, Multipart)      (zone="Z1", name="Fight Monsters", internal_name="Fight", option="fight", rule=rules["Z1 Has Combat"] & HasMana(2000), add_rules=AddRuleTuple("pyromancy", 8, rules["Has Pyromancy"])),
    Action(Multipart)               (zone="Z1", name="Small Dungeon", internal_name="SDungeon", option="sd", rule=rules["Z1 Has Magic"] | rules["Z1 Has Combat"]),

    Action(Skill)                   (zone="Z1", name="Combat", action_name="Warrior Lessons", internal_action_name="WarriorLessons", full_rule=rules["Z1 Has Combat"]),
    Action(Skill)                   (zone="Z1", name="Magic", action_name="Mage Lessons", internal_action_name="MageLessons", full_rule=rules["Z1 Has Magic"]),

    # Zone 2
    Action(Z2, Progress)            (zone="Z2", name="Explore Forest", internal_name="Forest", classification=ItemClassification.progression),
    # Explore Forest and Clear Thicket give 50
    Action(Z2, Batched, AddRule)    (zone="Z2", name="Wild Mana", internal_name="WildMana", count=100, classification=ItemClassification.progression, lootable_classification=ItemClassification.useful, add_rules=[
        AddRuleTuple("Explore or Thicket", 0, Has("Z2 - Explore Forest") | Has("Z2 - Clear Thicket"), 'full_add'),
        AddRuleTuple("Explore and Thicket", 51, Has("Z2 - Explore Forest") & Has("Z2 - Clear Thicket"), 'full_add')
    ]),
    # Explore Forest gives 50, Old Shortcut gives 20, Follow Flowers gives 130
    # aaaaaaaaaaaaaaaaa
    Action(Z2, Batched, AddRule)    (zone="Z2", name="Herb", internal_name="Herbs", count=200, classification=ItemClassification.progression, lootable_classification=ItemClassification.filler, rule=HasIfOptionManaReduction(rules["Z2 - Talk To Hermit"]), add_rules=[
        AddRuleTuple("Explore or Shortcut or Flowers", 0, Has("Z2 - Explore Forest") | Has("Z2 - Old Shortcut") | Has("Z2 - Follow Flowers"), 'full_add'),
        AddRuleTuple("Explore or Flowers", 21, Has("Z2 - Explore Forest") | Has("Z2 - Follow Flowers"), 'full_add'),
        AddRuleTuple("(Explore and Shortcut) or Flowers", 51, (Has("Z2 - Explore Forest") & Has("Z2 - Old Shortcut")) | Has("Z2 - Follow Flowers"), 'full_add'),
        AddRuleTuple("Flowers", 71, Has("Z2 - Follow Flowers"), 'full_add'),
        AddRuleTuple("(Explore or Shortcut) and Flowers", 131, (Has("Z2 - Explore Forest") | Has("Z2 - Old Shortcut")) & Has("Z2 - Follow Flowers"), 'full_add'),
        AddRuleTuple("Explore and Flowers", 151, Has("Z2 - Explore Forest") & Has("Z2 - Follow Flowers"), 'full_add'),
        AddRuleTuple("Explore and Shortcut and Flowers", 181, Has("Z2 - Explore Forest") & Has("Z2 - Old Shortcut") & Has("Z2 - Follow Flowers"), 'full_add')
    ]),
    Action(Z2, Limited)             (zone="Z2", name="Hunt", count=20, lootable_classification=ItemClassification.filler, rule=Has("Z2 - Explore Forest")),
    Action(Z2)                      (zone="Z2", name="Sit By Waterfall", internal_name="SitByWaterfall", rule=HasIfOptionVanillaAll("Z2 - Explore Forest")),
    Action(Z2, Progress)            (zone="Z2", name="Old Shortcut", internal_name="Shortcut", classification=ItemClassification.progression, full_rule=rules["Z2 - Old Shortcut"]),
    Action(Z2, Progress)            (zone="Z2", name="Talk To Hermit", internal_name="Hermit", classification=ItemClassification.progression, full_rule=rules["Z2 - Talk To Hermit"]),
    Action(Z2)                      (zone="Z2", name="Brew Potions", internal_name="BrewPotions", rule=HasIfOptionVanillaSkills(rules["Has Alchemy"])),
    Action(Z2)                      (zone="Z2", name="Train Dexterity", internal_name="TrainDexterity", rule=HasIfOptionVanillaAll("Z2 - Explore Forest")),
    Action(Z2)                      (zone="Z2", name="Train Speed", internal_name="TrainSpeed", rule=HasIfOptionVanillaAll("Z2 - Explore Forest")),
    Action(Z2, Progress)            (zone="Z2", name="Follow Flowers", internal_name="Flowers", classification=ItemClassification.progression, full_rule=rules["Z2 - Follow Flowers"]),
    Action(Z2)                      (zone="Z2", name="Bird Watching", internal_name="BirdWatching", rule=Has("Z1 - Buy Glasses") & HasIfOptionVanillaAll("Z2 - Follow Flowers")),
    Action(Z2, Progress)            (zone="Z2", name="Clear Thicket", internal_name="Thicket", classification=ItemClassification.progression, full_rule=rules["Z2 - Clear Thicket"]),
    Action(Z2, Progress)            (zone="Z2", name="Talk To Witch", internal_name="Witch", classification=ItemClassification.progression, full_rule=rules["Z2 - Talk To Witch"]),
    Action(Z2)                      (zone="Z2", name="Continue On", internal_name="ContinueOn", classification=ItemClassification.progression, rule=HasIfOptionManaReduction(rules["Z2 - Old Shortcut"])),

    Action(Z2, Skill)               (zone="Z2", name="Practical Magic", internal_name="Practical", action_name="Practical Magic", internal_action_name="PracticalMagic", classification=ItemClassification.progression, full_rule=rules["Has Practical Magic"]),
    # *techincally* there's a rule here for 10 herbs but pffft that's not going to be an issue
    Action(Z2, Skill)               (zone="Z2", name="Alchemy", action_name="Learn Alchemy", internal_action_name="LearnAlchemy", classification=ItemClassification.progression, option="alchemy", every=5, full_rule=rules["Has Alchemy"]),
    Action(Z2, Skill)               (zone="Z2", name="Dark Magic", internal_name="Dark", action_name="Dark Magic", classification=ItemClassification.progression, internal_action_name="DarkMagic", full_rule=rules["Has Dark Magic"]),
    Action(Z2, Buff)                (zone="Z2", name="Dark Ritual", internal_name="Ritual", action_name="Dark Ritual", internal_action_name="DarkRitual", option="ritual", every=1, rule=Has("Z2 - Dark Magic") & Has("Z1 - Haggle") & rules["Has Soulstones"] & HasIfOptionManaReduction(rules["Z2 - Talk To Witch"]) & HasIfOptionVanillaSkills(rules["Has Dark Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Talk To Witch"])),

    # Zone 3
    Action(Z3, Progress)            (zone="Z3", name="Explore City", internal_name="City", classification=ItemClassification.progression),
    Action(Z3, Limited)             (zone="Z3", name="Gamble", count=20, classification=ItemClassification.progression, rule=Has("Z3 - Explore City") & HasIfOptionVanillaAll("Z3 - Explore City")),
    Action(Z3, Progress)            (zone="Z3", name="Get Drunk", internal_name="Drunk", classification=ItemClassification.progression, full_rule=rules["Z3 - Get Drunk"]),
    Action(Z3)                      (zone="Z3", name="Buy Mana", internal_name="BuyMana", classification=ItemClassification.progression),
    Action(Z3)                      (zone="Z3", name="Sell Potions", internal_name="SellPotions", classification=ItemClassification.progression, rule=Has("Z2 - Brew Potions")),
    Action(Z3, Multipart)           (zone="Z3", name="Adventure Guild", internal_name="AdvGuild", rule=HasIfOptionVanillaAll(rules["Z3 - Get Drunk"])),
    Action(Z3)                      (zone="Z3", name="Gather Team", internal_name="GatherTeam", rule=Has("Z3 - Adventure Guild") & HasIfOptionVanillaAll(rules["Z3 - Get Drunk"])),
    Action(Z3, Multipart)           (zone="Z3", name="Crafting Guild", internal_name="CraftGuild", rule=HasIfOptionVanillaAll(rules["Z3 - Get Drunk"])),
    Action(Z3)                      (zone="Z3", name="Craft Armor", internal_name="CraftArmor", rule=HasIfOptionVanillaAll(rules["Z3 - Get Drunk"])),
    Action(Z3, Progress)            (zone="Z3", name="Apprentice", full_rule=rules["Z3 - Apprentice"]),
    Action(Z3, Progress)            (zone="Z3", name="Mason", full_rule=rules["Z3 - Mason"]),
    Action(Z3, Progress)            (zone="Z3", name="Architect", full_rule=rules["Z3 - Architect"]),
    Action(Z3)                      (zone="Z3", name="Read Books", internal_name="ReadBooks", rule=Has("Z1 - Buy Glasses")),
    Action(Z3)                      (zone="Z3", name="Buy Pickaxe", internal_name="BuyPickaxe"),
    Action(Z3)                      (zone="Z3", name="Start Trek", internal_name="StartTrek", classification=ItemClassification.progression),

    Action(Z3, Shop)                (zone="Z3", name="AP Shop", internal_name="APShop", min=500, max=1000, option="z3_shop", rule=Has("Z2 - Practical Magic") | (Has("Z2 - Brew Potions") & rules["Has Alchemy"])),

    # I'm going to say the guilds are Z5+, but you still need the item for Gather Team/LDungeon/Architect bars
    Action(Z3, AddRule, Multipart)  (zone="Z3", name="Large Dungeon", internal_name="LDungeon", option="ld", rule=rules["Z3 - Large Dungeon"], add_rules=AddRuleTuple("pyromancy", 3, rules["Has Pyromancy"])),
    # Incorrect, Craft Armor doesn't give any crafting exp, but there's nowhere better...
    Action(Z3, Skill)               (zone="Z3", name="Crafting", internal_name="Crafting", action_name="CraftArmor", option="crafting", internal_action_name="CraftArmor", full_rule=HasAll("Z3 - Crafting Guild", "Z3 - Apprentice", "Z3 - Mason", "Z3 - Architect")),

    # Zone 4
    Action(Z4, Progress)            (zone="Z4", name="Climb Mountain", internal_name="Mountain"),
    Action(Z4, Limited)             (zone="Z4", name="Mana Geyser", internal_name="Geysers", count=10, rule=Has("Z4 - Climb Mountain") & Has("Z3 - Buy Pickaxe")),
    Action(Z4, Progress)            (zone="Z4", name="Decipher Runes", internal_name="Runes", full_rule=rules["Z4 - Decipher Runes"]),
    Action(Z4, Progress)            (zone="Z4", name="Explore Cavern", internal_name="Cavern", full_rule=rules["Z4 - Explore Cavern"]),
    Action(Z4, Limited)             (zone="Z4", name="Soulstone", internal_name="MineSoulstones", count=30, rule=rules["Z4 - Explore Cavern"] & Has("Z3 - Buy Pickaxe")),
    Action(Z4, Progress)            (zone="Z4", name="Check Walls", internal_name="Illusions", full_rule=rules["Z4 - Check Walls"]),
    Action(Z4, Limited)             (zone="Z4", name="Artifact", internal_name="Artifacts", count=20, rule=rules["Z4 - Check Walls"]),
    # Can get to +-50 rep. -50 path has haggle and PM to have enough mana to do 50 Dark Magic actions
    Action(Z4)                      (zone="Z4", name="Face Judgement", internal_name="FaceJudgement", rule=(Has("Z1 - Heal The Sick") & Has("Z1 - Mage Lessons")) | (Has("Z2 - Talk To Witch") & Has("Z2 - Dark Magic") & Has("Z1 - Haggle") & Has("Z2 - Practical Magic"))),

    Action(Z4, Multipart)           (zone="Z4", name="Hunt Trolls", internal_name="HuntTrolls", option="trolls", rule=rules["Has Combat"] & rules["Has Pyromancy"] & HasIfOptionVanillaAll(rules["Z4 - Explore Cavern"])),

    Action(Z4, Skill)               (zone="Z4", name="Chronomancy", action_name="Chronomancy", rule=HasIfOptionManaReduction(rules["Z4 - Decipher Runes"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z4 - Decipher Runes"])),
    Action(Z4, Skill)               (zone="Z4", name="Pyromancy", action_name="Pyromancy", full_rule=rules["Has Pyromancy"]),
    Action(Z4, Buff)                (zone="Z4", name="Imbue Mind", action_name="Imbue Mind", internal_name="Imbuement", option="mind", every=1, rule=HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z4 - Check Walls"]))
]

all_actions = all_actions + filler_actions
for action in all_actions:
    locations, location_id = action.all_locations(location_id, location_name_to_id)
    all_locations += locations
    items, item_id = action.all_items(item_id, item_to_id)
    all_items += items

filler_item_names = [action.unlock_item_name() for action in filler_actions] + ["Z1 - Mana Pot"]

# Okay i'm getting tired of writing this file so it can be rune by itself to output the below.
# There's a way to add an option to the archipelago launcher that can dump these, right?

# For now i'll just try and remember to comment this in releases
# name_map = {}
# skill_map = {}
# for action in all_actions:
#     action.name_map(name_map, skill_map)

# with open("display_name_to_internal.json", "w") as f:
#     # Flip it for use in the mod
#     # Except the mod uses both ways heh
#     f.write(json.dumps(name_map))

# with open("display_skill_to_internal.json", "w") as f:
#     f.write(json.dumps(skill_map))
