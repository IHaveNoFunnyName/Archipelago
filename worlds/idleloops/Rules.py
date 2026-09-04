from dataclasses import dataclass
from NetUtils import JSONMessagePart
from Options import Option
from typing import Any, Optional, Tuple, TYPE_CHECKING, TypedDict, override

from BaseClasses import CollectionState
from rule_builder.options import Operator, OptionFilter
from rule_builder.rules import CanReachRegion, Has, HasFromList, Rule, True_
from .Options import Goal, LogicFightHeal, LogicVanilla, LogicManaReduction, LogicGlasses, IdleLoopsOptions, LogicVanillaAll

if TYPE_CHECKING:
    from . import IdleLoopsWorld


def HasIfOptionManaReduction(action: str | Rule) -> Rule:
    return (Has(action) if isinstance(action, str) else action) | OptionFilter(LogicManaReduction, 0) | Has("Hard")


def HasIfOptionVanillaSkills(action: str | Rule) -> Rule:
    return (Has(action) if isinstance(action, str) else action) | OptionFilter(LogicVanilla, 0)


def HasIfOptionVanillaAll(action: str | Rule) -> Rule:
    return (Has(action) if isinstance(action, str) else action) | OptionFilter(LogicVanillaAll, 0)


# I found myself having to think though how exactly OptionFilter was used *every single time* i looked at or used it,
# Was filtered resolution used when the option was true or false?

# Even if i bothered to internalise that i think i'd still write this helper,
# It seems like there's a bit of boilerplate to getting an if/else rule.

class conditionType(TypedDict):
    option: type[Option[IdleLoopsOptions]]
    value: Optional[Any]
    operator: Optional[Operator]


operator_inverse: dict[Operator, Operator] = {
    "eq": "ne",
    "ne": "eq",
    "gt": "le",
    "lt": "ge",
    "ge": "lt",
    "le": "gt",
}


def IfOption(condition: conditionType, true: Rule, false: Rule = None) -> Rule:
    if false is None:
        false = True_()
    if "value" not in condition:
        condition["value"] = 1
    if "operator" not in condition:
        condition["operator"] = "eq"
    return (true & OptionFilter(condition["option"], condition["value"], operator=condition["operator"])) | (false & OptionFilter(condition["option"], condition["value"], operator=operator_inverse[condition["operator"]]))


has_mana_dependencies = ["Z1 - Mana Pot", "Filler - 50 Starting Mana", "Filler - 1 Starting Gold", "Progressive Lootable", "Z1 - Short Quest", "Z1 - Long Quest", "Z1 - Lock", "Z1 - Fight Monsters", "Z1 - Warrior Lessons"]

limits = [
    ("LQuests", 2),
    ("SQuests", 20),
    ("LQuests", 10),
    ("Locks", 10),
]
mana_cost = [
    ("SQuests", 600, 20),
    ("Locks", 400, 10),
    ("LQuests", 1450, 30),
]


