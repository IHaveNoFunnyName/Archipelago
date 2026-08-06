from dataclasses import dataclass
from NetUtils import JSONMessagePart
from Options import Option
from typing import Any, Optional, TypedDict, override

from BaseClasses import CollectionState
from rule_builder.options import Operator, OptionFilter
from rule_builder.rules import Has, HasFromList, Rule, True_
from .Options import Goal, LogicFightHeal, LogicVanilla, LogicManaReduction, LogicGlasses, IdleLoopsOptions, LogicVanillaAll


def HasIfOptionManaReduction(action: str | Rule) -> Rule:
    return (Has(action) if isinstance(action, str) else action) | OptionFilter(LogicManaReduction, 0)


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


def has_mana_from_state(mana_goal: int, rep_goal: int, fight_segments: int, state: CollectionState, player: int) -> bool:
    # Simulate gaining gold with the most effecient action then selling it for mana
    # Fight Monsters is considered at 9 segments/180 gold in one action
    # You usually wouldn't grind that much combat in Z1 (the only place this rule should be used - you should always have enough mana after that)
    # But if you somehow need to push for it you can.
    mana = 250 + (state.count("Filler - 50 Starting Mana", player) + state.count("Filler - 1 Starting Gold", player) + state.count("Z1 - Mana Pot", player)) * 50
    # TODO: Hard logic here for (Lock > Buy Mana)xN if you don't have enough mana for SQuest.
    # This would put 100% of Meet People/Investigate into logic with doing them at 0.5/min
    # Scary
    # Hopefully one of those % is a mana item smile

    # We need to calculate Progresive Lootables to know how many SQuests we have
    # Simpler version of the client .js logic, if we have enough Progressive Lootables to cap SQuests, we have all the mana we ever need for Z1 actions
    # So we can ignore later lootables
    extra = state.count("Progressive Lootable", player)
    old_extra = extra
    LQuests = state.count("Z1 - Long Quest", player)
    if LQuests < 2:
        extra -= 2 - LQuests
        if extra >= 0:
            LQuests = 2
        if extra < 0:
            LQuests += old_extra
    rep = LQuests
    SQuests = state.count("Z1 - Short Quest", player) + max(extra, 0)

    if rep < rep_goal:
        return False

    # TODO: Abstract/generalise?
    # Eh, not worth
    while SQuests > 0:
        # Buy Mana
        mana -= 100

        reps = mana // 600
        reps = min(reps, SQuests)
        mana -= reps * 600
        SQuests -= reps
        mana += reps * 1000
        if reps == 0:
            return False
        if mana > mana_goal:
            return True

    Locks = state.count("Z1 - Lock", player)
    while Locks > 0:
        mana -= 100

        reps = mana // 400
        reps = min(reps, Locks)
        mana -= reps * 400
        Locks -= reps
        mana += reps * 500
        if reps == 0:
            return False
        if mana > mana_goal:
            return True

    # Oh wow these give 0 mana? Locks are better! I forgot that.
    # I guess to make them do something I should simulate stat mana reduction, saying they give 50 mana per instead
    # Surely this won't cause problems, right? Imagine a seed that gets like a million herbs, a couple pots and one LQuest
    # With the 50 mana from LQuest needed to do Meet People or whatever
    # If that happens i think
    while LQuests > 0:
        mana -= 100

        reps = mana // 1450
        reps = min(reps, LQuests)
        mana -= reps * 1450
        LQuests -= reps
        mana += reps * 1500
        if reps == 0:
            return False
        if mana > mana_goal:
            return True

    if state.has("Z1 - Fight Monsters", player) and state.has("Z1 - Warrior Lessons", player) and rep >= 2:
        if mana > 2100:
            mana += (fight_segments * 20 * 50) - 2100

    return mana > mana_goal

# I am *shocked* that caching didn't help with this rule.
# Also, i think the proper way to do this is to overwrite world.collect and a Mana pseudoitem
# But hey, i already wrote this and it seems to work. The other way might be faster.


@dataclass
class HasMana(Rule["IdleLoopsWorld"], game="Idle Loops"):
    mana_goal: int
    rep_goal: int = 0

    @override
    def _instantiate(self, world: "IdleLoopsWorld") -> Rule.Resolved:
        return self.Resolved(player=world.player, mana_goal=self.mana_goal, rep_goal=self.rep_goal, fight_segments=int(world.options.logic_fight), caching_enabled=False)

    class Resolved(Rule.Resolved):
        mana_goal: int
        rep_goal: int
        fight_segments: int

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            return has_mana_from_state(self.mana_goal, self.rep_goal, self.fight_segments, state, self.player)

        @override
        def item_dependencies(self) -> dict[str, set[int]]:
            return {name: {id(self)} for name in has_mana_dependencies}

        @override
        def explain_json(self, state: CollectionState | None = None) -> list[JSONMessagePart]:
            return [{"type": "text", "text": f"Has {self.mana_goal} mana{f' and {self.rep_goal} rep' if self.rep_goal > 0 else ''}"}]

        @override
        def explain_str(self, state: CollectionState | None = None) -> str:
            return self.__str__()

        @override
        def __str__(self) -> str:
            return f"Can get to {self.mana_goal} mana{f' and {self.rep_goal} rep' if self.rep_goal > 0 else ''}"


