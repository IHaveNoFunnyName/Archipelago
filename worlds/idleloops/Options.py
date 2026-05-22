from dataclasses import dataclass

from Options import Choice, DeathLinkMixin, PerGameCommonOptions

class Goal(Choice):
    """Defines the goal to accomplish in order to complete the randomizer.

    - Full Story In Order: Complete each act in order. You can return to previously completed acts.

    - Full Story Any Order: Complete each act in any order. All acts are available from the start.

    - First Act: Complete Act 1 by finding the New Game button. Great for a smaller scale randomizer."""
    display_name = "Goal"
    option_full_story_in_order = 0
    option_full_story_any_order = 1
    option_first_act = 2
    default = 0

@dataclass
class IdleLoopsOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