def mana_from_state(hard_lock_logic: bool, fight_segments: int, state: CollectionState, player: int) -> Tuple[int, int]:
    # Simulate gaining gold with the most effecient action then selling it for mana
    # Fight Monsters is considered at 9 segments/180 gold in one action
    # You usually wouldn't grind that much combat in Z1 (the only place this rule should be used - you should always have enough mana after that)
    # But if you somehow need to push for it you can.

    SQuest_done = False

    counts = {
        "LQuests": state.count("Z1 - Long Quest", player),
        "SQuests": state.count("Z1 - Short Quest", player),
        "Locks": state.count("Z1 - Lock", player),
    }

    # This is *so much* cleaner than it used to be wow
    # I really need to do it like this on the client too
    extra = state.count("Progressive Lootable", player)
    for name, limit in limits:
        if counts[name] < limit:
            extra -= limit - counts[name]
            if extra > 0:
                counts[name] = limit
            else:
                # Reminder extra is negative in this branch
                counts[name] = limit + extra
                break

    mana = 250 + (state.count("Filler - 50 Starting Mana", player) + state.count("Z1 - Mana Pot", player)) * 50
    gold = state.count("Filler - 1 Starting Gold", player)
    rep = 0

    # Do all gold earning actions we have mana for, then buy mana and repeat until we earn 0 gold
    while True:
        # Buy mana, cleaner to spend it first
        mana -= 100

        for name, cost, gain in mana_cost:
            # Don't do Locks unless we've already done a SQuest, because Locks are very inefficient when done 1-2 at a time
            # If you need that to get enough mana for locks/meet people it makes the loop way longer/less progress actions per minute.
            # But maybe you want that to be possible so it's an option
            if name == "Locks" and (not (hard_lock_logic or state.has("Hard", player)) and not SQuest_done):
                continue
            reps = mana // cost
            reps = min(reps, counts[name])
            mana -= reps * cost
            counts[name] -= reps
            gold += reps * gain
            if name == "SQuests" and reps > 0:
                SQuest_done = True
            if name == "LQuests":
                rep += reps

        # It's not worth selling 1 gold for 50 mana as buy mana costs 100
        # Relevant if 1 starting gold
        if gold > 1:
            mana += gold * 50
            gold = 0
        else:
            mana += 100  # un-buy mana
            break

    if state.has("Z1 - Fight Monsters", player) and state.has("Z1 - Warrior Lessons", player) and rep >= 2:
        # 5k means basically CanReachRegion("Combat to 30")
        if mana > 5000:
            mana += (fight_segments * 20 * 50) - 2100

    return (mana, rep)

# I am *shocked* that caching didn't help with this rule.
# Also, i think the proper way to do this is to overwrite world.collect and a Mana pseudoitem
# But hey, i already wrote this and it seems to work. The other way might be faster.

# Also that way wouldn't let me do /explain, but also i could just write a simple HasMana that uses the pseudoitem


@dataclass
class HasMana(Rule["IdleLoopsWorld"], game="Idle Loops"):
    mana_goal: int
    rep_goal: int = 0

    @override
    def _instantiate(self, world: "IdleLoopsWorld") -> Rule.Resolved:
        return self.Resolved(player=world.player, mana_goal=self.mana_goal, rep_goal=self.rep_goal, fight_segments=5, hard_lock_logic=bool(world.options.logic_hard_mana), caching_enabled=False)

    class Resolved(Rule.Resolved):
        mana_goal: int
        rep_goal: int
        fight_segments: int
        hard_lock_logic: bool

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            (mana, rep) = mana_from_state(self.hard_lock_logic, self.fight_segments, state, self.player)
            return mana >= self.mana_goal and rep >= self.rep_goal

        @override
        def item_dependencies(self) -> dict[str, set[int]]:
            return {name: {id(self)} for name in has_mana_dependencies}

        @override
        def explain_json(self, state: CollectionState | None = None) -> list[JSONMessagePart]:
            (mana, rep) = mana_from_state(self.hard_lock_logic, self.fight_segments, state, self.player)
            enough_mana = mana >= self.mana_goal
            enough_rep = rep >= self.rep_goal
            if not enough_mana:
                current_mana_text = [{"type": "text", "text": " ("},
                                     {"type": "color", "color": "salmon", "text": f"{mana}"},
                                     {"type": "text", "text": ") mana"}]
            else:
                current_mana_text = [{"type": "text", "text": " mana"}]
            if not enough_rep:
                current_rep = [{"type": "text", "text": " ("},
                               {"type": "color", "color": "salmon", "text": f"{rep}"},
                               {"type": "text", "text": ") rep"}]
            else:
                current_rep = [{"type": "text", "text": " rep"}]
            if self.rep_goal > 0:
                rep_text = [{"type": "text", "text": f" and {self.rep_goal}"},
                            *current_rep]
            else:
                rep_text = []

            return [{"type": "text", "text": f"Has {self.mana_goal}"},
                    *current_mana_text,
                    *rep_text]

        @override
        def explain_str(self, state: CollectionState | None = None) -> str:
            (mana, rep) = mana_from_state(self.hard_lock_logic, self.fight_segments, state, self.player)
            return f"Can get to {self.mana_goal} ({mana}) mana{f' and {self.rep_goal} ({rep}) rep' if self.rep_goal > 0 else ''}"

        @override
        def __str__(self) -> str:
            return f"Can get to {self.mana_goal} mana{f' and {self.rep_goal} rep' if self.rep_goal > 0 else ''}"


