from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Iterable, List, Tuple
from collections.abc import Sequence

from rule_builder.rules import CanReachLocation, Rule
from .Options import IdleLoopsOptions
from .Rules import HasMana, JourneyRule


if __name__ == "__main__":
    import json

    class ItemClassification:
        useful = "useful"
        filler = "filler"
        progression = "progression"

    class OptionFilter:
        def __init__(self, option_class, option_value):
            pass
    # class Logic:
    #     option_normal = 0

    class Has:
        def __init__(self, item_name):
            pass
    HasAll, True_, HasFromList = Has, Has, Has, Has

else:
    from BaseClasses import ItemClassification, Location, Item
    from rule_builder.rules import Has, HasAll, HasFromList, True_
    from rule_builder.options import OptionFilter
    # from .Options import Logic

    # Considering how tightly coupled Loctaions, Items and Rules are in this game, it makes sense to see them as Actions that generate said Locations, Items and Rules.

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


class Action:
    # I don't know enough about python's type hinting to get this to return something that the IDE can pick up on all kwargs with
    # Or rather, i didn't even try, that's more accurate
    def __new__(self, *args: type) -> type[_Action]:
        name = "_".join([x.__name__ for x in args])
        return type(name, args + (_Action,), {})


class _Action:
    def __init__(self, zone: str, name: str, internal_name: str, classification: ItemClassification = ItemClassification.progression, rule: Rule = None, base_count: int = 1):
        self.zone = zone
        self.region = "Z1"
        self.name = name
        self.internal_name = internal_name
        self.classification = classification
        self.rule = rule
        self.base_count = base_count

    def base_location_list(self) -> List[str]:
        return [(self.zone, self.name)]

    def location_list(self) -> List[str]:
        return self.base_location_list()

    def all_locations(self, location_id, location_name_to_id) -> Tuple[List[str], int]:
        name_parts = self.location_list()
        output = []
        for name_parts in name_parts:
            name = " - ".join(name_parts)
            location_name_to_id[name] = location_id
            output.append(name)
            location_id += 1
        return (output, location_id)

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        """
        Returns a list of (location ID, region).
        """
        return [(location_name_to_id[name], self.region) for name in self.location_list()]

    def base_rule(self) -> Rule:
        return Has(self.unlock_item_name())

    def rules(self) -> Dict[str, callable]:
        if self.rules_override is not None:
            return self.rules_override(self)
        rule = self.rule if self.rule is not None else True_()
        return {name: self.base_rule() & rule for name in self.location_list()}

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


class Start():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_count = 0

    def base_rule(self) -> Rule:
        return True_()


class Progress():
    progress_locations = ["1", "5", "10", "15", "20", "25", "30", "40", "50", "60", "70", "80", "90", "95", "99", "100"]

    def locations_progress_list(self) -> List[str]:
        return [(self.zone, self.name, progress) for progress in self.progress_locations]

    def location_list(self) -> List[str]:
        return self.base_location_list() + self.locations_progress_list()

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        if options.location_progress:
            return [(location_name_to_id[name], self.region) for name in self.locations_progress_list()]
        else:
            return [(location_name_to_id[name], self.region) for name in self.base_location_list()]


class Count():
    def __init__(self, count: Sequence[str | int], **kwargs):
        super().__init__(**kwargs)
        self.count = count


class Limited(Count):
    def __init__(self, item_count: int = None, lootable_classification: ItemClassification = ItemClassification.useful, **kwargs):
        super().__init__(**kwargs)
        self.lootable_classification = lootable_classification
        self.item_count = item_count if item_count is not None else len(self.count)

    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - #{i}" for i in self.count]

    def unlock_item_name(self) -> str:
        return f"{self.zone} - {self.name} - Search"

    def extra_items(self) -> List[str]:
        return [{
            "name": f"{self.zone} - {self.name}",
            "classification": self.lootable_classification,
            "count": self.item_count
        }]

    def included_items(self, options: IdleLoopsOptions) -> List[int]:
        if options.item_search:
            return self.item_list()
        else:
            return self.extra_items()


