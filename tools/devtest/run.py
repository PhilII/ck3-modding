"""Runs Dynasty Autopilot in the real game and reports what every feature did.

Usage:
  python3 tools/devtest/run.py suite            # one tick: scenario setup, one run, checks;
                                                # then the construction the run asked for
  python3 tools/devtest/run.py soak --years 30  # many years at full speed in observer mode
  python3 tools/devtest/run.py build            # a mod widget starts a real construction (ADR 0001)

All modes:
  - refuse to start if CK3 is already running (the user may be playing)
  - write temporary zz_devtest files into the mod, launch CK3 as the ruler of
    --play, wait for "DAPTEST done", a crash or the timeout, then print every
    DAPTEST line plus the mod's errors from error.log
  - always close CK3 and delete the temporary files, even on Ctrl-C

The soak mode adds a GUI widget that switches to observer mode, unpauses and
sets top speed by itself, so no clicks are needed and events never stop time.
The ruler you start as keeps being automated by the harness (marked with
dap_devtest_ai), and is followed through successions.

The build mode adds a GUI widget that, like a button in the mod's window, asks
for a construction; the mod then presses the holding view's real Build button.
The suite adds a GUI widget that waits for the construction its seasonal run
asked for, checks it, and only then runs the succession test.
"""

import argparse
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MOD = os.path.join(ROOT, "mods", "dynasty_autopilot")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from dap_settings import MODULES  # noqa: E402

STEAM_GAME = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Crusader Kings III")
BINARIES = os.path.join(STEAM_GAME, "binaries")
CK3 = os.path.join(BINARIES, "ck3.app", "Contents", "MacOS", "ck3")
LOGS = os.path.expanduser("~/Documents/Paradox Interactive/Crusader Kings III/logs")

FILES = {
    "on_action": "common/on_action/zz_devtest_on_actions.txt",
    "events": "events/zz_devtest_events.txt",
    "gui": "gui/zz_devtest_autorun.gui",
    "widgets": "gui/scripted_widgets/zz_devtest_widgets.txt",
    "sguis": "common/scripted_guis/zz_devtest_sguis.txt",
}

# Every player setting switched to a value that lets its feature act.
# Settings not listed keep their default.
TEST_VALUES = {
    "dap_master": 1, "dap_gold_reserve": 0, "dap_pause": 0, "dap_confirm": 0, "dap_who": 2,
    "dap_enabled": 1, "dap_skip_heir": 0, "dap_landed_family": 1, "dap_self": 1,
    "dap_concubines": 1, "dap_extra_spouses": 1, "dap_invite": 1, "dap_own_court": 1,
    "dap_betrothal_review": 2, "dap_remarry": 1, "dap_report": 1,
    "dap_guard_enabled": 1, "dap_guard_source": 1, "dap_guard_replace": 1,
    "dap_edu_enabled": 1, "dap_edu_override": 1,
    "dap_court_sway": 2, "dap_court_council": 2, "dap_court_knights": 1,
    "dap_grant_when": 3, "dap_grant_to": 2, "dap_grant_max_each": 3, "dap_grant_contract": 1,
    "dap_grant_duchies": 1, "dap_create_titles": 2, "dap_revoke_suggest": 1,
    "dap_court_positions": 2, "dap_maa_type": 1, "dap_build_reminder": 1, "dap_court_prisoners": 2,
    "dap_task_chancellor": 2, "dap_task_steward": 2, "dap_task_marshal": 1, "dap_task_spymaster": 1,
    "dap_faith_enabled": 1, "dap_faith_chaplain": 2, "dap_faith_task": 1, "dap_faith_family": 1,
    "dap_faith_spouses": 1, "dap_faith_vassals": 2, "dap_hof_gold": 1, "dap_excomm_alert": 1,
    "dap_faith_warn_heir": 1, "dap_faith_warn_vassals": 1, "dap_faith_report": 1,
    "dap_build_enabled": 1, "dap_build_development": 2,
}


