from dataclasses import dataclass

from Options import Choice, DeathLinkMixin, DefaultOnToggle, NamedRange, PerGameCommonOptions, Range, Toggle, Visibility


class Goal(Choice):
    """- Zone 1: Complete "Start Journey". Should take a few hours.
    (With 2-4x gamespeed).

    - Zone 2: Complete "Continue On".

    - Zone 3: Complete "Start Trek".

    - Zone 4: Complete "Face Judgement" with 50 or -50 reputation.
    Should take around a week (with 5-7x gamespeed).

    Content from Zones above the goal is not randomised."""
    display_name = "Goal"
    option_zone_1 = 0
    option_zone_2 = 1
    option_zone_3 = 2
    option_zone_4 = 3
    default = 0


class LogicBigSphere1(Toggle):
    """Find Meet People and Investigate early.
    Reduces the chance of a fill error.
    Gives a warning if this is not enabled for a Z3+ goal.

    Regardless of this option, Buy Mana is always found early."""
    display_name = "Logic: Force Early Meet People/Investigate"


class LogicVanilla(Choice):
    """Respect vanilla requirements for actions.

    Off: The only requirement for an action is receiving its item
    (Well, and in-loop requirements like rep).

    Skill: Skill requirements (Combat/Magic etc...) are Vanilla,
    but Progress Bar requirements are ignored.

    All: A hidden unsupported option, for all Vanilla requirements.
    It feels too close to Vanilla as most actions have a Progress requirement.
    (i.e. Z1 *has* to be Wander > Meet People > Investigate > Combat/Magic)
    and such constrained logic leads to fill errors (why it's unsupported).
    To enable add `logic_vanilla_all: 'true'` to the .yaml.
    This is bad UX, but i needed friction to make clear that it's unsupported."""
    display_name = "Logic: Vanilla Requirements"
    option_off = 0
    option_skill = 1
    default = 1


class LogicVanillaAll(Toggle):
    display_name = "hidden"
    visibility = Visibility.none


class LogicManaReduction(Toggle):
    """Makes Actions that reduce the Mana Cost of other Actions a requirement
    for what they reduce.
    (Also includes Old Shortcut for Talk To Hermit)"""
    display_name = "Logic: Mana Reduction Actions"


class LogicFight(Range):
    """The randomizer knows how much mana you have access to (In Z1).
    As the gold you get from Fight Monsters is variable,
    it needs to know how much you want to grind it up.
    9 takes some grinding a bit for, but it pays off to have done in Z2+.
    3-5 is more reasonable for a not-grindy z1 goal."""
    display_name = "Logic: Fight Monsters Segments"
    range_start = 1
    range_end = 9
    default = 9


class LogicGlasses(Toggle):
    """Forces Glasses to appear in Z1 (And available before 50% of Wander)."""
    display_name = "Logic: Buy Glasses in Z1"


class ItemGlasses(DefaultOnToggle):
    """Adds a second "Z1 - Buy Glasses" item to the pool.
    With both of them you start the loop with glasses."""
    display_name = "Items: Second Glasses"


class LocationProgress(DefaultOnToggle):
    """Adds locations to progress bars (around every 10%)

    Otherwise, there is only one location per progress bar,
    for the first completion of its action.

    Reduces the chance of a fill error.
    Gives a warning if this is not enabled for a Z3+ goal.
    """
    display_name = "Locations: Progress Bars"


class ItemSearch(DefaultOnToggle):
    """Adds "x - Search" items, needed to check each lootable type.
    (Lootables are stuff like Mana Pots)"""
    display_name = "Items: Lootable Search Items"


class LocationSkill(NamedRange):
    """Add an item every 10 levels up to this value for:
    Combat, Magic, Practical Magic, Dark Magic, Chronomancy and Pyromancy.

    "default" is based on goal (Z1 = 30, Z2 = 100, Z3 = 200, Z4 = 300)
    These are also what's in logic for each Zone.

    Gives a warning if set 'too high' for the goal."""
    display_name = "Locations: Skills"
    range_start = 0
    range_end = 500
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (30, 100, 200, 300)


