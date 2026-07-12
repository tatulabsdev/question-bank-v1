"""
One-off manual trial — NOT part of the production pipeline.
Covers every diagram-bearing topic at its MAXIMUM available difficulty
level, to stress-test the strengthened prompts (topper-quality mnemonics,
PhD-accessible story explanations) against real high-difficulty diagram
content spanning school/NEET/JEE/BITSAT through SSC/RRB/IBPS-level
reasoning and DI.

Uses process_job() directly (bypassing the normal coverage-sorted queue)
so we hit exactly these topics/levels, not whatever the daily cron would
naturally pick next. Runs concurrently (4 workers, matching the 4
generation providers) using the same ThreadPoolExecutor approach as the
main pipeline, since these jobs are fully independent of each other.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pipeline import process_job

# (topic_id, level) — level is each topic's actual current ceiling,
# confirmed against seed_topics.py's difficulty_range_for_subject()
JOBS = [
    # School / NEET / JEE / BITSAT-level geometry (ceiling widened to 10)
    ("maths_geometry_triangles", 10),
    ("maths_geometry_circles", 10),
    ("maths_geometry_quadrilaterals_and_polygons", 10),
    ("maths_geometry_coordinate_geometry", 10),
    ("maths_geometry_mensuration_2d", 10),
    ("maths_geometry_mensuration_3d", 10),
    # School / NEET / JEE-level trigonometry (ceiling widened to 10)
    ("maths_trigonometry_trigonometric_ratios_and_identities", 10),
    ("maths_trigonometry_heights_and_distances", 10),
    # SSC / Banking / CUET-PG-level stats & DI (ceiling widened to 9)
    ("maths_stats_bar_and_line_graph_interpretation", 9),
    ("maths_stats_pie_chart_interpretation", 9),
    ("data_interpretation_caselet_based_di", 9),
    ("data_interpretation_mixed_graph_di", 9),
    # CAT/XAT-level nonverbal reasoning (ceiling widened to 8)
    ("reasoning_nonverbal_mirror_image", 8),
    ("reasoning_nonverbal_paper_folding", 8),
    ("reasoning_nonverbal_embedded_figures", 8),
]

totals = {"generated": 0, "verified": 0, "saved": 0}

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(process_job, topic_id, level, 8, False): (topic_id, level) for topic_id, level in JOBS}
    for future in as_completed(futures):
        topic_id, level = futures[future]
        try:
            result = future.result()
            for k in totals:
                totals[k] += result[k]
        except Exception as e:
            print(f"   !! ERROR on {topic_id} L{level}: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print(f"HIGH-DIFFICULTY DIAGRAM TRIAL DONE")
print(f"generated={totals['generated']} verified={totals['verified']} saved={totals['saved']}")
print("=" * 60)