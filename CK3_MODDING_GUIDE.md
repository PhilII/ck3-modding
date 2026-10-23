# Crusader Kings III – Modding-guide (instruksjonsfil)

> Skrevet 2026-10-22 for **CK3 1.20.1.2 "Crozier"** (installert lokalt via Steam på macOS).
> Formål: oppslagsverk for å lage CK3-mods i dette prosjektet. Les denne før du skriver mod-kode.

---

## 0. Viktigste regler (TL;DR)

1. **Vanilla-filene er fasiten.** Wiki-sidene er ofte skrevet for 1.1–1.9 og kan være utdaterte. Kopier alltid mønster fra spillets egne filer og les `_*.info`-filene i samme mappe.
2. **Aldri rediger spillfilene direkte.** All endring skjer i en mod-mappe som speiler spillets mappestruktur.
3. **Ikke overskriv hele vanilla-filer** hvis du bare trenger å endre ett objekt. Bruk *single object override* (egen fil med annet navn, se §5).
4. **Alt skal være UTF-8 *med BOM*** (særlig `.yml`-lokalisering – uten BOM leses den ikke).
5. **Prefiks alle egne ID-er** med et mod-prefiks (f.eks. `pl_`), så de ikke kolliderer med vanilla eller andre mods.
6. **Test med `-debug_mode -develop`** og les `error.log` etter hver endring. Kjør `ck3-tiger` før publisering.

---

## 1. Viktige stier på denne maskinen (macOS)

| Hva | Sti |
|---|---|
| Spillfiler (vanilla, kun lesing!) | `~/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game/` |
| Launcher-innstillinger | `…/Crusader Kings III/launcher/launcher-settings.json` |
| Brukermappe | `~/Documents/Paradox Interactive/Crusader Kings III/` |
| Mod-mappe (lokale mods) | `~/Documents/Paradox Interactive/Crusader Kings III/mod/` (finnes ikke ennå – opprettes av launcheren eller manuelt) |
| Logger | `~/Documents/Paradox Interactive/Crusader Kings III/logs/` |
| Steam Workshop-mods (abonnert) | `~/Library/Application Support/Steam/steamapps/workshop/content/1158310/` |
| Lagrede spill | `~/Documents/Paradox Interactive/Crusader Kings III/save games/` |

Windows: `Documents\Paradox Interactive\Crusader Kings III\mod`. Linux: `~/.local/share/Paradox Interactive/Crusader Kings III/mod`.
Steam app-ID for CK3: **1158310**.

Praktisk shell-variabel:
```bash
G="$HOME/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game"
```

---

## 2. Anatomien til en mod

En lokal mod består av **to ting** i `mod/`-mappen:

```
mod/
├── my_mod.mod            ← "pekerfil" (launcheren leser denne)
└── my_mod/               ← selve moden, speiler game/-strukturen
    ├── descriptor.mod
    ├── thumbnail.png
    ├── common/
    │   ├── decisions/
    │   ├── scripted_effects/
    │   ├── scripted_triggers/
    │   ├── script_values/
    │   ├── on_action/
    │   ├── traits/
    │   └── defines/
    ├── events/
    ├── localization/
    │   └── english/
    ├── gfx/
    ├── gui/
    └── history/
```

### 2.1 `descriptor.mod` (inne i mod-mappen)
```
version="0.1.0"
tags={
	"Gameplay"
	"Decisions"
}
name="My Mod"
supported_version="1.20.*"
```

### 2.2 `my_mod.mod` (ved siden av mappen) – samme innhold + `path`
```
version="0.1.0"
tags={
	"Gameplay"
	"Decisions"
}
name="My Mod"
supported_version="1.20.*"
path="mod/my_mod"
```

| Felt | Betydning |
|---|---|
| `name` | Navn i launcheren (påkrevd, min. 3 tegn) |
| `version` | Modens egen versjon (påkrevd) |
| `supported_version` | Spillversjon, `*` som wildcard, f.eks. `"1.20.*"`. Launcheren varsler hvis utdatert |
| `tags` | Kategorier (minst én kreves ved opplasting). Eksempler: `"Gameplay"`, `"Decisions"`, `"Events"`, `"Culture"`, `"Religion"`, `"Fixes"`, `"Graphics"`, `"Map"`, `"Total Conversion"`, `"Utilities"` |
| `path` | Kun i den ytre `.mod`-filen. Relativ til brukermappen eller absolutt |
| `remote_file_id` | Workshop-ID, settes automatisk ved opplasting – ikke rør |
| `picture` | Forhåndsvisningsbilde (Steam bruker uansett `thumbnail.png`) |
| `replace_path` | `replace_path="history/characters"` – hindrer vanilla i å laste noe fra den mappen (brukes i total conversions) |

> CK3 bruker fortsatt `descriptor.mod` (ikke `.metadata/metadata.json` som Victoria 3/EU5).

**thumbnail.png**: kvadratisk, hold under ~1 MB (opplasting feiler ellers). 512×512 er trygt.

### 2.3 Opprette mod via launcher (anbefalt første gang)
Launcher → **Mods / Mod library** → **Upload Mod** → **Create a Mod** → fyll inn navn, versjon, mappe, tags. Launcheren lager begge filene. Legg så moden i en **playset** og start.

---