@dataclass
class JourneyRule(Rule["IdleLoopsWorld"], game="Idle Loops"):
    extra: bool = True

    @override
    def _instantiate(self, world: "IdleLoopsWorld") -> Rule.Resolved:
        return self.Resolved(player=world.player, extra_mana=int(world.options.logic_z2_mana and self.extra) * 10000, fight_segments=5, caching_enabled=False)

    class Resolved(Rule.Resolved):
        extra_mana: int
        fight_segments: int

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            extra_mana = self.extra_mana
            if state.has("Hard", self.player):
                extra_mana = 0
            if not state.has("Z1 - Buy Supplies", self.player):
                return False
            (mana, rep) = mana_from_state(False, self.fight_segments, state, self.player)
            haggles = 0
            if state.has("Z1 - Haggle", self.player):
                if state.has("Z1 - Heal The Sick", self.player) and state.has("Z1 - Mage Lessons", self.player):
                    haggles = 15
                else:
                    # rep can only be max 10 for now, but being safe so i don't have to remember to change this
                    # if there's more rep in the calculation later (I'm not sure why i would though)
                    haggles = min(15, rep)

            # Buy Supplies + Start Journey + 15 haggles + extra mana (Well, mana in it's unbought gold form) for each haggle under 15
            return mana >= 200 + 1000 + ((15 - haggles) * 900) + extra_mana

        @override
        def item_dependencies(self) -> dict[str, set[int]]:
            return {name: {id(self)} for name in has_mana_dependencies + ["Z1 - Start Journey", "Z1 - Buy Supplies", "Z1 - Haggle", "Z1 - Heal The Sick", "Z1 - Mage Lessons"]}

        def explain_json(self, state: CollectionState | None = None) -> list[JSONMessagePart]:
            (mana, rep) = mana_from_state(False, self.fight_segments, state, self.player)
            haggles = 0
            if state.has("Z1 - Haggle", self.player):
                if state.has("Z1 - Heal The Sick", self.player) and state.has("Z1 - Mage Lessons", self.player):
                    haggles = 15
                else:
                    # rep can only be max 10 for now, but being safe so i don't have to remember to change this
                    # if there's more rep in the calculation later (I'm not sure why i would though)
                    haggles = min(15, rep)

            mana_needed = (200 + 1000 + ((15 - haggles) * 900) + self.extra_mana) - mana

            supplies = "green" if state and state.has("Z1 - Buy Supplies", self.player) else "salmon"
            haggle = "green" if state and state.has("Z1 - Haggle", self.player) else "salmon"
            heal = "green" if state and state.has("Z1 - Heal The Sick", self.player) else "salmon"
            mage = "green" if state and state.has("Z1 - Mage Lessons", self.player) else "salmon"
            fight = "green" if state and state.has("Z1 - Fight Monsters", self.player) else "salmon"
            warrior = "green" if state and state.has("Z1 - Warrior Lessons", self.player) else "salmon"

            mana_text = [
                {"type": "color", "color": "salmon", "text": str(mana_needed)},
                {"type": "text", "text": " more mana needed"}] if mana_needed > 0 else [
                    {"type": "color", "color": "green", "text": "Enough"},
                    {"type": "text", "text": " mana"}]

            return [{"type": "text", "text": "Has "},
                    {"type": "color", "color": supplies, "text": "Z1 - Buy Supplies"},
                    {"type": "text", "text": " and "},
                    *mana_text,
                    {"type": "text", "text": f" to leave Z1{f' with {self.extra_mana} mana' if self.extra_mana > 0 else ''}, via (("},
                    {"type": "color", "color": haggle, "text": "Z1 - Haggle"},
                    {"type": "text", "text": ", "},
                    {"type": "color", "color": heal, "text": "Z1 - Heal The Sick"},
                    {"type": "text", "text": ", "},
                    {"type": "color", "color": mage, "text": "Z1 - Mage Lessons"},
                    {"type": "text", "text": ") OR ("},
                    {"type": "color", "color": fight, "text": "Z1 - Fight Monsters"},
                    {"type": "text", "text": ", "},
                    {"type": "color", "color": warrior, "text": "Z1 - Warrior Lessons"},
                    {"type": "text", "text": ") OR (Just have enough mana (and probably "},
                    {"type": "color", "color": haggle, "text": "Z1 - Haggle"},
                    {"type": "text", "text": ")))"}]

        def explain_str(self, state: CollectionState | None = None) -> str:
            return self.__str__()

        def __str__(self) -> str:
            return f"Has Buy Supplies and enough mana to leave Z1{f' with {self.extra_mana} mana' if self.extra_mana > 0 else ''}, via ((Z1 - Haggle, Z1 - Heal The Sick, Z1 - Mage Lessons) OR (Z1 - Fight Monsters, Z1 - Warrior Lessons) OR (Just have enough mana (and probably Z1 - Haggle)))"


