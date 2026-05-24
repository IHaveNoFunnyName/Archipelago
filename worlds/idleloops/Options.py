from dataclasses import dataclass

from Options import Choice, DeathLinkMixin, PerGameCommonOptions

class Goal(Choice):
    """Defines the goal to accomplish in order to complete the randomizer.

    - Zone 1: Complete "Start Journey". Should take a few hours.

    - Zone 2: Complete "Continue On". Z2 has a bunch of content but it's mostly side paths to make you stronger for Z3. Length depends on if you unlock "Continue On" early

    - Zone 3: Complete "whatever it is". Should take a few days
    """
    display_name = "Goal"
    option_z1 = 0
    option_z2 = 1
    option_z3 = 2
    default = 0

@dataclass
class IdleLoopsOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