def log_flags():
    """Every log action the mod can record, read from its custom localization."""
    with open(os.path.join(MOD, "common", "customizable_localization", "dap_custom_loc.txt"), encoding="utf-8-sig") as f:
        return sorted(set(re.findall(r"flag:(dap_log_\w+)", f.read())))


def player_keys():
    return {st["key"] for m in MODULES for sec in m["sections"] if sec["holder"] == "player" for st in sec["settings"]}


def apply_test_values():
    keys = player_keys()
    unknown = set(TEST_VALUES) - keys
    assert not unknown, f"TEST_VALUES has unknown settings: {unknown}"
    return "".join(f"\t\tset_variable = {{ name = {k} value = {v} }}\n" for k, v in sorted(TEST_VALUES.items()))


def count_effect(flags):
    out = ["dap_devtest_count_effect = {\n\tevery_in_list = {\n\t\tvariable = dap_log\n"]
    for flag in flags:
        out.append(f"\t\tif = {{\n\t\t\tlimit = {{ var:dap_log_action ?= flag:{flag} }}\n"
                   f"\t\t\troot = {{ change_variable = {{ name = dap_cnt_{flag} add = 1 }} }}\n\t\t}}\n")
    out.append("\t}\n}\n\n")
    out.append("dap_devtest_zero_counts_effect = {\n")
    for flag in flags:
        out.append(f"\tset_variable = {{ name = dap_cnt_{flag} value = 0 }}\n")
    out.append("}\n\n")
    out.append("dap_devtest_report_effect = {\n")
    for flag in flags:
        out.append(f"\tif = {{\n\t\tlimit = {{ var:dap_cnt_{flag} > 0 }}\n"
                   f"\t\tsave_scope_value_as = {{ name = count value = var:dap_cnt_{flag} }}\n"
                   f"\t\tdebug_log = \"DAPTEST fired {flag}\"\n\t\tdebug_log_scopes = yes\n\t}}\n"
                   f"\telse = {{\n\t\tdebug_log = \"DAPTEST never fired {flag}\"\n\t}}\n")
    out.append("}\n")
    return "".join(out)


ON_ACTIONS = """\
on_game_start_after_lobby = {
	on_actions = { dap_devtest_start }
}

dap_devtest_start = {
	effect = {
		every_player = { trigger_event = dap_devtest.1 }
	}
}

quarterly_playable_pulse = {
	on_actions = { dap_devtest_pulse }
}

dap_devtest_pulse = {
	trigger = { has_variable = dap_devtest_ai }
	effect = { trigger_event = dap_devtest.10 }
}

on_death = {
	on_actions = { dap_devtest_death }
}

dap_devtest_death = {
	trigger = { has_variable = dap_devtest_ai }
	effect = { dap_devtest_follow_heir_effect = yes }
}
"""

