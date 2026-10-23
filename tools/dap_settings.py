"""Dynasty Autopilot settings registry.

This is the single place where menu settings and presets are declared. Run
`python3 tools/build_dap.py` after editing it; the script regenerates the
defaults, the copy/clear/step/preset/slot effects, the value texts and the
menu rows.

Each module becomes a tab in the window. Each section becomes a titled block
of rows inside that tab. A section's `holder` says where its variables live:

  "player" - on the player character (module-wide switches)
  "rules"  - on the rule holder: the player for default rules, or a family
             member that has personal rules (copied/cleared together)

Each setting:
  key      - script variable name (keep the dap_ prefix)
  label    - row label
  tooltip  - row tooltip
  default  - starting value (index into values)
  values   - display text for each value 0..n-1; the game logic reads the index

Adding a setting here only adds it to the menu; the module logic
(dap_triggers.txt, dap_values.txt, dap_*_effects.txt) must also read it.
"""

AGE_LIMITS = ["Any", "Not at all", "Up to 5 years", "Up to 10 years", "Up to 15 years"]

MODULES = [
    {
        "id": "general",
        "tab": "General",
        "sections": [
            {
                "id": "main",
                "title": "Dynasty Autopilot",
                "holder": "player",
                "settings": [
                    {
                        "key": "dap_master",
                        "label": "All automation",
                        "tooltip": "Master switch. When off, nothing is automated, whatever each tab says.",
                        "default": 1,
                        "values": ["#N Paused#!", "#P Running#!"],
                    },
                    {
                        "key": "dap_gold_reserve",
                        "label": "Gold reserve",
                        "tooltip": "No automation spends gold (men-at-arms, new titles, court positions) if it would leave you with less than this.",
                        "default": 1,
                        "values": ["No reserve", "Keep 100", "Keep 300", "Keep 1000"],
                    },
                    {
                        "key": "dap_pause",
                        "label": "Pause automation",
                        "tooltip": "Stop all automation while one of these is true.",
                        "default": 0,
                        "values": ["Never", "During wars", "During wars, illness or captivity"],
                    },
                    {
                        "key": "dap_confirm",
                        "label": "Ask before big decisions",
                        "tooltip": "Ask you first before granting a duchy, creating a title or breaking a betrothal.",
                        "default": 1,
                        "values": ["No, just do it", "Yes, ask me"],
                    },
                    {
                        "key": "dap_who",
                        "label": "Family members managed",
                        "tooltip": "Which family members at your court the autopilot looks after, in every tab.",
                        "default": 0,
                        "values": [
                            "My children",
                            "Children and grandchildren",
                            "All dynasty members at court",
                        ],
                    },
                ],
            },
        ],
    },
    {
        "id": "marriage",
        "tab": "Marriage",
        "sections": [
            {
                "id": "general",
                "title": "Automation",
                "holder": "player",
                "settings": [
                    {
                        "key": "dap_enabled",
                        "label": "Marriage automation",
                        "tooltip": "When on, your steward searches for matches once every season.",
                        "default": 0,
                        "values": ["#N Off#!", "#P On#!"],
                    },
                    {
                        "key": "dap_skip_heir",
                        "label": "Primary heir",
                        "tooltip": "How your primary heir's marriage is handled. Ask me first offers the three best candidates, even when everything else is automatic.",
                        "default": 2,
                        "values": ["Automated too", "Handled manually", "Ask me first"],
                    },
                    {
                        "key": "dap_marriage_suggest",
                        "label": "Mode",
                        "tooltip": "Suggest only lists what the autopilot would do in the log (General tab), without doing it. Use it to check the marriage rules before trusting it.",
                        "default": 0,
                        "values": ["Act", "Suggest only"],
                    },
                    {
                        "key": "dap_landed_family",
                        "label": "Landed children",
                        "tooltip": "Children and family members who hold land of their own (such as your primary heir) arrange their own marriages. With this on, the autopilot proposes matches in their name too.",
                        "default": 1,
                        "values": ["Leave to them", "Arrange for them too"],
                    },
                    {
                        "key": "dap_self",
                        "label": "My own marriages",
                        "tooltip": "Also find spouses for you, up to the number your faith and culture allow. Pick which rules apply: your default rules, or a saved rule set.",
                        "default": 0,
                        "values": ["Off", "Use default rules", "Use saved rules 1", "Use saved rules 2", "Use saved rules 3"],
                    },
                    {
                        "key": "dap_concubines",
                        "label": "My concubines",
                        "tooltip": "If your faith allows concubines, fill your free concubine slots from your courtiers and prisoners, using the same rules as your own marriages.",
                        "default": 0,
                        "values": ["Off", "Fill free slots"],
                    },
                    {
                        "key": "dap_extra_spouses",
                        "label": "Extra spouses for family",
                        "tooltip": "Family members who are already married but may take more spouses through their faith or culture get additional matches.",
                        "default": 0,
                        "values": ["Off", "Fill free slots"],
                    },
                    {
                        "key": "dap_invite",
                        "label": "Invite candidates",
                        "tooltip": "When no one suitable is found, invite a fitting wanderer or guest to your court, so they can be married or taken as a concubine next season.",
                        "default": 0,
                        "values": ["Never", "When no one fits"],
                    },
                    {
                        "key": "dap_own_court",
                        "label": "Candidates from my court",
                        "tooltip": "Allow matches with your own courtiers. They always accept.",
                        "default": 0,
                        "values": ["Not allowed", "Allowed"],
                    },
                    {
                        "key": "dap_betrothal_review",
                        "label": "Review betrothals",
                        "tooltip": "Check betrothals the autopilot arranged. It can break them if the partner no longer meets the rules (bad traits, rival or enemy family), and also swap to a much better candidate.",
                        "default": 1,
                        "values": ["Never", "Break if rules are broken", "Also upgrade to much better"],
                    },
                    {
                        "key": "dap_remarry",
                        "label": "Widows and widowers",
                        "tooltip": "Whether family members who were married before are matched again. Only those who can still have children are remarried.",
                        "default": 1,
                        "values": ["Leave them be", "Remarry if fertile"],
                    },
                    {
                        "key": "dap_min_prestige",
                        "label": "Prestige reserve",
                        "tooltip": "The autopilot does not arrange matches while your prestige is below this.",
                        "default": 0,
                        "values": ["No limit", "Keep 100", "Keep 300", "Keep 1000"],
                    },
                    {
                        "key": "dap_report",
                        "label": "Yearly report",
                        "tooltip": "Once a year, sums up how many family members were matched and how many are still waiting. Each family member's latest result is always shown in the list below.",
                        "default": 1,
                        "values": ["Off", "On"],
                    },
                ],
            },
            {
                "id": "requirements",
                "title": "Requirements",
                "holder": "rules",
                "settings": [
                    {
                        "key": "dap_status",
                        "label": "Status",
                        "tooltip": "The lowest social standing a candidate may have.",
                        "default": 1,
                        "values": [
                            "Anyone, lowborn included",
                            "Highborn only",
                            "Rulers and their close family",
                            "Dukes or higher, and their close family",
                        ],
                    },
                    {
                        "key": "dap_same_faith",
                        "label": "Faith",
                        "tooltip": "Whether the candidate must share the family member's faith.",
                        "default": 1,
                        "values": ["Any faith", "Same faith"],
                    },
                    {
                        "key": "dap_same_culture",
                        "label": "Culture",
                        "tooltip": "Whether the candidate must share the family member's culture.",
                        "default": 0,
                        "values": ["Any culture", "Same culture"],
                    },
                    {
                        "key": "dap_realm",
                        "label": "Where from",
                        "tooltip": "Whether candidates must come from inside or outside your realm.",
                        "default": 0,
                        "values": ["Anywhere", "Inside my realm", "Outside my realm"],
                    },
                    {
                        "key": "dap_alliance",
                        "label": "Alliance",
                        "tooltip": "Require a candidate who is a ruler or a ruler's close family, so the marriage can bring an alliance.",
                        "default": 0,
                        "values": ["Not required", "Required"],
                    },
                    {
                        "key": "dap_same_sex",
                        "label": "Same-sex matches",
                        "tooltip": "Allow same-sex marriages where both partners' faith accepts them.",
                        "default": 0,
                        "values": ["Not allowed", "Allowed where accepted"],
                    },
                    {
                        "key": "dap_avoid_rivals",
                        "label": "Rivals and enemies",
                        "tooltip": "Reject candidates whose family is your rival or at war with you.",
                        "default": 1,
                        "values": ["Allowed", "Rejected"],
                    },
                ],
            },
            {
                "id": "age",
                "title": "Age and Fertility",
                "holder": "rules",
                "settings": [
                    {
                        "key": "dap_max_older",
                        "label": "Partner older by",
                        "tooltip": "How much older than the family member a candidate may be.",
                        "default": 3,
                        "values": AGE_LIMITS,
                    },
                    {
                        "key": "dap_max_younger",
                        "label": "Partner younger by",
                        "tooltip": "How much younger than the family member a candidate may be.",
                        "default": 3,
                        "values": AGE_LIMITS,
                    },
                    {
                        "key": "dap_female_max_age",
                        "label": "Female partner's age",
                        "tooltip": "The oldest a female candidate may be. Women's fertility falls from 30 and is nearly gone at 45.",
                        "default": 0,
                        "values": ["Any", "At most 30", "At most 35", "At most 40"],
                    },
                    {
                        "key": "dap_fertility",
                        "label": "Fertility",
                        "tooltip": "How fertile a candidate must be. $trait_fecund$ always counts as highly fertile.",
                        "default": 1,
                        "values": ["No requirement", "Can have children", "Highly fertile"],
                    },
                ],
            },
            {
                "id": "traits",
                "title": "Congenital Traits",
                "holder": "rules",
                "settings": [
                    {
                        "key": "dap_intellect",
                        "label": "Intellect (specific)",
                        "tooltip": "Require this particular trait line. Leave at No requirement to accept any intellect.",
                        "default": 0,
                        "values": [
                            "No requirement",
                            "At least $trait_intellect_good_1$",
                            "At least $trait_intellect_good_2$",
                            "Must be $trait_intellect_good_3$",
                        ],
                    },
                    {
                        "key": "dap_beauty",
                        "label": "Beauty (specific)",
                        "tooltip": "Require this particular trait line. Leave at No requirement to accept any looks.",
                        "default": 0,
                        "values": [
                            "No requirement",
                            "At least $trait_beauty_good_1$",
                            "At least $trait_beauty_good_2$",
                            "Must be $trait_beauty_good_3$",
                        ],
                    },
                    {
                        "key": "dap_physique",
                        "label": "Physique (specific)",
                        "tooltip": "Require this particular trait line. Leave at No requirement to accept any physique.",
                        "default": 0,
                        "values": [
                            "No requirement",
                            "At least $trait_physique_good_1$",
                            "At least $trait_physique_good_2$",
                            "Must be $trait_physique_good_3$",
                        ],
                    },
                    {
                        "key": "dap_required_trait",
                        "label": "Required trait",
                        "tooltip": "A specific trait the candidate must have.",
                        "default": 0,
                        "values": ["None", "$trait_fecund$", "$trait_giant$", "$trait_pure_blooded$"],
                    },
                    {
                        "key": "dap_genetic_min",
                        "label": "Good inheritable traits (any kind)",
                        "tooltip": "A count across all good inheritable traits: intellect, beauty, physique and $trait_fecund$. Any of them counts, so this works alongside the specific rows above.",
                        "default": 0,
                        "values": ["No requirement", "At least one of any kind", "At least two of any kind"],
                    },
                    {
                        "key": "dap_no_bad_genetic",
                        "label": "Bad inheritable traits",
                        "tooltip": "Whether candidates with bad inheritable traits are rejected.",
                        "default": 1,
                        "values": ["Allowed", "Rejected"],
                    },
                    {
                        "key": "dap_avoid_inbreeding",
                        "label": "Related candidates",
                        "tooltip": "Reject cousins and other extended family, who raise the risk of $trait_inbred$ children.",
                        "default": 1,
                        "values": ["Allowed", "Rejected"],
                    },
                ],
            },
            {
                "id": "personality",
                "title": "Personality and Skills",
                "holder": "rules",
                "settings": [
                    {
                        "key": "dap_skill_focus",
                        "label": "Required skill",
                        "tooltip": "A skill the candidate must be good at. Set the level below.",
                        "default": 0,
                        "values": ["None", "Diplomacy", "Martial", "Stewardship", "Intrigue", "Learning"],
                    },
                    {
                        "key": "dap_skill_min",
                        "label": "Skill level",
                        "tooltip": "The lowest level allowed in the required skill.",
                        "default": 1,
                        "values": ["At least 8", "At least 12", "At least 16", "At least 20"],
                    },
                    {
                        "key": "dap_reject_traits",
                        "label": "Unwanted traits",
                        "tooltip": "Reject candidates who are $trait_craven$, $trait_lunatic_1$, $trait_possessed_1$, $trait_deviant$ or $trait_cannibal$.",
                        "default": 0,
                        "values": ["Allowed", "Rejected"],
                    },
                ],
            },
            {
                "id": "strategy",
                "title": "Strategy",
                "holder": "rules",
                "settings": [
                    {
                        "key": "dap_lineality",
                        "label": "Lineage",
                        "tooltip": "Matrilineal marriages keep a daughter's children in your dynasty.",
                        "default": 0,
                        "values": ["Keep children in our dynasty", "Always regular marriages"],
                    },
                    {
                        "key": "dap_timing",
                        "label": "Timing",
                        "tooltip": "Whether children are betrothed early or only married as adults.",
                        "default": 0,
                        "values": ["Betroth children early", "Wait until adulthood"],
                    },
                    {
                        "key": "dap_priority",
                        "label": "Prefer",
                        "tooltip": "Among candidates who meet every requirement, what counts the most.",
                        "default": 0,
                        "values": [
                            "A balanced match",
                            "The best bloodline",
                            "The most powerful family",
                            "The most skilled spouse",
                        ],
                    },
                    {
                        "key": "dap_heiress",
                        "label": "Heirs to titles",
                        "tooltip": "Strongly prefer candidates who will inherit a landed title, so your grandchildren may inherit it too.",
                        "default": 0,
                        "values": ["No preference", "Strongly prefer"],
                    },
                    {
                        "key": "dap_prefer_neighbors",
                        "label": "Neighbours",
                        "tooltip": "Prefer candidates from realms bordering yours.",
                        "default": 0,
                        "values": ["No preference", "Prefer"],
                    },
                    {
                        "key": "dap_prefer_allies",
                        "label": "Useful alliances",
                        "tooltip": "Prefer families of powerful vassals, neighbours and rulers you are at war alongside.",
                        "default": 0,
                        "values": ["No preference", "Prefer"],
                    },
                    {
                        "key": "dap_prefer_opinion",
                        "label": "Opinion of you",
                        "tooltip": "Prefer candidates who like you, and avoid those who dislike you.",
                        "default": 0,
                        "values": ["Ignore", "Prefer friendly"],
                    },
                    {
                        "key": "dap_carriers",
                        "label": "Hidden traits",
                        "tooltip": "Count good inheritable traits a candidate carries without showing. Their children have a chance to inherit them.",
                        "default": 0,
                        "values": ["Ignore", "Count them"],
                    },
                    {
                        "key": "dap_complement",
                        "label": "Fill gaps in the bloodline",
                        "tooltip": "Prefer candidates with good inheritable traits that the family member lacks.",
                        "default": 0,
                        "values": ["Ignore", "Prefer"],
                    },
                ],
            },
            {
                "id": "control",
                "title": "Control",
                "holder": "rules",
                "settings": [
                    {
                        "key": "dap_mode",
                        "label": "Mode",
                        "tooltip": "Arrange matches on your behalf, or ask you to pick from the three best candidates first. Use Exclude to handle someone fully by hand.",
                        "default": 0,
                        "values": ["Arrange automatically", "Ask me first", "Ask only for my children"],
                    },
                    {
                        "key": "dap_relax_after",
                        "label": "Relax rules",
                        "tooltip": "If no match is found for this long, drop requirements step by step: first traits, then status, culture and realm, then faith and personality. Age, fertility, rivals and relatives are never relaxed.",
                        "default": 0,
                        "values": ["Never", "After 1 year", "After 2 years", "After 3 years"],
                    },
                ],
            },
        ],
    },

    {
        "id": "guardians",
        "tab": "Guardians",
        "sections": [
            {
                "id": "general",
                "title": "Guardians",
                "holder": "player",
                "settings": [
                    {
                        "key": "dap_guard_enabled",
                        "label": "Guardian automation",
                        "tooltip": "Give children in your family the best available guardian, once a season.",
                        "default": 0,
                        "values": ["#N Off#!", "#P On#!"],
                    },
                    {
                        "key": "dap_guard_suggest",
                        "label": "Mode",
                        "tooltip": "Suggest only lists what the autopilot would do in the log (General tab), without doing it. Use it to check the guardian choices before trusting it.",
                        "default": 0,
                        "values": ["Act", "Suggest only"],
                    },
                    {
                        "key": "dap_guard_source",
                        "label": "Where guardians come from",
                        "tooltip": "Guardians from other courts take the child with them as a ward.",
                        "default": 0,
                        "values": ["My court only", "My court and other courts"],
                    },
                    {
                        "key": "dap_guard_heir",
                        "label": "Guardian of my heir",
                        "tooltip": "Who educates your primary heir.",
                        "default": 0,
                        "values": ["Best available", "Me or my spouse if good enough", "Handled manually"],
                    },
                    {
                        "key": "dap_guard_not_me",
                        "label": "Pick me as guardian",
                        "tooltip": "Being a guardian brings childhood events where you choose for the child. Avoid it to keep those choices away from you.",
                        "default": 0,
                        "values": ["Allowed", "Never"],
                    },
                    {
                        "key": "dap_guard_replace",
                        "label": "Replace guardians",
                        "tooltip": "Replace a guardian who is imprisoned, has become your rival or enemy, or has gained an unwanted trait.",
                        "default": 1,
                        "values": ["Never", "When unfit"],
                    },
                ],
            },
            {
                "id": "rules",
                "title": "Choosing a Guardian",
                "holder": "rules",
                "settings": [
                    {
                        "key": "dap_guard_priority",
                        "label": "Best guardian means",
                        "tooltip": "Highest skill in the child's education focus, highest total skills, or the best personality to pass on.",
                        "default": 0,
                        "values": ["Skill in the child's focus", "Highest total skills", "Best personality"],
                    },
                    {
                        "key": "dap_guard_reject",
                        "label": "Unwanted guardian traits",
                        "tooltip": "Reject guardians who are $trait_lunatic_1$, $trait_possessed_1$, $trait_craven$, $trait_wrathful$, $trait_deceitful$, $trait_lazy$ or $trait_drunkard$.",
                        "default": 1,
                        "values": ["Allowed", "Rejected"],
                    },
                ],
            },
        ],
    },
    {
        "id": "education",
        "tab": "Education",
        "sections": [
            {
                "id": "general",
                "title": "Education",
                "holder": "player",
                "settings": [
                    {
                        "key": "dap_edu_enabled",
                        "label": "Education automation",
                        "tooltip": "Set the education focus of children in your family who have none, once a season.",
                        "default": 0,
                        "values": ["#N Off#!", "#P On#!"],
                    },
                    {
                        "key": "dap_edu_suggest",
                        "label": "Mode",
                        "tooltip": "Suggest only lists what the autopilot would do in the log (General tab), without doing it. Use it to check the focus choices before trusting it.",
                        "default": 0,
                        "values": ["Act", "Suggest only"],
                    },
                    {
                        "key": "dap_edu_override",
                        "label": "Existing focus",
                        "tooltip": "Whether a focus that is already set is changed to match the rules.",
                        "default": 0,
                        "values": ["Keep it", "Change it to the rules"],
                    },
                    {
                        "key": "dap_edu_heir",
                        "label": "Focus for my heir",
                        "tooltip": "Used for your primary heir when their rules say By role.",
                        "default": 3,
                        "values": ["Natural talent", "What my council lacks", "Diplomacy", "Stewardship", "Martial", "Intrigue", "Learning"],
                    },
                    {
                        "key": "dap_edu_sons",
                        "label": "Focus for other sons",
                        "tooltip": "Used for other sons when their rules say By role.",
                        "default": 4,
                        "values": ["Natural talent", "What my council lacks", "Diplomacy", "Stewardship", "Martial", "Intrigue", "Learning"],
                    },
                    {
                        "key": "dap_edu_daughters",
                        "label": "Focus for daughters",
                        "tooltip": "Used for daughters when their rules say By role.",
                        "default": 0,
                        "values": ["Natural talent", "What my council lacks", "Diplomacy", "Stewardship", "Martial", "Intrigue", "Learning"],
                    },
                ],
            },
            {
                "id": "rules",
                "title": "Education Focus",
                "holder": "rules",
                "settings": [
                    {
                        "key": "dap_edu_focus",
                        "label": "Focus",
                        "tooltip": "By role uses the focus set for heirs, sons or daughters in General Settings. Natural talent follows the child's childhood trait.",
                        "default": 0,
                        "values": ["By role", "Natural talent", "What my council lacks", "Diplomacy", "Stewardship", "Martial", "Intrigue", "Learning", "Handled manually"],
                    },
                ],
            },
        ],
    },
    {
        "id": "court",
        "tab": "Court",
        "sections": [
            {
                "id": "people",
                "title": "Relations and Council",
                "holder": "player",
                "settings": [
                    {
                        "key": "dap_court_suggest",
                        "label": "Mode",
                        "tooltip": "Suggest only lists what the autopilot would do in the log (General tab), without doing it. Use it to check the court and realm automation before trusting it.",
                        "default": 0,
                        "values": ["Act", "Suggest only"],
                    },
                    {
                        "key": "dap_court_sway",
                        "label": "Improve relations",
                        "tooltip": "Start a Sway scheme against the vassal who likes you least, when a scheme slot is free.",
                        "default": 0,
                        "values": ["Off", "Vassals below 0 opinion", "Vassals below 20 opinion"],
                    },
                    {
                        "key": "dap_court_council",
                        "label": "Council seats",
                        "tooltip": "Fill empty seats of Chancellor, Steward, Marshal and Spymaster with the most skilled courtier or vassal. Replacing also swaps a councillor for someone at least 4 points better.",
                        "default": 0,
                        "values": ["Off", "Fill empty seats", "Fill and replace weak ones"],
                    },
                    {
                        "key": "dap_court_knights",
                        "label": "Knights",
                        "tooltip": "The game already picks knights. Strict makes sure the highest prowess courtiers are always knights.",
                        "default": 0,
                        "values": ["Leave to the game", "Strictly by prowess"],
                    },
                ],
            },
            {
                "id": "titles",
                "title": "Granting Titles",
                "holder": "player",
                "settings": [
                    {
                        "key": "dap_grant_when",
                        "label": "Grant counties",
                        "tooltip": "Give away counties from your domain so you stay within your domain limit. Up to three counties are granted each season.",
                        "default": 0,
                        "values": ["Never", "When over domain limit", "Keep 1 county below the limit", "Keep 2 counties below the limit"],
                    },
                    {
                        "key": "dap_grant_which",
                        "label": "Which counties go first",
                        "tooltip": "Your capital county is never given away.",
                        "default": 0,
                        "values": ["Least developed", "Most recently gained", "Outside my capital duchy", "Other culture or faith"],
                    },
                    {
                        "key": "dap_grant_to",
                        "label": "Who receives them",
                        "tooltip": "Only unlanded adults at your court who may hold titles under your laws. Your primary heir is skipped, as they inherit anyway. Within a group, the most skilled comes first.",
                        "default": 1,
                        "values": ["My children", "My children, then my house", "Children, house, then best courtiers"],
                    },
                    {
                        "key": "dap_grant_max_each",
                        "label": "Counties per person",
                        "tooltip": "The most counties one person may hold through these grants. Family vassals below the limit can receive more.",
                        "default": 1,
                        "values": ["1", "2", "3", "No limit"],
                    },
                    {
                        "key": "dap_grant_cluster",
                        "label": "Keep holdings together",
                        "tooltip": "Prefer giving a county in a duchy where the receiver already holds land, so they can grow into a duke.",
                        "default": 1,
                        "values": ["No preference", "Prefer"],
                    },
                    {
                        "key": "dap_grant_keep_core",
                        "label": "Protect my heartland",
                        "tooltip": "Never give away counties of your capital duchy, so your heir keeps the core of the realm.",
                        "default": 1,
                        "values": ["No", "Keep my capital duchy"],
                    },
                    {
                        "key": "dap_grant_loyalty",
                        "label": "Loyal receivers only",
                        "tooltip": "Skip receivers who think poorly of you.",
                        "default": 1,
                        "values": ["Anyone", "Opinion of me 0 or higher", "Opinion of me 25 or higher"],
                    },
                    {
                        "key": "dap_grant_same",
                        "label": "Same culture and faith",
                        "tooltip": "Prefer receivers who share your culture and faith; such vassals like you more.",
                        "default": 1,
                        "values": ["No preference", "Prefer"],
                    },
                    {
                        "key": "dap_grant_contract",
                        "label": "Contract for new vassals",
                        "tooltip": "Set the contract of family and courtiers you grant land to. Only feudal vassals have adjustable taxes and levies; clan and tribal contracts are fixed. Higher obligations make them like you less.",
                        "default": 0,
                        "values": ["Leave as is", "High taxes", "High levies"],
                    },
                    {
                        "key": "dap_grant_duchies",
                        "label": "Duchy titles",
                        "tooltip": "Duchy titles you hold besides your primary title and capital duchy go to the vassal who holds most of the duchy's counties.",
                        "default": 0,
                        "values": ["Keep them", "Give to the vassal holding most of it"],
                    },
                    {
                        "key": "dap_create_titles",
                        "label": "Create titles",
                        "tooltip": "Create duchy or kingdom titles once you control more than half of their de jure counties and can pay the cost above your gold reserve. Titles with special requirements may still be created; check the log.",
                        "default": 0,
                        "values": ["Never", "Duchies", "Duchies and kingdoms"],
                    },
                    {
                        "key": "dap_revoke_suggest",
                        "label": "Hostile vassals",
                        "tooltip": "List vassals you have a valid reason to revoke a title from and who dislike you (below -25). Revoking stays your decision.",
                        "default": 0,
                        "values": ["Ignore", "Suggest in the log"],
                    },
                ],
            },
            {
                "id": "realm",
                "title": "Court and Realm",
                "holder": "player",
                "settings": [
                    {
                        "key": "dap_court_positions",
                        "label": "Court positions",
                        "tooltip": "Fill empty court positions with the most apt candidate. Essential means Physician, Bodyguard, Champion, Tutor and Master of Horse. Each position has a salary.",
                        "default": 0,
                        "values": ["Off", "Fill essential ones", "Fill all available"],
                    },
                    {
                        "key": "dap_maa_type",
                        "label": "Recruit men-at-arms",
                        "tooltip": "Recruit one regiment per season while you have free regiment slots and gold above your reserve. Refilling and upgrading are done by the game itself.",
                        "default": 0,
                        "values": ["Off", "Heavy infantry", "Pikemen", "Archers", "Light cavalry", "Heavy cavalry"],
                    },
                    {
                        "key": "dap_build_reminder",
                        "label": "Building reminder",
                        "tooltip": "The game has no way for mods to start a construction, so this reminds you once a year when you have gold above your reserve and free building slots.",
                        "default": 0,
                        "values": ["Off", "On"],
                    },
                    {
                        "key": "dap_court_prisoners",
                        "label": "Prisoners",
                        "tooltip": "Ransom prisoners whose families will pay. Release adds setting free those held longer than five years.",
                        "default": 0,
                        "values": ["Leave them", "Ransom when possible", "Ransom, else release after 5 years"],
                    },
                ],
            },
        ],
    },
]

