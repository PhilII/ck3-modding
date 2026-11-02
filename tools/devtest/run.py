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
import build_buildings  # noqa: E402

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
    "triggers": "common/scripted_triggers/zz_devtest_triggers.txt",
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
    "dap_grant_duchies": 1, "dap_grant_keep_core": 1, "dap_create_titles": 2, "dap_revoke_suggest": 1,
    "dap_court_positions": 2, "dap_maa_type": 1, "dap_build_reminder": 1, "dap_court_prisoners": 2,
    "dap_task_chancellor": 2, "dap_task_steward": 2, "dap_task_marshal": 1, "dap_task_spymaster": 1,
    "dap_faith_enabled": 1, "dap_faith_chaplain": 2, "dap_faith_task": 1, "dap_faith_family": 1,
    "dap_faith_spouses": 1, "dap_faith_vassals": 2, "dap_hof_gold": 1, "dap_excomm_alert": 1,
    "dap_faith_warn_heir": 1, "dap_faith_warn_vassals": 1, "dap_faith_report": 1,
    "dap_build_enabled": 1, "dap_build_suggest": 0, "dap_build_income": 2, "dap_build_development": 2,
    "dap_build_per_season": 3,
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
		# Buildings. Innovations so that upgrades can be built (castle_02, level 2 farms)
		culture = {
			add_innovation = innovation_windmills
			add_innovation = innovation_battlements
		}
		if = {
			limit = { culture = { NOT = { has_innovation = innovation_crop_rotation } } }
			culture = { add_innovation = innovation_crop_rotation }
		}
		# County stacking: a county of your own besides the capital's, with a vassal's holding
		# (granted here, or built and granted, if there is none), gets the most development
		# buildings: every other county of yours has none. Its duchy is the capital's if it can
		# be, as "keep core" stops the land module granting it away before the builder runs
		ordered_held_title = {
			limit = {
				tier = tier_county
				NOT = { this = root.capital_county }
				any_county_province = { dap_devtest_baron_holding_candidate_trigger = yes }
			}
			order_by = {
				value = 0
				if = {
					limit = { de_jure_liege ?= root.capital_county.de_jure_liege }
					add = 100
				}
				if = {
					limit = { any_county_province = { has_holding = yes province_owner = { is_vassal_of = root } } }
					add = 10
				}
			}
			save_scope_as = dap_t_stack
		}
		scope:dap_t_stack ?= {
			ordered_county_province = {
				limit = { dap_devtest_baron_holding_candidate_trigger = yes }
				order_by = {
					value = 0
					# A vassal's holding, else an empty barony, so the player's own castles stay
					# for the other scenarios
					if = {
						limit = { has_holding = yes province_owner = { is_vassal_of = root } }
						add = 2
					}
					if = {
						limit = { has_holding = no }
						add = 1
					}
				}
				save_scope_as = dap_t_baron_holding
			}
			scope:dap_t_baron_holding = {
				if = {
					limit = { has_holding = no }
					set_holding_type = castle_holding
				}
				if = {
					limit = { NOT = { province_owner ?= { is_vassal_of = root } } }
					create_character = { age = 30 gender = male faith = root.faith culture = root.culture employer = root save_scope_as = dap_t_baron }
					create_title_and_vassal_change = { type = granted save_scope_as = change add_claim_on_loss = no }
					barony = {
						change_title_holder = { holder = scope:dap_t_baron change = scope:change }
					}
					resolve_title_and_vassal_change = scope:change
				}
			}
		}
		capital_county = { save_scope_as = dap_capital_county }
		every_held_title = {
			limit = {
				tier = tier_county
				NOT = { this = scope:dap_t_stack }
			}
			every_county_province = { dap_devtest_remove_development_buildings_effect = yes }
		}
		# The development building goes in the baron's holding, which keeps a free slot; the
		# county's own castle is left for the main building scenario below
		scope:dap_t_baron_holding ?= {
			if = {
				limit = { has_free_building_slot = no }
				add_province_modifier = extra_building_slot
			}
			province_owner = { save_scope_as = holder }
			county = { save_scope_as = county }
			dap_devtest_add_development_effect = yes
			if = {
				limit = { has_free_building_slot = no }
				add_province_modifier = extra_building_slot
			}
		}
		if = {
			limit = {
				exists = scope:dap_t_baron_holding
				scope:dap_t_baron_holding.province_owner = { is_vassal_of = root }
				scope:dap_t_stack = {
					dap_county_development_buildings_value >= 1
				}
			}
			set_variable = { name = dap_t_baron_holding value = scope:dap_t_baron_holding }
			debug_log = "DAPTEST stacking county set up (most development buildings, a vassal baron's castle):"
			debug_log_scopes = yes
		}
		else = { debug_log = "DAPTEST FAIL could not set up a stacking county with a vassal baron's holding" }
		# A free slot in the capital's holding for a new building
		capital_province = {
			if = {
				limit = { has_free_building_slot = no }
				add_province_modifier = extra_building_slot
			}
		}
		# Another castle with no buildings that serve a focus and every slot full of buildings
		# that serve none: only the main building's upgrade (castle_02) is left there
		ordered_directly_owned_province = {
			limit = {
				NOT = { this = root.capital_province }
				NOT = { scope:dap_t_baron_holding ?= this }
				has_building = castle_01
				has_ongoing_construction = no
				# castle_02 needs the innovation in the holding's own culture
				culture = root.culture
			}
			# The holding with the fewest buildings, so the castle's upgrade has no rivals
			order_by = {
				value = 0
				subtract = num_buildings
				# The capital's duchy first: "keep core" stops the land module granting it away
				# before the builder runs
				if = {
					limit = { county.de_jure_liege ?= root.capital_county.de_jure_liege }
					add = 100
				}
			}
			save_scope_as = dap_t_main_upgrade
			dap_devtest_remove_focus_buildings_effect = yes
			dap_devtest_fill_slots_effect = yes
		}
		# A third holding with a level 1 income building and every other slot full: its upgrade
		# beats anything else there
		ordered_directly_owned_province = {
			limit = {
				NOT = { this = root.capital_province }
				NOT = { this = scope:dap_t_main_upgrade }
				NOT = { scope:dap_t_baron_holding ?= this }
				has_ongoing_construction = no
			}
			order_by = {
				value = 0
				subtract = num_buildings
				# The capital's duchy first: "keep core" stops the land module granting it away
				# before the builder runs
				if = {
					limit = { county.de_jure_liege ?= root.capital_county.de_jure_liege }
					add = 100
				}
			}
			save_scope_as = dap_t_upgrade
			province_owner = { save_scope_as = holder }
			county = { save_scope_as = county }
			dap_devtest_add_upgradable_effect = yes
			dap_devtest_fill_slots_effect = yes
		}
		# Buildings: nothing is asked for with the switch off, or without gold above the reserve
		set_variable = { name = dap_build_enabled value = 0 }
		dap_run_buildings_effect = yes
		dap_devtest_queued_effect = yes
		if = {
			limit = { local_var:dap_t_queued > 0 }
			debug_log = "DAPTEST FAIL a building was asked for with automatic building off"
		}
		else = { debug_log = "DAPTEST OK no building with automatic building off" }
		set_variable = { name = dap_build_enabled value = 1 }
		set_variable = { name = dap_gold_reserve value = 3 }
		remove_short_term_gold = gold
		add_gold = dap_gold_reserve_value
		dap_run_buildings_effect = yes
		dap_devtest_queued_effect = yes
		if = {
			limit = { local_var:dap_t_queued > 0 }
			debug_log = "DAPTEST FAIL a building was asked for without gold above the reserve"
		}
		else = { debug_log = "DAPTEST OK no building without gold above the reserve" }
		# Only 300 gold above the reserve: what is asked for costs no more than that
		add_gold = 300
		dap_run_buildings_effect = yes
		dap_devtest_queued_effect = yes
		if = {
			limit = {
				local_var:dap_t_queued >= 1
				local_var:dap_t_queued_cost <= 300
			}
			debug_log = "DAPTEST OK constructions asked for stay within the gold above the reserve"
		}
		else = {
			save_scope_value_as = { name = queued value = local_var:dap_t_queued }
			save_scope_value_as = { name = cost value = local_var:dap_t_queued_cost }
			debug_log = "DAPTEST FAIL constructions asked for do not fit the gold above the reserve"
			debug_log_scopes = yes
		}
		dap_devtest_cancel_builds_effect = yes
		set_variable = { name = dap_gold_reserve value = 0 }
		add_gold = 5000
		# One construction per season: one is asked for, and a second run asks for nothing more
		set_variable = { name = dap_build_per_season value = 0 }
		dap_run_buildings_effect = yes
		dap_run_buildings_effect = yes
		dap_devtest_queued_effect = yes
		if = {
			limit = { local_var:dap_t_queued = 1 }
			debug_log = "DAPTEST OK one construction with one allowed per season"
		}
		else = {
			save_scope_value_as = { name = queued value = local_var:dap_t_queued }
			debug_log = "DAPTEST FAIL not one construction with one allowed per season"
			debug_log_scopes = yes
		}
		dap_devtest_cancel_builds_effect = yes
		# Suggest only: nothing asked for, a suggestion in the log. Income alone and
		# development alone pick buildings serving that focus, and not the same ones
		set_variable = { name = dap_build_per_season value = 3 }
		set_variable = { name = dap_build_suggest value = 1 }
		set_local_variable = { name = dap_dry value = 1 }
		set_variable = { name = dap_build_development value = 0 }
		dap_run_buildings_effect = yes
		dap_devtest_queued_effect = yes
		if = {
			limit = {
				local_var:dap_t_queued = 0
				NOT = { any_in_list = { variable = dap_build_queue } }
				var:dap_log_action ?= flag:dap_log_build_suggested
			}
			debug_log = "DAPTEST OK Suggest only asks for nothing and logs a suggestion"
		}
		else = { debug_log = "DAPTEST FAIL Suggest only asked for a construction or logged no suggestion" }
		every_directly_owned_province = {
			limit = { has_variable = dap_bc_building }
			set_variable = { name = dap_t_income_pick value = var:dap_bc_building }
		}
		if = {
			limit = {
				any_directly_owned_province = { has_variable = dap_t_income_pick }
				NOT = { any_directly_owned_province = { has_variable = dap_bc_building dap_devtest_income_pick_trigger = no } }
			}
			debug_log = "DAPTEST OK income alone picks income buildings"
		}
		else = { debug_log = "DAPTEST FAIL income alone picks a building that gives no income" }
		# In a vassal's holding, holding and holder bonuses count only as the tax they pay you
		scope:dap_t_baron_holding ?= {
			province_owner = { save_scope_value_as = { name = tax_share value = dap_vassal_tax_share_value } }
			if = {
				limit = { has_variable = dap_bc_value }
				dap_devtest_income_parts_effect = yes
				save_scope_value_as = { name = value value = var:dap_bc_value }
				save_scope_value_as = { name = holding_part value = local_var:dap_t_holding }
				save_scope_value_as = { name = county_part value = local_var:dap_t_county }
				# At most the share of the holding's income, plus the county's tax if this is the
				# stacking county; a holding valued in full would exceed it
				if = {
					limit = {
						scope:tax_share < 0.95
						var:dap_bc_value <= {
							value = local_var:dap_t_holding
							multiply = scope:tax_share
							add = local_var:dap_t_county
							multiply = 1.01
						}
					}
					debug_log = "DAPTEST OK income in a vassal's holding is valued as your tax share, below its value in your own"
				}
				else_if = {
					limit = { scope:tax_share >= 0.95 }
					debug_log = "DAPTEST note the vassal pays nearly all their income in tax, so the share cannot be told apart"
				}
				else = { debug_log = "DAPTEST FAIL income in a vassal's holding is valued above your tax share" }
				save_scope_as = holding
				debug_log_scopes = yes
			}
			else_if = {
				limit = { scope:tax_share = 0 }
				debug_log = "DAPTEST OK no income pick in a vassal's holding that pays you no tax"
			}
			else = { debug_log = "DAPTEST note no income pick in the vassal baron's holding" }
		}
		set_variable = { name = dap_build_income value = 0 }
		set_variable = { name = dap_build_development value = 2 }
		dap_run_buildings_effect = yes
		if = {
			limit = {
				any_in_list = { variable = dap_build_holdings has_variable = dap_bc_building }
				NOT = { any_in_list = { variable = dap_build_holdings has_variable = dap_bc_building dap_devtest_development_pick_trigger = no } }
			}
			debug_log = "DAPTEST OK development alone picks development buildings"
		}
		else = { debug_log = "DAPTEST FAIL development alone picks a building that gives no development" }
		if = {
			limit = {
				exists = scope:dap_t_stack
				any_in_list = { variable = dap_build_holdings has_variable = dap_bc_building county = scope:dap_t_stack }
				NOT = {
					any_in_list = {
						variable = dap_build_holdings
						has_variable = dap_bc_building
						NOT = { county = scope:dap_t_stack }
					}
				}
			}
			debug_log = "DAPTEST OK development alone builds only in the stacking county, the one with the most development buildings"
		}
		else = {
			debug_log = "DAPTEST FAIL development alone does not build only in the county with the most development buildings"
			every_in_list = {
				variable = dap_build_holdings
				limit = { has_variable = dap_bc_building }
				save_scope_as = holding
				debug_log = "DAPTEST   picked in:"
				debug_log_scopes = yes
			}
		}
		scope:dap_t_baron_holding ?= {
			if = {
				limit = { dap_devtest_development_pick_trigger = yes }
				debug_log = "DAPTEST OK a vassal baron's holding in the stacking county gets a development building"
			}
			else = {
				debug_log = "DAPTEST FAIL a vassal baron's holding in the stacking county gets no development building"
				dap_devtest_explain_effect = yes
			}
		}
		if = {
			limit = {
				any_directly_owned_province = {
					has_variable = dap_t_income_pick
					NOT = { var:dap_bc_building ?= var:dap_t_income_pick }
				}
			}
			debug_log = "DAPTEST OK income and development weights pick different buildings"
		}
		else = { debug_log = "DAPTEST FAIL income and development weights pick the same buildings everywhere" }
		every_directly_owned_province = {
			limit = { has_variable = dap_t_income_pick }
			save_scope_as = holding
			debug_log = "DAPTEST   holding; its income pick, then its development pick:"
			debug_log_scopes = yes
			dap_devtest_name_income_pick_effect = yes
			dap_devtest_name_pick_effect = yes
			remove_variable = dap_t_income_pick
		}
		remove_local_variable = dap_dry
		set_variable = { name = dap_build_suggest value = 0 }
		set_variable = { name = dap_build_income value = 2 }
		set_variable = { name = dap_build_per_season value = 3 }
		# Gold for every construction the seasonal run asks for, the vassal's holding included
		add_gold = 10000
		clear_variable_list = dap_log