class Batched(Limited):
    def __init__(self, batch_size: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.batch_size = batch_size

    def batched_location_list(self) -> List[str]:
        return [f"{self.zone} - x{self.batch_size} {self.name} - #{i}" for i in range(1, (len(self.count) + self.batch_size - 1) // self.batch_size + 1)]

    def location_list(self) -> List[str]:
        return super().location_list() + self.batched_location_list()

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        if options.batch_z2:
            return [(location_name_to_id[name], self.region) for name in self.batched_location_list()]
        else:
            # It's not the cleanest to copy the list definition from the parent, but we overwrite location_list so super won't work.
            return [(location_name_to_id[name], self.region) for name in [f"{self.zone} - {self.name} - #{i}" for i in self.count]]


class Multipart(Count):
    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - Completion #{i}" for i in self.count]


class Skill(Count):
    skill_locations = [1] + list(range(10, 501, 10))

    def __init__(self, skill: str, **kwargs):
        super().__init__(**kwargs)
        self.skill = skill

    def location_list(self) -> List[str]:
        return [f"{self.skill} - Level {n}" for n in self.skill_locations]

    def included_locations(self, options: IdleLoopsOptions) -> List[Tuple[int, int]]:
        region = 1
        locations = []
        for level in self.skill_locations:
            if level > options.location_skill:
                break
            # Goal is 0-indexed so we want this cap to be one above
            if level in [50, 100, 200, 300] and region <= options.goal:
                region += 1
            locations.append((location_name_to_id[f"{self.skill} - Level {level}"], region))
        return locations


class Buff(Skill):
    def __init__(self, buff: str, **kwargs):
        super().__init__(skill=buff, **kwargs)

# Stops this action from adding items to the pool
# This will break later with unlocking more limited actions through like survye
# (and technically now with forest and thicket/flowers but whatever i'll keep those &'ed)


class OnlyLocations():
    def items(self, item_id, item_to_id) -> Tuple[List[str], int]:
        return ([], item_id)


class Filler():
    def location_list(self) -> List[str]:
        return []


class Z2():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = "Z2"


class Z3():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = "Z3"


class Z4():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = "Z4"


def has_2_rep(self: _Action) -> Dict[str, callable]:
    rule = Has(self.unlock_item_name()) & HasFromList("Z1 - Long Quest", "Filler - Progressive Lootable", count=2)
    return {name: rule for name in self.location_list()}

# Can get to +-50 rep. -50 path has haggle and PM to have enough mana to do 50 Dark Magic actions


def judgementRules(self: _Action) -> Dict[str, callable]:
    rule = Has("Z4 - Face Judgement") & ((Has("Z1 - Heal The Sick") & Has("Z1 - Mage Lessons")) | (Has("Z2 - Talk To Witch") & Has("Z2 - Dark Magic") & Has("Z1 - Haggle") & Has("Z2 - Practical Magic")))
    return {name: rule for name in self.location_list()}


# ofc filler actions are only items but calling it actions makes it fit with the others
filler_actions = [
    Action(Filler)(name="50 Starting Mana"),
    Action(Filler)(name="1 Starting Gold"),
    Action(Filler)(name="+0.1 Game Speed", classification=ItemClassification.filler),
    Action(Filler)(name="+0.1 Exp Multiplier", classification=ItemClassification.filler),
    Action(Filler)(name="Nothing", classification=ItemClassification.filler),
]

# Progressive lootable acts as an extra count for limited actions, (up to their usual max, for when you don't have them capped) in rough order of usefullness/progression
# Long Quests (up to 2) > Short Quests > Long Quests (Rest) > Locks > Wild Mana ... > n-1 > Mana Pot
progressive_lootable = Action(Filler)(name="Progressive Lootable")


# ZX Class means that action should be included if the goal is >=n, the zone arg is for display/to hint what zone the item/location is in
# e.g. you can stretch to Small Dungeon completion 3 in Z1 if you really want to, but you're only doing 4+ in Z3 (Z4 with pyromancy? idk i forget this game)
# i.e. Action(Z1, Multipart)(zone="Z1", name="SDungeon", count=[1, 2, 3]...) & Action(Z3, Multipart)(zone="Z1", name="SDungeon", count=[4, 5, 6]...)
#       Will put checks in Small Dungeon completion 4-6 only if the goal is Z3 or higher
all_actions = [

    # Zone 1

    Action(Start, Progress)                         (zone="Z1", name="Wander"),
    Action(Start, Limited)                          (zone="Z1", name="Mana Pot", count=range(1, 51)),
    Action(Limited)                                 (zone="Z1", name="Lock", count=range(1, 11)),
    Action()                                          (zone="Z1", name="Buy Glasses"),
    Action()                                          (zone="Z1", name="Buy Mana"),
    Action(Progress)                                (zone="Z1", name="Meet People", rule=HasMana(800)),
    Action()                                          (zone="Z1", name="Train Strength"),
    Action(Limited)                    (zone="Z1", name="Short Quest", count=range(1, 21), requirements=["Z1 - Meet People"], lootable_classification=ItemClassification.progression),
    Action(Progress)                                (zone="Z1", name="Investigate", rule=HasMana(1000)),
    Action(Limited)                   (zone="Z1", name="Long Quest", count=range(1, 11), requirements=["Z1 - Investigate"], lootable_classification=ItemClassification.progression),
    Action()                                          (zone="Z1", name="Throw Party", rules=has_2_rep),
    Action(Skill)                                   (zone="Z1", name="Warrior Lessons", skill="Combat", count=[1] + list(range(10, 101, 10)), rule=HasFromList("Z1 - Long Quest", "Filler - Progressive Lootable", count=2)),
    Action(Skill)                                   (zone="Z1", name="Mage Lessons", skill="Magic", count=[1] + list(range(10, 101, 10)), rule=HasFromList("Z1 - Long Quest", "Filler - Progressive Lootable", count=2)),
    Action(Multipart)                 (zone="Z1", name="Heal The Sick", count=[1, 2, 3, 4, 5], rule=Has("Z1 - Mage Lessons")),
    Action(Multipart)                 (zone="Z1", name="Fight Monsters", count=[1, 2, 3], rule=Has("Z1 - Warrior Lessons")),
    # Should be OR, i'm eternally finding things to refactor and make more complicated...
    Action(Multipart)                 (zone="Z1", name="Small Dungeon", count=[1, 2, 3], rule=Has("Z1 - Mage Lessons") & Has("Z1 - Warrior Lessons")),
    Action()                                          (zone="Z1", name="Buy Supplies"),
    Action()                                          (zone="Z1", name="Haggle", rule=HasFromList("Z1 - Long Quest", "Filler - Progressive Lootable", count=1)),
    Action()                                          (zone="Z1", name="Start Journey", rule=JourneyRule()),

    # Zone 2

    Action(Z2, OnlyLocations, Skill)                    (zone="Z1", name="Warrior Lessons", skill="Combat", count=range(101, 151, 10)),
    Action(Z2, OnlyLocations, Skill)                    (zone="Z1", name="Mage Lessons", skill="Magic", count=range(101, 151, 10)),
    Action(Z2, OnlyLocations, Multipart, Requirements)  (zone="Z1", name="Heal The Sick", count=[6, 7], requirements=["Z1 - Mage Lessons"]),
    Action(Z2, OnlyLocations, Multipart, Requirements)  (zone="Z1", name="Fight Monsters", count=[4, 5], requirements=["Z1 - Warrior Lessons"]),
    Action(Z2, OnlyLocations, Multipart, Requirements)  (zone="Z1", name="Small Dungeon", count=[4], requirements=["Z1 - Mage Lessons", "Z1 - Warrior Lessons"]),

    Action(Z2, Progress)                                (zone="Z2", name="Explore Forest"),
    Action(Z2, Limited, Requirements)                   (zone="Z2", name="Wild Mana", count=range(1, 101), requirements=["Z2 - Explore Forest", "Z2 - Clear Thicket"], lootable_classification=ItemClassification.filler),
    Action(Z2, Limited, Requirements)                   (zone="Z2", name="Herb", count=range(1, 201), requirements=["Z2 - Explore Forest", "Z2 - Old Shortcut", "Z2 - Follow Flowers"], lootable_classification=ItemClassification.filler),
    Action(Z2, Limited, Requirements)                   (zone="Z2", name="Hunt", count=range(1, 21), requirements=["Z2 - Explore Forest"], lootable_classification=ItemClassification.filler),
    Action(Z2)                                          (zone="Z2", name="Sit By Waterfall"),
    Action(Z2, Progress)                                (zone="Z2", name="Old Shortcut"),
    Action(Z2, Progress)                                (zone="Z2", name="Talk To Hermit"),
    Action(Z2, Skill)                                   (zone="Z2", name="Practical Magic", skill="Practical Magic", count=[1] + list(range(10, 101, 10))),
    # *techincally* there's a rule here for 10 herbs but pffft that's not going to be an issue
    Action(Z2, Skill)                                   (zone="Z2", name="Learn Alchemy", skill="Alchemy", count=[1, 10, 20]),
    Action(Z2)                                          (zone="Z2", name="Brew Potions"),
    Action(Z2)                                          (zone="Z2", name="Train Dexterity"),
    Action(Z2)                                          (zone="Z2", name="Train Speed"),
    Action(Z2, Progress)                                (zone="Z2", name="Follow Flowers"),
    Action(Z2, Requirements)                            (zone="Z2", name="Bird Watching", requirements=["Z1 - Buy Glasses"]),
    Action(Z2, Progress)                                (zone="Z2", name="Clear Thicket"),
    Action(Z2, Progress)                                (zone="Z2", name="Talk To Witch"),
    # Haggle isn't a requirement - I did it without haggle to finish a Z4 multiworld - maybe a hard logic option
    Action(Z2, Skill, Requirements)                     (zone="Z2", name="Dark Magic", skill="Dark Magic", count=[1] + list(range(10, 101, 10)), requirements=["Z1 - Haggle"]),
    # This feels like a Z3 location, but you can stretch for at least the first one in Z2 with ~100 Dark Magic, it's just not a good idea with the soul stone cost
    Action(Z2, Buff)                                    (zone="Z2", name="Dark Ritual", buff="Ritual", count=[1], rule=Has("Z2 - Dark Magic") & (CanReachLocation("Z1 - Small Dungeon - Completion #1") | CanReachLocation("Z3 - Large Dungeon - Completion #1") | (CanReachLocation("Z3 - Start Trek") & Has("Z4 - Soulstone")))),
    Action(Z2)                                          (zone="Z2", name="Continue On"),

    # Zone 3

    Action(Z3, OnlyLocations, Multipart, Requirements)  (zone="Z1", name="Heal The Sick", count=[8, 9], requirements=["Z1 - Mage Lessons"]),
    Action(Z3, OnlyLocations, Skill)                    (zone="Z1", name="Warrior Lessons", skill="Combat", count=[160, 170, 180, 190, 200]),
    Action(Z3, OnlyLocations, Skill)                    (zone="Z1", name="Mage Lessons", skill="Magic", count=[160, 170, 180, 190, 200]),
    Action(Z3, OnlyLocations, Multipart, Requirements)  (zone="Z1", name="Fight Monsters", count=[6, 7], requirements=["Z1 - Warrior Lessons"]),
    Action(Z3, OnlyLocations, Multipart, Requirements)  (zone="Z1", name="Small Dungeon", count=[5, 6], requirements=["Z1 - Mage Lessons", "Z1 - Warrior Lessons"]),
    Action(Z3, OnlyLocations, Skill)                    (zone="Z2", name="Practical Magic", skill="Practical Magic", count=[110, 120, 130, 140, 150, 160, 170, 180, 190, 200]),
    Action(Z3, Skill)                                   (zone="Z2", name="Learn Alchemy", skill="Alchemy", count=[30, 40, 50]),
    Action(Z3, OnlyLocations, Skill)                    (zone="Z2", name="Dark Magic", skill="Dark Magic", count=[110, 120, 130, 140, 150, 160, 170, 180, 190, 200]),

    Action(Z3, Progress)                                (zone="Z3", name="Explore City"),
    Action(Z3, Limited, Requirements)                   (zone="Z3", name="Gamble", count=range(1, 21), requirements=["Z3 - Explore City"]),
    Action(Z3, Progress)                                (zone="Z3", name="Get Drunk"),
    Action(Z3)                                          (zone="Z3", name="Buy Mana"),
    Action(Z3, Requirements)                            (zone="Z3", name="Sell Potions", requirements=["Z2 - Brew Potions"]),
    # I'm going to say the guilds are Z5+, but you still need the item for Gather Team/LDungeon/Architect bars
    Action(Z3, Multipart)                               (zone="Z3", name="Adventure Guild", count=[]),
    Action(Z3, Requirements)                            (zone="Z3", name="Gather Team", requirements=["Z3 - Adventure Guild"]),
    Action(Z3, Multipart, Requirements)                 (zone="Z3", name="Large Dungeon", count=[1, 2], requirements=["Z3 - Adventure Guild", "Z3 - Gather Team", "Z1 - Warrior Lessons", "Z1 - Mage Lessons"]),
    Action(Z3, Multipart)                               (zone="Z3", name="Crafting Guild", count=[]),
    Action(Z3, Progress, Requirements)                  (zone="Z3", name="Apprentice", requirements=["Z3 - Crafting Guild"]),
    Action(Z3, Progress, Requirements)                  (zone="Z3", name="Mason", requirements=["Z3 - Crafting Guild"]),
    Action(Z3, Progress, Requirements)                  (zone="Z3", name="Architect", requirements=["Z3 - Crafting Guild"]),
    Action(Z3, Requirements)                            (zone="Z3", name="Read Books", requirements=["Z1 - Buy Glasses"]),
    Action(Z3)                                          (zone="Z3", name="Buy Pickaxe"),
    Action(Z3)                                          (zone="Z3", name="Start Trek"),

    # Zone 4

    Action(Z4, OnlyLocations, Skill)                    (zone="Z1", name="Warrior Lessons", skill="Combat", count=[210, 220, 230, 240, 250, 260, 270, 280, 290, 300]),
    Action(Z4, OnlyLocations, Skill)                    (zone="Z1", name="Mage Lessons", skill="Magic", count=[210, 220, 230, 240, 250, 260, 270, 280, 290, 300]),
    Action(Z4, OnlyLocations, Multipart, Requirements)  (zone="Z1", name="Heal The Sick", count=[10], requirements=["Z1 - Mage Lessons"]),
    Action(Z4, OnlyLocations, Multipart, Requirements)  (zone="Z1", name="Fight Monsters", count=[8, 9, 10], requirements=["Z1 - Warrior Lessons", "Z4 - Pyromancy"]),
    Action(Z4, OnlyLocations, Skill)                    (zone="Z2", name="Practical Magic", skill="Practical Magic", count=[210, 220, 230, 240, 250, 260, 270, 280, 290, 300]),
    Action(Z3, OnlyLocations, Skill)                    (zone="Z2", name="Learn Alchemy", skill="Alchemy", count=[60, 70, 80, 90, 100]),
    Action(Z4, OnlyLocations, Skill)                    (zone="Z2", name="Dark Magic", skill="Dark Magic", count=[210, 220, 230, 240, 250, 260, 270, 280, 290, 300]),
    Action(Z4, OnlyLocations, Multipart, Requirements)  (zone="Z3", name="Large Dungeon", count=[3, 4, 5, 6, 7, 8, 9], requirements=["Z4 - Pyromancy"]),

    Action(Z4, Progress)                                (zone="Z4", name="Climb Mountain"),
    Action(Z4, Limited, Requirements)                   (zone="Z4", name="Mana Geyser", count=range(1, 11), requirements=["Z4 - Climb Mountain", "Z3 - Buy Pickaxe"]),
    Action(Z4, Progress)                                (zone="Z4", name="Decipher Runes"),
    Action(Z4, Skill)                                   (zone="Z4", name="Chronomancy", skill="Chronomancy", count=[1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
    Action(Z4, Skill)                                   (zone="Z4", name="Pyromancy", skill="Pyromancy", count=[1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
    Action(Z4, Progress)                                (zone="Z4", name="Explore Cavern"),
    Action(Z4, Limited, Requirements)                   (zone="Z4", name="Soulstone", count=range(1, 31), requirements=["Z4 - Explore Cavern", "Z3 - Buy Pickaxe"]),
    Action(Z4, Multipart, Requirements)                 (zone="Z4", name="Hunt Trolls", count=[1, 2, 3, 4, 5], requirements=["Z4 - Pyromancy"]),
    Action(Z4, Progress)                                (zone="Z4", name="Check Walls"),
    Action(Z4, Limited, Requirements)                   (zone="Z4", name="Artifact", count=range(1, 21), requirements=["Z4 - Check Walls"]),
    Action(Z4, Buff)                                    (zone="Z4", name="Imbue Mind", buff="Imbue Mind", count=[1]),
    Action(Z4)                                          (zone="Z4", name="Face Judgement", rules=judgementRules)
]

all_actions = all_actions + filler_actions + [progressive_lootable]
all_locations
for action in all_actions:
    all_items
    locations, location_id = action.locations(location_id, location_name_to_id)
    all_locations += locations
    items, item_id = action.items(item_id, item_to_id)
    all_items += items

filler_item_names = [action.unlock_item_name() for action in filler_actions] + ["Z1 - Mana Pot"]

if __name__ == "__main__":
    name_map = {
        "Wander": "Wander",
        "Mana Pot": "Pots",
        "Lock": "Locks",
        "Buy Glasses": "BuyGlasses",
        "Buy Mana": "BuyMana",
        "Meet People": "Met",
        "Train Strength": "TrainStrength",
        "Short Quest": "SQuests",
        "Investigate": "Secrets",
        "Long Quest": "LQuests",
        "Throw Party": "ThrowParty",
        "Warrior Lessons": "WarriorLessons",
        "Mage Lessons": "MageLessons",
        "Heal The Sick": "Heal",
        "Fight Monsters": "Fight",
        "Small Dungeon": "SDungeon",
        "Buy Supplies": "BuySupplies",
        "Haggle": "Haggle",
        "Start Journey": "StartJourney",

        "Explore Forest": "Forest",
        "Wild Mana": "WildMana",
        "Herb": "Herbs",
        "Hunt": "Hunt",
        "Sit By Waterfall": "SitByWaterfall",
        "Old Shortcut": "Shortcut",
        "Talk To Hermit": "Hermit",
        "Practical Magic": "PracticalMagic",
        "Learn Alchemy": "LearnAlchemy",
        "Brew Potions": "BrewPotions",
        "Train Dexterity": "TrainDexterity",
        "Train Speed": "TrainSpeed",
        "Follow Flowers": "Flowers",
        "Bird Watching": "BirdWatching",
        "Clear Thicket": "Thicket",
        "Talk To Witch": "Witch",
        "Dark Magic": "DarkMagic",
        "Dark Ritual": "DarkRitual",
        "Continue On": "ContinueOn",

        "Explore City": "City",
        "Gamble": "Gamble",
        "Get Drunk": "Drunk",
        "Sell Potions": "SellPotions",
        "Adventure Guild": "AdvGuild",
        "Gather Team": "GatherTeam",
        "Large Dungeon": "LDungeon",
        "Crafting Guild": "CraftGuild",
        "Apprentice": "Apprentice",
        "Mason": "Mason",
        "Architect": "Architect",
        "Read Books": "ReadBooks",
        "Buy Pickaxe": "BuyPickaxe",
        "Start Trek": "StartTrek",

        "Climb Mountain": "Mountain",
        "Mana Geyser": "Geysers",
        "Decipher Runes": "Runes",
        "Chronomancy": "Chronomancy",
        "Pyromancy": "Pyromancy",
        "Explore Cavern": "Cavern",
        "Soulstone": "MineSoulstones",
        "Hunt Trolls": "HuntTrolls",
        "Check Walls": "Illusions",
        "Artifact": "Artifacts",
        "Face Judgement": "FaceJudgement",

        "Combat": "Combat",
        "Magic": "Magic",
        "Practical Magic": "Practical",
        "Alchemy": "Alchemy",
        "Dark Magic": "Dark",
        "Dark Ritual": "DarkRitual",
        "Ritual": "Ritual",
        "Imbue Mind": "Imbuement"
    }

    for location in location_name_to_id:
        split = location.split(" - ")
        display_name = split[1] if split[0].startswith("Z") else split[0]

        if display_name not in name_map:
            raise Exception(f"Missing {location}: {display_name} in name_map")
    print("All location names are in name_map")
    with open("display_name_to_internal.json", "w") as f:
        # Flip it for use in the mod
        f.write(json.dumps(name_map))

    with open("location_name_to_id.json", "w") as f:
        # Awful line
        f.write(json.dumps({k.replace(k.split(" - ")[1] if k.split(" - ")[0].startswith("Z") else k.split(" - ")[0], name_map[k.split(" - ")[1] if k.split(" - ")[0].startswith("Z") else k.split(" - ")[0]]): v for k, v in location_name_to_id.items()}))
    print("Dumped location_name_to_id")