# Same tick: build a situation for each feature, run once, check.
SUITE_SETUP = """\
		add_gold = 5000
		add_piety = 3000
		add_prestige = 3000
		# Marriage: unmarried adult children at court
		create_character = { age = 19 gender = male dynasty_house = root.house father = root faith = root.faith culture = root.culture employer = root save_scope_as = dap_t_son }
		create_character = { age = 18 gender = female dynasty_house = root.house father = root faith = root.faith culture = root.culture employer = root save_scope_as = dap_t_daughter }
		# Guardians and education: young children
		create_character = { age = 6 gender = male dynasty_house = root.house father = root faith = root.faith culture = root.culture employer = root save_scope_as = dap_t_kid1 }
		create_character = { age = 7 gender = female dynasty_house = root.house father = root faith = root.faith culture = root.culture employer = root save_scope_as = dap_t_kid2 }
		# Faith: a family member and a county of another faith, a vassal of a hostile faith who hates us
		create_character = { age = 25 gender = male dynasty_house = root.house father = root faith = faith:orthodox culture = root.culture employer = root save_scope_as = dap_t_orthodox }
		ordered_realm_county = {
			limit = { NOT = { this = root.capital_county } }
			order_by = development_level
			max = 2
			set_county_faith = faith:orthodox
		}
		random_vassal = {
			set_character_faith = faith:norse_pagan
			add_opinion = { target = root modifier = hate_opinion opinion = -80 }
		}
		# Council tasks: a county with low control (the hating vassal above covers the chancellor)
		ordered_realm_county = {
			limit = { NOT = { this = root.capital_county } }
			order_by = development_level
			max = 1
			change_county_control = -60
			save_scope_as = dap_t_low_control
		}
		# Court: an empty council seat and a prisoner
		cp:councillor_chancellor ?= { save_scope_as = dap_t_chancellor }
		if = {
			limit = { exists = scope:dap_t_chancellor }
			fire_councillor = scope:dap_t_chancellor
		}
		create_character = { age = 30 gender = male faith = root.faith culture = root.culture location = root.capital_province save_scope_as = dap_t_prisoner }
		imprison = { target = scope:dap_t_prisoner type = dungeon }
		# A free slot in the capital's holding for the seasonal run below, and a development
		# building that may go there (Norway's watermills need this innovation in 1066)
		culture = { add_innovation = innovation_windmills }
		capital_province = {
			if = {
				limit = { has_free_building_slot = no }
				add_province_modifier = extra_building_slot
			}
		}
		# Buildings: nothing is asked for with the switch off, or without gold above the reserve
		set_variable = { name = dap_build_enabled value = 0 }
		dap_run_buildings_effect = yes
		if = {
			limit = { has_variable = dap_build_building }
			debug_log = "DAPTEST FAIL a building was asked for with automatic building off"
		}
		else = { debug_log = "DAPTEST OK no building with automatic building off" }
		set_variable = { name = dap_build_enabled value = 1 }
		set_variable = { name = dap_gold_reserve value = 3 }
		remove_short_term_gold = gold
		add_gold = dap_gold_reserve_value
		dap_run_buildings_effect = yes
		if = {
			limit = { has_variable = dap_build_building }
			debug_log = "DAPTEST FAIL a building was asked for without gold above the reserve"
		}
		else = { debug_log = "DAPTEST OK no building without gold above the reserve" }
		set_variable = { name = dap_gold_reserve value = 0 }
		add_gold = 5000
"""