"""

SUITE_CHECKS = """\
		# The seasonal run asked for constructions in the capital (a new building), and upgrades
		# in the full holdings; the holding view presses them after this tick
		# (dap_devtest_suite_build_check). A second run with nothing changed asks for nothing new.
		dap_devtest_queued_effect = yes
		set_local_variable = { name = dap_t_first_run value = local_var:dap_t_queued }
		dap_run_buildings_effect = yes
		dap_devtest_queued_effect = yes
		if = {
			limit = { local_var:dap_t_queued = local_var:dap_t_first_run }
			debug_log = "DAPTEST OK a second run with nothing changed asks for nothing new"
		}
		else = { debug_log = "DAPTEST FAIL a second run with nothing changed asked for more" }
		capital_province = {
			if = {
				limit = { dap_devtest_waiting_trigger = yes var:dap_bc_from ?= flag:none }
				debug_log = "DAPTEST OK the seasonal run asked for a new building in the capital"
			}
			else = {
				debug_log = "DAPTEST FAIL the seasonal run asked for no new building in the capital"
				dap_devtest_explain_effect = yes
			}
		}
		scope:dap_t_main_upgrade ?= {
			if = {
				limit = { dap_devtest_waiting_trigger = yes var:dap_bc_from ?= flag:castle_01 }
				debug_log = "DAPTEST OK the seasonal run asked for the main building's upgrade in a full holding"
			}
			else = {
				debug_log = "DAPTEST FAIL the seasonal run asked for no main building upgrade in a full holding"
				dap_devtest_explain_effect = yes
			}
		}
		scope:dap_t_upgrade ?= {
			if = {
				limit = {
					dap_devtest_waiting_trigger = yes
					exists = var:dap_bc_from
					NOT = { var:dap_bc_from = flag:none }
					NOT = { var:dap_bc_from = flag:castle_01 }
				}
				debug_log = "DAPTEST OK the seasonal run asked for a building's upgrade where it beats any new building"
			}
			else = {
				debug_log = "DAPTEST FAIL the seasonal run asked for no building upgrade where it beats any new building"
				dap_devtest_explain_effect = yes
			}
		}
		scope:dap_t_baron_holding ?= {
			if = {
				limit = { dap_devtest_waiting_trigger = yes }
				debug_log = "DAPTEST OK the seasonal run asked for a construction in a vassal baron's holding in the stacking county"
			}
			else = {
				debug_log = "DAPTEST FAIL the seasonal run asked for no construction in the vassal baron's holding"
				dap_devtest_explain_effect = yes
			}
		}
		# Remember what was asked for, to check it once pressed
		every_in_list = {
			variable = dap_build_holdings
			limit = { dap_devtest_waiting_trigger = yes }
			root = { add_to_variable_list = { name = dap_t_asked target = prev } }
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
		set_variable = { name = dap_build_building value = flag:military_camps_01 days = 1 }
		set_variable = { name = dap_build_from value = flag:none days = 1 }
		dap_build_open_effect = yes
	}
}
"""

# The suite's seasonal run asked for constructions; once the holding view pressed
# every one (or gave up), check them, then go on to the succession test.
SUITE_GUI = """\
widget = {
	name = "dap_devtest_autorun"
	size = { 1 1 }
	alwaystransparent = yes
	visible = "[GetPlayer.IsValid]"

	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = give_up
			trigger_on_create = yes
			delay = 120
			on_finish = "[GetScriptedGui( 'dap_devtest_suite_build_timeout' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		}
	}

	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = watch_requests
			trigger_when = "[GetPlayer.MakeScope.Var( 'dap_build_building' ).IsSet]"
			on_finish = "[GetScriptedGui( 'dap_devtest_log_request' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		}
	}

	widget = {
		size = { 1 1 }
		alwaystransparent = yes
		state = {
			name = check
			trigger_when = "[GetScriptedGui( 'dap_devtest_suite_queue_done' ).IsShown( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
			delay = 2
			on_finish = "[GetScriptedGui( 'dap_devtest_suite_build_check' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
		}
	}
}
"""

SUITE_SGUIS = """\
dap_devtest_suite_queue_done = {
	scope = character
	is_shown = {
		exists = global_var:dap_devtest_requested
		NOT = { has_variable = dap_build_building }
		NOT = { any_in_list = { variable = dap_build_queue } }
	}
}

