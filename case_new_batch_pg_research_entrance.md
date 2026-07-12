# TRYIT EDUCATIONS — PG/RESEARCH-ENTRANCE BATCH (NEW)
# CUET-PG, UGC-NET/JRF, CSIR-NET, CAT, XAT
# Verified against live sources, July 2026
# Fills a direct gap: CUET-PG wasn't in the registry at all; UGC-NET/JRF and
# CSIR-NET are the two main PhD-gateway exams named in the founder's brief;
# CAT and XAT are the flagship MBA-entrance pair. Follows the same format
# and sourcing discipline as case3_batch1_flagship_govt_exams.md.

---

## GROUND RULES (same as Batch 1)
- Difficulty Score: not assigned in this batch, same reasoning as Batch 1 —
  these are all "must-clear" competitive/PG exams where difficulty framing
  works differently from a simple 1-10 scale.
- PYQ: format/question-type description only, no reproduced questions.
- Where sources disagreed on a minor detail (e.g. exact GK section length
  across XAT cycles), the most recent (2026-cycle) figure is used and the
  discrepancy is flagged rather than silently picking one.

---

# 1. CUET-PG (Common University Entrance Test — Postgraduate) — Graduate level

| Field | Detail |
|---|---|
| Conducting Body | NTA (National Testing Agency) |
| Structure | Single domain-specific section per subject paper — the earlier separate General Aptitude section (Section A) was removed starting the 2025 cycle and stays removed for 2026. |
| Paper | 75 MCQs, 300 marks, 90 minutes, computer-based test (CBT). |
| Marking | +4 for correct, −1 for incorrect. No penalty for unattempted questions. |
| Subjects | 157 distinct subject papers offered; a candidate can select up to 4 paper codes across different postgraduate programs they're applying to. |
| Volume | ~6 lakh applicants (2025 cycle) across ~7.68 lakh individual exam attempts (some candidates sit multiple subject papers). |
| Language | English and Hindi for most subjects; language-specific papers (Sanskrit, French, etc.) are conducted in that language only. |
| Key structural note | Since the General Aptitude section was scrapped, CUET-PG is now a pure domain-knowledge test — a math/science/commerce paper tests only that subject, not reasoning/English/GK alongside it. This is a different shape from UPSC/SSC/Banking, where GK or reasoning always shares the paper regardless of specialization. |

---

# 2. UGC-NET / JRF (University Grants Commission National Eligibility Test) — PG level, PhD-gateway

| Field | Detail |
|---|---|
| Conducting Body | NTA, on behalf of UGC |
| Structure | 2 compulsory papers in one 3-hour session, no break between them. |
| Paper 1 | 50 MCQs, 100 marks (2 marks/question). Common for ALL candidates regardless of subject. Covers 10 units: Teaching Aptitude, Research Aptitude, Comprehension, Communication, Mathematical Reasoning, Logical Reasoning, Data Interpretation, ICT, People & Environment, Higher Education System. |
| Paper 2 | 100 MCQs, 200 marks (2 marks/question). Subject-specific, chosen from 85-87 subjects (Forestry and Statistics were newly added starting the 2026 June session). |
| Marking | +2 per correct answer. **No negative marking at all**, in either paper. |
| Frequency | Twice yearly (June and December sessions). |
| Purpose | Eligibility for Assistant Professor posts, Junior Research Fellowship (JRF), and (per current guidance) PhD admission relevance at many universities. |
| Key structural note | Paper 1's syllabus (Mathematical Reasoning, Logical Reasoning, Data Interpretation) is IDENTICAL in concept to what TryIT's existing `reasoning_*` and `data_interpretation_*` topic groups already cover — meaning real overlap exists with content you already generate, just needs exam-tag mapping, not new topic-building. |

---

# 3. CSIR-NET (Joint CSIR-UGC NET) — PG level, PhD-gateway, pure sciences