## 3. Arbeidsflyt og testing

### 3.1 Startparametre
Sett i Steam → CK3 → Egenskaper → Startalternativer:
```
-debug_mode -develop
```
| Flagg | Effekt |
|---|---|
| `-debug_mode` | Konsoll (`` ` `` / `§`), debug-tooltips (viser ID-er), Ctrl-klikk = bytt karakter, Alt-klikk = drep, Ctrl+Alt-klikk = Explorer |
| `-develop` | Hot-reload av de fleste filer ved lagring |
| `-skip` | Hopp over hovedmeny, rett inn i 1066-lobby |
| `-play=k_norway` | Start direkte som innehaver av en tittel |
| `-bookmark=bm_867_carolingians` | Velg bookmark (ny i 1.20) |
| `-continuelastsave` / `-loadsave=<navn>` | Last siste/navngitt save |
| `-random_seed=42` | Fast RNG (kun med debug_mode) |
| `-suppress_error_log` | Ikke åpne error-log automatisk |
| `-mapeditor` | Kartredigerer |

Full liste: `$G/_commandline_options.info`. Launcheren har også "Open game in Debug Mode".

### 3.2 Logger (i `logs/`)
- **`error.log`** – det viktigste. Vanilla har *noen* feil allerede: kjør først uten mods for å kjenne baseline, og søk deretter etter ditt mod-prefiks/filnavn.
- **`database_conflicts.log`** – viser hvilke objekter/filer som overstyrer hverandre. Ha mod-navnet i filnavnene så du finner dine.
- **`debug.log`** – kan vises i spillet med konsollkommandoen `log_viewer`.
- **`game.log`** – utdata fra `debug_log`-effekten.

### 3.3 Konsollkommandoer (med `-debug_mode`)
| Kommando | Bruk |
|---|---|
| `script_docs` | Dumper **alle effects, triggers, scopes, on_actions, modifiers, event targets** for *din* versjon til `logs/` (script_documentation). **Kjør denne etter hver patch – dette er den autoritative listen.** |
| `dump_data_types` | Dumper data-typer/funksjoner brukbare i lokalisering og GUI (`[GetName]` osv.) |
| `data_types_explorer` | Utforsk data-typer interaktivt |
| `event <id>` / `event <id> <char_id>` | Fyr av et event |
| `effect add_gold = 100` | Kjør vilkårlig effekt på spilleren |
| `trigger is_adult = yes` | Test en trigger |
| `explorer` | Åpner Explorer for å inspisere objekter |
| `release_mode` | Viser feilteller ("errorhoof") |
| `reload <fil/mappe>` | Manuell reload |
| `help` | Liste over kommandoer |

### 3.4 Debug-effekter i script
```
debug_log = "pl: mitt event kjørte"
debug_log_scopes = yes      # logger alle scopes
error_log = "pl: dette skal ikke skje"
```

### 3.5 Anbefalt loop
1. Finn tilsvarende vanilla-fil i `$G` (bruk `grep -r`).
2. Les `_*.info`-filen i samme mappe.
3. Skriv i mod-mappen med eget prefiks.
4. Lagre → hot-reload (`-develop`) → test i spillet via konsoll (`event pl_events.1`).
5. Sjekk `error.log` og `database_conflicts.log`.
6. Kjør `ck3-tiger` på `descriptor.mod`.

---

## 4. Script-syntaks (Jomini/Clausewitz)

### 4.1 Grunnleggende
```
key = value
key = { ... }              # blokk
is_ai = yes                # boolsk
gold >= 100                # sammenligning: = != < <= > >=
capital_county ?= title:c_roma   # ?= sjekker at scopet finnes først
@my_constant = 365         # konstant (filnivå, øverst i filen)
# kommentar
```

### 4.2 Triggers vs. effects
- **Trigger** = sjekk (true/false). Brukes i `trigger`, `limit`, `is_shown`, `is_valid`, `potential`, `any_*`.
- **Effect** = gjør noe. Brukes i `immediate`, `option`, `effect`, `after`, `every_*`/`random_*`/`ordered_*`.

### 4.3 Scopes
```
root                      # scopet scriptet startet i
this                      # nåværende scope
prev                      # forrige scope (ett nivå)
scope:my_target           # lagret scope
liege.primary_title.holder   # kjeding
character:163110  title:k_norway  culture:norse  faith:norse_pagan  dynasty:...
```
Lagre scope:
```
random_courtier = { save_scope_as = lover }
scope:lover = { add_opinion = { target = root modifier = friendliness_opinion opinion = 20 } }
save_temporary_scope_as = tmp   # bare i nåværende kjøring
```

### 4.4 Iteratorer
| Prefiks | Kontekst |
|---|---|
| `any_X` | trigger (kan ha `count >= 2`, `percent`) |
| `every_X` | effect – alle |
| `random_X` | effect – én tilfeldig (støtter `weight`) |
| `ordered_X` | effect – sortert (`order_by`, `position`, `max`) |

```
every_vassal = {
	limit = { opinion = { target = root value < 0 } }
	add_opinion = { target = root modifier = respect_opinion opinion = 10 }
}
```
Lister: `add_to_list = x`, `every_in_list = { list = x }`, `is_in_list = x`.

### 4.5 Logikk og flyt
```
if = { limit = { ... } ... }
else_if = { limit = { ... } ... }
else = { ... }

trigger_if = { limit = { is_ai = yes } gold > 50 }   # kun i trigger-blokker
trigger_else = { always = yes }

AND = {} OR = {} NOT = {} NOR = {} NAND = {}
switch = { trigger = has_culture  culture:norse = { ... } fallback = { ... } }
random_list = { 50 = { ... } 50 = { modifier = { add = 20 is_ai = yes } ... } }
```

### 4.6 Script values og matematikk
`common/script_values/pl_values.txt`:
```
pl_bribe_cost = {
	value = 50
	add = { value = primary_title.tier multiply = 25 }
	if = { limit = { has_trait = greedy } multiply = 1.5 }
	min = 25
	max = 500
}
```
Brukes: `remove_short_term_gold = pl_bribe_cost`. Inline: `value = { add = age divide = 2 }`.

### 4.7 Variabler og flagg
```
set_variable = { name = pl_counter value = 1 }
change_variable = { name = pl_counter add = 1 }
has_variable = pl_counter
var:pl_counter >= 3
remove_variable = pl_counter
set_variable = { name = pl_flag value = flag:tower }   # flagg-verdi
set_global_variable = { name = pl_mod_loaded value = yes }   # global_var:
set_local_variable = ...   # local_var:, kun i nåværende kjøring
set_variable = { name = x value = 1 days = 365 }      # utløper
```
Character flags: `add_character_flag = { flag = pl_x days = 30 }`, `has_character_flag = pl_x`.

### 4.8 Scripted effects / triggers (gjenbruk + parametre)
`common/scripted_effects/pl_effects.txt`:
```
pl_give_gold_effect = {
	add_gold = $AMOUNT$
}
```
Kall: `pl_give_gold_effect = { AMOUNT = 100 }` (uten parametre: `pl_x_effect = yes`).
`common/scripted_triggers/pl_triggers.txt`:
```
pl_is_valid_target_trigger = { is_adult = yes is_imprisoned = no }
```
Kall: `pl_is_valid_target_trigger = yes`.

### 4.9 Tooltips
```
custom_tooltip = pl_some_loc_key          # vis tekst
custom_description = { text = key subject = scope:x ... }  # tekst + skjul effekter
show_as_tooltip = { ... }                 # vis effekter uten å utføre dem
hidden_effect = { ... }                   # utfør uten å vise
```

### 4.10 Vekter (AI og random)
```
ai_will_do = {
	base = 10
	modifier = { add = 20 has_trait = ambitious }
	modifier = { factor = 0 is_at_war = yes }
}
```

---

## 5. Overstyring, lasting og kompatibilitet

### 5.1 To måter å overstyre vanilla
**A. Full fil-overstyring** – samme sti *og* samme filnavn som vanilla → hele vanilla-filen erstattes. Bruk bare når nødvendig (høy konfliktrisiko, går i stykker ved patcher).

**B. Single object override** – samme mappe, *annet* filnavn, definer objektet med samme nøkkel.
- De fleste databaser bruker **LIOS** (Last In Only Served): filen som sorteres **sist** (ASCII-rekkefølge) vinner → navngi f.eks. `zz_pl_traits.txt` eller `01_pl_defines.txt`.
- **GUI-typer/templates** bruker **FIOS** (First In Only Served) → navngi f.eks. `00_pl_types.gui`.
- Bare toppnivå-objekter kan overstyres. Man kan ikke *fjerne* objekter, bare erstatte.
- **Events** (fra 1.20): definer samme event-ID i egen fil med `id_override_priority = 1` (høyest vinner, vanilla = 0).
- **Historiske karakterer** (fra 1.20): `history_override_priority = 1`.

### 5.2 Spesialtilfeller
- **Defines**: lag `common/defines/pl_defines.txt` og skriv bare verdiene du endrer:
  ```
  NCharacter = {
  	MAX_STRESS = 400
  }
  ```
- **on_actions**: `events`, `random_events`, `on_actions`-lister **legges til** (append) vanilla. Men `trigger` og `effect` **overskriver** vanilla → ikke legg `effect` i vanilla on_actions. Lag heller egen on_action og hekt den på:
  ```
  # common/on_action/pl_on_actions.txt
  on_game_start = {
  	on_actions = { pl_on_game_start }
  }
  pl_on_game_start = {
  	effect = { set_global_variable = { name = pl_mod_loaded value = yes } }
  	events = { pl_events.1 }
  }
  ```
- **Lokalisering**: for å endre enkeltnøkler fra vanilla, legg filen i `localization/english/replace/` (eller `localization/replace/english/`).
- **GUI-vinduer**: må overstyres som hele fila (f.eks. `gui/window_character.gui`) → stor konfliktfare.
- **Bygninger**: `common/holdings/holdings.txt` krever ofte full overstyring.

### 5.3 Lastrekkefølge
Mods lastes topp → bunn i playset; den nederste vinner ved identiske filer. Kompatibilitetspatcher legges under modene de slår sammen. Lastrekkefølge betyr bare noe når mods rører samme filer/objekter.

### 5.4 Kompatibilitetsteknikker
- **Lite fotavtrykk**: rør så få vanilla-filer/objekter som mulig.
- **Delte variabler**: én mod setter `var:x`, en annen sjekker `has_variable`.
- **Mod-deteksjon via scripted trigger**: din mod definerer `othermod_is_loaded = { always = no }` i en tidlig fil (`aaa_…`); den andre moden definerer `always = yes` i en sen fil.
- **Global variabel** satt i `on_game_start` (virker bare hvis moden var aktiv ved spillstart).
- **Hook-effekter**: kall en scripted effect som andre mods kan overstyre i en senere fil.

---

## 6. Events

Fil: `events/pl_events.txt` (UTF-8 BOM). Dokumentasjon: `$G/events/_events.info`.

```
namespace = pl_events

pl_events.1 = {
	type = character_event            # character_event / letter_event / court_event / activity_event
	title = pl_events.1.t
	desc = pl_events.1.desc
	theme = intrigue                  # bestemmer bakgrunn/musikk
	left_portrait = {
		character = root
		animation = happiness
	}
	right_portrait = scope:target

	trigger = {                       # må være sann for at eventet fyrer
		is_adult = yes
	}

	immediate = {                     # kjøres før vinduet vises; sett opp scopes her
		random_courtier = {
			limit = { is_adult = yes }
			save_scope_as = target
		}
	}

	option = {
		name = pl_events.1.a
		add_gold = 50
		ai_chance = { base = 50 }
	}
	option = {
		name = pl_events.1.b
		trigger = { has_trait = brave }   # kun synlig hvis sann
		add_prestige = 100
		stress_impact = { craven = medium_stress_impact_gain }
		ai_chance = {
			base = 50
			modifier = { factor = 2 has_trait = ambitious }
		}
	}

	after = { }                       # kjøres etter valgt option
	cooldown = { years = 5 }
}
```

Nøkkelpunkter:
- Events fyrer **aldri av seg selv** – de må kalles fra on_action, decision, interaction, story cycle eller `trigger_event`.
- Hold event-nummer ≤ 9999.
- `hidden = yes` → ingen popup (rene logikk-events). Events uten karakter-root må normalt være `hidden` eller `major`; bruk `scope = none` for global scope.
- `trigger` kan ikke se scopes som lages i `immediate`.
- Fyre fra script: `trigger_event = { id = pl_events.2 days = { 7 14 } }` eller `trigger_event = { on_action = pl_my_on_action }`.
- Fyr på andre: `scope:target = { trigger_event = pl_events.3 }`.
- Dynamisk tekst:
  ```
  desc = {
  	first_valid = {
  		triggered_desc = { trigger = { has_trait = brave } desc = pl_events.1.desc_brave }
  		desc = pl_events.1.desc_default      # fallback uten trigger sist
  	}
  }
  ```
  Også `random_valid = { ... }`. Flere `desc` i rad slås sammen med mellomrom.
- Bakgrunn: `override_background = { reference = throne_room }`.
- Animasjoner: `idle`, `happiness`, `sadness`, `anger`, `fear`, `scheme`, `stress`, `worry`, `shock`, `personality_bold`, `throne_room_bow_1` osv. (se `animations.txt`).

### 6.1 Tilfeldige/periodiske events via on_action
```
# common/on_action/pl_on_actions.txt
yearly_playable_pulse = {
	on_actions = { pl_yearly_pulse }
}
pl_yearly_pulse = {
	random_events = {
		chance_to_happen = 25
		100 = pl_events.1
		100 = 0            # sjanse for ingen event
	}
}
```
Pulser: `yearly_global_pulse`, `yearly_playable_pulse`, `quarterly_playable_pulse`, `three_year_playable_pulse`, `five_year_playable_pulse`, `random_yearly_playable_pulse`, `random_yearly_everyone_pulse`. Andre nyttige: `on_game_start`, `on_game_start_after_lobby`, `on_birth_child`, `on_death`, `on_marriage`, `on_title_gain`, `on_war_started`, `on_trait_gained` (ny 1.20). Full liste: `script_docs` → on_actions-logg, og `$G/common/on_action/`.

---

## 7. Decisions

Fil: `common/decisions/pl_decisions.txt`. Dokumentasjon: `$G/common/decisions/_decisions.info`.

```
pl_host_feast_decision = {
	picture = {
		reference = "gfx/interface/illustrations/decisions/decision_personal_religious.dds"
	}
	decision_group_type = major       # fra common/decision_group_types
	sort_order = 50
	desc = pl_host_feast_decision_desc
	selection_tooltip = pl_host_feast_decision_tooltip
	confirm_text = pl_host_feast_decision_confirm

	cooldown = { years = 2 }

	is_shown = {                      # synlig i listen?
		is_landed = yes
	}
	is_valid_showing_failures_only = {   # vises bare når den feiler
		is_at_war = no
	}
	is_valid = {
		gold >= 100
	}
	cost = {
		gold = 100
	}
	effect = {
		add_prestige = 150
		trigger_event = pl_events.1
	}

	ai_check_interval = 60            # måneder; 0 = AI sjekker aldri. Påkrevd (med mindre ai_goal = yes)
	ai_potential = { is_at_war = no }
	ai_will_do = { base = 25 }
}
```
Lokaliseringsnøkler: `<id>` (tittel – **ingen** `_title`-suffiks), `<id>_desc`, `<id>_tooltip`, `<id>_confirm`.

---

## 8. Lokalisering

Fil: `localization/english/pl_mod_l_english.yml` – **UTF-8 med BOM**, filnavn må slutte på `_l_english.yml`, første linje `l_english:`.

```
l_english:
 pl_events.1.t: "En uventet gjest"
 pl_events.1.desc: "[target.GetTitledFirstName] ankommer hoffet ditt med en gave."
 pl_events.1.a: "Ta imot gaven"
 pl_events.1.b: "Send dem bort, #N stolt#!"
 pl_host_feast_decision: "Hold et gjestebud"
 pl_host_feast_decision_desc: "Inviter vasallene dine til fest. Koster @gold_icon! 100."
 pl_host_feast_decision_tooltip: "Øker [prestige|E]"
 pl_host_feast_decision_confirm: "Til bords!"
```

- Format: ` key: "tekst"` (ledende mellomrom, `:0` er valgfritt/foreldet – vanilla bruker det fortsatt).
- Språk: `english, french, german, spanish, russian, korean, simp_chinese, polish, japanese`. **Kopier engelsk-filen til alle språkmapper** (med riktig filnavn og header), ellers ser andre språk rå nøkler.
- Stavemåte: `localization` (amerikansk), lille `l` i `l_english`.
- Formatering: `#P grønn#!`, `#N rød#!`, `#bold …#!`, `#italic …#!`, `#E konsept#!`, `#high;bold …#!`. Husk alltid `#!`.
- Linjeskift `\n`, sitattegn `\"`.
- Referer annen nøkkel: `$other_key$`.
- Data-funksjoner: `[ROOT.Char.GetName]`, `[scope:target.GetFirstName]`, `[GetTitleByKey('k_norway').GetName]`, `[ROOT.Char.GetHerHis]`, `|U` (stor forbokstav), `|L`.
- Spillkonsepter (klikkbare lenker): `[prestige|E]`, `[faith|El]` (liten forbokstav).
- Ikoner: `@gold_icon!`, `@prestige_icon!`, `@piety_icon!` (definert i `gui/texticons.gui`).
- Overstyre vanilla-tekst: legg i `localization/english/replace/`.

---

## 9. Andre vanlige innholdstyper (kort)

Les alltid `_*.info` i mappen og kopier et vanilla-eksempel.

| Type | Mappe | Notater |
|---|---|---|
| Traits | `common/traits/` | Se `_traits.info`. Trenger loc `trait_<id>`, `trait_<id>_desc` og ikon `gfx/interface/icons/traits/<id>.dds` |
| Modifiers (statiske) | `common/modifiers/` | `add_character_modifier = { modifier = pl_x years = 5 }`. Loc: `<id>`, `<id>_desc`. Gyldige modifier-nøkler: `script_docs` (modifiers-logg) |
| Opinion modifiers | `common/opinion_modifiers/` | |
| Character interactions | `common/character_interactions/` | Se `_character_interactions.info` |
| Casus belli | `common/casus_belli_types/` | |
| Schemes | `common/schemes/` | |
| Story cycles | `common/story_cycles/` | Langvarige "historier" med egne effekter over tid |
| Kulturer / traditions | `common/culture/` | |
| Religioner / faiths | `common/religion/` | **Omstrukturert i 1.20**: egne databaser for faith, rite, tenet, doctrine. Gamle religion-mods er ødelagt |
| Governments | `common/governments/` | 1.20: admin/teokrati bruker nå "mechanics" og flagg |
| Laws | `common/laws/`, `common/law_groups/` | 1.20: nye lover krever ikke å endre gruppe-fila |
| Buildings | `common/buildings/` | |
| Titler | `common/landed_titles/` | |
| Historie | `history/characters/`, `history/titles/`, `history/provinces/` | |
| Game rules | `common/game_rules/` | Gjør mod-funksjoner valgbare: `has_game_rule = pl_rule_on` |
| GUI | `gui/` | Data-binding; se `$G/data_binding/`. Scripted GUIs i `common/scripted_guis/` |
| Grafikk | `gfx/` | Bilder som `.dds` (BC3/DXT5 med mipmaps for ikoner); bruk GIMP/Paint.NET med DDS-plugin |
| Kart | `map_data/` | Stort tema; se wiki "Map modding" |

---

## 10. Endringer i 1.20 "Crozier" (sept./okt. 2026) som påvirker modding

- Religion-databasen er splittet: `FaithType` egen database; nye `rite_types`, `rite_names`, `rite_icons`, `tenet_types`; doktriner lagrer egen gruppe; nye effekter `change_doctrine`, `set_faith_name`, `set_rite_name`; on_actions `on_rite_change`, `on_rite_created`, `on_county_rite_change`.
- Administrativ-script skrevet om til eksplisitte mechanics/flagg (mods kan lage egne admin-regjeringer).
- **Omdøpt**: `has_commander_trait_trigger` → `has_trait_with_flag`; `lease_out_to` → `lease_out_to_holy_order`.
- Nytt: `id_override_priority` (events), `history_override_priority` (karakterer), `-bookmark=`-flagg, `on_trait_gained`/`on_trait_lost`, `on_character_created`, `on_player_character_change`, `?=` i script values, `clear_father`/`clear_mother`, scripted rules `can_create_title`/`can_destroy_title`, puppet-database, `inheritance_blocker` på traits.
- Lover og lovgrupper splittet; `change_authority_effect` håndterer alle autoritetssteg.

**Konsekvens:** eldre guider/mods (≤1.19) for religion, regjeringer og lover kan være ødelagt. Verifiser alltid mot `script_docs` og vanilla-filene for 1.20.

---

## 11. Verktøy

| Verktøy | Bruk |
|---|---|
| **VS Code** + **Paradox Modding Toolkit** / **Paradox Highlight** | Syntaksfarging, autofullføring |
| **ck3-tiger** (github.com/amtep/ck3-tiger) | Validator: syntaksfeil, manglende lokalisering, feil scopes. `ck3-tiger "path/to/my_mod.mod"`. Flagg: `--unused`, `--json`, `-c`. Kan bygges på Mac med `cargo run --release -p ck3-tiger -- <MODPATH>` |
| ck3-tiger for VS Code | Viser tiger-funn i Problems-panelet |
| IntelliJ + Paradox Language Support | Alternativ IDE |
| CWTools | Utdatert for CK3 – unngå |
| Irony Mod Manager | Konfliktanalyse mellom mods |
| WinMerge / `diff` | Sammenligne med vanilla etter patcher |
| GIMP / Paint.NET (DDS) | Grafikk |
| jesec/ck3-mod-base (GitHub) | Git-versjonert vanilla-filer – nyttig for å diffe patcher |

---

## 12. Publisering

1. Fjern debug-ting, sett riktig `version` og `supported_version`.
2. Legg ved `thumbnail.png` (< 1 MB, kvadratisk).
3. Launcher → Mods → **Upload Mod** → velg moden → velg **Steam Workshop** og/eller **Paradox Mods** → last opp. `remote_file_id` skrives inn automatisk.
4. Ikke ha både lokal og Workshop-kopi aktiv samtidig – det kan hindre lasting.
5. Mods som endrer spillregler endrer **checksum** → Ironman/achievements deaktiveres. Rene grafikk-/lokaliseringsmods påvirker vanligvis ikke checksum.

---

## 13. Feilsøking

| Problem | Løsning |
|---|---|
| Tekst vises som rå nøkkel | Manglende BOM, feil filnavn (`_l_english.yml`), feil header, eller feil mappe |
| Event fyrer ikke | Ikke kalt fra noe; `trigger` usann; feil namespace; ID > 9999; sjekk `error.log` |
| Mod vises ikke i launcher | Sjekk at `.mod` og mappe har riktig `path`; "Reload mods" i launcheren |
| Mod sluttet å virke | Fjern fra playset, legg til igjen. Siste utvei: slett `mods_registry.json` og `launcher-v2.sqlite` i brukermappen (tar backup først) |
| Uventet overstyring | `database_conflicts.log`; sjekk filnavn-sortering (LIOS/FIOS) |
| Endring tar ikke effekt | Noen filer krever omstart (ikke alt hot-reloader); hot-reload ignorerer `id_override_priority` |
| Unknown effect/trigger | Navnet er endret i ny patch – sjekk `script_docs`-dump |

Søk i vanilla etter eksempler:
```bash
grep -rn "has_trait_with_flag" "$G/common" | head
```

---

## 14. Minimal "hello world"-mod (sjekkliste)

1. `mod/pl_hello.mod` og `mod/pl_hello/descriptor.mod` (se §2).
2. `mod/pl_hello/events/pl_hello_events.txt` – ett event `pl_hello.1` med én option.
3. `mod/pl_hello/common/on_action/pl_hello_on_actions.txt` – hekt `pl_hello.1` på `on_game_start_after_lobby` via egen on_action.
4. `mod/pl_hello/localization/english/pl_hello_l_english.yml` (UTF-8 BOM).
5. Aktiver i playset, start med `-debug_mode -develop`, test med konsoll `event pl_hello.1`, sjekk `error.log`.

Lag BOM-fil fra shell:
```bash
printf '\xEF\xBB\xBF' > file.yml && cat body.yml >> file.yml
```
Sjekk BOM: `head -c 3 file.yml | xxd` → `efbb bf`.

---

## 14b. Lærdommer fra Dynasty Autopilot (verifisert i 1.20.1.2)

- **Spillets egen effekt-/trigger-dokumentasjon ligger i binærfilen.** Uten å starte spillet: `strings -n 8 ".../binaries/ck3.app/Contents/MacOS/ck3" > ck3strings.txt`, så `grep -n "^navn$"` og les linjene rundt. Iteratorer står oppført under listenavnet (f.eks. `living_character`, `courtier`), ikke som `every_…`.
- **`run_interaction`**: `interaction`, `actor`, `recipient`, valgfritt `secondary_actor`/`secondary_recipient`, `redirect = yes/no`, og minst én av `execute_threshold`/`send_threshold = accept/maybe/decline`. Kan **ikke** velge send-options (f.eks. matrilinealt).
- **`is_character_interaction_potentially_accepted`** (trigger): `recipient`, `interaction`, `secondary_actor`, `secondary_recipient`, `required_response = yes/maybe`, `ai_accept = <min>`. Sjekker om AI-en vil si ja før du sender.
- Ved arrange marriage er `recipient` kandidatens `matchmaker`, `secondary_recipient` er kandidaten.
- Ekteskapseffekter: `marry`, `marry_matrilineal`, `create_betrothal`, `create_betrothal_matrilineal`.
- Trait-nivå: `has_trait_rank = { trait = intellect_good rank >= 2 }` (grupper: `intellect_good`, `beauty_good`, `physique_good`). Telle-triggere: `num_of_good_genetic_traits`, `num_of_bad_genetic_traits`.
- `trigger_else_if` **krever** en `trigger_else` etter seg (ellers feil ved lasting).
- Interaksjoner: `ai_potential` uten `ai_frequency` gir feil – utelat AI-blokker for rene spillerinteraksjoner.
- Decisions krever loc-nøkkel `<id>_confirm` (ellers feil i error.log).
- **Tooltips evaluerer effekter.** En option som kjører et tungt søk må pakkes i `hidden_effect = { ... }`, ellers kjøres søket (og eventuelle feil) hver gang man holder musepekeren over. Bruk `save_temporary_scope_as` i stedet for `prev` i triggere – `prev` kan være null i tooltip-kontekst.
- `.mod`-filen kan peke til en **absolutt sti** (`path="/Users/.../mods/x"`), så mod-koden kan ligge i prosjektmappen. Verifisert: `debug.log` viser `Mounted Data: <sti>`.
- `-skip -play=k_norway` starter rett i et spill – rask måte å teste lasting på.
- **Ikke start spillet på nytt uten å spørre** hvis en CK3-prosess allerede kjører – brukeren kan være midt i en test. `open ck3.app` på en kjørende instans bare fokuserer den (laster ikke på nytt).

### GUI (verifisert i 1.20.1.2)
- **Eget vindu uten å overstyre vanilla:** `gui/scripted_widgets/<navn>.txt` med linjen `gui/min_fil.gui = mitt_vindu`. Vinduet lages når kartet lastes.
- **Åpne/lukke fra script:** `visible = "[GetPlayer.MakeScope.Var('min_var').IsSet]"` på vinduet; en decision setter variabelen, en scripted GUI (`common/scripted_guis/`) fjerner den.
- **Knapp → script:** `onclick = "[GetScriptedGui( 'navn' ).Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).AddScope( 'x', Character.MakeScope ).AddScope( 'f', MakeScopeFlag( 'min_flagg' ) ).End )]"`; i SGUI-en: `saved_scopes = { x f }`. `onrightclick` fungerer også.
- **Vise verdier som tekst:** customizable localization (`common/customizable_localization/`, `type = character`, `text = { trigger = {...} localization_key = ... }`, `fallback = yes`) og `[Character.Custom( 'nøkkel' )]` i GUI.
- **Lister:** `datamodel = "[GetPlayer.MakeScope.GetList('liste')]"` (variabelliste via `add_to_variable_list`), og i `item`: `datacontext = "[Scope.GetCharacter]"`.
- **Faner:** `GetVariableSystem.Set/HasValue( 'tab', 'x' )`, `button_tab` med `down = ...`.
- **Fallgruve:** `using = Background_Area` direkte på en `hbox`/`vbox` gir «Error setting properties». Bruk `background = { using = Background_Area }`.
- Nyttige vanilla-typer: `header_pattern` (blockoverride `header_text`, `button_close`), `button_standard`, `button_tab`, `scrollbox` (blockoverride `scrollbox_content`, `scrollbox_empty`), `portrait_head_small`, `text_single`, `text_multi`; maler `Window_Background`, `Window_Decoration`, `Window_Margins`, `Font_Size_Medium`.
- **Validator-støy:** flagg som bare sendes inn fra GUI (`flag:x`) gir «Flag is used but never set», og variabler som bare leses i GUI gir «set but never used». Løs det med en effekt som faktisk brukes og som setter/leser dem.
- **`on_game_start_after_lobby` har ingen root.** Bruk `every_player = { trigger_event = ... }` i stedet for å kalle effekter som bruker `root`.
- **`change_variable` på en variabel som ikke finnes** gir «Variable not of the 'value' scope type». Sett den til 0 først.
- Validatoren teller ikke bruk i localization/GUI: variabler og flagg som bare vises i GUI trenger en ekte lesing i script (f.eks. som vakt i et `if`).
- **Ekteskap/konkubiner (1.20):** `allowed_more_spouses`, `allowed_concubines`, `allowed_more_concubines` er kode-triggere som tar hensyn til tro og kultur. Konkubiner kan bare tas fra egne hoffolk og fanger (`make_concubine_interaction`, `can_become_concubine_of_character_trigger = { CHARACTER = x }`). Sunni-islam i 1.20 har *ikke* konkubiner; f.eks. `faith:zun_pagan` har det.
- Rangér etter poeng **blant dem som faktisk sier ja** (`is_character_interaction_potentially_accepted` i `limit`), ellers takker de mektigste nei og ingen match blir gjort. Et fullt søk tok ~1 sekund i 1066-starten.
- **Verger:** `educate_child_interaction` (actor = barnets eier, recipient = vergens hoff-eier, secondary_actor = verge, secondary_recipient = barn) har `auto_accept = yes`. En verge kan ha maks 2 myndlinger (`num_of_relation_ward < 2`). Fjerne: `barn = { remove_relation_guardian = verge }`.
- **Utdanning:** `set_focus = education_martial` osv.; talent via `has_<skill>_education_affinity_childhood_trait_trigger`. Barndomstrait-valg ligger i vanilla-events (`child_personality_events.txt`) og kan ikke automatiseres uten å overskrive dem.
- **Hoff:** `start_scheme = { type = sway target_character = x }` (sjekk `can_start_scheme` først), `assign_councillor_type = { type = councillor_steward target = x remove_existing_councillor = yes }` med `can_be_steward_trigger = { COURT_OWNER = root }`, `appoint_court_position = { recipient = x court_position = y }` med `can_be_employed_as = y` og rangering `aptitude:y`, `release_from_prison = yes`, `time_in_prison = { years >= 5 }`, landgave via `create_title_and_vassal_change` + `change_title_holder` + `resolve_title_and_vassal_change`.
- **Titler:** `can_be_granted_titles_by = { RULER = root }` (mottaker), `is_leased_out`, `is_noble_family_title`, `is_nomad_title`, `has_clerical_region`, `title_held_years`, `development_level`. Opprettelse: kostnad `create_duchy_title_value` / `create_kingdom_title_value`, `create_title_and_vassal_change = { type = created }`. Kontrakter: `vassal_contract_set_obligation_level = { type = feudal_government_taxes level = feudal_tax_high }` – kun føydale; klan/stamme har faste kontrakter.
- **Leiesoldater (1.20):** `maa_regiments_count < maa_regiments_max_count`, `create_maa_regiment = { type = armored_footmen check_can_recruit = yes }`, kostnad via `heavy_infantry_recruitment_cost` osv. (`has_personal_maa_space` finnes IKKE som trigger). Bygging kan ikke startes fra script – bare `add_building` (umiddelbart, gratis).
- **Tilbaketaking:** `has_revoke_title_reason = vasall`, men `run_interaction` kan ikke sende med tittel, så revoke kan ikke kjøres riktig fra script.
- **«Suggest only»-mønster:** sett `set_local_variable = { name = dap_dry value = ... }` før hver modul og sjekk `exists = local_var:dap_dry` ved hver handling. Lokale variabler forsvinner ved neste event, så bekreftelses-events kjører alltid «på ekte».
- **Lister lever gjennom hele effekt-kjøringen.** To kjøringer i samme event deler `add_to_list`-lister – bare en test-artefakt, men verdt å vite.
- **macOS spør om tilgang til Dokumenter** når CK3 startes med `open`, fordi `ck3.app` er ad-hoc-signert og macOS ikke husker valget. Løsning: start binærfilen direkte fra terminalen (`nohup ".../ck3.app/Contents/MacOS/ck3" -debug_mode ... & disown`), så arver spillet terminalens tilgang og spør ikke. Lukk testspill med `pkill -9 -x ck3` (ikke `osascript quit`, som åpner spillets Exit-dialog).
- **Langtidstest:** `-nographics` krasjer på Mac (spillets portrettkode under lasting). Bruk vanlig spill, en midlertidig GUI-knapp med `onclick = "[ExecuteConsoleCommand('observe')]"`, og la pulsen gjelde en markert AI-hersker (`OR = { is_ai = no has_variable = dap_devtest_ai }`). Da går tiden uten event-pauser, ca. 5 spillår per minutt. Husk: AI-en stokker om rådet sitt selv, så «samme rådsmedlem igjen og igjen» er en test-artefakt. `debug_log_date = yes` gir spilldato i loggen.
- **Endre aldri .gui-filer mens brukeren spiller med `-develop`** – hot reload av GUI krasjet spillet én gang.
- **Teste uten klikk:** en midlertidig `on_game_start_after_lobby` → `every_player = { trigger_event = <skjult event> }` som kjører effekten, med `debug_log` (havner i `debug.log`). Slett testfilene etterpå.
- **Starte testspill uten å stjele fokus:** `open -g ck3.app --args ...`. Ta aldri skjermbilde av hele skjermen – brukeren kan holde på med noe annet.

---

## 15. Kilder

- CK3 Wiki – Modding: https://ck3.paradoxwikis.com/Modding
- CK3 Wiki – Patch 1.20: https://ck3.paradoxwikis.com/Patch_1.20
- Wiki-speil på GitHub (sider for Mod structure, Event modding, Scripting, Localization, Decisions, Mod compatibility, Modding tools): https://github.com/jesec/ck3-modding-wiki
- ck3-tiger: https://github.com/amtep/ck3-tiger
- Metadata-format på tvers av Paradox-spill: https://github.com/happy-dwarf-team/paradox-workshop-publish/issues/4
- awesome-ck3: https://github.com/ck3-mods/awesome-ck3/wiki
- **Lokale spillfiler (1.20.1.2)**: `$G/_commandline_options.info`, `$G/events/_events.info`, `$G/common/on_action/_on_actions.info`, `$G/common/traits/_traits.info`, `$G/history/_characters.info`, `$G/common/decisions/00_lifestyle_decisions.txt`, `$G/common/defines/00_defines.txt`, `$G/localization/english/*.yml`

Usikkert / ikke verifisert: eksakt thumbnail-krav fra Paradox, og eksakt filnavn på `script_docs`-utdata – kjør kommandoen og se i `logs/`.
