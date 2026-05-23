from dataclasses import dataclass

from Options import Choice, DeathLinkMixin, PerGameCommonOptions

class Goal(Choice):
    """Defines the goal to accomplish in order to complete the randomizer.

    - Zone 1: Complete "Start Journey".

    - Zone 2:

    - Zone 3:"""
    display_name = "Goal"
    option_z1 = 0
    option_z2 = 1
    option_z3 = 2
    default = 0

@dataclass
class IdleLoopsOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