class LocationAlchemy(NamedRange):
    """Add an item every 5 levels up to this value for Alchemy.

    "default" is based on goal (Z2 = 25, Z3 = 50, Z4 = 75)
    These values are also what's in logic for each Zone."""
    display_name = "Locations: Alchemy (Skill)"
    range_start = 0
    range_end = 100
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (0, 25, 50, 75)


class LocationCrafting(NamedRange):
    """Look, I straight up forgot how fast crafting is to level.
    Or even that crafting existed as a skill.
    How'd I miss it for previous apworld versions? I had the crafting guild!

    Add an item every 5 levels up to this value for Crafting.

    "default" is based on goal (Z3 = 25, Z4 = 50)
    These values are also what's in logic for each Zone."""
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

    "default" is based on goal (Z1 = 5, Z2 = 7, Z3 = 9, Z4 = 15)
    These values are also what's in logic for each Zone.

    Gives a warning if set 'too high' for the goal.

    I should probably change these defaults after some playtesting.
    I don't think they take into account doing multiple actions in one loop."""
    display_name = "Locations: Heal The Sick"
    range_start = 0
    range_end = 20
    special_range_names = {
        "default": -1,
    }
    default = "default"
    defaults = (5, 7, 9, 15)


class LocationFight(NamedRange):
    """How many monsters to put items on.

    "default" is based on goal (Z1 = 3, Z2 = 5, Z3 = 7, Z4 = 10)
    These values are also what's in logic for each Zone.

    Gives a warning if set 'too high' for the goal.

    I should probably change these defaults after some playtesting.
    I don't think they take into account doing multiple actions in one loop."""
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

    "default" is based on goal (Z1 = 3, Z2 = 4, Z3 = 6/max)
    These values are also what's in logic for each Zone.
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

    "default" is based on goal (Z3 = 2, Z4 = 9/max)
    These values are also what's in logic for each Zone.
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

    No goal-dependent "default" this time,
    as it's Z4 content and the highest goal is Z4. Watch this space."""
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
    range_end = 10
    default = 1
    defaults = (0, 1, 1, 10)


class LocationMind(Range):
    """Max level of Imbue Mind to put items on.

    I'm not up to Imbue Mind in my casual playthrough yet,
    so I don't know what a reasonable default is."""
    display_name = "Locations: Imbue Mind"
    range_start = 0
    range_end = 5
    default = 5
    defaults = (0, 0, 0, 5)


class ItemShop(Toggle):
    """Requires items to be found to unlock the shop actions below"""
    display_name = "Items: AP Shop Unlock"


class LocationZ1Shop(Range):
    """Adds an action to Z1 to buy up to N items for gold."""
    display_name = "Locations: Z1 AP Shop"
    range_start = 0
    range_end = 20
    default = 0


class Z1ShopMin(Range):
    """Minimum cost of items in Z1 AP Shop"""
    display_name = "Z1 AP Shop: Min Cost"
    range_start = 10
    range_end = 100
    default = 50


class Z1ShopMax(Range):
    """Maximum cost of items in Z1 AP Shop.

    Throws an error if set above 200 gold for a Z1 goal.
    For now that's a random guess at how much you can get in Z1.
    I'll change it after playtesting."""
    display_name = "Z1 AP Shop: Max Cost"
    range_start = 50
    range_end = 300
    default = 300


class LocationZ3Shop(Range):
    """Adds an action to Z3 to buy up to N items for gold."""
    display_name = "Locations: Z3 AP Shop"
    range_start = 0
    range_end = 20
    default = 0


class Z3ShopMin(Range):
    """Minimum cost of items in Z3 AP Shop"""
    display_name = "Z3 AP Shop: Min Cost"
    range_start = 100
    range_end = 1000
    default = 500


class Z3ShopMax(Range):
    """Maximum cost of items in Z3 AP Shop"""
    display_name = "Z3 AP Shop: Max Cost"
    range_start = 500
    range_end = 2000
    default = 1000


