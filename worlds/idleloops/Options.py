from dataclasses import dataclass

from Options import Choice, DeathLinkMixin, DefaultOnToggle, NamedRange, PerGameCommonOptions, Range, Toggle


class Goal(Choice):
    """Defines the goal to accomplish in order to complete the randomizer.

    - Zone 1: Complete "Start Journey". Should take a few hours to a day.

    - Zone 2: Complete "Continue On". Should be a few days, high variability.

    - Zone 3: Complete "Start Trek". Similar length to Z2.

    - Zone 4: Complete "Face Judgement" with 50 or -50 reputation. Should take around a week."""
    display_name = "Goal"
    option_z1 = 0
    option_z2 = 1
    option_z3 = 2
    option_z4 = 3
    default = 0


class LocationProgress(DefaultOnToggle):
    """Adds locations to progress bars (Every 10%, some extras toward 0% and 100%)

    As there are no vanilla unlock or action story locations for progress bars (yet) without this option,
    you get nothing from progress bars except vanilla mechanics.
    (lootables [which are checks], mana reduction on certain actions, etc...)

    Non-vanilla locations force Filler items to be added to the pool."""
    display_name = "Locations: Progress Bars"


class ItemSearch(DefaultOnToggle):
    """Requires (and adds to the item pool) "x - Search" items for each lootable, being needed to check them."""
    display_name = "Items: Search Items"


class LocationSkill(NamedRange):
    """
    For 'normal' scaling skills, an item will be placed every 10 levels up to this value.

    "default" is based on goal (Z1 = 50, Z2 = 100, Z3 = 200, Z4 = 300)

    Applies to Combat, Magic, Practical Magic, Dark Magic, Chronomancy and Pyromancy.

    For each zone, the "default" above is also the last location in logic for that zone
    (i.e. With setting this to 500 and a Z4 goal, "Continue On" [required to leave Z2] can not be placed above 100).

    Non-vanilla locations force Filler items to be added to the pool.

    I wanted to split this per skill and per zone logic, but that seems like entirely too many options.
    """
    display_name = "Locations: Skills"
    range_start = 0
    range_end = 500
    special_range_names = {
        "default": -1,
    }
    default = "default"


class LocationAlchemy(NamedRange):
    """
    An item will be placed every 5 levels up to this value.

    "default" is based on goal (Z2 = 25, Z3 = 50, Z4 = 75)

    For each zone, the "default" above is also the last location in logic for that zone

    Non-vanilla locations force Filler items to be added to the pool.
    """
    display_name = "Locations: Alchemy (Skill)"
    range_start = 0
    range_end = 100
    special_range_names = {
        "default": -1,
    }
    default = "default"


class LocationCrafting(NamedRange):
    """
    Look, I straight up forgot how fast crafting is to level. Or even that crafting existed as a skill. How'd I miss it for previous apworld versions? I had the crafting guild!

    An item will be placed every 5 levels up to this value.

    "default" is based on goal (Z3 = 25, Z4 = 50), random guess until I'm better informed. I remember it being slow.

    For each zone, the "default" above is also the last location in logic for that zone.

    Non-vanilla locations force Filler items to be added to the pool."""
    display_name = "Locations: Crafting (Skill)"
    range_start = 0
    range_end = 100
    special_range_names = {
        "default": -1,
    }
    default = "default"


class BatchZ2(DefaultOnToggle):
    """Batches Herbs/Wild Mana locations and items 10x

    Herbs/Wild Mana basically give you 300 checks the moment you can get to them, way more dense than anywhere else in the game.

    This cuts down on that, reducing the chance that like 4 important items are just lying on the forest floor, and reducing total 'filler' in the pool.
    """
    display_name = "Batch Herbs/Wild Mana 10x"


class FillerStartingMana(DefaultOnToggle):
    """Filler items can include +50 starting mana"""
    display_name = "Filler Item: Starting Mana"


class FillerStartingGold(DefaultOnToggle):
    """Filler items can include +1 starting gold"""
    display_name = "Filler Item: Starting Gold"


class FillerExtraManaPot(DefaultOnToggle):
    """Filler items can include extra Mana Pots"""
    display_name = "Filler Item: Extra Mana Pot"


class FillerNothing(Range):
    """Percent chance a filler item will be 'nothing' (instead of one of the filler items above)."""
    display_name = "Filler Item: Nothing"
    range_start = 0
    range_end = 100
    default = 50


class FillerGameSpeed(Range):
    """Adds +0.1 Game Speed items to the pool, to a total of (value)x with all collected."""
    display_name = "Item: Game Speed (total)"
    range_start = 1
    range_end = 10
    default = 5


class FillerExpMult(Range):
    """Adds +0.1 Exp Multiplier items to the pool, to a total of (value)x with all collected."""
    display_name = "Item: Exp Mult (total)"
    range_start = 1
    range_end = 10
    default = 5


class FillerProgressiveLootable(DefaultOnToggle):
    """Shuffles in 20 extra Lootables into the pool, supplanting each Lootable to their max in turn - in *rough* order of usefulness/zone. 
    i.e. 15 Short Quests, 8 Long Quests, 3 Locks, 10 Progressive Lootables = 20 Short Quests, 10 Long Quests, 6 Locks
    And finding another Short Quest would in effect be one more Lock.
    If what an item practically gives is different from its name, there will be an entry in the log.
    When doing Z4 testing I found myself having almost no mana in Z1 a few times, and this is a way to solve that without going over the vanilla maximum."""
    display_name = "Item: Progressive Lootables"


class Bonus(Choice):
    """How much bonus time to start with.

    I recommend at least a day, so the start isn't as much of a slog, but caution against infinite as the idea behind this game's bonus time is that time spent paused figuring out what's best for the next loop doesn't cost you anything, as you get that time back in bonus.
    If you never run out however, that time actually costs you.

    But I totally get that the game is reeaaallllyyy slow without 5x speed so you do you. There's also Gamespeed Filler items to speed it up."""
    display_name = "Bonus Time"
    option_none = 0
    option_1_hour = 3600000
    option_1_day = 86400000
    option_1_week = 604800000
    option_infinite = 9999999999999
    default = 86400000


class SoulLink(Toggle):
    """All players playing Idle Loops with this option enabled will share soulstones."""
    display_name = "Soul Link"

# class EnergyLink(Toggle):
#     """Very experimental to see how easy it is to add an action to the game (also, how xLink stuff is implimented clientside).

#     If enabled, adds two extra actions to Z1:

#     1) An action roughly as difficult as Small Dungeon, that takes mana out of the energy link.

#     2) An action that instantly puts the remainder of your mana into the energy link."""
#     display_name = "Energy Link"

# class Logic(Choice):
#     """Whelp, turns out the one case I had for this turned out to be patched out on the new fork, so commenting this out for now."""
#     display_name = "Logic Difficulty"
#     option_normal = 0
#     option_hard = 1
#     default = 0


@dataclass
class IdleLoopsOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
    location_progress: LocationProgress
    item_search: ItemSearch
    location_skill: LocationSkill
    location_alchemy: LocationAlchemy
    location_crafting: LocationCrafting
    batch_z2: BatchZ2
    filler_starting_mana: FillerStartingMana
    filler_starting_gold: FillerStartingGold
    filler_extra_mana_pot: FillerExtraManaPot
    filler_nothing: FillerNothing
    filler_game_speed: FillerGameSpeed
    filler_exp_mult: FillerExpMult
    filler_progressive_lootable: FillerProgressiveLootable
    bonus: Bonus
    soul_link: SoulLink
    # energy_link: EnergyLink
    # logic: Logic
