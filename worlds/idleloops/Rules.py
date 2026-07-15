from dataclasses import dataclass
from math import floor
from typing import override

from BaseClasses import CollectionState
from rule_builder.rules import Has, Rule
from worlds.stardew_valley.stardew_rule import state

def has_mana_from_state(mana_goal:int, state: CollectionState, player: int) -> int:
    # Simulate gaining gold with the most effecient action then selling it for mana
    # Fight Monsters is considered at 9 segments/180 gold in one action
    # You usually wouldn't grind that much combat in Z1 (the only place this rule should be used - you should always have enough mana after that)
    # But if you somehow need to push for it you can.
    mana = 250 + (state.count("Filler - 50 Starting Mana", player) + state.count("Filler - 1 Starting Gold", player) + state.count("Z1 - Mana Pot", player)) * 50
    #TODO: Hard logic here for (Lock > Buy Mana)xN if you don't have enough mana for SQuest.
    # This would put 100% of Meet People/Investigate into logic with doing them at 0.5/min
    # Scary
    # Hopefully one of those % is a mana item smile
    
    # We need to calculate Progresive Lootables to know how many SQuests we have
    # Simpler version of the client .js logic, if we have enough Progressive Lootables to cap SQuests, we have all the mana we ever need for Z1 actions
    # So we can ignore later lootables 
    extra = state.count("Filler - Progressive Lootable", player)
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
    
    #TODO: Abstract/generalise?
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

    if state.has("Z1 - Fight Monsters", player) and state.has("Z1 - Warrior Training", player) and rep >= 2:
        if mana > 2100:
            mana += 6900
    
    return mana > mana_goal

@dataclass
class HasMana(Rule["IdleLoopsWorld"], game="Idle Loops"):
    mana_goal: int
    @override
    def _instantiate(self, world: "IdleLoopsWorld") -> Rule.Resolved: 
        return self.Resolved(self.mana_goal, player=world.player, caching_enabled=False)

    class Resolved(Rule.Resolved):
        mana_goal: int
        
        @override
        def _evaluate(self, state: CollectionState) -> bool:
            return has_mana_from_state(self.mana_goal, state, self.player)

class JourneyRule(Rule["IdleLoopsWorld"], game="Idle Loops"):
    @override
    def _instantiate(self, world: "IdleLoopsWorld") -> Rule.Resolved:
        return self.Resolved(player=world.player, caching_enabled=False)

    class Resolved(Rule.Resolved):
        @override
        def _evaluate(self, state: CollectionState) -> bool:
            if not (state.has("Z1 - Start Journey", self.player) and state.has("Z1 - Buy Supplies", self.player)):
                return False
            haggles = 0
            if state.has("Z1 - Haggle", self.player):
                if state.has("Z1 - Heal The Sick", self.player) and state.has("Z1 - Mage Lessons", self.player):
                    haggles = 15

                extra = state.count("Filler - Progressive Lootable", self.player)
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
            # I want to do this but clearly it won't work as it's not passed world or player or state
            return has_mana_from_state(1200 + 1500 + ((15 - haggles) * 900), state, self.player)