class BatchZ2(Toggle):
    """Batches Herbs/Wild Mana locations and items 10x.

    Herbs/Wild Mana basically give you 300 checks the moment
    you can get to them, way more dense than anywhere else in the game.

    This cuts down on that, reducing the chance that like 4 important items
    are just lying on the forest floor, and also reducing total 'filler'.
    """
    display_name = "Batch Herbs/Wild Mana 10x"
    visibility = Visibility.none


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
    """Percent chance a filler item will be 'nothing'
    (instead of one of the filler items above)."""
    display_name = "Filler Item: Nothing"
    range_start = 0
    range_end = 100
    default = 50


class FillerProgressiveLootable(Range):
    """Adds extra Lootables to the pool,
    helping each Lootable to their max in *rough* order of usefulness and zone.
    If what an item practically gives is different from its name,
    there will be an entry in the log."""
    display_name = "Item: Progressive Lootables"
    range_start = 0
    range_end = 40
    default = 20


class FillerGameSpeed(Range):
    """Adds +0.1 Game Speed items to the pool, to a total of (value)x.
    Multiplicative with Starting Game Speed below.

    The game slows down over time so some of this can help it feel more even."""
    display_name = "Item: Game Speed (total)"
    range_start = 1
    range_end = 10
    default = 2


class FillerExpMult(Range):
    """Adds +0.1 Exp Multiplier items to the pool, to a total of (value)x.
    Multiplicative with Starting Exp Mult below."""
    display_name = "Item: Exp Mult (total)"
    range_start = 1
    range_end = 10
    default = 5


class GameSpeed(Range):
    """Multiplicative with Filler Game Speed above."""
    display_name = "Global Game Speed"
    range_start = 1
    range_end = 10
    default = 2


class StatExpMult(Range):
    """Multiplicative with Filler Exp Mult above.

    I think the filler version of this feels better,
    but no reason not to have this option."""
    display_name = "Global Stat Exp Mult"
    range_start = 1
    range_end = 10
    default = 1


class SkillExpMult(Range):
    """Skills are easily the most grindy part of the game
    lets cut that down huh?"""
    display_name = "Global Skill Exp Mult"
    range_start = 1
    range_end = 10
    default = 2


class Bonus(Choice):
    """How much bonus time to start with."""
    display_name = "Bonus Time"
    option_none = 0
    option_5_hours = 18000000
    option_1_day = 86400000
    option_1_week = 604800000
    option_infinite = 9999999999999
    default = 86400000


# class SoulLink(Toggle):
#     """All players playing Idle Loops with this option enabled will share soulstones."""
#     display_name = "Soul Link"


# class EnergyLink(Toggle):
#     """Primarily to see how easy it is to add an action to the game rather than an actual feature
#     (also, how xLink stuff is implimented clientside, but that's also SoulLink above).

#     If enabled, adds two extra actions to Z1:

#     1) An action roughly as difficult as Small Dungeon, that takes mana out of the energy link.

#     2) An action that instantly puts the remainder of your mana into the energy link."""
#     display_name = "Energy Link"


class ModUICrime(DefaultOnToggle):
    """Replaces the confusing and obtuse n <- n <- n display for Lootables
    with n / n Unchecked: n
    Which you can actually understand without already knowing what it means."""
    display_name = "Mod: Fix Vanilla UI Crimes"


@dataclass
class IdleLoopsOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
    logic_big_sphere1: LogicBigSphere1
    logic_vanilla: LogicVanilla
    logic_vanilla_all: LogicVanillaAll
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
    z1_shop_min: Z1ShopMin
    z1_shop_max: Z1ShopMax
    location_z3_shop: LocationZ3Shop
    z3_shop_min: Z3ShopMin
    z3_shop_max: Z3ShopMax
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
    # soul_link: SoulLink
    # energy_link: EnergyLink
    mod_ui_crime: ModUICrime
