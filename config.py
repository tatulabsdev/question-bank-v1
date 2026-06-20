"""
TryIT Question Engine — Configuration
=======================================
Single source of truth for: difficulty levels, topic tree, quota tiers,
exam metadata, and provider model defaults.

RECONCILED LEVEL SCALE (read this first)
------------------------------------------
Your original brief said "Layer 1 = 6th standard, Layer 7 = SSC/Banking/
Railway/TNPSC/State, Layer 10 = UPSC/PhD." Your own MASTER_QUESTION_PIPELINE.md
used a slightly different anchor (L4 = Class 8-10, L6 = Graduate/Competitive,
L9 = Civil Services/PhD). Both can't be literally true at once, so this file
locks ONE final scale that keeps your two anchor points (6th standard low-mid,
UPSC/PhD at the very top) and reconciles the rest. If a level feels off for a
specific exam, change it here — every other file reads from this one place.
"""

# ──────────────────────────────────────────────────────────
# DIFFICULTY LEVELS (final, reconciled)
# ──────────────────────────────────────────────────────────
LEVELS = {
    1:  "LKG-UKG, picture-based, very simple",
    2:  "Class 1-4, basic operations",
    3:  "Class 5-7 (includes 6th standard), foundation concepts",
    4:  "Class 8-10, intermediate school",
    5:  "Class 11-12, advanced school",
    6:  "Graduate / foundation competitive level",
    7:  "SSC, Banking, Railways, TNPSC, State PSC — core competitive level",
    8:  "Professional: GATE, CAT, CLAT, NEET, JEE Advanced",
    9:  "UPSC Prelims / State PSC Mains / PG entrance",
    10: "UPSC Mains advanced, PhD entrance, research level",
}

# ──────────────────────────────────────────────────────────
# QUOTA TIERS — total bank-size floors (NOT daily output)
# Daily output target is handled in the GitHub Actions schedule,
# these are the minimum cumulative questions per topic-per-level cell.
# ──────────────────────────────────────────────────────────
TIER_QUOTAS = {
    "crowded": 30000,   # topic appears in 15+ exams
    "medium":  20000,   # topic appears in 6-14 exams
    "niche":   10000,   # topic appears in 1-5 exams, no ceiling
}

GENERATION_ORDER = ["crowded", "medium", "niche"]  # crowded first, locked

