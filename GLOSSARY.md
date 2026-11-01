# Dynasty Autopilot

A Crusader Kings III mod that takes over the tedious parts of running a dynasty, following rules the player sets.

## Language

### Building

**Building focus**:
A goal the automatic builder pursues (Income, Development or Military stacking), each weighted Off, Low or High; active focuses are weighed together, not taken in turn.
_Avoid_: Build mode, priority

**County stacking**:
Filling every free building slot in all holdings of one county, the player's and their vassals', with buildings whose county-wide bonus serves a building focus.
_Avoid_: Spamming, county focus

**Stacking county**:
The county currently being filled by county stacking; the one that already has the most buildings for that focus, the capital breaking ties.

**Military base**:
A holding in the player's own domain where one men-at-arms type's stationed bonuses are stacked, so regiments of that type should be stationed there; a type gets a second base only when its first is full.
_Avoid_: Garrison, barracks

**Specialty**:
The men-at-arms type a military base stacks bonuses for; taken from what is already built there among types the player owns, then from terrain, unless the player sets it.
_Avoid_: Unit type, military focus

**Reach** (of a building bonus):
Who a building's bonus benefits: the whole county, only its holding, or only the holder of that holding.

**Excluded holding**:
A county or holding the player has taken out of automatic building.
_Avoid_: Locked, blacklisted
