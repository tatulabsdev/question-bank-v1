# TRYIT EDUCATIONS — CASE 3 DEEP-DIVE, BATCH 3
# SSC MTS, SSC GD Constable, IBPS Clerk
# Verified against live sources, July 2026

---

# 1. SSC MTS (Multi-Tasking Staff) + Havaldar — 10th-pass level

| Field | Detail |
|---|---|
| Conducting Body | SSC |
| Posts | MTS (Non-Technical) across central govt departments; Havaldar (CBIC & CBN) |
| Structure | Single CBT with 2 mandatory sessions, same sitting — NOT a Tier 1/Tier 2 split like CGL/CHSL. Both sessions compulsory; skipping either disqualifies the candidate. |
| Session 1 | 40 questions, 120 marks (3 marks/question) — Numerical Ability + Reasoning. **No negative marking.** |
| Session 2 | 50 questions, 150 marks (3 marks/question) — English Language + General Awareness. **1 mark deducted per wrong answer.** |
| Total | 90 questions, 270 marks, 90 minutes (45 min/session; scribe candidates get 60 min/session) |
| Mode | Online CBT, available in **15 languages** (English, Hindi + 13 regional) |
| Havaldar-specific | Additional PET/PST after CBT, qualifying only |
| Key structural note | The zero-vs-full negative marking split is by **session (Maths+Reasoning vs English+GA)**, not by objective-vs-subjective like CA Foundation/CSEET — a third distinct variant of the "hybrid negative marking within one exam" pattern already tracked across this database. |

---

# 2. SSC GD Constable (General Duty) — 10th-pass level, Defence/Paramilitary

| Field | Detail |
|---|---|
| Conducting Body | SSC |
| Recruits For | BSF, CRPF, CISF, SSB, ITBP, Assam Rifles (as Rifleman), SSF, and Sepoy in Narcotics Control Bureau — the exact "CRPF/BSF-type" exam you flagged as a target category |
| Structure | Single CBT, one sitting, no tiers |
| Sections | 4 equal sections, 20 questions/40 marks each: General Intelligence & Reasoning, General Knowledge & General Awareness, Elementary Mathematics, English/Hindi |
| Total | 80 questions, 160 marks (2 marks/question), 60 minutes |
| Negative Marking | 0.25 marks per wrong answer |
| Mode | Online CBT, English/Hindi + 13 regional languages |
| Final Merit | Based on normalized CBT score alone (multiple shifts require normalization) + NCC bonus marks where applicable. PET/PST/Medical/Document Verification are qualifying-only, no marks. |
| Level | Class 10 standard content — the same foundational level as SSC MTS, but with a paramilitary-specific physical-fitness gate layered on top |
| Key structural note | This is a genuinely clean, flat 25/25/25/25 split with a single low negative-marking rate (0.25) — structurally the simplest exam pattern found in the Case 3 research so far, in contrast to CGL/CHSL's Tier1-vs-Tier2 asymmetric weighting. |

---

# 3. IBPS Clerk — Graduate level, Banking

| Field | Detail |
|---|---|
| Conducting Body | IBPS |
| Prelims | 100 questions, 100 marks, 60 min, **qualifying only**. 3 sections (individually timed, 20 min each): English Language, Reasoning Ability, Numerical Ability. |
| Mains | Recently revised (2026 cycle): 155 questions, 200 marks, 120 minutes (down from the older 190-question/160-minute format — any content or mock tests built on the pre-revision pattern is now outdated). 4 sections: General/Financial Awareness, General English, Reasoning Ability (now merged with Computer Aptitude into one section), Quantitative Aptitude. |
| Negative Marking | 0.25 marks per wrong answer, both Prelims and Mains. No penalty for unattempted. |
| Final Selection | 100% Mains marks — Prelims marks never count. No interview at all. |
| Language Proficiency Test (LPT) | Final qualifying stage — tests proficiency in the official language of the state applied to; exempted if the candidate studied that language in/above Class 10. Failing LPT disqualifies even after clearing Prelims+Mains. |
| Exact section-wise Mains question split | Multiple sources show minor variation post-revision (e.g., some cite GA~50Q/English~40Q/Reasoning~60Q, others show different splits) — recommend confirming the exact current numbers against the official 2026 IBPS Clerk notification once released, expected around July-August 2026. |
| Key structural note | IBPS Clerk's LPT is a genuinely distinct mechanism not seen in SSC/UPSC/RRB — a state-specific regional-language competency gate that sits AFTER the merit list, meaning a candidate can top Mains and still be disqualified for language reasons. This is directly relevant to your regional-language translation prioritization: IBPS-track students specifically need strength in whichever state's official language they're applying under, not just Hindi/English. |

---

## CROSS-EXAM COMPARISON — BATCH 3

| Exam | Merit-deciding stage | Negative marking pattern | Sections | Level |
|---|---|---|---|---|
| SSC MTS | Single CBT (both sessions) | Session 1: none. Session 2: 1 mark | Maths+Reasoning / English+GA | 10th |
| SSC GD Constable | Single CBT | 0.25 mark flat | 4 equal (Reasoning/GK/Maths/English-Hindi) | 10th |
| IBPS Clerk | Mains only | 0.25 mark flat, both stages | 3 (Prelims) / 4 (Mains) | Graduate |

## UPDATED CROSS-DATABASE FINDING

**The "zero negative marking on one component, penalty on another, within the same single-sitting exam" pattern is now confirmed a FOURTH way** — SSC MTS splits it by session (not by paper like CA Foundation, not by question-type like GATE/JAM, not by section-marking-scheme like UCEED). Four structurally distinct variants of hybrid marking now exist across this database, each requiring its own explicit rule in any scoring-simulator tool built for TryIT.

## EXAM REGISTRY UPDATE
`ssc_mts`, `ssc_gd_constable`, and `ibps_clerk` move from `pass1_mapped_only`/`not_started` to `deep_dived` in the exam registry (see updated `seed_exam_registry.py`).

## STILL PENDING (Case 3 Batch 4+)
- SSC CPO, SSC JE, IBPS SO, IBPS RRB PO/Clerk, SBI PO/Clerk, RBI Grade B/Assistant, RRB Group D/JE/ALP, NABARD Grade A, LIC AAO, State Judicial Services, State TETs — all still `pass1_mapped_only` or `not_started`.
