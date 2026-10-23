"""Static checks for the Dynasty Autopilot mod. Runs locally and in GitHub Actions.

Usage: python3 tools/check_mod.py

The game itself is not needed. Checks:
  - script, GUI and localization files are UTF-8 with BOM
  - curly braces balance in every script and GUI file
  - localization files start with the right l_<language>: header
  - every dap_* scripted effect, trigger and script value that is used is defined
  - every dap_* localization key used by GUI, custom localization or events exists
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
    check_no_dev_leftovers()
    for error in errors:
        print("ERROR", error)
    print(f"{len(errors)} problem(s) found" if errors else "All checks passed")
    sys.exit(1 if errors else 0)
