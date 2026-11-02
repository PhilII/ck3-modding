"""Static checks for the Dynasty Autopilot mod. Runs locally and in GitHub Actions.

Usage: python3 tools/check_mod.py

The game itself is not needed. Checks:
  - script, GUI and localization files are UTF-8 with BOM
  - curly braces balance in every script and GUI file
  - localization files start with the right l_<language>: header
  - every dap_* scripted effect, trigger and script value that is used is defined
  - every dap_* localization key used by GUI, custom localization or events exists
  - the generated building data classifies known buildings by reach as expected, and
    counts the known ones with county-wide bonuses for picking the stacking county
  - it gives known buildings the stationed men-at-arms bonuses they have, by base type,
    and counts the known ones a holding has for picking a military base's specialty
  - it has the requirements and cost of starting the new holdings automatic building starts
  - no dev-test scaffolding or debug_log lines are left in the mod
Exits with status 1 if anything fails.
"""

import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MOD = os.path.join(ROOT, "mods", "dynasty_autopilot")
TEXT_EXTENSIONS = (".txt", ".gui", ".yml")

errors = []


def files(*extensions):
    for folder, _, names in os.walk(MOD):
        for name in sorted(names):
            if name.endswith(extensions):
                yield os.path.join(folder, name)


def rel(path):
    return os.path.relpath(path, ROOT)


def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def strip_comments_and_strings(text):
    text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
    return re.sub(r"#[^\n]*", "", text)


def check_bom():
    for path in files(*TEXT_EXTENSIONS):
        with open(path, "rb") as f:
            if f.read(3) != b"\xef\xbb\xbf":
                errors.append(f"{rel(path)}: missing UTF-8 BOM")


def check_braces():
    for path in files(".txt", ".gui"):
        depth = 0
        for number, line in enumerate(strip_comments_and_strings(read(path)).split("\n"), 1):
            depth += line.count("{") - line.count("}")
            if depth < 0:
                errors.append(f"{rel(path)}:{number}: closing brace without an opening one")
                break
        if depth > 0:
            errors.append(f"{rel(path)}: {depth} unclosed brace(s)")


def check_localization_headers():
    for path in files(".yml"):
        language = os.path.basename(os.path.dirname(path))
        if not path.endswith(f"_l_{language}.yml"):
            errors.append(f"{rel(path)}: file name must end with _l_{language}.yml")
        first = read(path).split("\n", 1)[0].strip()
        if first != f"l_{language}:":
            errors.append(f"{rel(path)}: first line must be 'l_{language}:', found '{first}'")


def definitions(subfolder):
    names = set()
    for path in files(".txt"):
        if f"{os.sep}{subfolder}{os.sep}" in path:
            names.update(re.findall(r"^(dap_[a-z0-9_]+)\s*=\s*\{", read(path), re.M))
    return names


def variable_names():
    """Names used as variables; they can look like effects or localization keys."""
    names = set()
    for path in files(".txt", ".gui"):
        names.update(re.findall(r"(?:\bvar:|local_var:|has_variable = |remove_variable = |Var\(\s*')(dap_[a-z0-9_]+)", read(path)))
    return names


def check_script_references():
    defined = definitions("scripted_effects") | definitions("scripted_triggers") | definitions("script_values")
    defined |= variable_names()
    for path in files(".txt"):
        text = strip_comments_and_strings(read(path))
        for name in sorted(set(re.findall(r"\b(dap_[a-z0-9_]+_(?:effect|trigger|value|score))\b", text))):
            if name not in defined:
                errors.append(f"{rel(path)}: '{name}' is used but not defined")


def check_localization_keys():
    english = os.path.join(MOD, "localization", "english")
    keys = set()
    for name in os.listdir(english):
        keys.update(re.findall(r"^\s*([A-Za-z0-9_.]+):", read(os.path.join(english, name)), re.M))
    patterns = [
        r'text = "(dap_[a-z0-9_.]+)"',
        r'tooltip = "(dap_[a-z0-9_.]+)"',
        r"localization_key = (dap_[a-z0-9_.]+)",
        # Only when alone on the line: "name = x" inside set_variable is a variable name
        r"^\s*(?:title|desc|name|confirm_text|selection_tooltip|custom_tooltip) = (dap_[a-z0-9_.]+)\s*$",
    ]
    keys |= variable_names()
    for path in files(".txt", ".gui"):
        text = read(path)
        for pattern in patterns:
            for key in re.findall(pattern, text, re.M):
                if key not in keys:
                    errors.append(f"{rel(path)}: localization key '{key}' is missing")


