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

**Vassals' counties** (an option):
Counties held by the player's direct vassals; automatic building may use every holding in them (the vassal's own and their vassals', two levels below the player) only once the player's own counties have no candidate and no county left to stack, and has its own stacking county there.
_Avoid_: Realm counties

**Replace buildings** (an option):
Lets automatic building replace a building that serves none of the active building focuses with a new one, only in a county with no free slot left (excluded holdings aside), and only when the new building gives at least 50% more than all the old one gave, whatever focus it served.
_Avoid_: Demolish, rebuild

**New holdings** (an option):
Lets automatic building start a new holding in an empty barony of a county the player holds once there is nowhere left to build for a focus: a city when no county has room for an Income or Development county-wide bonus, a castle when a military base is full; one at a time.
_Avoid_: Expand, settle

**Excluded holding**:
A county or holding the player has taken out of automatic building.
_Avoid_: Locked, blacklisted