# TODO: Here I go, not colocating things again!
# To fit with what i do everywhere else for actions, i should make it so this Just Works as a part of Action
# Like being able to do rule=Action("Z1 - Meet People").rule() or something
# But that'd be a refactor and this is less thinky

# Most rules are defined on Actions, and rules are added to the world via Actions.
# This is to store reusable rules.
rules = {}

rules["Z1 - Meet People"] = Has("Z1 - Meet People") & HasMana(800)
# You'd expect the Vanilla Hard rule to need "Meet People Progress" instead, but the difference between them is the addition of Throw Party
# Which is locked behind Meet People already via Investigate, so it would cause an infinite loop.
rules["Z1 - Investigate"] = Has("Z1 - Investigate") & HasMana(1000) & HasIfOptionVanillaAll(Has("Z1 - Meet People"))
rules["Z1 - Throw Party"] = Has("Z1 - Throw Party") & HasMana(1600, 2) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))
# Extra rule because Throw Party also gives progress to everything Meet People does.
rules["Meet People Progress"] = rules["Z1 - Meet People"] | rules["Z1 - Throw Party"]

rules["Combat to 2"] = (
    # The training actions themselves take 1k, but you need enough to do long quests.
    Has("Z1 - Warrior Lessons") & HasMana(1600, 2) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))) | (
    # Pyromancy provides self combat
    OptionFilter(Goal, Goal.option_z4, "ge") & CanReachRegion("Z4 Pyromancy") & Has("Z1 - Fight Monsters")) | (
    OptionFilter(Goal, Goal.option_z4, "ge") & CanReachRegion("Z4 Pyromancy") & CanReachRegion("Z4 Hunt Trolls")) | (
    # Be able to do the action which needs non-zero (Magic + Self Combat), not complete a floor
    (CanReachRegion("Magic to 2") | (OptionFilter(Goal, Goal.option_z4, "ge") & CanReachRegion("Z4 Pyromancy"))) & Has("Z1 - Small Dungeon") & HasMana(2000, 2) & HasIfOptionVanillaSkills(CanReachRegion("Magic to 30")) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))) | (
    OptionFilter(Goal, Goal.option_z3, "ge") & (CanReachRegion("Magic to 2") | (OptionFilter(Goal, Goal.option_z4, "ge") & CanReachRegion("Z4 Pyromancy"))) & CanReachRegion("Z3") & Has("Z3 - Large Dungeon") & Has("Z3 - Adventure Guild") & Has("Z3 - Gather Team") & HasIfOptionVanillaAll(CanReachRegion("Get Drunk"))
)

