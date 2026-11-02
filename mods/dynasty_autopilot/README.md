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
| Buildings | Once a season, starts the new buildings and upgrades (main castle, city or temple building included) worth the most for their cost to your Income, Development and Military stacking focuses (Off, Low or High; High counts three times as much) in your own holdings and your vassal barons', cities' and temples' holdings inside your own counties (where income counts only as the tax they pay you), with gold above your reserve and up to a set number per season, by pressing the real Build or Upgrade button. County-wide bonuses are stacked by county stacking: they go only into the stacking county, the one with the most buildings serving that focus (your capital breaking ties) that still has room for more. Stationed men-at-arms bonuses are stacked in military bases in your own domain: one holding per men-at-arms type you own (a second only when the first has no room left), whose specialty follows the stationed bonuses already built there, then the terrain, unless you set it. The Buildings tab lists every base, its specialty and whether regiments of it are stationed there; station them yourself. Opt-in: building in your vassals' counties, replacing buildings that serve no focus, starting new holdings, duchy capital buildings (in the capital barony of a duchy you hold) and special buildings such as mines (in their own slot; a new one only where the game's files say which building the slot is for). Great projects are never automated. Skips holdings with construction under way. The yearly building reminder is off while it is on |

Every module has a **Mode** setting: *Act* or *Suggest only* (log what it would do without doing it).

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
