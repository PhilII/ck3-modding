# Dynasty Autopilot

A Crusader Kings III (1.20 "Crozier") mod that automates the tedious parts of running a dynasty, with rules you choose.

Open it from **Decisions → Dynasty Autopilot**, or right-click a family member → **Dynasty Autopilot Rules**.
Everything runs once per season (or immediately with **Run now**) and is recorded in the log in the **General** tab.

## Tabs

| Tab | What it automates |
|---|---|
| General | Master switch, which family members are managed, gold reserve, pause during war/illness/captivity, asking before big decisions, the action log |
| Marriage | Matches for children, grandchildren or the whole dynasty at court; your own spouses and concubines; extra spouses where faith allows; widows; betrothal reviews; inviting candidates; "ask me first" |
| Guardians | Best guardian per child (by focus skill, total skills or personality, optionally of your faith), replacing unfit guardians |
| Education | Education focus by role (heir, sons, daughters), natural talent, council needs or a fixed skill |
| Court | Sway hostile vassals, fill council seats and court positions, set council tasks (Domestic Affairs for unhappy vassals, taxes when short of gold, development or culture, control in unruly counties, disrupting exposed schemes), knights, prisoners, granting counties and duchies, creating titles, recruiting men-at-arms, building reminder |
| Faith | Fill the Court Chaplain seat, have the chaplain convert counties of another faith or rite (capital duchy or most/least developed first), ask family members, spouses and vassals who would accept to adopt your faith, piety reserve, ask the Head of Faith for gold, excommunication alert, warnings about an heir of another faith or hostile-faith vassals, yearly faith report |
| Buildings | Once a season, starts the new buildings and upgrades worth the most for their cost to the focuses you choose, by pressing the real Build button; see [Buildings tab](#buildings-tab) |

Every module has a **Mode** setting: *Act* or *Suggest only* (log what it would do without doing it).

## Buildings tab

Automatic building is off until you switch it on. Once a season it scores every new building and upgrade it may build, and starts those worth the most for their cost, within the gold above your reserve and up to **Constructions per season**. It presses the real Build or Upgrade button in the holding view (which opens for a moment), so each construction costs what it costs you and takes the game's construction time. Holdings with construction under way are skipped. The yearly building reminder is off while it is on.

**Focuses** (Off, Low or High; High counts three times as much as Low):

- **Income**: buildings that raise your gold. In a vassal's holding only the tax they pay you counts.
- **Development**: buildings that make a county's development grow faster.
- **Military stacking**: bonuses for stationed men-at-arms, in military bases in your own domain.

**Where it builds**: your own holdings, and your vassal barons', cities' and temples' holdings inside your own counties. Bonuses to a whole county go by *county stacking*: into one stacking county at a time, the one with the most buildings already serving that focus (your capital breaking ties) that still has room. Military bases are one holding per men-at-arms type you own (a second only when the first is full); a base's specialty follows the stationed bonuses already built there, then the terrain, unless you set it. The tab lists every base, its specialty and whether regiments of that type are stationed there: station them yourself. It also lists your counties and their holdings, where you can exclude a holding or a whole county.

**Options** (all off by default):

| Option | When on |
|---|---|
| Vassals' counties | Also builds in your direct vassals' counties, once your own have nothing left worth building |
| Replace buildings | In a full county, replaces a building that serves no active focus with one that gives at least 50% more |
| New holdings | Once there is nowhere left to build for a focus, starts a city (Income or Development) or a castle (a full military base) in an empty barony of a county you hold, paying its base price |
| Duchy capital buildings | Builds and upgrades them in the capital barony of a duchy you hold |
| Special buildings | Builds and upgrades special buildings such as mines in their own slot; a new one only where the game's files say which building the slot is for |

Great projects are never automated. Use **Mode: Suggest only** to see in the log what it would build before trusting it with your gold.

**Tested** in a 30-year observer-mode soak as the King of Norway from 1066, with every option on and 100 gold a season (the AI ruler spends its own gold, leaving almost none for building): 35 constructions started (10 new buildings, 23 upgrades, 2 new holdings) through a succession, with 0 mod errors. No replacement, duchy capital or special building was ever worth it there; the in-game suite covers those.

## Rules

Marriage, guardian and education rules have **default rules** and optional **personal rules** per family member.
Requirements must all be met; among candidates who meet them, the best is ranked by the chosen priority.
Presets (Bloodline, Power, Quick) and three save slots are available, plus copy-to-all and reset-all.

## Not automated, and why

- **Childhood personality choices**: they live in vanilla event files; automating them would mean overwriting those events. Use *Pick me as guardian: Never* to avoid them.
- **Revoking titles**: the vanilla revoke interaction cannot be run from script with a specific title, and doing it directly would skip the vassal's right to refuse. Hostile vassals you could revoke from are listed in the log instead.
- **Building** serves the Income, Development and Military stacking focuses only. Great projects are never automated, and new special buildings only go where the game's files place their slot (slots that events add elsewhere get one only once something stands in them, as an upgrade). In Suggest only mode, and in the log generally, only the latest building entry is kept.
- **Concubines** come only from your court and prisoners, as in vanilla. Sunni Islam in 1.20 has no concubines.

## Compatibility

No vanilla files are overridden. It appends to `quarterly_playable_pulse` and adds its own window through `gui/scripted_widgets`. One vanilla GUI type is redefined: the holding view's building slot (`widget_building_item`, in `gui/00_dap_building_item.gui`), so the mod can press the real Build button. UI mods that also redefine that type conflict with it. Safe to add mid-game; removing it mid-game leaves harmless unused variables.

## Development

Settings live in `tools/dap_settings.py` (outside the mod folder). Run `python3 tools/build_dap.py` to regenerate the `*_generated*` files and the copies of the English text for other languages.
Building data (`dap_buildings_generated.txt`, `dap_military_generated.txt`) comes from the installed game: run `python3 tools/build_buildings.py` after game patches.
