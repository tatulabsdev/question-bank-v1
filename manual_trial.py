"""
One-off manual trial — NOT part of the production pipeline.
Directly calls the real process_job() for a chosen topic/level, bypassing
build_today_jobs()'s auto-selection, so we can specifically test a
diagram (geometry_svg) topic at higher levels (7-8) that the coverage-
sorted queue hasn't reached yet.
"""
from pipeline import process_job

TOPIC_ID = "maths_trigonometry_heights_and_distances"

for level in [7, 8]:
    result = process_job(TOPIC_ID, level, count=10, dry_run=False)
    print(f"LEVEL {level} RESULT: {result}\n")