# ──────────────────────────────────────────────────────────
# TOPIC TREE
# Extend this dict as coverage grows — same schema every time.
# "exam_tags" = which exam_ids (see EXAMS below) this topic feeds.
# "levels" = which difficulty levels actually apply to this topic.
# ──────────────────────────────────────────────────────────
TOPICS = {
    # ---------- MATHEMATICS / ARITHMETIC (crowded — nearly every exam) ----------
    "arith_number_system": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Number System",
        "tier": "crowded", "levels": [2, 3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ssc_chsl", "ibps_po", "ibps_clerk", "sbi_po", "sbi_clerk",
                      "rrb_ntpc", "tnpsc_group1", "tnpsc_group2", "nda", "cds", "ctet"],
    },
    "arith_percentage": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Percentage",
        "tier": "crowded", "levels": [3, 4, 5, 6, 7, 8],
        "exam_tags": ["ssc_cgl", "ssc_chsl", "ibps_po", "ibps_clerk", "sbi_po", "sbi_clerk",
                      "rrb_ntpc", "tnpsc_group1", "tnpsc_group2", "nda", "cds", "upsc_cse",
                      "jee_main", "cat", "clat"],
    },
    "arith_profit_loss": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Profit Loss Discount",
        "tier": "crowded", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "ibps_clerk", "sbi_po", "rrb_ntpc",
                      "tnpsc_group1", "tnpsc_group2", "cat"],
    },
    "arith_ratio_proportion": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Ratio and Proportion",
        "tier": "crowded", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "rrb_ntpc", "tnpsc_group1"],
    },
    "arith_simple_compound_interest": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Simple & Compound Interest",
        "tier": "medium", "levels": [4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "ibps_clerk", "tnpsc_group2"],
    },
    "arith_time_speed_distance": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Time Speed Distance",
        "tier": "crowded", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "rrb_ntpc", "tnpsc_group1", "nda"],
    },
    "arith_time_work": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Time and Work",
        "tier": "crowded", "levels": [4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "rrb_ntpc", "tnpsc_group1"],
    },
    "arith_mixture_alligation": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Mixture and Alligation",
        "tier": "medium", "levels": [5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "rrb_ntpc"],
    },
    "arith_average": {
        "subject": "Mathematics", "chapter": "Arithmetic", "topic": "Average",
        "tier": "crowded", "levels": [2, 3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "rrb_ntpc", "tnpsc_group1", "ctet"],
    },
    "algebra_linear_quadratic": {
        "subject": "Mathematics", "chapter": "Algebra", "topic": "Linear & Quadratic Equations",
        "tier": "medium", "levels": [4, 5, 6, 7, 8],
        "exam_tags": ["ssc_cgl", "jee_main", "cat", "nda"],
    },
    "geometry_triangles_circles": {
        "subject": "Mathematics", "chapter": "Geometry", "topic": "Triangles & Circles",
        "tier": "medium", "levels": [4, 5, 6, 7, 8],
        "exam_tags": ["ssc_cgl", "jee_main", "nda"],
        "diagram_required": True, "diagram_kind": "geometry_svg", "auto_generate": True,
    },
    "trigonometry_heights_distances": {
        "subject": "Mathematics", "chapter": "Trigonometry", "topic": "Heights and Distances",
        "tier": "medium", "levels": [5, 6, 7, 8],
        "exam_tags": ["ssc_cgl", "jee_main", "nda"],
        "diagram_required": True, "diagram_kind": "geometry_svg", "auto_generate": True,
    },
    "mensuration_2d_3d": {
        "subject": "Mathematics", "chapter": "Mensuration", "topic": "Area, Volume, Surface Area",
        "tier": "medium", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "rrb_ntpc"],
        "diagram_required": True, "diagram_kind": "geometry_svg", "auto_generate": True,
    },
    "stats_data_interpretation": {
        "subject": "Mathematics", "chapter": "Statistics", "topic": "Data Interpretation",
        "tier": "crowded", "levels": [5, 6, 7, 8],
        "exam_tags": ["ssc_cgl", "ibps_po", "sbi_po", "cat", "upsc_cse"],
        "diagram_required": True, "diagram_kind": "chart_data", "auto_generate": True,
    },

    # ---------- REASONING (crowded) ----------
    "reason_analogy": {
        "subject": "Reasoning", "chapter": "Verbal Reasoning", "topic": "Analogy",
        "tier": "crowded", "levels": [2, 3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ssc_chsl", "ibps_po", "ibps_clerk", "rrb_ntpc",
                      "tnpsc_group1", "tnpsc_group2", "upsc_cse", "nda", "ctet"],
    },
    "reason_series_completion": {
        "subject": "Reasoning", "chapter": "Verbal Reasoning", "topic": "Series Completion",
        "tier": "crowded", "levels": [2, 3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "ibps_clerk", "rrb_ntpc", "tnpsc_group1"],
    },
    "reason_coding_decoding": {
        "subject": "Reasoning", "chapter": "Verbal Reasoning", "topic": "Coding Decoding",
        "tier": "crowded", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "rrb_ntpc", "tnpsc_group1"],
    },
    "reason_blood_relations": {
        "subject": "Reasoning", "chapter": "Verbal Reasoning", "topic": "Blood Relations",
        "tier": "medium", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "rrb_ntpc"],
    },
    "reason_syllogism": {
        "subject": "Reasoning", "chapter": "Verbal Reasoning", "topic": "Syllogism",
        "tier": "crowded", "levels": [4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "ibps_clerk", "upsc_cse"],
    },
    "reason_seating_arrangement": {
        "subject": "Reasoning", "chapter": "Analytical Reasoning", "topic": "Seating Arrangement",
        "tier": "crowded", "levels": [4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "ibps_clerk", "sbi_po"],
    },
    "reason_mirror_image": {
        "subject": "Reasoning", "chapter": "Non-Verbal Reasoning", "topic": "Mirror Image",
        "tier": "medium", "levels": [2, 3, 4, 5, 6],
        "exam_tags": ["ssc_cgl", "rrb_ntpc", "ctet"],
        "diagram_required": True, "diagram_kind": "nonverbal_mirror_svg", "auto_generate": True,
    },
    "reason_paper_folding": {
        "subject": "Reasoning", "chapter": "Non-Verbal Reasoning", "topic": "Paper Folding",
        "tier": "medium", "levels": [2, 3, 4, 5, 6],
        "exam_tags": ["ssc_cgl", "rrb_ntpc", "ctet"],
        "diagram_required": True, "diagram_kind": "paper_fold", "auto_generate": True,
    },
    "reason_embedded_figures": {
        "subject": "Reasoning", "chapter": "Non-Verbal Reasoning", "topic": "Embedded Figures",
        "tier": "medium", "levels": [2, 3, 4, 5, 6],
        "exam_tags": ["ssc_cgl", "rrb_ntpc", "ctet"],
        "diagram_required": True, "diagram_kind": "embedded_figure", "auto_generate": True,
    },

    # ---------- ENGLISH (crowded) ----------
    "eng_synonyms_antonyms": {
        "subject": "English", "chapter": "Vocabulary", "topic": "Synonyms and Antonyms",
        "tier": "crowded", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ssc_chsl", "ibps_po", "ibps_clerk", "rrb_ntpc", "tnpsc_group1"],
    },
    "eng_error_spotting": {
        "subject": "English", "chapter": "Grammar", "topic": "Error Spotting",
        "tier": "crowded", "levels": [4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "ibps_clerk", "sbi_po"],
    },
    "eng_para_jumbles": {
        "subject": "English", "chapter": "Verbal Reasoning", "topic": "Para Jumbles",
        "tier": "medium", "levels": [4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ibps_po", "ibps_clerk"],
    },
    "eng_reading_comprehension": {
        "subject": "English", "chapter": "Reading Comprehension", "topic": "Main Idea / Inference",
        "tier": "crowded", "levels": [4, 5, 6, 7, 8],
        "exam_tags": ["ssc_cgl", "ibps_po", "sbi_po", "cat", "clat", "upsc_cse"],
    },
    "eng_one_word_idioms": {
        "subject": "English", "chapter": "Vocabulary", "topic": "One Word Substitution & Idioms",
        "tier": "medium", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "ssc_chsl", "ibps_clerk"],
    },

    # ---------- GK / CURRENT AFFAIRS (crowded for History/Polity, medium for rest) ----------
    "hist_modern_india": {
        "subject": "GK", "chapter": "History", "topic": "Modern India / Freedom Movement",
        "tier": "crowded", "levels": [3, 4, 5, 6, 7, 8, 9],
        "exam_tags": ["upsc_cse", "ssc_cgl", "tnpsc_group1", "tnpsc_group2", "rrb_ntpc", "ctet"],
    },
    "pol_fundamental_rights_parliament": {
        "subject": "GK", "chapter": "Polity", "topic": "Fundamental Rights & Parliament",
        "tier": "crowded", "levels": [3, 4, 5, 6, 7, 8, 9],
        "exam_tags": ["upsc_cse", "ssc_cgl", "tnpsc_group1", "tnpsc_group2", "nda"],
    },
    "geo_indian_physical": {
        "subject": "GK", "chapter": "Geography", "topic": "Indian Physical Geography",
        "tier": "medium", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["upsc_cse", "ssc_cgl", "tnpsc_group1", "rrb_ntpc"],
        # Text-only for now. Rivers/mountains/plateaus would need their own
        # sourced, verified canonical list the same way states/UTs got one
        # below — not built yet, so this stays text-only rather than risking
        # an LLM inventing river courses.
    },
    "geo_state_identification": {
        "subject": "GK", "chapter": "Geography", "topic": "State/UT Identification on Map",
        "tier": "medium", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["upsc_cse", "ssc_cgl", "tnpsc_group1", "rrb_ntpc"],
        "diagram_required": True, "diagram_kind": "map_region", "auto_generate": True,
    },
    "economy_basic_indian": {
        "subject": "GK", "chapter": "Economy", "topic": "Indian Economy Basics",
        "tier": "medium", "levels": [4, 5, 6, 7, 8],
        "exam_tags": ["upsc_cse", "ssc_cgl", "tnpsc_group1"],
    },
    "current_affairs_national": {
        "subject": "GK", "chapter": "Current Affairs", "topic": "National News & Schemes",
        "tier": "crowded", "levels": [4, 5, 6, 7, 8],
        "exam_tags": ["upsc_cse", "ssc_cgl", "tnpsc_group1", "ibps_po", "rrb_ntpc"],
    },
    "sci_gk_physics_chem_bio": {
        "subject": "GK", "chapter": "Science", "topic": "General Science (Physics/Chem/Bio basics)",
        "tier": "medium", "levels": [3, 4, 5, 6, 7],
        "exam_tags": ["ssc_cgl", "rrb_ntpc", "ctet"],
    },

    # ---------- LEGAL (niche — only law exams) ----------
    "law_torts_negligence": {
        "subject": "Legal", "chapter": "Law of Torts", "topic": "Negligence & Liability",
        "tier": "niche", "levels": [8],
        "exam_tags": ["clat"],
    },
    "law_contract_offer": {
        "subject": "Legal", "chapter": "Contract Law", "topic": "Offer, Acceptance, Consideration",
        "tier": "niche", "levels": [8],
        "exam_tags": ["clat"],
    },
    "law_constitutional_basics": {
        "subject": "Legal", "chapter": "Constitutional Law", "topic": "Constitutional Principles",
        "tier": "niche", "levels": [8, 9],
        "exam_tags": ["clat", "judiciary_exams"],
    },

    # ---------- SCIENCE for Medical/Engineering (medium — NEET/JEE specific) ----------
    "sci_bio_cell_genetics": {
        "subject": "Science", "chapter": "Biology", "topic": "Cell Biology & Genetics",
        "tier": "medium", "levels": [5, 6, 8],
        "exam_tags": ["neet_ug"],
    },
    "sci_physics_mechanics_electricity": {
        "subject": "Science", "chapter": "Physics", "topic": "Mechanics & Electricity",
        "tier": "medium", "levels": [4, 5, 6, 8],
        "exam_tags": ["jee_main", "neet_ug", "ssc_cgl"],
    },
    "sci_chem_organic_inorganic": {
        "subject": "Science", "chapter": "Chemistry", "topic": "Organic & Inorganic Basics",
        "tier": "medium", "levels": [5, 6, 8],
        "exam_tags": ["jee_main", "neet_ug"],
    },

    # ---------- STATE SPECIFIC (niche by design — 1-2 exams each) ----------
    "tn_dravidian_movement": {
        "subject": "State", "chapter": "Tamil Nadu", "topic": "Dravidian Movement & TN History",
        "tier": "niche", "levels": [4, 5, 6, 7],
        "exam_tags": ["tnpsc_group1", "tnpsc_group2"],
    },
    "tn_geography_schemes": {
        "subject": "State", "chapter": "Tamil Nadu", "topic": "TN Geography & Govt Schemes",
        "tier": "niche", "levels": [4, 5, 6, 7],
        "exam_tags": ["tnpsc_group1", "tnpsc_group2"],
    },
    # Add more states following this exact schema as coverage grows.
}

