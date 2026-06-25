from dataclasses import dataclass

from Options import Choice, DeathLinkMixin, DefaultOnToggle, PerGameCommonOptions

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

# class Logic(Choice):
#     """Whelp, turns out the one case I had for this turned out to be patched out on the new fork, so commenting this out for now."""
#     display_name = "Logic Difficulty"
#     option_normal = 0
#     option_hard = 1
#     default = 0

class ProggressiveLootable(DefaultOnToggle):
    """Shuffles in 20 extra Lootables into the pool, supplanting each Lootable to their max in turn - in *rough* order of usefulness/zone. 
    i.e. 15 Short Quests, 8 Long Quests, 3 Locks, 10 Progressive Lootables = 20 Short Quests, 10 Long Quests, 6 Locks
    And finding another Short Quest would in effect be one more Lock.
    If what an item practically gives is different from its name, there will be an entry in the log.
    When doing Z4 testing I found myself having almost no mana in Z1 a few times, and this is a way to solve that without going over the vanilla maximum."""
    display_name = "Progressive Lootables"

class Bonus(Choice):
    """How much bonus time to start with.
    
    I recommend some time to start with, so the start isn't as much of a slog, but caution against infinite as the idea behind this game's bonus time is that time spent paused figuring out what's best for the next loop doesn't cost you anything, as you get that time back in bonus.
    If you never run out however, that time actually costs you.
    
    But I totally get that the game is reeaaallllyyy slow without 5x speed so you do you. Keep in mind that with the Gamespeed Filler item, you can easy get 5-10x gamespeed by Z4"""
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
    # logic: Logic
    bonus: Bonus
    proggressive_lootable: ProggressiveLootable