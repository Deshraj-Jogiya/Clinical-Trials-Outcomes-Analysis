"""Refresh the whole outcomes report in one process: ETL, statistical tests, Tableau extracts and the dashboard image.

Running the four steps as separate scripts starts Python four times and imports pandas, SciPy, lifelines and matplotlib in each;
here they load once. `python make_report.py --benchmark` times both ways (best of 3) and writes exports/report_refresh_benchmark.csv.
"""

import contextlib
import io
import os
import subprocess
import sys
import time

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["etl/clinical_etl.py", "analytics/statistical_tests.py", "viz/tableau_export.py", "viz/dashboard_export.py"]
for folder in ("etl", "analytics", "viz", ""):
    sys.path.insert(0, os.path.join(BASE, folder))


def refresh(quiet=False):
    import clinical_etl
    import dashboard_export
    import statistical_tests
    import tableau_export
    sink = io.StringIO() if quiet else sys.stdout
    with contextlib.redirect_stdout(sink):
        for module in (clinical_etl, statistical_tests, tableau_export, dashboard_export):
            module.main()


def _separate():
    for step in STEPS:
        subprocess.run([sys.executable, os.path.join(BASE, step)], check=True, capture_output=True, cwd=BASE)


def _single():
    subprocess.run([sys.executable, os.path.join(BASE, "make_report.py"), "--quiet"], check=True, capture_output=True, cwd=BASE)


def benchmark(repeats=3):
    def best(fn):
        times = []
        for _ in range(repeats):
            start = time.perf_counter(); fn(); times.append(time.perf_counter() - start)
        return min(times)
    separate, single = best(_separate), best(_single)
    row = {"separate_scripts_seconds": round(separate, 2), "one_process_seconds": round(single, 2),
           "time_saved": round(1 - single / separate, 4)}
    pd.DataFrame([row]).to_csv(os.path.join(BASE, "exports", "report_refresh_benchmark.csv"), index=False)
    return row


if __name__ == "__main__":
    if "--benchmark" in sys.argv:
        print(benchmark())
    else:
        refresh(quiet="--quiet" in sys.argv)