# Presets set every rule to its default, then apply these values.
PRESETS = [
    {
        "id": "breeding",
        "label": "Bloodline",
        "tooltip": "Young, highly fertile candidates with good inheritable traits.",
        "values": {
            "dap_fertility": 2,
            "dap_female_max_age": 1,
            "dap_genetic_min": 1,
            "dap_no_bad_genetic": 1,
            "dap_avoid_inbreeding": 1,
            "dap_priority": 1,
            "dap_carriers": 1,
            "dap_complement": 1,
            "dap_relax_after": 2,
        },
    },
    {
        "id": "power",
        "label": "Power",
        "tooltip": "Rulers' families of duke rank or higher that bring alliances, heirs to titles first.",
        "values": {
            "dap_status": 3,
            "dap_alliance": 1,
            "dap_heiress": 1,
            "dap_priority": 2,
            "dap_prefer_neighbors": 1,
            "dap_relax_after": 1,
        },
    },
    {
        "id": "cheap",
        "label": "Quick",
        "tooltip": "Few requirements, so everyone is married off fast.",
        "values": {
            "dap_status": 0,
            "dap_same_faith": 0,
            "dap_max_older": 0,
            "dap_max_younger": 0,
            "dap_fertility": 0,
            "dap_no_bad_genetic": 0,
            "dap_avoid_rivals": 0,
        },
    },
]

# Number of custom save slots for rule sets
SAVE_SLOTS = 3
