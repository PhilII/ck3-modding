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

Upgrades (issue 4) go the same way: the widget opens the slot holding the building to upgrade (`GUIBuildingItem.GetCurrentOrConstrucingBuilding`), or, for the holding's main building, which has no slot of its own, `HoldingView.GetGUIHoldingBuilding` from the first regular slot; then it presses `GUITrackItem.OnClick` on `HoldingView.GetTrack` when its next building is the one wanted. Several constructions a season are queued, and a small always-present widget (`gui/dap_build_driver.gui`) asks for the next one a second after the last was pressed, so only one view is ever opened at a time:

- Opening the holding view twice in one tick (once per run) loses the request, so script only queues and the driver alone opens the view.
- Each press must be followed by `HoldingView.CloseSubwindows`, as vanilla's buttons do; without it the open panel carries over to the next holding and its upgrade is never pressed.
- A delayed GUI state cannot time out an unpressed request: its delay did not restart on a re-trigger, so it fired at once and cut short upgrades still being pressed. An unpressed request lapses after a day instead.

Simulation was not needed. Re-copy the type after game patches that change it.

Later finding (issue 8): when two requests in a row want the same building, the open panel's widgets are reused and a press whose condition stayed true never fires again, so the queue stalled. The override now has two presses for new buildings and two for upgrades that take turns request by request (`var:dap_build_turn`, flipped in `dap_build_open_effect`; scripted GUIs `dap_build_pending_a` and `_b`). The turn is checked in the press's `trigger_when`, not its `visible`, since a hidden widget does not see its condition turn false either. The same route also builds in vassals' holdings, two levels down included.

Replacing buildings (issue 9) goes the same way, through vanilla's own Replace button: the widget opens the slot holding the building to replace, as for an upgrade, selects that building in the slot's track (`GUITrackItem.OnCurrentBuildingClick`) when it is not selected already, and presses `GUITrackItem.Replace`, which offers the new buildings; then the usual Build press picks the new one (`var:dap_build_replacing` marks such a request). Two Replace presses take turns, as for Build.

New holdings (issue 10) do not take this route: they use the engine's own holding construction, `begin_create_holding`, which shows as a holding under construction like the player's own. It charges nothing, so the mod pays the holding's base price itself (its main building's `cost_gold`, as vanilla's petition events do). This contradicts the decision above in one respect, accepted for now: like the rejected simulation, the price ignores holding cost modifiers such as `city_holding_holding_build_gold_cost`, and the player is not told.
