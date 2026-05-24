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
    Z2 = 0
    Z3 = 1

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
        return [self.unlock_item_name()] + [f"{self.skill} - Level {n}" for n in self.skill_locations]

class FillerItem(Action):
    def __init__(self, name: str, classification: ItemClassification=ItemClassification.filler, tags: List[Tags]=None):
        super().__init__("Filler", name, classification, tags=tags)
    def location_list(self) -> List[str]:
        return []

# Can i finagle the MRO enough to not have to subclass action? Probably! But lets be safe.
class A2(Action):
    def __init__(self, *args, tags: List[Tags]=None, **kwargs):
        super().__init__(*args, **kwargs, tags=(tags or []) + [Tags.Z2])

class A2Action(A2, Action):
    pass
class A2ProgressAction(A2, ProgressAction):
    pass
class A2LimitedAction(A2, LimitedAction):
    def __init__(self, *args, classification: ItemClassification=ItemClassification.useful, **kwargs):
        super().__init__(*args, classification=classification, **kwargs)
class A2MultipartAction(A2, MultipartAction):
    pass
class A2SkillAction(A2, SkillAction):
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

# It's only items but calling it actions makes it fit with the others
filler_actions = [
    FillerItem("50 Starting Mana"),
    FillerItem("1 Starting Gold"),
    FillerItem("+0.1 Game Speed"),
]

z1_actions = [
    # I assume this is not the proper way to handle rules for starting items,
    # but the world failed to generate because wander locations needed wander item, so nothing could be placed anywhere.
    # I assumed this is what push_precollected was for - i guess not - deleting the rule solved it.
    ProgressAction("Z1", "Wander", rules=lambda *args: {}),
    LimitedAction("Z1", "Pots", [], 50, 0, lootable_classification=ItemClassification.filler, rules=lambda *args: {}),
    LimitedAction("Z1", "Locks", [], 10),
    Action("Z1", "BuyGlasses"),
    Action("Z1", "BuyManaZ1", ItemClassification.progression),
    ProgressAction("Z1", "Met", ItemClassification.progression),
    Action("Z1", "TrainStrength"),
    LimitedAction("Z1", "SQuests", ["Z1 - Met"], 20),
    ProgressAction("Z1", "Secrets", ItemClassification.progression),
    LimitedAction("Z1", "LQuests", ["Z1 - Secrets"], 10),
    Action("Z1", "ThrowParty"),
    SkillAction("Z1", "WarriorLessons", "Combat"),
    SkillAction("Z1", "MageLessons", "Magic"),
    # Looking for feedback on these limits, what's reasonably reachable in Z1/Z2. I feel 10/10/6 works for Z3+.
    MultipartAction("Z1", "Heal", range(1, 4), rules=healRules),
    MultipartAction("Z1", "Fight", range(1, 4), rules=fightRules),
    MultipartAction("Z1", "SDungeon", range(1, 4), rules=dungeonRules),
    Action("Z1", "BuySupplies", ItemClassification.progression),
    Action("Z1", "Haggle", ItemClassification.progression),
    Action("Z1", "StartJourney", ItemClassification.progression, rules=journeyRules)
]
z2_actions = [
    A2ProgressAction("Z2", "Forest"),
    A2LimitedAction("Z2", "WildMana", ["Z2 - Forest", "Z2 - Thicket"], 100, lootable_classification=ItemClassification.filler),
    A2LimitedAction("Z2", "Herbs", ["Z2 - Forest", "Z2 - Shortcut"], 200, lootable_classification=ItemClassification.filler),
    A2LimitedAction("Z2", "Hunt", ["Z2 - Forest"], 20, lootable_classification=ItemClassification.filler),
    A2Action("Z2", "SitByWaterfall"),
    A2ProgressAction("Z2", "Shortcut"),
    A2ProgressAction("Z2", "Hermit"),
    A2SkillAction("Z2", "PracticalMagic", "Practical"),
    # *techincally* there's a rule here for herbs but pffft that's not going to be an issue
    A2SkillAction("Z2", "LearnAlchemy", "Alchemy"),
    A2Action("Z2", "BrewPotions"),
    A2Action("Z2", "TrainDexterity"),
    A2Action("Z2", "TrainSpeed"),
    A2ProgressAction("Z2", "Flowers"),
    A2Action("Z2", "BirdWatching"),
    A2ProgressAction("Z2", "Thicket"),
    A2ProgressAction("Z2", "Witch"),
    A2SkillAction("Z2", "DarkMagic", "Dark"),
    # This feels like a Z3 location, but you can stretch for at least the first one in Z2
    A2MultipartAction("Z2", "DarkRitual", range(1, 2)),
    A2Action("Z2", "ContinueOn")
]

location_id = 1
location_to_id = {}
item_id = 1
item_to_id = {}

all_locations = []
all_items = []

all_actions = filler_actions + z1_actions + z2_actions

for action in all_actions:
    locations, location_id = action.locations(location_id, location_to_id)
    all_locations += locations
    items, item_id = action.items(item_id, item_to_id)
    all_items += items

# Two pots for double chance
filler_item_names = [action.unlock_item_name() for action in filler_actions] + ["Z1 - Pots", "Z1 - Pots"]