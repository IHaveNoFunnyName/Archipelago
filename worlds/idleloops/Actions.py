from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

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

class Action:
    def __init__(self, zone: str, name: str, classification: ItemClassification=ItemClassification.useful, rules: callable=None):
        self.zone = zone
        self.name = name
        self.classification = classification
        self.rules_override = rules

    def location_list(self) -> List[str]:
        # Base 'complete action for the first time' location
        return [f"{self.zone} - {self.name}"]
    
    def locations(self, location_id, location_to_id) -> Tuple[List[str], int]:
        names = self.location_list()
        output = []
        for name in names:
            location_to_id[name] = location_id
            output.append(name)
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
    progress_locations = ["1", "10", "25", "50", "75", "90", "95", "99", "100"]
    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - {progress}%" for progress in self.progress_locations]

class LimitedAction(Action):
    def __init__(self, zone: str, name: str, count: int=1, item_count: int=None, classification: ItemClassification=ItemClassification.progression, lootable_classification: ItemClassification=ItemClassification.filler, rules: callable=None):
        super().__init__(zone, name, classification, rules)
        self.lootable_classification = lootable_classification
        self.count = count
        self.item_count = item_count if item_count is not None else count
    
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

class MultipartAction(Action):
    def __init__(self, zone: str, name: str, count: int, classification: ItemClassification=ItemClassification.useful, rules: callable=None):
        super().__init__(zone, name, classification, rules)
        self.count = count
    
    def location_list(self) -> List[str]:
        return [f"{self.zone} - {self.name} - Completion #{i}" for i in range(1, self.count + 1)]

# I'm not happy with the boilerplate this needs, but just passing rule would lose access to Action.self

# I actually can't remember how leaving Z1 works at first, do you get through it haggling or buying for full cost?
# I think it's haggling because Z2 doesn't use gold, to bring more mana into Z2.
# But also, this is a rando, maybe it should be haggle || full cost and then let the rando sort it out.
# That's probably future work once i actually know how to construct rules, this is fine for now.
def suppliesRules(self: Action, world, player) -> Dict[str, callable]:
    def rule(state: CollectionState) -> bool:
        return state.has_all_counts({
            "Z1 - LQuests": 10,
            "Z1 - SQuests": 10,
            "Z1 - BuyManaZ1": 1,
            "Z1 - Haggle": 1,
            self.unlock_item_name(): 1,
        }, player)
    return {name: rule for name in self.location_list()}

def journeyRules(self: Action, world, player) -> Dict[str, callable]:
    def rule(state: CollectionState) -> bool:
        return state.has_all_counts({
            "Z1 - BuySupplies": 1,
            self.unlock_item_name(): 1,
        }, player)
    return {name: rule for name in self.location_list()}

all_actions = [
    # I assume this is not the proper way to handle rules for starting items,
    # but the world failed to generate because wander locations needed wander item, so nothing could be placed anywhere.
    # I assumed this is what push_precollected was for - i guess not - deleting the rule solved it.
    ProgressAction("Z1", "Wander", rules=lambda *args: {}),
    LimitedAction("Z1", "Pots", 50, 25, rules=lambda *args: {}),
    LimitedAction("Z1", "Locks", 10),
    Action("Z1", "BuyGlasses"),
    Action("Z1", "BuyManaZ1", ItemClassification.progression),
    ProgressAction("Z1", "Met"),
    Action("Z1", "TrainStrength"),
    LimitedAction("Z1", "SQuests", 20),
    ProgressAction("Z1", "Secrets"),
    LimitedAction("Z1", "LQuests", 10),
    Action("Z1", "ThrowParty"),
    Action("Z1", "WarriorLessons"),
    Action("Z1", "MageLessons"),
    # Heal/Fight Monsters with 0 skill still grants exp, so these are not blocked by Mage/Warrior Lessons 
    MultipartAction("Z1", "Heal", 1),
    MultipartAction("Z1", "Fight", 1),
    MultipartAction("Z1", "SDungeon", 1),
    Action("Z1", "BuySupplies", ItemClassification.progression, rules=suppliesRules),
    Action("Z1", "Haggle", ItemClassification.progression),
    Action("Z1", "StartJourney", ItemClassification.progression, rules=journeyRules)
]

location_id = 1
location_to_id = {}
item_id = 1
item_to_id = {}

all_locations = []
all_items = []

for action in all_actions:
    locations, location_id = action.locations(location_id, location_to_id)
    all_locations += locations
    items, item_id = action.items(item_id, item_to_id)
    all_items += items