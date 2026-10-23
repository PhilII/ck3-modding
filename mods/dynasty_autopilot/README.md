# Dynasty Autopilot

A Crusader Kings III (1.20 "Crozier") mod that automates the tedious parts of running a dynasty, with rules you choose.

Open it from **Decisions → Dynasty Autopilot**, or right-click a family member → **Dynasty Autopilot Rules**.
Everything runs once per season (or immediately with **Run now**) and is recorded in the log in the **General** tab.

## Tabs

| Tab | What it automates |
|---|---|
| General | Master switch, which family members are managed, gold reserve, pause during war/illness/captivity, asking before big decisions, the action log |
| Marriage | Matches for children, grandchildren or the whole dynasty at court; your own spouses and concubines; extra spouses where faith allows; widows; betrothal reviews; inviting candidates; "ask me first" |
| Guardians | Best guardian per child (by focus skill, total skills or personality), replacing unfit guardians |
| Education | Education focus by role (heir, sons, daughters), natural talent, council needs or a fixed skill |
| Court | Sway hostile vassals, fill council seats and court positions, knights, prisoners, granting counties and duchies, creating titles, recruiting men-at-arms, building reminder |

Every module has a **Mode** setting: *Act* or *Suggest only* (log what it would do without doing it).

## Rules

Marriage, guardian and education rules have **default rules** and optional **personal rules** per family member.
Requirements must all be met; among candidates who meet them, the best is ranked by the chosen priority.
Presets (Bloodline, Power, Quick) and three save slots are available, plus copy-to-all and reset-all.

## Not automated, and why

- **Childhood personality choices**: they live in vanilla event files; automating them would mean overwriting those events. Use *Pick me as guardian: Never* to avoid them.
- **Revoking titles**: the vanilla revoke interaction cannot be run from script with a specific title, and doing it directly would skip the vassal's right to refuse. Hostile vassals you could revoke from are listed in the log instead.
- **Building**: mods cannot start a construction, only add finished buildings for free. A yearly reminder is sent instead.
- **Concubines** come only from your court and prisoners, as in vanilla. Sunni Islam in 1.20 has no concubines.

## Compatibility

No vanilla files are overridden. It appends to `quarterly_playable_pulse` and adds its own window through `gui/scripted_widgets`. Safe to add mid-game; removing it mid-game leaves harmless unused variables.

## Development

Settings live in `tools/dap_settings.py` (outside the mod folder). Run `python3 tools/build_dap.py` to regenerate the `*_generated*` files and the copies of the English text for other languages.
