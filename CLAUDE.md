# CK3 modding project

Before writing any Crusader Kings III mod code, read `CK3_MODDING_GUIDE.md` in this folder.

- Game version installed: 1.20.1.2 "Crozier" (macOS, Steam).
- Vanilla files (read-only reference): `~/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game/`
- Mods go in: `~/Documents/Paradox Interactive/Crusader Kings III/mod/`
- Logs: `~/Documents/Paradox Interactive/Crusader Kings III/logs/error.log`
- Vanilla files and their `_*.info` docs beat wiki pages, which are often written for older versions.

## Dynasty Autopilot (mods/dynasty_autopilot)
- Loaded via `mod/dynasty_autopilot.mod` with an absolute `path` to this folder.
- Menu settings are declared in `tools/dap_settings.py`; run `python3 tools/build_dap.py` after editing it. Files named `*_generated*` are output: never edit them by hand.
- Building data (`dap_buildings_generated.txt`: every regular building's requirement triggers, cost, construction time, next level and focus scores by reach; names; per focus, the count of buildings with county-wide bonuses that picks the stacking county; per men-at-arms base type, stationed bonuses and terrain fit for military bases, in `dap_military_generated.txt` too) is generated from the installed game's building files by `python3 tools/build_buildings.py`; CI cannot run it, so rerun it after game patches and commit the output.
- Run `python3 tools/check_mod.py` before committing; CI runs it plus a check that generated files are up to date.
- Automatic building queues its picks; `gui/dap_build_driver.gui` opens the holding view for one at a time and the slot override (`gui/00_dap_building_item.gui`) presses Build or Upgrade (ADR 0001).
- Window: `gui/dap_window.gui`; button actions: `common/scripted_guis/dap_scripted_guis.txt`.
- Never restart or screenshot CK3 without asking if the user may be using it.
- In-game tests: `python3 tools/devtest/run.py suite` (one tick, ~1.5 min: sets up a scenario per feature, runs once, prints OK/FAIL and mod errors) and `python3 tools/devtest/run.py soak --years 30` (observer mode at top speed, no clicks needed, ~1 game year per minute; counts how often each log action fired). `python3 tools/devtest/run.py build` (~1 min) proves a real construction through the holding view's Build button (ADR 0001). All modes refuse to start while CK3 runs, and always close it and delete their temporary `zz_devtest` files. Run long soaks detached (`nohup … & disown`).
- Launch CK3 by running `ck3.app/Contents/MacOS/ck3` directly with `nohup … & disown` (not `open`), so macOS does not ask for Documents access; close test runs with `pkill -9 -x ck3`.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for PhilII/ck3-modding, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root (created when first needed). See `docs/agents/domain.md`.