dap_devtest_log_request = {
	scope = character
	effect = {
		set_global_variable = { name = dap_devtest_requested value = yes }
		var:dap_build_province ?= { save_scope_as = holding }
		debug_log = "DAPTEST   the driver asked the holding view for:"
		debug_log_scopes = yes
		dap_devtest_name_request_effect = yes
	}
}

dap_devtest_suite_build_check = {
	scope = character
	effect = {
		set_global_variable = { name = dap_devtest_build_checked value = yes }
		save_scope_value_as = { name = asked value = { value = 0 every_in_list = { variable = dap_t_asked add = 1 } } }
		debug_log = "DAPTEST holding view pressed Build or Upgrade for every queued construction"
		debug_log_scopes = yes
		if = {
			limit = {
				any_in_list = { variable = dap_t_asked }
				NOT = { any_in_list = { variable = dap_t_asked has_ongoing_construction = no } }
			}
			debug_log = "DAPTEST OK every construction asked for is under way"
		}
		else = {
			debug_log = "DAPTEST FAIL a construction asked for is not under way"
			every_in_list = {
				variable = dap_t_asked
				limit = { has_ongoing_construction = no }
				save_scope_as = holding
				debug_log = "DAPTEST   not under way:"
				debug_log_scopes = yes
			}
		}
		if = {
			limit = { capital_province = { has_ongoing_construction = yes } }
			debug_log = "DAPTEST OK a new building is under construction in the capital"
		}
		else = { debug_log = "DAPTEST FAIL no construction under way in the capital" }
		var:dap_t_baron_holding ?= {
			if = {
				limit = {
					has_ongoing_construction = yes
					dap_devtest_development_pick_trigger = yes
				}
				debug_log = "DAPTEST OK a development building is under construction in a vassal baron's holding"
			}
			else = {
				debug_log = "DAPTEST FAIL no development building under construction in the vassal baron's holding"
				dap_devtest_explain_effect = yes
			}
		}
		if = {
			limit = {
				is_target_in_variable_list = { name = dap_log target = root }
				var:dap_log_action ?= flag:dap_log_built
				has_variable = dap_log_building
				has_variable = dap_log_province
			}
			debug_log = "DAPTEST OK the log names the building and the holding"
		}
		else = { debug_log = "DAPTEST FAIL the log does not name the building and the holding" }
		# Another run, the season's count forgotten and gold to spare: holdings with
		# construction under way are skipped
		remove_variable = dap_build_season_count
		add_gold = 5000
		dap_run_buildings_effect = yes
		if = {
			limit = {
				any_in_list = {
					variable = dap_t_asked
					has_ongoing_construction = yes
					has_variable = dap_build_queued
				}
			}
			debug_log = "DAPTEST FAIL a holding with construction under way was asked for again"
		}
		else = { debug_log = "DAPTEST OK holdings with construction under way are skipped" }
		dap_devtest_cancel_builds_effect = yes
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


def building_helpers():
    """(effects, triggers) for the suite's building scenarios, from the generated building data."""
    found, _ = build_buildings.candidates(build_buildings.DEFAULT_GAME)
    first = [c for c in found if not c["previous"] and not c["main"]]
    fillers = [c["key"] for c in first if not any(v > 0 for v in c["scores"].values())]
    income = lambda c: sum(c["scores"][k] for k in ("INCOME_HOLDING", "INCOME_HOLDER", "INCOME_COUNTY")) > 0
    upgradable = [c["previous"] for c in found
                  if c["previous"] and income(c) and any(f["key"] == c["previous"] for f in first)]
    effects = ["""
# this = province; fills its free slots with buildings that serve no focus
dap_devtest_fill_slots_effect = {
	while = {
		count = 12
		if = {
			limit = { has_free_building_slot = yes }
"""]
    for i, key in enumerate(fillers):
        effects.append(f"\t\t\t{'if' if i == 0 else 'else_if'} = {{\n\t\t\t\tlimit = {{ NOT = {{ has_building_or_higher = {key} }} }}\n"
                       f"\t\t\t\tadd_building = {key}\n\t\t\t}}\n")
    effects.append("\t\t}\n\t}\n}\n")
    effects.append("""
# this = province, scope:holder and scope:county saved; adds a level 1 income building that
# can be built there and has an upgrade
dap_devtest_add_upgradable_effect = {
""")
    for i, key in enumerate(upgradable):
        effects.append(f"\t{'if' if i == 0 else 'else_if'} = {{\n\t\tlimit = {{ dap_can_build_{key}_trigger = yes }}\n"
                       f"\t\tadd_building = {key}\n\t}}\n")
    effects.append("}\n")
    effects.append("""
# this = player; how many constructions are asked for (queued or waiting for the holding
# view) in local_var:dap_t_queued, and their price in local_var:dap_t_queued_cost
dap_devtest_queued_effect = {
	set_local_variable = { name = dap_t_queued value = 0 }
	set_local_variable = { name = dap_t_queued_cost value = 0 }
	every_in_list = {
		variable = dap_build_holdings
		limit = { has_variable = dap_build_queued }
		change_local_variable = { name = dap_t_queued add = 1 }
		change_local_variable = { name = dap_t_queued_cost add = var:dap_bc_cost }
	}
}

# this = player; forgets every construction asked for, and the season's count
dap_devtest_cancel_builds_effect = {
	if = {
		limit = { has_variable = dap_build_building }
		remove_variable = dap_build_province
		remove_variable = dap_build_building
		remove_variable = dap_build_from
		remove_variable = dap_build_gold_before
	}
	every_in_list = {
		variable = dap_build_holdings
		limit = { has_variable = dap_build_queued }
		remove_variable = dap_build_queued
	}
	clear_variable_list = dap_build_queue
	if = {
		limit = { has_variable = dap_build_season_count }
		remove_variable = dap_build_season_count
	}
}

# this = province; why the builder did not ask for what the test expected
dap_devtest_explain_effect = {
	save_scope_as = holding
	debug_log_scopes = yes
	if = {
		limit = { has_free_building_slot = no }
		debug_log = "DAPTEST   no free slot"
	}
	if = {
		limit = { has_ongoing_construction = yes }
		debug_log = "DAPTEST   construction already under way"
	}
	if = {
		limit = { has_variable = dap_bc_building }
		debug_log = "DAPTEST   its pick:"
		dap_devtest_name_pick_effect = yes
	}
	else = { debug_log = "DAPTEST   nothing there serves a focus" }
	if = {
		limit = {
			NOT = { province_owner = root }
			NOT = { province_owner = { is_vassal_of = root } }
		}
		debug_log = "DAPTEST   no longer yours or a vassal's (granted away by the land module?)"
	}
}
""")

    keys = [c["key"] for c in found] + ["none"]

    def chain(var):
        return "".join(f"\t{'if' if i == 0 else 'else_if'} = {{\n\t\tlimit = {{ var:{var} ?= flag:{key} }}\n"
                       f"\t\tdebug_log = \"DAPTEST     {var}: {key}\"\n\t}}\n" for i, key in enumerate(keys))

    effects.append("\n# this = player; logs the building asked for\n"
                   f"dap_devtest_name_request_effect = {{\n{chain('dap_build_building')}{chain('dap_build_from')}}}\n")
    effects.append("\n# this = province; logs its income-only pick\n"
                   f"dap_devtest_name_income_pick_effect = {{\n{chain('dap_t_income_pick')}}}\n")
    effects.append("\n# this = province; removes every building there that serves a focus\n"
                   "dap_devtest_remove_focus_buildings_effect = {\n"
                   + "".join(f"\tif = {{\n\t\tlimit = {{ has_building = {c['key']} }}\n\t\tremove_building = {c['key']}\n\t}}\n"
                             for c in found if not c["main"] and any(v > 0 for v in c["scores"].values()))
                   + "}\n")
    dev_first = [c for c in first if c["scores"]["DEVELOPMENT_COUNTY"] > 0]
    effects.append("\n# this = province; removes every building there whose county-wide bonus serves Development\n"
                   "dap_devtest_remove_development_buildings_effect = {\n"
                   + "".join(f"\tif = {{\n\t\tlimit = {{ has_building = {c['key']} }}\n\t\tremove_building = {c['key']}\n\t}}\n"
                             for c in found if not c["main"] and c["total"]["DEVELOPMENT_COUNTY"] > 0)
                   + "}\n")
    effects.append("\n# this = province, scope:holder and scope:county saved; adds a level 1 development\n"
                   "# building that can be built there\ndap_devtest_add_development_effect = {\n"
                   + "".join(f"\t{'if' if i == 0 else 'else_if'} = {{\n\t\tlimit = {{ dap_can_build_{c['key']}_trigger = yes }}\n"
                             f"\t\tadd_building = {c['key']}\n\t}}\n" for i, c in enumerate(dev_first))
                   + "}\n")
    def part(c, keys):
        return f"{sum(max(c['scores'][k], 0) for k in keys):.3f}"
    effects.append("\n# this = province; its pick's value with Income alone on High, split into the holding's\n"
                   "# and holder's income (local_var:dap_t_holding) and the county's tax (local_var:dap_t_county)\n"
                   "dap_devtest_income_parts_effect = {\n\tset_local_variable = { name = dap_t_holding value = 0 }\n"
                   "\tset_local_variable = { name = dap_t_county value = 0 }\n"
                   + "".join(f"\tif = {{\n\t\tlimit = {{ var:dap_bc_building = flag:{c['key']} }}\n"
                             f"\t\tset_local_variable = {{ name = dap_t_holding value = {{ value = "
                             f"{part(c, ('INCOME_HOLDING', 'INCOME_HOLDER'))} multiply = 3000 divide = {c['cost']} }} }}\n"
                             f"\t\tset_local_variable = {{ name = dap_t_county value = {{ value = "
                             f"{part(c, ('INCOME_COUNTY',))} multiply = 3000 divide = {c['cost']} }} }}\n\t}}\n"
                             for c in found if income(c))
                   + "}\n")
    effects.append("\n# this = province; logs its pick\n"
                   f"dap_devtest_name_pick_effect = {{\n{chain('dap_bc_building')}{chain('dap_bc_from')}}}\n")

    def pick_trigger(name, keys):
        lines = "".join(f"\t\tvar:dap_bc_building = flag:{k}\n" for k in keys)
        return f"{name} = {{\n\texists = var:dap_bc_building\n\tOR = {{\n{lines}\t}}\n}}\n\n"

    triggers = ["# this = province; its pick serves the focus\n",
                pick_trigger("dap_devtest_income_pick_trigger", [c["key"] for c in found if income(c)]),
                pick_trigger("dap_devtest_development_pick_trigger",
                             [c["key"] for c in found if c["scores"]["DEVELOPMENT_COUNTY"] > 0]),
                "# this = province; could be the vassal baron's holding in the stacking county: a\n"
                "# vassal's holding, or one of the player's castles or cities, or an empty barony\n"
                "dap_devtest_baron_holding_candidate_trigger = {\n"
                "\tNOT = { this = county.title_province }\n\thas_ongoing_construction = no\n\tOR = {\n"
                "\t\tAND = {\n\t\t\thas_holding = yes\n\t\t\tprovince_owner = { is_vassal_of = root }\n\t\t}\n"
                "\t\tAND = {\n\t\t\tprovince_owner = root\n\t\t\tOR = {\n\t\t\t\thas_holding_type = castle_holding\n"
                "\t\t\t\thas_holding_type = city_holding\n\t\t\t}\n\t\t}\n\t\thas_holding = no\n\t}\n}\n\n"
                "# this = province; a construction is asked for there\n"
                "dap_devtest_waiting_trigger = {\n\thas_variable = dap_build_queued\n}\n"]
    return "".join(effects), "".join(triggers)


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
            helpers, triggers = building_helpers()
            write("common/scripted_effects/zz_devtest_effects.txt", effects + helpers)
            write(FILES["triggers"], triggers)
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