SUITE_CHECKS = """\
		# The seasonal run asked for a development building in the capital; the holding
		# view presses Build after this tick (dap_devtest_suite_build_check)
		if = {
			limit = {
				has_variable = dap_build_building
				var:dap_build_province ?= root.capital_province
			}
			debug_log = "DAPTEST OK the seasonal run asked for a building in the capital"
		}
		else = {
			debug_log = "DAPTEST FAIL the seasonal run asked for no building in the capital"
			capital_province = {
				dap_pick_building_in_province_effect = yes
				if = {
					limit = { has_free_building_slot = no }
					debug_log = "DAPTEST   the capital has no free slot"
				}
				if = {
					limit = { has_ongoing_construction = yes }
					debug_log = "DAPTEST   the capital has a construction under way"
				}
			}
			if = {
				limit = { NOT = { exists = scope:dap_build_building } }
				debug_log = "DAPTEST   no development building can be built in the capital"
			}
		}
		if = {
			limit = { cp:councillor_chancellor ?= { is_performing_council_task = task_domestic_affairs } }
			debug_log = "DAPTEST OK chancellor on Domestic Affairs (a vassal hates you)"
		}
		else = { debug_log = "DAPTEST FAIL chancellor not on Domestic Affairs" }
		if = {
			limit = {
				cp:councillor_steward ?= {
					OR = {
						is_performing_council_task = task_promote_culture
						is_performing_council_task = task_develop_county
					}
				}
			}
			debug_log = "DAPTEST OK steward promoting culture or developing"
		}
		else = { debug_log = "DAPTEST FAIL steward not on culture or development" }
		if = {
			limit = { cp:councillor_marshal ?= { is_performing_council_task = task_increase_control } }
			debug_log = "DAPTEST OK marshal increasing control"
		}
		else = { debug_log = "DAPTEST FAIL marshal not increasing control" }
		if = {
			limit = { cp:councillor_spymaster ?= { is_performing_council_task = task_find_secrets } }
			debug_log = "DAPTEST OK spymaster finding secrets"
		}
		else = { debug_log = "DAPTEST FAIL spymaster not finding secrets" }
		# Running again with nothing changed must not switch any task
		clear_variable_list = dap_log
		dap_run_council_tasks_effect = yes
		if = {
			limit = { has_variable_list = dap_log variable_list_size = { name = dap_log value > 0 } }
			debug_log = "DAPTEST FAIL council tasks switched again with nothing changed"
			every_in_list = {
				variable = dap_log
				debug_log = "DAPTEST   switched again:"
				debug_log_scopes = yes
			}
		}
		else = { debug_log = "DAPTEST OK council tasks stay put on a second run" }
		# Broke, and an exposed murder plot: the steward must collect taxes, the spymaster disrupt
		remove_short_term_gold = gold
		set_variable = { name = dap_gold_reserve value = 3 }
		create_character = { age = 30 gender = male faith = root.faith culture = root.culture employer = root save_scope_as = dap_t_plotter }
		scope:dap_t_plotter = {
			start_scheme = { type = murder target_character = root }
			random_scheme = { expose_scheme = yes }
		}
		dap_run_council_tasks_effect = yes
		if = {
			limit = { cp:councillor_steward ?= { is_performing_council_task = task_collect_taxes } }
			debug_log = "DAPTEST OK steward collecting taxes when broke"
		}
		else = { debug_log = "DAPTEST FAIL steward not collecting taxes when broke" }
		if = {
			limit = { dap_exposed_hostile_scheme_trigger = yes }
			if = {
				limit = { cp:councillor_spymaster ?= { is_performing_council_task = task_disrupt_schemes } }
				debug_log = "DAPTEST OK spymaster disrupting an exposed scheme"
			}
			else = { debug_log = "DAPTEST FAIL spymaster not disrupting an exposed scheme" }
		}
		else = { debug_log = "DAPTEST note could not set up an exposed scheme" }
		scope:dap_t_kid1 = {
			if = {
				limit = { any_relation = { type = guardian } }
				debug_log = "DAPTEST OK guardian assigned"
			}
			else = { debug_log = "DAPTEST FAIL no guardian for a child" }
		}
		scope:dap_t_kid2 = {
			if = {
				limit = { dap_has_education_focus_trigger = yes }
				debug_log = "DAPTEST OK child has an education focus"
			}
			else = { debug_log = "DAPTEST FAIL child has no education focus" }
		}
		if = {
			limit = { exists = cp:councillor_chancellor }
			debug_log = "DAPTEST OK chancellor seat filled"
		}
		else = { debug_log = "DAPTEST FAIL chancellor seat still empty" }
		if = {
			limit = { cp:councillor_court_chaplain ?= { is_performing_council_task = task_conversion } }
			debug_log = "DAPTEST OK chaplain converting"
		}
		else = { debug_log = "DAPTEST FAIL chaplain not converting" }
		if = {
			limit = { scope:dap_t_orthodox.faith = root.faith }
			debug_log = "DAPTEST OK family member converted"
		}
		else = { debug_log = "DAPTEST note family member not converted (may refuse)" }
		if = {
			limit = {
				OR = {
					scope:dap_t_son = { OR = { is_married = yes is_betrothed = yes } }
					scope:dap_t_daughter = { OR = { is_married = yes is_betrothed = yes } }
					scope:dap_t_son = { has_variable = dap_proposal_sent }
					scope:dap_t_daughter = { has_variable = dap_proposal_sent }
				}
			}
			debug_log = "DAPTEST OK marriage arranged or proposed"
		}
		else = { debug_log = "DAPTEST FAIL no marriage for adult children" }
		# The Build button must still be affordable after the broke-steward check
		add_gold = 5000
"""


