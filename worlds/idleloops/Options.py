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


class LogicBigSphere1(Toggle):
    """Puts Meet People and Investigate in Sphere 1 (i.e. Somewhere that doesn't require any items to access)
    to make it harder to be blocked early, but makes Z1 feel samey.

    Also, if the options you want create a restrictive start (i.e. fails to generate), having this on will help.

    Regardless of this option, Buy Mana is always a Local Sphere 1 item (meaning it's guaranteed to be in Wander or Pots)"""
    display_name = "Logic: Force Early Meet People/Investigate"


class LogicVanilla(Choice):
    """Respect vanilla requirements for actions.

    Off: The only requirement for an action is receiving its item (Well, and in-loop requirements like rep).

    Easy: Requirements like Small Dungeon requiring (Magic + Combat = 35) or PM requiring 50 Magic exist, but not progress bar requirements like PM requiring 25% Hermit Knowledge.
    Provides a reason to level Magic outside of the checks on itself.

    Hard: All vanilla requirements. Might feel quite close to vanilla as most actions have a progress bar requirement, constraining logic quite heavily."""
    display_name = "Logic: Vanilla Requirements"
    option_off = 0
    option_easy = 1
    option_hard = 2
    default = 1


class LogicManaReduction(DefaultOnToggle):
    """Should the randomiser consider Actions that reduce the Mana Cost of other Actions (Like Old Shortcut and Continue On, Talk To Witch and Dark Magic etc...)
    a logical requirement?

    Also includes Old Shortcut making Talk To Hermit give more Hermit Knowledge, that's basically the same thing despite not being a reduction."""
    display_name = "Logic: Mana Reduction Actions"


class LogicFight(Range):
    """The randomizer knows how much mana (and gold) you have access to (In Z1).
    As the gold you get from Fight Monsters is variable, it needs an estimate for how much you want to grind it up.
    9 is something you have to grind a bit for, but it pays off to have done in Z2+.
    3-5 is more reasonable for a not-grindy z1 goal."""
    display_name = "Logic: Fight Monsters Segments"
    range_start = 1
    range_end = 9
    default = 9


class LogicGlasses(Toggle):
    """Forces Glasses to appear in Z1 (And not deeper than 50% of Wander)."""
    display_name = "Logic: Buy Glasses in Z1"


class ItemGlasses(DefaultOnToggle):
    """Adds a second "Z1 - Buy Glasses" item to the pool, with both of them you start the loop with glasses."""
    display_name = "Items: Second Glasses"


class LocationProgress(DefaultOnToggle):
    """Adds locations to progress bars (Every 10%, some extras toward 0% and 100%)

    As there are no vanilla unlock or action story locations for progress bars (yet) without this option,
    you get nothing from progress bars after the first completion, except vanilla mechanics.
    (lootables [which are checks], mana reduction on certain actions, etc...)"""
    display_name = "Locations: Progress Bars"


class ItemSearch(DefaultOnToggle):
    """Requires "x - Search" items to be found to check for each lootable."""
    display_name = "Items: Search Items"


class LocationSkill(NamedRange):
    """For 'normal' scaling skills, an item will be placed every 10 levels up to this value.

    "default" is based on goal (Z1 = 50, Z2 = 100, Z3 = 200, Z4 = 300), these values are also what's in logic for each Zone.

    Applies to Combat, Magic, Practical Magic, Dark Magic, Chronomancy and Pyromancy.

    I wanted to split this per skill and per zone logic, but that seems like entirely too many options."""
    display_name = "Locations: Skills"
    range_start = 0
    range_end = 500
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (50, 100, 200, 300)


class LocationAlchemy(NamedRange):
    """An item will be placed every 5 levels up to this value.

    "default" is based on goal (Z2 = 25, Z3 = 50, Z4 = 75), these values are also what's in logic for each Zone."""
    display_name = "Locations: Alchemy (Skill)"
    range_start = 0
    range_end = 100
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (0, 25, 50, 75)


