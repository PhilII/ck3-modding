# Automatic building presses the real Build button

No script effect starts construction of a specific building, but the vanilla holding view's Build button (`GUIPotentialBuildingItem.Construct`) does, and script can open that view (`open_view_data = holding_view` on the province). The automatic builder uses that real construction path, so buildings cost what they cost the player and show as under construction, rather than simulating construction with `add_building`. If no clean way exists to press the button from the mod's own widget, we accept overriding the vanilla holding view GUI, breaking the mod's otherwise strict no-override rule, because the player wants an assistant that builds exactly as they would, not one that bends the game's rules.

## Considered Options

- Simulate: pay the base cost, wait the build time, then `add_building`. Fully compatible, but invisible as construction and blind to cost modifiers such as `build_gold_cost`.
- Drop the feature.

## Consequences

If the Build button cannot be pressed from script at all (for example, only while the window is visible to the player), the builder falls back to simulation, and the player is told before that is built.

## Outcome of the prototype (game version 1.20.1.2)

The clean route, pressing Build from the mod's own widget, is impossible: no GUI function returns a `HoldingView` or a `GUIPotentialBuildingItem` outside the holding view window, so only widgets inside that window can reach the button.

The override route works, and it is kept small: instead of overriding the whole `window_county_view.gui`, the mod redefines one type, the building slot `widget_building_item`, copied unchanged with one invisible widget added (`gui/00_dap_building_item.gui`). The mod stores the holding and building it wants, then opens the holding view from script (`open_view_data = holding_view`). In that holding's view, the added widget clicks a free slot and presses `GUIPotentialBuildingItem.Construct` on the building whose key matches, then calls back into script and closes the view. `python3 tools/devtest/run.py build` proves it: construction under way in the holding the mod picked, and the real price (100 gold for military camps in Norway) paid once.

Things learned on the way:

- The first definition of a GUI type wins, so the override's file name must sort before vanilla's `window_county_view.gui`; a `zz_` name is silently ignored.
- `HoldingView.IsSelectingNewBuilding` is already true when the view opens, so it cannot tell whether a slot was clicked; `GUIBuildingItem.IsHighlighted` marks the clicked slot.
- Every slot instance holds the widget, so only the highlighted slot may press Build, and the view must close in a later GUI state: closing it while another press is queued crashed the game in `CHoldingView::Construct`.
- The holding view opens on screen for a moment while this runs.

Simulation was not needed. Re-copy the type after game patches that change it.