# Last, once the construction is checked: the player dies; the heir must take over the
# settings (on_player_character_change)
SUITE_SUCCESSION = """
dap_devtest_succession_effect = {
	remove_variable = dap_devtest_ai
	primary_heir ?= { save_scope_as = dap_t_heir }
	if = {
		limit = { exists = scope:dap_t_heir }
		death = natural
		scope:dap_t_heir = { trigger_event = dap_devtest.30 }
	}
	else = {
		debug_log = "DAPTEST note no heir, succession not tested"
		debug_log = "DAPTEST done"
	}
}
"""

SUITE_AFTER_DEATH = """
dap_devtest.30 = {
	hidden = yes
	immediate = {
		if = {
			limit = { is_ai = no }
			debug_log = "DAPTEST OK heir is now the player"
		}
		else = { debug_log = "DAPTEST note heir is not the player" }
		if = {
			limit = {
				has_variable = dap_initialized
				var:dap_faith_enabled ?= 1
				var:dap_court_council ?= 2
			}
			debug_log = "DAPTEST OK heir kept the Dynasty Autopilot settings"
		}
		else = { debug_log = "DAPTEST FAIL heir lost the Dynasty Autopilot settings" }
		debug_log = "DAPTEST done"
	}
}
"""


def events_file(mode, years, flags):
    effects = count_effect(flags)
    out = ["namespace = dap_devtest\n"]
    out.append("""
dap_devtest.1 = {
	hidden = yes
	immediate = {
		debug_log_date = yes
		set_variable = dap_devtest_ai
		dap_init_player_effect = yes
""" + apply_test_values())
    out.append("\t\tdap_devtest_zero_counts_effect = yes\n")
    if mode == "build":
        out.append("\t\tadd_gold = 5000\n\t\tdebug_log = \"DAPTEST build test set up\"\n")
    elif mode == "suite":
        out.append(SUITE_SETUP)
        out.append("\t\tclear_variable_list = dap_log\n\t\tdap_run_all_effect = yes\n\t\tdap_devtest_count_effect = yes\n")
        out.append(SUITE_CHECKS)
        out.append("\t\tdap_devtest_report_effect = yes\n")
    else:
        out.append(f"\t\tset_variable = {{ name = dap_devtest_pulses_left value = {years * 4} }}\n")
        out.append("\t\tdebug_log = \"DAPTEST soak started\"\n")
    out.append("\t}\n}\n")
    out.append("""
dap_devtest.10 = {
	hidden = yes
	immediate = {
		if = {
			limit = { NOT = { has_variable = dap_devtest_pulses_left } }
			set_variable = { name = dap_devtest_pulses_left value = 0 }
		}
		if = {
			limit = { NOT = { has_variable = dap_initialized } }
			debug_log = "DAPTEST BUG automated ruler has no Dynasty Autopilot settings"
			debug_log_scopes = yes
		}
		clear_variable_list = dap_log
		dap_run_all_effect = yes
		dap_devtest_count_effect = yes
		change_variable = { name = dap_devtest_pulses_left add = -1 }
		if = {
			limit = { var:dap_devtest_pulses_left = 0 }
			debug_log_date = yes
			dap_devtest_report_effect = yes
			debug_log = "DAPTEST done"
		}
		else_if = {
			limit = { NOT = { has_variable = dap_devtest_year_mark } }
			set_variable = { name = dap_devtest_year_mark value = 1 days = 360 }
			debug_log_date = yes
			debug_log = "DAPTEST year passed"
		}
	}
}
""")
    if mode == "suite":
        out.append(SUITE_AFTER_DEATH)
    # Runs from on_death itself: events cannot fire for a dead character
    follow = ["""
# this = the automated ruler, dying; the harness keeps automating their heir
dap_devtest_follow_heir_effect = {
	debug_log_date = yes
	primary_heir ?= {
		set_variable = dap_devtest_ai
		set_variable = { name = dap_devtest_pulses_left value = root.var:dap_devtest_pulses_left }
		# Copy the counts so the final report covers the whole run
"""]
    for flag in flags:
        follow.append(f"\t\tset_variable = {{ name = dap_cnt_{flag} value = root.var:dap_cnt_{flag} }}\n")
    follow.append("\t\tdap_init_player_effect = yes\n" + apply_test_values() + """	}
	debug_log = "DAPTEST succession"
}
""")
    if mode == "build":
        effects += BUILD_PICK
    elif mode == "suite":
        effects += SUITE_SUCCESSION
    return "".join(out), effects + "".join(follow)