class LocationCrafting(NamedRange):
    """Look, I straight up forgot how fast crafting is to level. Or even that crafting existed as a skill. How'd I miss it for previous apworld versions? I had the crafting guild!

    An item will be placed every 5 levels up to this value.

    "default" is based on goal (Z3 = 25, Z4 = 50), these values are also what's in logic for each Zone."""
    display_name = "Locations: Crafting (Skill)"
    range_start = 0
    range_end = 100
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (0, 0, 25, 50)


class LocationHeal(NamedRange):
    """How many patients to put items on.

    "default" is based on goal (Z1 = 5, Z2 = 7, Z3 = 9, Z4 = 10), these values are also what's in logic for each Zone.

    I should probably change these defaults as I don't think they take into account doing multiple actions in one loop."""
    display_name = "Locations: Heal The Sick"
    range_start = 0
    range_end = 20
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (5, 7, 9, 10)


class LocationFight(NamedRange):
    """How many monsters to put items on.

    "default" is based on goal (Z1 = 3, Z2 = 5, Z3 = 7, Z4 = 10), these values are also what's in logic for each Zone.

    I should probably change these defaults as
    I don't think they take into account how high you can get doing multiple actions in one loop."""
    display_name = "Locations: Fight Monsters"
    range_start = 0
    range_end = 15
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (3, 5, 7, 10)


class LocationSmallDungeon(NamedRange):
    """How many Small Dungeon floors to put items on.

    "default" is based on goal (Z1 = 3, Z2 = 4, Z3 = 6/max), these values are also what's in logic for each Zone.
    """
    display_name = "Locations: Small Dungeon"
    range_start = 0
    range_end = 6
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (3, 4, 6, 6)


class LocationLargeDungeon(NamedRange):
    """How many Large Dungeon floors to put items on.

    "default" is based on goal (Z3 = 2, Z4 = 9/max), these values are also what's in logic for each Zone.
    """
    display_name = "Locations: Large Dungeon"
    range_start = 0
    range_end = 9
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (0, 0, 2, 9)


class LocationTrolls(Range):
    """How many trolls to put items on.

    No goal-dependent "default" this time as it's Z4 content and the highest goal is Z4. Watch this space."""
    display_name = "Locations: Trolls"
    range_start = 0
    range_end = 10
    default = 5
    defaults = (0, 0, 0, 5)


class LocationRitual(Range):
    """Max level of Dark Ritual to put items on.

    1 is in logic for Z2, 2+ is Z4."""
    display_name = "Locations: Dark Ritual"
    range_start = 0
    range_end = 66
    default = 1
    defaults = (0, 1, 1, 10)


class LocationMind(Range):
    """Max level of Imbue Mind to put items on.

    I'm not up to Imbue Mind in my casual playthrough yet, so I don't know what a reasonable default is.

    I'm pretty sure the vanilla cap was *unreasonably* high too, I'll just put 50."""
    display_name = "Locations: Imbue Mind"
    range_start = 0
    range_end = 50
    default = 5
    defaults = (0, 0, 0, 5)


class ItemShop(DefaultOnToggle):
    """Requires items to be found to unlock the shop actions below"""
    display_name = "Items: AP Shop Unlock"


class LocationZ1Shop(Range):
    """Adds an action to Z1 to buy up to N items for gold. Starting at 50 and ramping up to 300"""
    display_name = "Locations: Z1 AP Shop"
    range_start = 0
    range_end = 20
    default = 0


class LocationZ3Shop(Range):
    """Adds an action to Z3 to buy up to N items for gold. Starting at, I don't know, 500 and ramping up to 1000. Sure."""
    display_name = "Locations: Z3 AP Shop"
    range_start = 0
    range_end = 20
    default = 0