def generated_building_scores():
    """BUILDING -> its score parameters, from the generated building candidates."""
    path = os.path.join(MOD, "common", "scripted_effects", "dap_buildings_generated.txt")
    scores = {}
    for call in re.findall(r"dap_consider_building_effect = \{([^}]*)\}", read(path)):
        params = dict(re.findall(r"(\w+) = (\S+)", call))
        scores[params["BUILDING"]] = params
    return scores


# Known classifications that a game patch could silently break: (building, reach, focus) pairs
# that must score above zero, and ones that must not
KNOWN_SCORES = {
    "watermills_01": {"DEVELOPMENT_COUNTY": True, "INCOME_HOLDING": True, "INCOME_COUNTY": False},
    "guild_halls_01": {"DEVELOPMENT_COUNTY": True},
    "farm_estates_01": {"INCOME_HOLDING": True, "INCOME_COUNTY": False, "DEVELOPMENT_COUNTY": False},
    "watermills_02": {"DEVELOPMENT_COUNTY": True, "INCOME_HOLDING": True},
    "castle_02": {"INCOME_HOLDING": True},
}


def check_building_classifications():
    scores = generated_building_scores()
    for building, expected in KNOWN_SCORES.items():
        if building not in scores:
            errors.append(f"generated building data: {building} is not a candidate")
            continue
        for param, positive in expected.items():
            if (float(scores[building].get(param, 0)) > 0) != positive:
                errors.append(f"generated building data: {building} {param} should be "
                              f"{'above zero' if positive else 'zero'}, is {scores[building].get(param)}")


# Buildings that must, or must not, count towards a focus when picking the stacking county
KNOWN_COUNTY_COUNTS = {
    "dap_holding_development_buildings_value": {"watermills_01": True, "guild_halls_01": True, "farm_estates_01": False},
    "dap_holding_income_buildings_value": {"cereal_fields_02": True, "watermills_01": False},
}


def check_county_counts():
    path = os.path.join(MOD, "common", "script_values", "dap_buildings_generated.txt")
    blocks = dict(re.findall(r"^(dap_\w+) = \{(.*?)^\}", read(path), re.M | re.S))
    for value, expected in KNOWN_COUNTY_COUNTS.items():
        counted = set(re.findall(r"has_building = (\w+)", blocks.get(value, "")))
        for building, positive in expected.items():
            if (building in counted) != positive:
                errors.append(f"generated building data: {value} should {'' if positive else 'not '}count {building}")


# Stationed men-at-arms bonuses of known buildings: base type (or "maa", as the game calls
# bonuses to every type stationed there) -> whether it gets one
KNOWN_STATIONED = {
    "military_camps_01": {"skirmishers": True, "archers": True, "light_cavalry": False, "maa": False},
    "stables_01": {"light_cavalry": True, "heavy_cavalry": True, "skirmishers": False},
    "regimental_grounds_01": {"maa": True, "skirmishers": False},
    "watermills_01": {"maa": False, "skirmishers": False},
}
# Buildings that must, or must not, count towards a type when choosing a base's specialty
KNOWN_SPECIALTY_COUNTS = {
    "dap_holding_skirmishers_stationed_value": {"military_camps_01": True, "regimental_grounds_01": False},
    "dap_holding_light_cavalry_stationed_value": {"stables_01": True, "military_camps_01": False},
}


def check_stationed_bonuses():
    path = os.path.join(MOD, "common", "script_values", "dap_buildings_generated.txt")
    blocks = dict(re.findall(r"^(dap_\w+) = \{(.*?)^\}", read(path), re.M | re.S))
    for building, expected in KNOWN_STATIONED.items():
        block = blocks.get(f"dap_stationed_{building}_value", "")
        found = {"maa": float((re.search(r"^\tvalue = (\S+)", block, re.M) or [0, "0"])[1]) > 0}
        for base_type, amount in re.findall(r"flag:(\w+) \}\s*add = (\S+)", block):
            found[base_type] = float(amount) > 0
        for base_type, positive in expected.items():
            if found.get(base_type, False) != positive:
                errors.append(f"generated building data: {building} should {'' if positive else 'not '}"
                              f"have a stationed bonus for {base_type}")
    for value, expected in KNOWN_SPECIALTY_COUNTS.items():
        counted = set(re.findall(r"has_building = (\w+)", blocks.get(value, "")))
        for building, positive in expected.items():
            if (building in counted) != positive:
                errors.append(f"generated building data: {value} should {'' if positive else 'not '}count {building}")