AUTORUN_GUI = """\
widget = {
	name = "dap_devtest_autorun"
	size = { 1 1 }
	alwaystransparent = yes

	# Switch to observer mode once, a few seconds after the map is up
	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = observe
			trigger_on_create = yes
			delay = 3
			on_finish = "[ExecuteConsoleCommand('observe')]"
		}
	}

	# Whenever the game stands paused, unpause it and set top speed
	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = unpause
			trigger_on_create = yes
			trigger_when = "[IsGamePaused]"
			delay = 1
			on_finish = "[OnPause]"
			next = speed
		}
		state = {
			name = speed
			on_finish = "[SetGameSpeed('(int32)4')]"
		}
	}
}
"""


# A widget asks for a construction a few seconds after the map is up, as a button
# in the mod's window would, then checks it once the holding view pressed Build.
BUILD_GUI = """\
widget = {
	name = "dap_devtest_autorun"
	size = { 1 1 }
	alwaystransparent = yes

	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = request
			trigger_on_create = yes
			delay = 5
			on_finish = "[GetScriptedGui( 'dap_devtest_build_request' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
			next = give_up
		}
		state = {
			name = give_up
			delay = 30
			on_finish = "[GetScriptedGui( 'dap_devtest_build_timeout' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		}
	}

	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = check
			trigger_when = "[GetPlayer.MakeScope.Var( 'dap_build_last_province' ).IsSet]"
			delay = 1
			on_finish = "[GetScriptedGui( 'dap_devtest_build_check' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		}
	}
}
"""

BUILD_SGUIS = """\
dap_devtest_build_request = {
	scope = character
	effect = {
		dap_devtest_pick_camps_effect = yes
		if = {
			limit = { has_variable = dap_build_building }
			var:dap_build_province = { save_scope_as = holding }
			debug_log = "DAPTEST asked for a construction"
			debug_log_scopes = yes
		}
		else = {
			debug_log = "DAPTEST FAIL no holding with a free slot for the prototype"
			debug_log = "DAPTEST done"
		}
	}
}

dap_devtest_build_check = {
	scope = character
	effect = {
		var:dap_build_last_province = { save_scope_as = holding }
		save_scope_value_as = { name = paid value = var:dap_build_last_paid }
		save_scope_value_as = { name = base_cost value = cheap_building_tier_1_cost }
		debug_log = "DAPTEST holding view pressed Build"
		debug_log_scopes = yes
		if = {
			limit = { scope:holding = { has_ongoing_construction = yes } }
			debug_log = "DAPTEST OK construction under way in the picked holding"
		}
		else = { debug_log = "DAPTEST FAIL no construction under way in the picked holding" }
		if = {
			limit = { var:dap_build_last_paid > 0 }
			debug_log = "DAPTEST OK gold was paid for it"
		}
		else = { debug_log = "DAPTEST FAIL no gold was paid" }
		# Norway in 1066 has no building discounts, so the real price is the base price
		if = {
			limit = { var:dap_build_last_paid = cheap_building_tier_1_cost }
			debug_log = "DAPTEST OK paid the price once, not once per press"
		}
		else = { debug_log = "DAPTEST FAIL paid something other than the price" }
		debug_log = "DAPTEST done"
	}
}

dap_devtest_build_timeout = {
	scope = character
	effect = {
		if = {
			limit = { NOT = { has_variable = dap_build_last_province } }
			debug_log = "DAPTEST FAIL the holding view never pressed Build"
			debug_log = "DAPTEST done"
		}
	}
}
"""