rules["Combat to 10"] = (
    Has("Z1 - Warrior Lessons") & HasMana(1600, 2) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))) | (
    OptionFilter(Goal, Goal.option_z4, "ge") & CanReachRegion("Z4 Pyromancy") & CanReachRegion("Z4 Hunt Trolls")
)
rules["Combat to 30"] = (Has("Z1 - Warrior Lessons") & HasMana(5000, 2) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))) | (
    OptionFilter(Goal, Goal.option_z4, "ge") & CanReachRegion("Z4 Pyromancy") & CanReachRegion("Z4 Hunt Trolls")
)
rules["Combat"] = Has("Z1 - Warrior Lessons") | (OptionFilter(Goal, Goal.option_z4, "ge") & CanReachRegion("Z4 Pyromancy") & CanReachRegion("Z4 Hunt Trolls"))

rules["Magic to 2"] = (
    Has("Z1 - Mage Lessons") & HasMana(1600, 2) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))) | (
    CanReachRegion("Combat to 2") & Has("Z1 - Small Dungeon") & HasMana(2000, 2) & HasIfOptionVanillaSkills(CanReachRegion("Combat to 30")) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))) | (
    CanReachRegion("Combat to 2") & CanReachRegion("Z3") & Has("Z3 - Large Dungeon") & Has("Z3 - Adventure Guild") & Has("Z3 - Gather Team") & HasIfOptionVanillaAll(CanReachRegion("Get Drunk"))) | (
    # This will have HasIfOptionVanillaSkills(CanReachRegion("Z2 Magic")) in it, causing a loop. Is that a problem or does AP resolve that to false? I'll find out!
    OptionFilter(Goal, Goal.option_z2, "ge") & CanReachRegion("Z2 Alchemy")
)
rules["Magic to 10"] = (
    Has("Z1 - Mage Lessons") & HasMana(1600, 2) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))) | (
    OptionFilter(Goal, Goal.option_z2, "ge") & CanReachRegion("Alchemy to 25")
)
rules["Magic to 30"] = (
    Has("Z1 - Mage Lessons") & HasMana(5000, 2) & HasIfOptionVanillaAll(CanReachRegion("Investigate"))) | (
    OptionFilter(Goal, Goal.option_z2, "ge") & CanReachRegion("Alchemy to 25")
)

# Arbitrary HasMana rule so you're able to do some decent Wandering after buying them.
rules["Option Has Glasses"] = (Has("Z1 - Buy Glasses") & HasMana(1500)) | OptionFilter(LogicGlasses, 0) | Has("Hard")

# Simpler rules for after Z1.
rules["Has Combat"] = Has("Z1 - Warrior Lessons") | (OptionFilter(Goal, Goal.option_z4, "ge") & CanReachRegion("Z4 Pyromancy") & CanReachRegion("Z4 Hunt Trolls"))
rules["Has Magic"] = Has("Z1 - Mage Lessons")

