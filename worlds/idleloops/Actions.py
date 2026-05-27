from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterable, List, Tuple

from BaseClasses import CollectionState, ItemClassification, Location, Item

# Considering how tightly coupled Loctaions, Checks and Rules are in this game, it makes sense to see them as Actions that generate said Locations, Checks and Rules.

class IdleLoopsLocation(Location):
    game = "Idle Loops"

class IdleLoopsItem(Item):
    game = "Idle Loops"

# class CollectionState:
#     pass
# class ItemClassification:
#     useful = "useful"
#     filler = "filler"
#     progression = "progression"

class Tags:
    Z1 = 0
    Z2 = 1
    Z3 = 2
    Z4 = 3

class Action:
    def __init__(self, zone: str, name: str, classification: ItemClassification=ItemClassification.useful, tags: List[Tags]=None, rules: callable=None):
        self.zone = zone
        self.name = name
        self.tags = tags if tags is not None else []
        self.classification = classification
        self.rules_override = rules

    def location_list(self) -> List[str]:
        # Base 'complete action for the first time' location
        return [f"{self.zone} - {self.name}"]
    
    def locations(self, location_id, location_to_id) -> Tuple[List[Tuple[str, List[Tags]]], int]:
        names = self.location_list()
        output = []
        for name in names:
            location_to_id[name] = location_id
            output.append((name, self.tags))
            location_id += 1
        return (output, location_id)
        
    def rules(self, world, player) -> Dict[str, callable]:
        if self.rules_override is not None:
            return self.rules_override(self, world, player)
        # Base rule of 'you need to unlock this action to complete it'
        unlock_item_name = self.unlock_item_name()
        def rule(state: CollectionState) -> bool:
            return state.has(unlock_item_name, player)
        return {name: rule for name in self.location_list()}
    
    def unlock_item_name(self) -> str:
        """
        I can't think of a better function name, i mean the name of the item that is required to complete the locations for this Action.
        This is a function and not a property solely so i can add this heredoc
        """
        return f"{self.zone} - {self.name}"
    
    def item_list(self) -> List[str]:
        return [{
            "name": self.unlock_item_name(),
            "classification": self.classification,
            "count": 1
        }]

    def items(self, item_id, item_to_id) -> Tuple[List[str], int]:
        items = self.item_list()
        output = []
        for name in items:
                item_to_id[name["name"]] = item_id
                output.append({
                    "name": name["name"],
                    "classification": name["classification"],
                    "count": name["count"]
                })
                item_id += 1
        return (output, item_id)


class ProgressAction(Action):
    progress_locations = ["1", "5", "10", "15", "20", "25", "30", "40", "50", "60", "70", "80", "90", "95", "99", "100"]
    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - {progress}%" for progress in self.progress_locations]

class LimitedAction(Action):
    def __init__(self, zone: str, name: str, required_action: list, count: int=1, item_count: int=None, classification: ItemClassification=ItemClassification.progression, lootable_classification: ItemClassification=ItemClassification.useful, tags: List[Tags]=None, rules: callable=None):
        super().__init__(zone, name, classification, tags=tags, rules=rules)
        self.lootable_classification = lootable_classification
        self.count = count
        self.item_count = item_count if item_count is not None else count
        self.required_action = required_action
    
    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - #{i}" for i in range(1, self.count + 1)]

    def unlock_item_name(self) -> str:
        return f"{self.zone} - {self.name} - Search"

    def item_list(self) -> List[str]:
        return super().item_list() + [
            {
                "name": f"{self.zone} - {self.name}",
                "classification": self.lootable_classification,
                "count": self.item_count
            }
        ]
    
    def rules(self, world, player) -> Dict[str, callable]:
        if self.rules_override is not None:
            return self.rules_override(self, world, player)
        # Base rule of 'you need to unlock this action to complete it'
        unlock_item_name = self.unlock_item_name()
        def rule(state: CollectionState) -> bool:
            return state.has(unlock_item_name, player) & (state.has_all(self.required_action, player) if len(self.required_action) > 0 else True)
        return {name: rule for name in self.location_list()}