# A fixed pick with a known price (military camps cost cheap_building_tier_1_cost in
# Norway in 1066): a holding of the player's own with a free slot
BUILD_PICK = """
dap_devtest_pick_camps_effect = {
	ordered_directly_owned_province = {
		limit = {
			has_free_building_slot = yes
			has_ongoing_construction = no
			NOT = { has_building_or_higher = military_camps_01 }
			building_requirement_castle_city_church = { LEVEL = 01 }
		}
		order_by = combined_building_level
		save_scope_as = dap_build_province
	}
	if = {
		limit = { exists = scope:dap_build_province }
		save_scope_value_as = { name = dap_build_building value = flag:military_camps_01 }
		dap_build_request_effect = yes
	}
}
"""

# The suite's seasonal run asked for a construction; once the holding view pressed
# Build (or it never did), check it, then go on to the succession test.
SUITE_GUI = """\
widget = {
	name = "dap_devtest_autorun"
	size = { 1 1 }
	alwaystransparent = yes

	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = give_up
			trigger_on_create = yes
			delay = 60
			on_finish = "[GetScriptedGui( 'dap_devtest_suite_build_timeout' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		}
	}

	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = check
			trigger_when = "[GetPlayer.MakeScope.Var( 'dap_build_last_province' ).IsSet]"
			delay = 1
			on_finish = "[GetScriptedGui( 'dap_devtest_suite_build_check' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		}
	}
}
"""

SUITE_SGUIS = """\
dap_devtest_suite_build_check = {
	scope = character
	effect = {
		set_global_variable = { name = dap_devtest_build_checked value = yes }
		var:dap_build_last_province = { save_scope_as = holding }
		debug_log = "DAPTEST holding view pressed Build"
		debug_log_scopes = yes
		if = {
			limit = {
				var:dap_build_last_province = capital_province
				capital_province = { has_ongoing_construction = yes }
			}
			debug_log = "DAPTEST OK a development building is under construction in the capital"
		}
		else = { debug_log = "DAPTEST FAIL no construction under way in the capital" }
		if = {
			limit = {
				is_target_in_variable_list = { name = dap_log target = root }
				var:dap_log_action ?= flag:dap_log_built
				has_variable = dap_log_building
				var:dap_log_province ?= capital_province
			}
			debug_log = "DAPTEST OK the log names the building and the holding"
		}
		else = { debug_log = "DAPTEST FAIL the log does not name the building and the holding" }
		dap_devtest_succession_effect = yes
	}
}

dap_devtest_suite_build_timeout = {
	scope = character
	effect = {
		if = {
			limit = { NOT = { exists = global_var:dap_devtest_build_checked } }
			set_global_variable = { name = dap_devtest_build_checked value = yes }
			debug_log = "DAPTEST FAIL the holding view never pressed Build"
			dap_devtest_succession_effect = yes
		}
	}
}
"""


