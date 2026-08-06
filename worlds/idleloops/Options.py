from dataclasses import dataclass

from Options import Choice, DeathLinkMixin, DefaultOnToggle, NamedRange, OptionGroup, PerGameCommonOptions, Range, Toggle, Visibility


class Goal(Choice):
    """- Z1: Complete "Start Journey". Should take a few hours.
    (With 2-4x gamespeed).

    - Z2: Complete "Continue On".

    - Z3: Complete "Start Trek".

    - Z4: Complete "Face Judgement" with 50 or -50 reputation.
    Should take around a week (with 5-7x gamespeed).

    Content from Zones above the goal is not randomised."""
    display_name = "Goal"
    option_z1 = 0
    option_z2 = 1
    option_z3 = 2
    option_z4 = 3
    default = 0


class LogicVanilla(Toggle):
    """Respect Vanilla Skill requirements.
    e.g. With this on Buy Supplies requires (Combat + Magic) >= 35.

    Progress Bar requirements are ignored."""
    display_name = "Logic: Vanilla Skill Requirements"


class LogicVanillaAll(Toggle):
    """UNSUPPORTED: Respect Vanilla Skill and Progress bar
    requirements for actions.

    Overwrites "Logic: Vanilla Skill Requirements" if enabled.

    Unsupported because it contrains logic enough to cause
    Fill Errors, and having it on leads to gameplay
    way too close to vanilla. Buutt, I did finish the logic
    so that'll go to waste without this option."""
    display_name = "Logic: Vanilla Requirements (All)"


class LogicGlasses(DefaultOnToggle):
    """Forces Glasses to appear before 50% of Wander."""
    display_name = "Logic: Buy Glasses"


class ItemGlasses(DefaultOnToggle):
    """Adds a second "Z1 - Buy Glasses" item to the pool.
    With both of them you start the loop with glasses."""
    display_name = "Items: Second Glasses"


class LogicFightHeal(Range):
    """Percent chance either Fight Monsters or Heal The Sick
    will (be forced to) appear in Z1.
    Without this the vast majority of seed's Z1s were like,
    "Lots of short quests then 4 haggles and leave".
    Felt a bit samey."""
    display_name = "Logic: Fight/Heal in Z1"
    range_start = 0
    range_end = 100
    default = 75


class LogicFight(NamedRange):
    """The randomizer knows how much mana you have access to (In Z1).
    As the gold you get from Fight Monsters is variable,
    it needs to know how much you want to grind it up.

    "Goal Based" is (Z1 = 5, Z2+ = 9)"""
    display_name = "Logic: Fight Monsters Segments"
    range_start = 3
    range_end = 9
    default = "goal_based"
    special_range_names = {
        "goal_based": -1,
    }
    defaults = (5, 9, 9, 9)


class LogicZ2Mana(DefaultOnToggle):
    """Have a minimum of 10k mana after Start Journey.
    (With all possible items in Z1)"""
    display_name = "Logic: Z2 Minimum Mana"


class LogicManaReduction(DefaultOnToggle):
    """Makes Actions that reduce Mana Cost a requirement for what they reduce.
    It feels so bad to have PM being your block without Hermit
    (Also includes Old Shortcut for Talk To Hermit)"""
    display_name = "Logic: Mana Reduction Actions"


class LocationProgress(DefaultOnToggle):
    """Adds locations to progress bars (around every 10%)

    Otherwise, there is only one location per progress bar,
    for the first completion of its action."""
    display_name = "Locations: Progress Bars"


class ItemSearch(DefaultOnToggle):
    """Adds "x - Search" items, needed to check each lootable type.
    (Lootables are stuff like Mana Pots)
    Breaks the pool for a Progress Action that gives Lootables in two"""
    display_name = "Items: Lootable Search Items"


class LocationSkillToggle(DefaultOnToggle):
    """Adds locations for skills based on the goal:
    Combat, Magic, Practical Magic, Dark Magic, Chronomancy and Pyromancy:
    (Z1 = 30, Z2 = 50, Z3 = 100, Z4 = 200)
    Alchemy: (Z2 = 25, Z3 = 50, Z4 = 75)
    Crafting: (Z3 = 25, Z4 = 50)"""
    display_name = "Locations: Skills"