class MultipartAction(Action):
    def __init__(self, zone: str, name: str, count: Iterable[str], classification: ItemClassification=ItemClassification.useful, tags: List[Tags]=None, rules: callable=None):
        super().__init__(zone, name, classification, tags=tags, rules=rules)
        self.count = count
    
    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - Completion #{i}" for i in self.count]

class SkillAction(Action):
    skill_locations = ["1", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"]
    def __init__(self, zone: str, name: str, skill: str, classification: ItemClassification=ItemClassification.useful, tags: List[Tags]=None, rules: callable=None):
        super().__init__(zone, name, classification, tags=tags, rules=rules)
        self.skill = skill
    
    def location_list(self) -> List[str]:
        return [f"{self.skill} - Level {n}" for n in self.skill_locations]

class FillerItem(Action):
    def __init__(self, name: str, classification: ItemClassification=ItemClassification.filler, tags: List[Tags]=None):
        super().__init__("Filler", name, classification, tags=tags)
    def location_list(self) -> List[str]:
        return []

# Can i finagle the MRO enough to not have to subclass action? Probably! But lets be safe.
class Z1(Action):
    def __init__(self, *args, tags: List[Tags]=None, **kwargs):
        super().__init__(*args, **kwargs, tags=(tags or []) + [Tags.Z1])
class Z1Action(Z1, Action):
    pass
class Z1ProgressAction(Z1, ProgressAction):
    pass
class Z1LimitedAction(Z1, LimitedAction):
    pass
class Z1MultipartAction(Z1, MultipartAction):
    pass
class Z1SkillAction(Z1, SkillAction):
    pass

class Z2(Action):
    def __init__(self, *args, tags: List[Tags]=None, **kwargs):
        super().__init__(*args, **kwargs, tags=(tags or []) + [Tags.Z2])
class Z2Action(Z2, Action):
    pass
class Z2ProgressAction(Z2, ProgressAction):
    pass
class Z2LimitedAction(Z2, LimitedAction):
    def __init__(self, *args, classification: ItemClassification=ItemClassification.useful, **kwargs):
        super().__init__(*args, classification=classification, **kwargs)
class Z2MultipartAction(Z2, MultipartAction):
    pass
class Z2SkillAction(Z2, SkillAction):
    pass

class Z3(Action):
    def __init__(self, *args, tags: List[Tags]=None, **kwargs):
        super().__init__(*args, **kwargs, tags=(tags or []) + [Tags.Z3])
class Z3Action(Z3, Action):
    pass
class Z3ProgressAction(Z3, ProgressAction):
    pass
class Z3LimitedAction(Z3, LimitedAction):
    def __init__(self, *args, classification: ItemClassification=ItemClassification.useful, **kwargs):
        super().__init__(*args, classification=classification, **kwargs)
class Z3MultipartAction(Z3, MultipartAction):
    pass
class Z3SkillAction(Z3, SkillAction):
    pass

class Z4(Action):
    def __init__(self, *args, tags: List[Tags]=None, **kwargs):
        super().__init__(*args, **kwargs, tags=(tags or []) + [Tags.Z4])
class Z4Action(Z4, Action):
    pass
class Z4ProgressAction(Z4, ProgressAction):
    pass
class Z4LimitedAction(Z4, LimitedAction):
    def __init__(self, *args, classification: ItemClassification=ItemClassification.useful, **kwargs):
        super().__init__(*args, classification=classification, **kwargs)
class Z4MultipartAction(Z4, MultipartAction):
    pass
class Z4SkillAction(Z4, SkillAction):
    pass

# I'm not happy with the boilerplate this needs, but just passing rule would lose access to Action.self

# I actually can't remember how leaving Z1 works at first, do you get through it haggling or buying for full cost?
# I think it's haggling because Z2 doesn't use gold, to bring more mana into Z2.
# But also, this is a rando, maybe it should be haggle || full cost and then let the rando sort it out.
# That's probably future work once i actually know how to construct rules, this is fine for now.
def journeyRules(self: Action, world, player) -> Dict[str, callable]:
    def rule(state: CollectionState) -> bool:
        return state.has_all_counts({
            "Z1 - BuySupplies": 1,
            "Z1 - BuyManaZ1": 1,
            "Z1 - Haggle": 1,
            self.unlock_item_name(): 1
        }, player)
    return {name: rule for name in self.location_list()}

def healRules(self: Action, world, player) -> Dict[str, callable]:
    def rule(state: CollectionState) -> bool:
        return state.has(self.unlock_item_name(), player) & state.has("Z1 - MageLessons", player)
    return {name: rule for name in self.location_list()}

def fightRules(self: Action, world, player) -> Dict[str, callable]:
    def rule(state: CollectionState) -> bool:
        return state.has(self.unlock_item_name(), player) & state.has("Z1 - WarriorLessons", player)
    return {name: rule for name in self.location_list()}

def dungeonRules(self: Action, world, player) -> Dict[str, callable]:
    def rule(state: CollectionState) -> bool:
        return state.has(self.unlock_item_name(), player) & state.has("Z1 - MageLessons", player) & state.has("Z1 - WarriorLessons", player)
    return {name: rule for name in self.location_list()}

def judgementRules(self: Action, world, player) -> Dict[str, callable]:
    def rule(state: CollectionState) -> bool:
        return state.has(self.unlock_item_name(), player) & state.has("Z1 - Heal", player)
    return {name: rule for name in self.location_list()}

# ofc filler actions are only items but calling it actions makes it fit with the others
filler_actions = [
    FillerItem("50 Starting Mana"),
    FillerItem("1 Starting Gold"),
    FillerItem("+0.1 Game Speed"),
]

# Zn Class means that action should be included if the goal is >=n, the "Zn" argument is for display/to hint what zone the item/location is in
# e.g. you can stretch to Small Dungeon completion 3 in Z1 if you really want to, but you're only doing 4+ in Z3 (Z4 with pyromancy? idk i forget this game)
# i.e. Z1MultipartAction("Z1", "SDungeon", [1, 2, 3]...) & Z3MultiPartAction("Z1", "SDungeon", [4, 5, 6]...)
#           Will put checks in Small Dungeon completion 4-6 only if the goal is Z3 or higher
all_actions = [

    # Zone 1

    # I assume this is not the proper way to handle rules for starting items,
    # but the world failed to generate because wander locations needed wander item, so nothing could be placed anywhere.
    # I assumed push_precollected would have "Z1 - Wander" in state - i guess not - deleting the rule solved it.
    Z1ProgressAction("Z1", "Wander", rules=lambda *args: {}),
    Z1LimitedAction("Z1", "Pots", [], 50, 25, lootable_classification=ItemClassification.filler, rules=lambda *args: {}),
    Z1LimitedAction("Z1", "Locks", [], 10),
    Z1Action("Z1", "BuyGlasses"),
    Z1Action("Z1", "BuyManaZ1", ItemClassification.progression),
    Z1ProgressAction("Z1", "Met", ItemClassification.progression),
    Z1Action("Z1", "TrainStrength"),
    Z1LimitedAction("Z1", "SQuests", ["Z1 - Met"], 20),
    Z1ProgressAction("Z1", "Secrets", ItemClassification.progression),
    Z1LimitedAction("Z1", "LQuests", ["Z1 - Secrets"], 10),
    Z1Action("Z1", "ThrowParty"),
    Z1SkillAction("Z1", "WarriorLessons", "Combat"),
    Z1SkillAction("Z1", "MageLessons", "Magic"),
    # Looking for feedback on these limits, what's reasonably reachable in Z1/Z2. I feel 10/10/6 works for Z3+.
    Z1MultipartAction("Z1", "Heal", [1, 2, 3], rules=healRules),
    Z1MultipartAction("Z1", "Fight", [1, 2, 3], rules=fightRules),
    Z1MultipartAction("Z1", "SDungeon", [1, 2, 3], rules=dungeonRules),
    Z1Action("Z1", "BuySupplies", ItemClassification.progression),
    Z1Action("Z1", "Haggle", ItemClassification.progression),
    Z1Action("Z1", "StartJourney", ItemClassification.progression, rules=journeyRules),

    # Zone 2

    Z2ProgressAction("Z2", "Forest"),
    Z2LimitedAction("Z2", "WildMana", ["Z2 - Forest", "Z2 - Thicket"], 100, lootable_classification=ItemClassification.filler),
    Z2LimitedAction("Z2", "Herbs", ["Z2 - Forest", "Z2 - Shortcut"], 200, lootable_classification=ItemClassification.filler),
    Z2LimitedAction("Z2", "Hunt", ["Z2 - Forest"], 20, lootable_classification=ItemClassification.filler),
    Z2Action("Z2", "SitByWaterfall"),
    Z2ProgressAction("Z2", "Shortcut"),
    Z2ProgressAction("Z2", "Hermit"),
    Z2SkillAction("Z2", "PracticalMagic", "Practical"),
    # *techincally* there's a rule here for herbs but pffft that's not going to be an issue
    Z2SkillAction("Z2", "LearnAlchemy", "Alchemy"),
    Z2Action("Z2", "BrewPotions"),
    Z2Action("Z2", "TrainDexterity"),
    Z2Action("Z2", "TrainSpeed"),
    Z2ProgressAction("Z2", "Flowers"),
    Z2Action("Z2", "BirdWatching"),
    Z2ProgressAction("Z2", "Thicket"),
    Z2ProgressAction("Z2", "Witch"),
    Z2SkillAction("Z2", "DarkMagic", "Dark"),
    # This feels like a Z3 location, but you can stretch for at least the first one in Z2
    Z2MultipartAction("Z2", "DarkRitual", [1]),
    Z2Action("Z2", "ContinueOn"),

    # Zone 3

    Z3ProgressAction("Z3", "City"),
    Z3LimitedAction("Z3", "Gamble", ["Z3 - City"], 20),
    Z3Action("Z3", "Drunk"),
    Z3Action("Z3", "BuyManaZ3"),
    Z3Action("Z3", "SellPotions"),
    # I remember this being hard, i'll put this here to unlock it during testing and see if it's like Z5+ content
    Z3MultipartAction("Z3", "AdvGuild", [1]),
    Z3Action("Z3", "GatherTeam"),
    Z3MultipartAction("Z3", "LDungeon", [1, 2, 3]),
    # Ditto
    Z3MultipartAction("Z3", "CraftGuild", [1]),
    Z3ProgressAction("Z3", "Apprentice"),
    Z3ProgressAction("Z3", "Mason"),
    Z3ProgressAction("Z3", "Architect"),
    Z3Action("Z3", "ReadBooks"),
    Z3Action("Z3", "BuyPickaxe"),
    Z3Action("Z3", "StartTrek"),
    
    # Zone 4

    Z4ProgressAction("Z4", "Mountain"),
    Z4LimitedAction("Z4", "Geysers", ["Z4 - Mountain"], 20),
    Z4ProgressAction("Z4", "Runes"),
    Z4SkillAction("Z4", "Chronomancy", "Chronomancy"),
    # I forget if this is Z5+ content, I think it is because you need twice the possible herbs
    # Z4Action("Z4", "LoopingPotion"),
    Z4SkillAction("Z4", "Pyromancy", "Pyromancy"),
    Z4ProgressAction("Z4", "Cavern"),
    Z4LimitedAction("Z4", "MineSoulstones", ["Z4 - Cavern"], 30),
    Z4MultipartAction("Z4", "HuntTrolls", [1]),
    Z4ProgressAction("Z4", "Illusions"),
    Z4LimitedAction("Z4", "Artifacts", ["Z4 - Illusions"], 20),
    Z4MultipartAction("Z4", "ImbueMind", [1]),
    # This one was *absolutely* later content
    # Z4MultipartAction("Z4", "ImbueBody", [1]),
    Z4Action("Z4", "FaceJudgement", rules=judgementRules)
]

location_id = 1
location_to_id = {}
item_id = 1
item_to_id = {}

all_locations = []
all_items = []

all_actions = all_actions + filler_actions

for action in all_actions:
    locations, location_id = action.locations(location_id, location_to_id)
    all_locations += locations
    items, item_id = action.items(item_id, item_to_id)
    all_items += items

# Two pots for double chance
filler_item_names = [action.unlock_item_name() for action in filler_actions] + ["Z1 - Pots", "Z1 - Pots"]