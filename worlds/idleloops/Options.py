from dataclasses import dataclass

from Options import Choice, DeathLinkMixin, PerGameCommonOptions

class Goal(Choice):
    """Defines the goal to accomplish in order to complete the randomizer.

    - Zone 1: Complete "Start Journey". Should take a few hours-a day.

    - Zone 2: Complete "Continue On". Z2 has a bunch of content but it's mostly side paths to make you stronger for Z3. Length depends on where "Continue On" is placed.

    - Zone 3: Complete "Start Trek". Should take a few days

    - Zone 4: Complete Face Judgement"""
    display_name = "Goal"
    option_z1 = 0
    option_z2 = 1
    option_z3 = 2
    option_z4 = 3
    default = 0

class Logic(Choice):
    """Weather to include 'hard' logic, like leaving Z1 with Fight Monsters or Heal, but without Warrior or Magic Lessons respectively.
    
    I say "like", but that's the only effect right now."""
    display_name = "Logic Difficulty"
    option_normal = 0
    option_hard = 1
    default = 0

class Bonus(Choice):
    """How much bonus time to start with.
    
    I recommend some time to start with, so the start isn't as much of a slog, but caution against infinite as the idea behind this game's bonus time is that time spent paused figuring out what's best for the next loop doesn't cost you anything, as you get that time back in bonus.
    If you never run out however, that time actually costs you.
    
    But I totally get that the game is reeaaallllyyy slow without 5x speed so you do you."""
    display_name = "Bonus Time"
    option_none = 0
    option_1_hour = 3600000
    option_1_day = 86400000
    option_1_week = 604800000
    option_infinite = 9999999999999
    default = 86400000

@dataclass
class IdleLoopsOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
    logic: Logic
    bonus: Bonus