# Fill in defaults for any topic that didn't explicitly set diagram fields —
# most topics (Percentage, Analogy, Vocabulary, etc.) are text-only, so they
# shouldn't all need three extra lines each. Geometry/DI/mirror-image/maps
# set their own values above; everything else defaults to "no diagram".
for _topic_id, _meta in TOPICS.items():
    _meta.setdefault("diagram_required", False)
    _meta.setdefault("diagram_kind", None)
    _meta.setdefault("auto_generate", True)

# ──────────────────────────────────────────────────────────
# CANONICAL INDIAN STATES / UNION TERRITORIES
# Used to validate map_region questions: the LLM only picks a NAME from
# this closed list, never draws geometry, so "is this a real place" is a
# simple lookup instead of a trust-the-drawing problem.
#
# Current as of this writing (28 states + 8 UTs, stable since the 2019
# J&K/Ladakh reorganization). Double-check before relying on this long
#-term — administrative boundaries do occasionally change.
#
# The actual map RENDERING (the visual boundaries) is a frontend concern,
# not this backend's — wire your app's map component to an openly-licensed
# boundary dataset such as india-geodata (CC0-1.0 / CC-BY-4.0, sourced
# from LGD/Survey of India/Bhuvan/DataMeet) or geoBoundaries (via HDX).
# This backend never generates map geometry — only validates region names.
# ──────────────────────────────────────────────────────────
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal",
]

