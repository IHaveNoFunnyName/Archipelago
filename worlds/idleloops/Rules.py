from typing import Dict, Callable, TYPE_CHECKING
from BaseClasses import CollectionState
from .Options import Goal

if TYPE_CHECKING:
    from . import IdleLoopsWorld
else:
    IdleLoopsWorld = object


# Based on The Messenger's implementation
class IdleLoopsRules:
    player: int
    world: IdleLoopsWorld
    location_rules: Dict[str, Callable[[CollectionState], bool]]
    region_rules: Dict[str, Callable[[CollectionState], bool]]

    def __init__(self, world: IdleLoopsWorld) -> None:
        self.player = world.player
        self.world = world
        self.location_rules = {
        }
        self.region_rules = {
        }

    def set_all_rules(self) -> None:
        multiworld = self.world.multiworld
        for region in multiworld.get_regions(self.player):
            if self.world.options.goal == Goal.option_full_story_in_order:
                if region.name in self.region_rules:
                    for entrance in region.entrances:
                        entrance.access_rule = self.region_rules[region.name]
            for loc in region.locations:
                if loc.name in self.location_rules:
                    loc.access_rule = self.location_rules[loc.name]
