# Automatic building presses the real Build button

No script effect starts construction of a specific building, but the vanilla holding view's Build button (`GUIPotentialBuildingItem.Construct`) does, and script can open that view (`open_view_data = { view = holding_view }`). The automatic builder uses that real construction path, so buildings cost what they cost the player and show as under construction, rather than simulating construction with `add_building`. If no clean way exists to press the button from the mod's own widget, we accept overriding the vanilla holding view GUI, breaking the mod's otherwise strict no-override rule, because the player wants an assistant that builds exactly as they would, not one that bends the game's rules.

## Considered Options

- Simulate: pay the base cost, wait the build time, then `add_building`. Fully compatible, but invisible as construction and blind to cost modifiers such as `build_gold_cost`.
- Drop the feature.

## Consequences

If the Build button cannot be pressed from script at all (for example, only while the window is visible to the player), the builder falls back to simulation, and the player is told before that is built.