rules["Z2 - Old Shortcut"] = Has("Z2 - Old Shortcut") & HasIfOptionVanillaAll("Z2 - Explore Forest")
rules["Z2 - Talk To Hermit"] = Has("Z2 - Talk To Hermit") & HasIfOptionManaReduction(rules["Z2 - Old Shortcut"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Old Shortcut"])
rules["Z2 - Follow Flowers"] = Has("Z2 - Follow Flowers") & HasIfOptionVanillaAll("Z2 - Explore Forest")
rules["Z2 - Clear Thicket"] = Has("Z2 - Clear Thicket") & HasIfOptionVanillaAll("Z2 - Follow Flowers")
rules["Z2 - Talk To Witch"] = Has("Z2 - Talk To Witch") & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Clear Thicket"])
rules["Alchemy to 25"] = (Has("Z2 - Learn Alchemy") | HasIfOptionVanillaSkills(Has("Z2 - Learn Alchemy") & Has("Z2 - Brew Potions"))) & (
    (Has("Z2 - Herb", 100) | Has("Z2 - x10 Herb", 10)) | (Has("Hard") & Has("Z2 - Herb", 10) & Has("Z2 - x10 Herb", 1))
) & HasIfOptionManaReduction(rules["Z2 - Talk To Hermit"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Talk To Hermit"])
rules["Has Alchemy"] = Has("Z2 - Learn Alchemy") & (
    (Has("Z2 - Herb", 100) | Has("Z2 - x10 Herb", 10)) | (Has("Hard") & Has("Z2 - Herb", 10) & Has("Z2 - x10 Herb", 1))
) & HasIfOptionManaReduction(rules["Z2 - Talk To Hermit"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Talk To Hermit"])
rules["Has Practical Magic"] = Has("Z2 - Practical Magic") & HasIfOptionManaReduction(rules["Z2 - Talk To Hermit"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Talk To Hermit"])
rules["Has Dark Magic"] = Has("Z2 - Dark Magic") & Has("Z1 - Haggle") & HasIfOptionManaReduction(rules["Z2 - Talk To Witch"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Talk To Witch"])

rules["Z3 - Get Drunk"] = Has("Z3 - Get Drunk") & HasIfOptionVanillaAll("Z3 - Explore City")
rules["Z3 - Large Dungeon"] = Has("Z3 - Large Dungeon") & Has("Z3 - Adventure Guild") & Has("Z3 - Gather Team") & rules["Has Combat"] & rules["Has Magic"] & HasIfOptionVanillaAll(rules["Z3 - Get Drunk"])
rules["Z3 - Apprentice"] = Has("Z3 - Apprentice") & Has("Z3 - Crafting Guild") & HasIfOptionVanillaAll(rules["Z3 - Get Drunk"])
rules["Z3 - Mason"] = Has("Z3 - Mason") & Has("Z3 - Crafting Guild") & HasIfOptionVanillaAll(rules["Z3 - Apprentice"])
rules["Z3 - Architect"] = Has("Z3 - Architect") & Has("Z3 - Crafting Guild") & HasIfOptionVanillaAll(rules["Z3 - Mason"])

rules["Z4 - Decipher Runes"] = Has("Z4 - Decipher Runes") & HasIfOptionVanillaAll("Z4 - Climb Mountain")
rules["Z4 - Explore Cavern"] = Has("Z4 - Explore Cavern") & HasIfOptionVanillaAll("Z4 - Climb Mountain")
rules["Z4 - Check Walls"] = Has("Z4 - Check Walls") & HasIfOptionVanillaAll(rules["Z4 - Explore Cavern"])

rules["Has Soulstones"] = (
    (Has("Z1 - Small Dungeon") & (rules["Has Magic"] | rules["Has Combat"])) |
    (rules["Z3 - Large Dungeon"] & (Has("Z2 - Continue On") & HasIfOptionManaReduction(rules["Z2 - Old Shortcut"])) & rules["Has Magic"] & rules["Has Combat"]) |
    (Has("Z2 - Continue On") & Has("Z3 - Start Trek") & Has("Z3 - Buy Pickaxe") & (Has("Z4 - Soulstone") & rules["Z4 - Explore Cavern"]))
)

rules["Has Pyromancy"] = OptionFilter(Goal, Goal.option_z4, "lt") | Has("Z4 - Pyromancy") & HasIfOptionManaReduction(rules["Z4 - Decipher Runes"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z4 - Decipher Runes"])