class LocationBuffToggle(DefaultOnToggle):
    """Adds locations for buffs based on the goal:
    Dark Ritual: (Z2 = 1, Z3 = 2, Z4 = 10)
    Imbue Mind: (Z4 = 1)"""
    display_name = "Locations: Buffs"


class LocationSkill(NamedRange):
    """Overwrite the max level for 'normal' skills.
    (Combat, Magic, Practical Magic, Dark Magic, Chronomancy and Pyromancy)"""
    display_name = "Locations: Skills Max Level"
    range_start = 0
    range_end = 500
    special_range_names = {
        "goal_based": -1,
    }
    default = "goal_based"
    defaults = (30, 50, 100, 200)


class LocationAlchemy(NamedRange):
    """Overwrite the max Alchemy level."""
    display_name = "Locations: Alchemy (Skill)"
    range_start = 0
    range_end = 100
    special_range_names = {
        "goal_based": -1,
    }
    default = "goal_based"
    defaults = (0, 25, 50, 75)


class LocationCrafting(NamedRange):
    """Overwrite the max Crafting level.
    FYI in Vanilla:
    Apprentice gets you to 75
    Mason gets you to 140
    Architect gets you to 200."""
    display_name = "Locations: Crafting (Skill)"
    range_start = 0
    range_end = 100
    special_range_names = {
        "goal_based": -1,
    }
    default = "goal_based"
    defaults = (0, 0, 70, 140)


class LocationMultipartToggle(DefaultOnToggle):
    """Adds locations for multipart actions based on the goal:
    Heal The Sick: (Z1 = 5, Z2 = 6, Z3 = 7, Z4 = 15)
    Fight Monsters: (Z1 = 3, Z2 = 4, Z3 = 5, Z4 = 10)
    Small Dungeon: (Z1 = 3, Z2 = 4, Z3 = 6/max)
    Large Dungeon: (Z3 = 2, Z4 = 9/max)
    Trolls: (Z4 = 5)
    The Guilds do not have locations on them."""
    display_name = "Locations: Multipart Actions"


class LocationHeal(NamedRange):
    """Overwrite how many patients to heal."""
    display_name = "Locations: Heal The Sick"
    range_start = 0
    range_end = 20
    special_range_names = {
        "goal_based": -1,
    }
    default = "goal_based"
    defaults = (5, 6, 7, 15)


class LocationFight(NamedRange):
    """Overwrite how many monsters to fight."""
    display_name = "Locations: Fight Monsters"
    range_start = 0
    range_end = 15
    special_range_names = {
        "goal_based": -1,
    }
    default = "goal_based"
    defaults = (3, 4, 5, 10)


class LocationSmallDungeon(NamedRange):
    """Overwrite how many Small Dungeon floors to clear."""
    display_name = "Locations: Small Dungeon"
    range_start = 0
    range_end = 6
    special_range_names = {
        "goal_based": -1,
    }
    default = "goal_based"
    defaults = (3, 4, 6, 6)


class LocationLargeDungeon(NamedRange):
    """Overwrite how many Large Dungeon floors to clear."""
    display_name = "Locations: Large Dungeon"
    range_start = 0
    range_end = 9
    special_range_names = {
        "goal_based": -1,
    }
    default = "goal_based"
    defaults = (0, 0, 2, 9)


class LocationTrolls(Range):
    """Overwrite how many of Trolls to fight."""
    display_name = "Locations: Trolls"
    range_start = 0
    range_end = 10
    default = 5
    defaults = (0, 0, 0, 5)


class LocationRitual(NamedRange):
    """Overwrite how many Dark Rituals to perform."""
    display_name = "Locations: Dark Ritual"
    range_start = 0
    range_end = 10
    special_range_names = {
        "goal_based": -1,
    }
    default = "goal_based"
    defaults = (0, 1, 2, 10)


