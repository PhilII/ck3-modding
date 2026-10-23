# CK3 Modding

Crusader Kings III (1.20 "Crozier") mods and modding notes.

| Path | What it is |
|---|---|
| [`mods/dynasty_autopilot/`](mods/dynasty_autopilot/) | **Dynasty Autopilot** – automates marriages, guardians, education and court/realm chores with configurable rules. See its [README](mods/dynasty_autopilot/README.md). |
| [`tools/`](tools/) | `dap_settings.py` (settings registry), `build_dap.py` (generates the settings files), `check_mod.py` (static checks). |
| [`CK3_MODDING_GUIDE.md`](CK3_MODDING_GUIDE.md) | Practical CK3 modding reference (Norwegian), verified against the 1.20 game files. |
| [`CLAUDE.md`](CLAUDE.md) | Working notes for Claude Code sessions in this project. |

## Using the mod locally

CK3 finds local mods through a `.mod` file in `~/Documents/Paradox Interactive/Crusader Kings III/mod/`. Point it at this checkout:

```
version="0.2.0"
tags={
	"Gameplay"
	"Character Interactions"
	"Decisions"
}
name="Dynasty Autopilot"
supported_version="1.20.*"
path="/absolute/path/to/this/repo/mods/dynasty_autopilot"
```

Then enable *Dynasty Autopilot* in a playset in the Paradox launcher.

## Changing settings

All menu settings and presets are declared in `tools/dap_settings.py`. After editing it:

```
python3 tools/build_dap.py
python3 tools/check_mod.py
```

Files with `generated` in their name are written by `build_dap.py`; never edit them by hand. `check_mod.py` also runs in GitHub Actions on every push and pull request.