def write(rel, text):
    path = os.path.join(MOD, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write(text)


def cleanup():
    for rel in FILES.values():
        path = os.path.join(MOD, rel)
        if os.path.exists(path):
            os.remove(path)
    # The effects file lives next to the mod's own scripted effects
    path = os.path.join(MOD, "common", "scripted_effects", "zz_devtest_effects.txt")
    if os.path.exists(path):
        os.remove(path)


def ck3_running():
    return subprocess.run(["pgrep", "-x", "ck3"], capture_output=True).returncode == 0


def main():
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["suite", "soak", "build"])
    parser.add_argument("--years", type=int, default=30, help="soak length in game years")
    parser.add_argument("--play", default="k_norway", help="title whose ruler you start as")
    parser.add_argument("--seed", type=int, default=1066, help="random seed, for repeatable runs")
    parser.add_argument("--timeout", type=int, default=0, help="seconds before giving up (default: by mode)")
    args = parser.parse_args()

    if ck3_running():
        sys.exit("CK3 is already running; close it first (it may be someone's game).")

    flags = log_flags()
    events, effects = events_file(args.mode, args.years, flags)
    timeout = args.timeout or (420 + args.years * 75 if args.mode == "soak" else 420)
    debug_log = os.path.join(LOGS, "debug.log")
    error_log = os.path.join(LOGS, "error.log")

    try:
        write(FILES["on_action"], ON_ACTIONS)
        write(FILES["events"], events)
        write("common/scripted_effects/zz_devtest_effects.txt", effects)
        if args.mode == "soak":
            write(FILES["gui"], AUTORUN_GUI)
            write(FILES["widgets"], "gui/zz_devtest_autorun.gui = dap_devtest_autorun\n")
        elif args.mode == "build":
            write(FILES["gui"], BUILD_GUI)
            write(FILES["sguis"], BUILD_SGUIS)
            write(FILES["widgets"], "gui/zz_devtest_autorun.gui = dap_devtest_autorun\n")
        else:
            write(FILES["gui"], SUITE_GUI)
            write(FILES["sguis"], SUITE_SGUIS)
            write(FILES["widgets"], "gui/zz_devtest_autorun.gui = dap_devtest_autorun\n")

        started = time.time()
        subprocess.Popen(
            [CK3, "-gdpr-compliant", "-debug_mode", "-skip", f"-play={args.play}", f"-random_seed={args.seed}"],
            cwd=BINARIES, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
        )
        print(f"Started CK3 ({args.mode}, {args.play}); waiting up to {timeout} s")
        outcome = "timeout"
        years_seen = 0
        while time.time() - started < timeout:
            time.sleep(3)
            if not ck3_running():
                outcome = "crashed or closed"
                break
            if os.path.exists(debug_log) and os.path.getmtime(debug_log) >= started:
                with open(debug_log, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                years = text.count("DAPTEST year passed")
                if years != years_seen:
                    years_seen = years
                    print(f"  {years} game year(s) passed ({int(time.time() - started)} s)")
                if "DAPTEST done" in text:
                    outcome = "done"
                    break
    finally:
        if ck3_running():
            subprocess.run(["pkill", "-9", "-x", "ck3"])
        cleanup()

    print(f"\nOutcome: {outcome}\n")
    if os.path.exists(debug_log):
        with open(debug_log, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        for i, line in enumerate(lines):
            if "DAPTEST" in line and "year passed" not in line:
                msg = line.split("): ", 1)[-1]
                # A count is printed by debug_log_scopes a few lines further down
                if msg.startswith("DAPTEST fired"):
                    for extra in lines[i + 1:i + 30]:
                        m = re.match(r"\s*count: (\S+)", extra)
                        if m:
                            msg += f" x{m.group(1)}"
                            break
                print(msg)
    if os.path.exists(error_log):
        with open(error_log, encoding="utf-8", errors="replace") as f:
            errors = [l for l in f.read().splitlines()
                      if "dap_" in l or "dynasty_autopilot" in l or "zz_devtest" in l]
        print(f"\nMod errors in error.log: {len(errors)}")
        for line in errors[:40]:
            print("  " + line[:220])
    sys.exit(0 if outcome == "done" else 1)


if __name__ == "__main__":
    main()