class LocationMind(Range):
    """Overwrite how many Imbues to Mind."""
    display_name = "Locations: Imbue Mind"
    range_start = 0
    range_end = 5
    default = 1
    defaults = (0, 0, 0, 1)


class ItemShop(Toggle):
    """Requires items to be found to unlock the shop actions below.

    With this on, you might not get the shop until after you can
    already buy everything, kinda defeating the point."""
    display_name = "Items: AP Shop Unlock"


class LocationZ1ShopCheap(DefaultOnToggle):
    """Adds 10 buyable items to Z1, ranging from 50 to 200 gold."""
    display_name = "Locations: Z1 AP Shop"
    option_false = 0
    option_true = 10


class LocationZ1ShopExpensive(DefaultOnToggle):
    """Adds 10 extra, more expensive, items to the Z1 shop.
    Min gold cost is 300,
    Max gold cost is based on the goal:
    (Z2 = 400, Z3 = 600, Z4 = 1000)
    Affordable after you get PM."""
    display_name = "Locations: Z1 AP Shop (Expensive)"
    option_false = 0
    option_true = 10


class Z1ShopExpensiveMax(NamedRange):
    """Maximum cost of items in Z1 AP Shop (Expensive)
    1500 is affordable with 300 PM.
    Set responsibly if you don't want to go that deep."""
    display_name = "Z1 AP Shop (Expensive): Max Cost"
    range_start = 300
    range_end = 1500
    default = "goal_based"
    special_range_names = {
        "goal_based": -1,
    }
    defaults = (0, 400, 600, 1000)


class LocationZ3Shop(DefaultOnToggle):
    """Adds 10 buyable items to Z3, ranging from 500 to 1000 gold."""
    display_name = "Locations: Z3 AP Shop"
    option_false = 0
    option_true = 10


class BatchZ2(DefaultOnToggle):
    """Batches Herbs/Wild Mana locations and items 10x.

    Herbs/Wild Mana basically give you 300 checks the moment
    you can get to them, way more dense than anywhere else in the game.

    This cuts down on that, reducing the chance that like 4 important items
    are just lying on the forest floor, and also reducing total 'filler'.
    """
    display_name = "Batch Herbs/Wild Mana 10x"


class ItemPots(Toggle):
    """Removes the 50 "Z1 - Mana Pot" items from Vanilla from the randomiser.
    Makes your ratio of Mana Pots/Starting Gold/Mana nice and even."""
    display_name = "Filler Item: Remove Vanilla 50 Mana Pots"


class FillerStartingMana(DefaultOnToggle):
    """Filler items can include +50 starting mana"""
    display_name = "Filler Item: Starting Mana"


class FillerStartingGold(DefaultOnToggle):
    """Filler items can include +1 starting gold"""
    display_name = "Filler Item: Starting Gold"


class FillerExtraManaPot(DefaultOnToggle):
    """Filler items can include extra Mana Pots"""
    display_name = "Filler Item: Extra Mana Pot"


class FillerNothing(NamedRange):
    """Percent chance a filler item will be 'nothing'
    (instead of one of the filler items above).
    "Goal Based" is (Z1 = 0, Z2 = 25, Z3 = 50, Z4 = 75)"""
    display_name = "Filler Item: Nothing"
    range_start = 0
    range_end = 100
    default = "goal_based"
    special_range_names = {
        "goal_based": -1,
    }
    defaults = (0, 25, 50, 75)


class ItemProgressiveLootable(NamedRange):
    """Adds extra Lootables to the pool,
    helping each Lootable to their max in *rough* order of usefulness and zone.
    If what an item practically gives is different from its name,
    there will be an entry in the log.
    "Goal Based" is (Z1 = 0, Z2+ = 20)"""
    display_name = "Item: Progressive Lootables"
    range_start = 0
    range_end = 40
    default = "goal_based"
    special_range_names = {
        "goal_based": -1,
    }
    defaults = (0, 20, 20, 20)


class GameSpeed(NamedRange):
    """Multiplicative with the option below.
    "Goal Based" is (Z1/2 = 2, Z3/4 = 3)"""
    display_name = "Global Game Speed"
    range_start = 1
    range_end = 5
    default = "goal_based"
    special_range_names = {
        "goal_based": -1,
    }
    defaults = (2, 2, 3, 3)


