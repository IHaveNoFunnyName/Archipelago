# Idle Loops

## Where is the options page?

The [player options page for this game](../player-options) contains all the options you need to configure and export a config file.

## What does randomization do to this game?
Action unlocks are randomized, your count of 'Lootable' actions are randomized, as is what gaining another Lootable count actually gives. Nothing inside a loop is randomized, i.e. you always get supplies from "Buy Supplies" and always need supplies to leave Z1.

## What is the goal of Inscryption when randomized?
For now, finishing Zone 1. More zones will be added in the future. I'm planning to make Z3 the default, that seems good for like a week long async.

## Which items can be in another player's world?
All Actions, all Lootable counts, other stuff i'll discover and decide on while finishing Z1. For Filler items, right now there are only extra copies of lootable actions. This will completely mess with the balance of the game but hey it's a rando, Balatro gives you +hand size as a filler item i'm in good company. In the future I'm planning on adding more filler items such as "Starting Mana", "Soul Stones", "Starting Gold" etc...

## What locations can have items?
- Finishing an action for the first time
- Progress in progress bar actions (at 1%, 10%, 25%, 50%, 75%, 90%, 95%, 99%, 100%)
- Gaining a lootable count (i.e. how many pots you can smash)
- Reaching new highs for actions like "Fight Monsters" or "Small Dungeon"

Some of these will have options in the future.

Actions are combined in cases where there's overlap (such as finishing an action for the first time giving 1% progress), or even similar-in-spirit-but-not-technically-overlapping (such as finishing an action for first time and gaining a lootable count, which happens after the first x finishes)

## What does another world's item look like in Inscryption?
Right now, nothing. All descriptions are unmodded. I am planning on changing this so every location that can grant and item has some description or hovertext to scout its item.

## When the player receives an item, what happens?
Most items will only take effect starting on the next loop. For example, consider "Smash Pots". Behind the scenes when you gain a Pot, you instantly gain a "good" pot, but the in-loop "goodTempPot" is unchanged.

Right now, if the last action you take in a loop grants an item (and it's your own), you *won't* get it in the next loop, because the next loop has already started by the time the server sends the item back. This seems scary to fix.

## How many items can I find or receive in my world?
idk i'll count later. 