# What replacing a known building loses: all it gives, not just its last level's increase;
# None for a building that comes with its holding and is never replaced
KNOWN_REPLACEMENT_WORTH = {
    "military_camps_01": {"MILITARY": True, "INCOME_HOLDING": False, "DEVELOPMENT_COUNTY": False},
    "watermills_02": {"DEVELOPMENT_COUNTY": True, "INCOME_HOLDING": True, "MILITARY": False},
    "castle_01": None,
    "castle_02": None,
}


def check_replacement_worth():
    path = os.path.join(MOD, "common", "scripted_effects", "dap_buildings_generated.txt")
    worth = {}
    for call in re.findall(r"dap_consider_replacement_effect = \{([^}]*)\}", read(path)):
        params = dict(re.findall(r"(\w+) = (\S+)", call))
        worth[params["FROM"]] = params
    for building, expected in KNOWN_REPLACEMENT_WORTH.items():
        if expected is None:
            if building in worth:
                errors.append(f"generated building data: {building} comes with its holding but could be replaced")
            continue
        if building not in worth:
            errors.append(f"generated building data: {building} cannot be replaced")
            continue
        for param, positive in expected.items():
            if (float(worth[building].get(param, 0)) > 0) != positive:
                errors.append(f"generated building data: replacing {building} loses {param} "
                              f"{worth[building].get(param)}, expected {'above zero' if positive else 'zero'}")
    # An upgrade's worth is all the building gives, so it is more than its level's increase
    upgrade = generated_building_scores().get("watermills_02", {})
    if worth.get("watermills_02") and float(worth["watermills_02"]["DEVELOPMENT_COUNTY"]) <= float(upgrade.get("DEVELOPMENT_COUNTY", 0)):
        errors.append("generated building data: replacing watermills_02 should lose more than its upgrade adds")


# New holdings: the holding type started for each focus, and a requirement the game sets for it
KNOWN_NEW_HOLDINGS = {"city_holding": "innovation_city_planning", "castle_holding": "innovation_motte"}


def check_new_holdings():
    triggers = read(os.path.join(MOD, "common", "scripted_triggers", "dap_buildings_generated.txt"))
    values = read(os.path.join(MOD, "common", "script_values", "dap_buildings_generated.txt"))
    for holding, innovation in KNOWN_NEW_HOLDINGS.items():
        block = re.search(rf"^dap_can_create_{holding}_trigger = \{{(.*?)^\}}", triggers, re.M | re.S)
        if not block:
            errors.append(f"generated building data: no trigger for starting a new {holding}")
            continue
        for needed in ("has_holding = no", innovation):
            if needed not in block[1]:
                errors.append(f"generated building data: starting a new {holding} should need {needed}")
        if not re.search(rf"^dap_{holding}_cost_value = \{{\s*value = main_building_tier_1_cost", values, re.M):
            errors.append(f"generated building data: a new {holding} should cost main_building_tier_1_cost")


def check_no_dev_leftovers():
    for path in files(*TEXT_EXTENSIONS):
        if "zz_devtest" in os.path.basename(path):
            errors.append(f"{rel(path)}: dev-test file must not be committed")
            continue
        for number, line in enumerate(read(path).split("\n"), 1):
            if re.search(r"\bdebug_log(_scopes|_date)?\s*=", line) or "devtest" in line:
                errors.append(f"{rel(path)}:{number}: debug/dev-test line left in the mod")


if __name__ == "__main__":
    check_bom()
    check_braces()
    check_localization_headers()
    check_script_references()
    check_localization_keys()
    check_building_classifications()
    check_county_counts()
    check_stationed_bonuses()
    check_replacement_worth()
    check_new_holdings()
    check_no_dev_leftovers()
    for error in errors:
        print("ERROR", error)
    print(f"{len(errors)} problem(s) found" if errors else "All checks passed")
    sys.exit(1 if errors else 0)
