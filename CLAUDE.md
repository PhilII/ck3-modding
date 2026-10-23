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
- Run `python3 tools/check_mod.py` before committing; CI runs it plus a check that generated files are up to date.
- Window: `gui/dap_window.gui`; button actions: `common/scripted_guis/dap_scripted_guis.txt`.
- Never restart or screenshot CK3 without asking if the user may be using it.
- Launch CK3 by running `ck3.app/Contents/MacOS/ck3` directly with `nohup … & disown` (not `open`), so macOS does not ask for Documents access; close test runs with `pkill -9 -x ck3`.