INDIAN_UTS = [
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

INDIAN_STATES_UTS = INDIAN_STATES + INDIAN_UTS

# ──────────────────────────────────────────────────────────
# EXAM METADATA — drives exam_mapping block in final JSON
# ──────────────────────────────────────────────────────────
EXAMS = {
    "ssc_cgl":       {"name": "SSC CGL",        "pattern": "standalone_mcq4", "negative_marking": -0.5,  "time_per_q_sec": 90},
    "ssc_chsl":      {"name": "SSC CHSL",       "pattern": "standalone_mcq4", "negative_marking": -0.5,  "time_per_q_sec": 90},
    "ibps_po":       {"name": "IBPS PO",        "pattern": "standalone_mcq4", "negative_marking": -0.25, "time_per_q_sec": 72},
    "ibps_clerk":    {"name": "IBPS Clerk",     "pattern": "standalone_mcq4", "negative_marking": -0.25, "time_per_q_sec": 72},
    "sbi_po":        {"name": "SBI PO",         "pattern": "standalone_mcq4", "negative_marking": -0.25, "time_per_q_sec": 72},
    "sbi_clerk":     {"name": "SBI Clerk",      "pattern": "standalone_mcq4", "negative_marking": -0.25, "time_per_q_sec": 72},
    "rrb_ntpc":      {"name": "RRB NTPC",       "pattern": "standalone_mcq4", "negative_marking": -0.33, "time_per_q_sec": 60},
    "tnpsc_group1":  {"name": "TNPSC Group 1",  "pattern": "standalone_mcq4", "negative_marking": 0,     "time_per_q_sec": 72},
    "tnpsc_group2":  {"name": "TNPSC Group 2",  "pattern": "standalone_mcq4", "negative_marking": 0,     "time_per_q_sec": 72},
    "upsc_cse":      {"name": "UPSC CSE Prelims","pattern": "standalone_mcq4","negative_marking": -0.66, "time_per_q_sec": 80},
    "nda":           {"name": "NDA",            "pattern": "standalone_mcq4", "negative_marking": -0.33, "time_per_q_sec": 60},
    "cds":           {"name": "CDS",            "pattern": "standalone_mcq4", "negative_marking": -0.33, "time_per_q_sec": 60},
    "ctet":          {"name": "CTET",           "pattern": "standalone_mcq4", "negative_marking": 0,     "time_per_q_sec": 60},
    "jee_main":      {"name": "JEE Main",       "pattern": "standalone_mcq4", "negative_marking": -1,    "time_per_q_sec": 180},
    "neet_ug":       {"name": "NEET UG",        "pattern": "standalone_mcq4", "negative_marking": -1,    "time_per_q_sec": 60},
    "cat":           {"name": "CAT",            "pattern": "passage_based",   "negative_marking": -1,    "time_per_q_sec": 120},
    "clat":          {"name": "CLAT",           "pattern": "passage_based",   "negative_marking": -0.25, "time_per_q_sec": 90},
    "judiciary_exams":{"name": "State Judiciary","pattern": "standalone_mcq4","negative_marking": 0,     "time_per_q_sec": 90},
}

# ──────────────────────────────────────────────────────────
# PROVIDER MODEL DEFAULTS (see providers.py for the call logic)
# ──────────────────────────────────────────────────────────
PROVIDER_MODELS = {
    "cerebras":   "llama-3.3-70b",
    "groq_fast":  "llama-3.1-8b-instant",
    "groq_strong":"llama-3.3-70b-versatile",
    "gemini":     "gemini-2.5-flash",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "mistral":    "mistral-small-latest",
}

QUALITY_SCORE_THRESHOLD = 7  # out of 10, standardized (was inconsistent: 6 vs 7 across old docs)
JSON_BATCH_SIZE = 300        # questions per output JSON file (your spec said 200-500)