class JourneyRule(Rule["IdleLoopsWorld"], game="Idle Loops"):
    @override
    def _instantiate(self, world: "IdleLoopsWorld") -> Rule.Resolved:
        return self.Resolved(player=world.player, extra_mana=int(world.options.logic_z2_mana) * 10000, fight_segments=int(world.options.logic_fight), caching_enabled=False)

    class Resolved(Rule.Resolved):
        extra_mana: int
        fight_segments: int

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            if not state.has("Z1 - Buy Supplies", self.player):
                return False
            haggles = 0
            if state.has("Z1 - Haggle", self.player):
                if state.has("Z1 - Heal The Sick", self.player) and state.has("Z1 - Mage Lessons", self.player):
                    haggles = 15

                extra = state.count("Progressive Lootable", self.player)
                old_extra = extra
                LQuests = state.count("Z1 - Long Quest", self.player)
                if LQuests < 2:
                    extra -= 2 - LQuests
                    if extra >= 0:
                        LQuests = 2
                    if extra < 0:
                        LQuests += old_extra
                SQuests = state.count("Z1 - Short Quest", self.player) + max(extra, 0)

                # It came to me that you can also do it this way
                # I don't like doing an algorithm two different ways, but i think this is more understandable
                # So I should go and redo the others
                extra = SQuests - 20
                if extra > 0:
                    LQuests += extra
                haggles = min(LQuests, 10)

            # Buy Supplies + Start Journey + 15 haggles + extra mana (Well, mana in it's unbought gold form) for each haggle under 15
            return has_mana_from_state(1200 + 1500 + ((15 - haggles) * 900) + self.extra_mana, 0, self.fight_segments, state, self.player)

        @override
        def item_dependencies(self) -> dict[str, set[int]]:
            return {name: {id(self)} for name in has_mana_dependencies + ["Z1 - Start Journey", "Z1 - Buy Supplies", "Z1 - Haggle", "Z1 - Heal The Sick", "Z1 - Mage Lessons"]}

        def explain_json(self, state: CollectionState | None = None) -> list[JSONMessagePart]:
            supplies = "green" if state and state.has("Z1 - Buy Supplies", self.player) else "salmon"
            haggle = "green" if state and state.has("Z1 - Haggle", self.player) else "salmon"
            heal = "green" if state and state.has("Z1 - Heal The Sick", self.player) else "salmon"
            mage = "green" if state and state.has("Z1 - Mage Lessons", self.player) else "salmon"
            fight = "green" if state and state.has("Z1 - Fight Monsters", self.player) else "salmon"
            warrior = "green" if state and state.has("Z1 - Warrior Lessons", self.player) else "salmon"
            return [{"type": "text", "text": f"Has "},
                    {"type": "color", "color": supplies, "text": "Z1 - Buy Supplies"},
                    {"type": "text", "text": f" and enough mana to leave Z1{f' with {self.extra_mana} mana' if self.extra_mana > 0 else ''}, via (("},
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
rules["Z1 - Investigate"] = Has("Z1 - Investigate") & HasMana(1000) & HasIfOptionVanillaAll(rules["Z1 - Meet People"])
rules["Z1 - Throw Party"] = Has("Z1 - Throw Party") & HasMana(1600, 2) & HasIfOptionVanillaAll(rules["Z1 - Investigate"])
# Extra rule because Throw Party also gives progress to everything Meet People does.
rules["Meet People Progress"] = rules["Z1 - Meet People"] | rules["Z1 - Throw Party"]
# The training actions themselves take 1k, but you need enough to do long quests.
rules["Z1 Has Combat"] = Has("Z1 - Warrior Lessons") & HasMana(1600, 2) & HasIfOptionVanillaAll(rules["Z1 - Investigate"])
rules["Z1 Has Magic"] = Has("Z1 - Mage Lessons") & HasMana(1600, 2) & HasIfOptionVanillaAll(rules["Z1 - Investigate"])

rules["Option Has Glasses"] = Has("Z1 - Buy Glasses") | OptionFilter(LogicGlasses, 0)

# Simpler rules for after Z1. I'm *pretty sure* you need either heal/haggle or fight monsters to get out of Z1, so we shouldn't need to check for rep.
rules["Has Combat"] = Has("Z1 - Warrior Lessons")
rules["Has Magic"] = Has("Z1 - Mage Lessons")

rules["Z2 - Old Shortcut"] = Has("Z2 - Old Shortcut") & HasIfOptionVanillaAll("Z2 - Explore Forest")
rules["Z2 - Talk To Hermit"] = Has("Z2 - Talk To Hermit") & HasIfOptionManaReduction(rules["Z2 - Old Shortcut"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Old Shortcut"])
rules["Z2 - Follow Flowers"] = Has("Z2 - Follow Flowers") & HasIfOptionVanillaAll("Z2 - Explore Forest")
rules["Z2 - Clear Thicket"] = Has("Z2 - Clear Thicket") & HasIfOptionVanillaAll("Z2 - Follow Flowers")
rules["Z2 - Talk To Witch"] = Has("Z2 - Talk To Witch") & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Clear Thicket"])
rules["Has Alchemy"] = Has("Z2 - Learn Alchemy") & HasIfOptionManaReduction(rules["Z2 - Talk To Hermit"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z2 - Talk To Hermit"])
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

rules["Has Pyromancy"] = OptionFilter(Goal, 4, "lt") | Has("Z4 - Pyromancy") & HasIfOptionManaReduction(rules["Z4 - Decipher Runes"]) & HasIfOptionVanillaSkills(rules["Has Magic"]) & HasIfOptionVanillaAll(rules["Z4 - Decipher Runes"])