class BatchZ2(DefaultOnToggle):
    """Batches Herbs/Wild Mana locations and items to give 10x each.

    Herbs/Wild Mana basically give you 300 checks the moment you can get to them, way more dense than anywhere else in the game.

    This cuts down on that, reducing the chance that like 4 important items are just lying on the forest floor, and also reducing total 'filler' in the pool.
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


class FillerProgressiveLootable(Range):
    """Adds extra Progressive Lootables to the pool, helping each Lootable to their max in turn - in *rough* order of usefulness/zone. 
    i.e. 15 Short Quests, 8 Long Quests, 3 Locks, 10 Progressive Lootables = 20 Short Quests, 10 Long Quests, 6 Locks
    And finding another Short Quest would in effect be one more Lock.
    If what an item practically gives is different from its name, there will be an entry in the log.
    When doing Z4 testing I found myself having almost no mana in Z1 a few times, and this is a way to solve that without going over the vanilla maximum."""
    display_name = "Item: Progressive Lootables"
    range_start = 0
    range_end = 40
    default = 20


class FillerGameSpeed(Range):
    """Adds +0.1 Game Speed items to the pool, to a total of (value)x with all collected.
    Multiplicative with Starting Game Speed below."""
    display_name = "Item: Game Speed (total)"
    range_start = 1
    range_end = 10
    default = 5


class FillerExpMult(Range):
    """Adds +0.1 Exp Multiplier items to the pool, to a total of (value)x with all collected.
    Multiplicative with Starting Exp Mult below."""
    display_name = "Item: Exp Mult (total)"
    range_start = 1
    range_end = 10
    default = 5


class GameSpeed(Range):
    """Multiplicative with Filler Game Speed above."""
    display_name = "Starting Game Speed"
    range_start = 1
    range_end = 10
    default = 1


class StatExpMult(Range):
    """Multiplicative with Filler Exp Mult above."""
    display_name = "Starting Stat Exp Mult"
    range_start = 1
    range_end = 10
    default = 1


class SkillExpMult(Range):
    """Skills are easily the most grindy part of the game, lets cut that down huh?"""
    display_name = "Skill Exp Mult"
    range_start = 1
    range_end = 10
    default = 1


class Bonus(Choice):
    """How much bonus time to start with."""
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
#     """Primarily to see how easy it is to add an action to the game rather than an actual feature
#     (also, how xLink stuff is implimented clientside, but that's also SoulLink above).

#     If enabled, adds two extra actions to Z1:

#     1) An action roughly as difficult as Small Dungeon, that takes mana out of the energy link.

#     2) An action that instantly puts the remainder of your mana into the energy link."""
#     display_name = "Energy Link"


class ModUICrime(DefaultOnToggle):
    """Replaces the confusing and obtuse n <- n <- n UI for Lootables with n / n Unchecked: n
    Which you can actually parse without having to already know what it means."""
    display_name = "Mod: Fix Vanilla UI Crime"


@dataclass
class IdleLoopsOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
    logic_big_sphere1: LogicBigSphere1
    logic_vanilla: LogicVanilla
    logic_mana_reduction: LogicManaReduction
    logic_fight: LogicFight
    logic_glasses: LogicGlasses
    item_glasses: ItemGlasses
    location_progress: LocationProgress
    item_search: ItemSearch
    location_skill: LocationSkill
    location_alchemy: LocationAlchemy
    location_crafting: LocationCrafting
    location_heal: LocationHeal
    location_fight: LocationFight
    location_sd: LocationSmallDungeon
    location_ritual: LocationRitual
    location_ld: LocationLargeDungeon
    location_trolls: LocationTrolls
    location_mind: LocationMind
    item_shop: ItemShop
    location_z1_shop: LocationZ1Shop
    location_z3_shop: LocationZ3Shop
    batch_z2: BatchZ2
    filler_starting_mana: FillerStartingMana
    filler_starting_gold: FillerStartingGold
    filler_extra_mana_pot: FillerExtraManaPot
    filler_nothing: FillerNothing
    filler_progressive_lootable: FillerProgressiveLootable
    filler_game_speed: FillerGameSpeed
    filler_exp_mult: FillerExpMult
    game_speed: GameSpeed
    stat_exp_mult: StatExpMult
    skill_exp_mult: SkillExpMult
    bonus: Bonus
    soul_link: SoulLink
    # energy_link: EnergyLink
    mod_ui_crime: ModUICrime