| Field | Detail |
|---|---|
| Conducting Body | NTA, on behalf of CSIR (Council of Scientific and Industrial Research) |
| Structure | Single paper, 3 hours, divided into Part A (common to all 5 subjects) + Part B + Part C (both subject-specific). CBT mode. |
| Part A | Common across all subjects. General aptitude: logical reasoning, graphical analysis, analytical/numerical ability, quantitative comparison, series formation, puzzles. |
| Part B | Subject-specific, conventional-difficulty MCQs from the syllabus. |
| Part C | Subject-specific, higher-order-thinking (HOTS) questions applying scientific concepts, not just recalling them. |
| Subjects | 5 total: Chemical Sciences, Earth/Atmospheric/Ocean/Planetary Sciences, Life Sciences, Mathematical Sciences, Physical Sciences. |
| Marking (varies significantly by subject) | Chemical Sciences: 75Q total across A/B/C, Parts A&B = 2 marks/Q, Part C = 4 marks/Q, 25% negative marking all parts. Physical Sciences: attempt 55 of a larger pool, Part A = 2 marks/Q, Part B = 3.5 marks/Q, Part C = 5 marks/Q, 25% negative marking all parts. Earth Sciences: 25% negative in Parts A/B, but 33% in Part C specifically (highest penalty rate of any subject/part combination found). Mathematical Sciences: 25% negative in Parts A/B, but **zero** negative marking in Part C — though Part C uses multiple-select questions (MSQs) where you only get credit for selecting ALL correct options and NO incorrect ones, making it effectively harder despite no explicit penalty. |
| Total marks | 200, across all subjects, regardless of the differing question-count/marks-per-question splits above. |
| Purpose | JRF + Lectureship (Assistant Professor) eligibility in science disciplines; PhD admission relevance. |
| Key structural note | This is the most subject-dependent marking scheme of any exam researched so far (in either batch) — a flat "CSIR-NET negative marking is X%" statement would be wrong for at least 2 of the 5 subjects. Any exam_syllabus_map entries for this exam MUST be subject-specific, not exam-wide. |

---

# 4. CAT (Common Admission Test) — Graduate level, MBA entrance