class ItemGameSpeed(NamedRange):
    """Adds +0.1 Game Speed items to the pool, to a total of (value)x.
    Multiplicative with the option above.
    The game slows down over time so this helps it feel more even.
    "Goal Based" is (Z1/2 = 2, Z3/4 = 3)"""
    display_name = "Item: Game Speed"
    range_start = 1
    range_end = 5
    default = "goal_based"
    special_range_names = {
        "goal_based": -1,
    }
    defaults = (2, 2, 3, 3)


class StatExpMult(Range):
    """Multiplicative with the option below."""
    display_name = "Global Stat Exp Mult"
    range_start = 1
    range_end = 5
    default = 1


class ItemExpMult(Range):
    """Adds +0.1 Exp Multiplier items to the pool, to a total of (value)x.
    Multiplicative with the option above."""
    display_name = "Item: Exp Mult"
    range_start = 1
    range_end = 5
    default = 1


class SkillExpMult(Range):
    """Skills are easily the most grindy part of the game
    lets cut that down huh?"""
    display_name = "Global Skill Exp Mult"
    range_start = 1
    range_end = 5
    default = 1


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


class ModColor(DefaultOnToggle):
    """Fixes the inverted color display of the Lloyd fork's dark mode.
    Mana is Blue and Strength is Red again!
    (and aligns AP colors with other games)"""
    display_name = "Mod: Fix Lloyd Fork's Dark Mode Colors"


option_groups = [
    OptionGroup("Advanced", [
        LogicFight,
        LogicZ2Mana,
        LocationSkill,
        LocationAlchemy,
        LocationCrafting,
        LocationHeal,
        LocationFight,
        LocationSmallDungeon,
        LocationRitual,
        LocationLargeDungeon,
        Z1ShopExpensiveMax,
        LocationTrolls,
        LocationMind,
        LogicVanillaAll,
    ])
]


@dataclass
class IdleLoopsOptions(DeathLinkMixin, PerGameCommonOptions):
    goal: Goal
    logic_vanilla: LogicVanilla
    logic_mana_reduction: LogicManaReduction
    logic_fight: LogicFight
    logic_glasses: LogicGlasses
    item_glasses: ItemGlasses
    logic_z2_mana: LogicZ2Mana
    logic_fight_heal: LogicFightHeal
    location_progress: LocationProgress
    location_skill_toggle: LocationSkillToggle
    location_buff_toggle: LocationBuffToggle
    location_skill: LocationSkill
    location_alchemy: LocationAlchemy
    location_crafting: LocationCrafting
    location_multipart_toggle: LocationMultipartToggle
    location_heal: LocationHeal
    location_fight: LocationFight
    location_sd: LocationSmallDungeon
    location_ritual: LocationRitual
    location_ld: LocationLargeDungeon
    location_trolls: LocationTrolls
    location_mind: LocationMind
    item_search: ItemSearch
    item_shop: ItemShop
    location_z1_shop: LocationZ1ShopCheap
    location_z1_shop_expensive: LocationZ1ShopExpensive
    z1_shop_expensive_max: Z1ShopExpensiveMax
    location_z3_shop: LocationZ3Shop
    batch_z2: BatchZ2
    item_pots: ItemPots
    filler_starting_mana: FillerStartingMana
    filler_starting_gold: FillerStartingGold
    filler_extra_mana_pot: FillerExtraManaPot
    filler_nothing: FillerNothing
    item_progressive_lootable: ItemProgressiveLootable
    game_speed: GameSpeed
    item_game_speed: ItemGameSpeed
    stat_exp_mult: StatExpMult
    item_exp_mult: ItemExpMult
    skill_exp_mult: SkillExpMult
    logic_vanilla_all: LogicVanillaAll
    bonus: Bonus
    # soul_link: SoulLink
    # energy_link: EnergyLink
    mod_ui_crime: ModUICrime
    mod_color: ModColor