| Field | Detail |
|---|---|
| Conducting Body | IIMs (rotating — a different IIM administers each year) |
| Structure | 3 sections, strict sectional lock (cannot move between sections early or return once a section's time expires). Fixed order: VARC → DILR → QA. |
| VARC (Verbal Ability & Reading Comprehension) | 24 questions, 72 marks, 40 minutes. ~16 of the 24 are Reading Comprehension (4 passages × 4 questions), remainder are para-jumbles/para-summary/odd-sentence-out. |
| DILR (Data Interpretation & Logical Reasoning) | 22 questions, 66 marks, 40 minutes. Presented as ~5 sets of 4-5 questions each: puzzles, family trees, blood relations, series, pie/bar/line charts, tables, syllogisms. |
| QA (Quantitative Ability) | 22 questions, 66 marks, 40 minutes. Arithmetic and Algebra dominate (~11-12 of 22 questions); syllabus capped at Class 9-10 level math, but applied with high difficulty/speed pressure. |
| Total | 68 questions, 204 marks, 120 minutes overall. |
| Question types | Mix of MCQ and TITA (Type-In-The-Answer, no options given). MCQ: +3 correct / −1 incorrect. TITA: +3 correct / **zero penalty** for incorrect — meaningfully different risk profile from MCQs in the same section. |
| Volume | ~2.5-3 lakh applicants/year. |
| Key structural note | The MCQ/TITA distinction matters directly for how TryIT should tag CAT-relevant questions — a "TITA-style" quant question (no options, direct numeric answer) is a materially different UX/difficulty experience from an MCQ version of the same underlying problem, even at identical mathematical difficulty. |

---

# 5. XAT (Xavier Aptitude Test) — Graduate level, MBA entrance

| Field | Detail |
|---|---|
| Conducting Body | XLRI Jamshedpur (on behalf of XAMI — Xavier Association of Management Institutes), used by 250+ B-schools |
| Structure | 2 parts, no sectional time limit within Part 1 (candidates can move freely between its 3 sections), but Part 2 is separate and untimed-relative-to-Part-1. |
| Part 1 | ~75 questions across 3 sections — Verbal Ability & Logical Reasoning (~26Q), Decision Making (~21Q), Quantitative Ability & Data Interpretation (~28Q) — 170 minutes total. |
| Part 2 | General Knowledge, ~20 questions, 10 minutes. |
| Marking (Part 1) | +1 correct, −0.25 incorrect. Additionally: **−0.10 penalty for every unattempted question beyond the first 8** — a rule not seen in any other exam in either batch; XAT is unique in penalizing excessive skipping, not just wrong answers. |
| Marking (Part 2 / GK) | +1 correct, **zero negative marking**. Critically: GK marks are NOT included in the percentile calculation at all — but XLRI DOES use the raw GK score directly in its own final admission decision, separate from the percentile. |
| Key structural note | XAT's Decision Making section (ethics/prioritization caselets, evaluating which stakeholder-balanced answer is "most correct" rather than objectively correct) has no equivalent in CAT, UPSC, SSC, or Banking — this is a genuinely distinct question TYPE that would need its own topic/pattern design, not a variant of existing reasoning_* topics. |

---

## CROSS-EXAM COMPARISON — THIS BATCH

| Exam | Negative marking | Unique structural feature | Volume |
|---|---|---|---|
| CUET-PG | −1 per wrong (out of +4 correct) | Pure single-subject test, no GK/reasoning mixed in | ~6 lakh |
| UGC-NET/JRF | **None at all** | Paper 1 overlaps directly with existing `reasoning_*`/`data_interpretation_*` topics | Twice-yearly, high volume (not confirmed exact figure) |
| CSIR-NET | Varies 0%-33% by subject AND by part within the same subject | Only exam in either batch where a flat "the negative marking is X%" claim is provably wrong | Not confirmed |
| CAT | −1 MCQ / 0 TITA (same section, different penalty by question type) | Strict sectional lock, cannot revisit an earlier section at all | ~2.5-3 lakh/year |
| XAT | −0.25 wrong / −0.10 excess-skip / 0 for GK | Only exam found with a skip-penalty distinct from a wrong-answer penalty; GK scored but excluded from percentile | Not confirmed |

## KEY OBSERVATIONS FOR QUESTION-BANK WEIGHTING

1. **"No negative marking" is not one uniform category.** UGC-NET has zero negative marking anywhere. CSIR-NET has zero negative marking ONLY in Mathematical Sciences Part C, and only because it swapped in an all-or-nothing MSQ format instead — arguably harsher despite no explicit penalty. Treating these as equivalent "safe to guess" exams would be a real content-design mistake.
2. **CAT and XAT, despite both being MBA entrance exams, have almost nothing in common structurally** — different penalty rules, different skip-penalty existence, XAT's Decision Making section has no CAT equivalent at all. A single "MBA entrance" content bucket would poorly serve either exam specifically.
3. **UGC-NET Paper 1 is the strongest direct-reuse opportunity found in either batch** — its stated syllabus units (Mathematical Reasoning, Logical Reasoning, Data Interpretation) already match existing TryIT topic groups conceptually. This is the fastest real exam_syllabus_map win available right now.
4. **CSIR-NET cannot be tagged as one exam_id with one weightage profile** — its marking scheme genuinely differs by subject and by part-within-subject. Any syllabus mapping needs to branch by CSIR-NET subject, not treat it as a single flat entity the way SSC CGL (one merit-deciding tier) could be.

## WHAT'S STILL MISSING (this exam family)
- CSIR-NET's exact syllabus-to-topic weightage per subject (5 subjects, each would need its own mini-analysis — this batch confirms the marking-scheme structure but not per-topic weightage within any one subject)
- UGC-NET Paper 2's 85-87 subject-specific syllabi (only Paper 1, the common paper, was researched in depth this batch)
- CAT/XAT applicant-volume figures for XAT specifically (CAT's ~2.5-3 lakh is sourced; XAT's volume was not found in this pass)
- NMAT, SNAP, MAT, CMAT — other MBA entrance exams not yet touched by either batch
- GRE/GMAT/IELTS/TOEFL/PTE — still correctly flagged as needing separate product-shape design (not MCQ-bank-shaped in the same way), not attempted in this batch either

Recommend continuing in this same batch style for the next gap — CSIR-NET per-subject weightage would be the highest-value next target given how directly it affects existing science topic groups.