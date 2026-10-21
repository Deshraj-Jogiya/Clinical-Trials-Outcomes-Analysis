import os
import subprocess
import sys

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_one_process_refresh_writes_the_same_extracts_as_the_separate_scripts():
    for step in ("etl/clinical_etl.py", "analytics/statistical_tests.py", "viz/tableau_export.py"):
        subprocess.run([sys.executable, os.path.join(BASE, step)], check=True, capture_output=True, cwd=BASE)
    names = ("km_curves.csv", "logrank_tests.csv", "patient_outcomes.csv")
    before = {n: pd.read_csv(os.path.join(BASE, "exports", n)) for n in names}
    subprocess.run([sys.executable, os.path.join(BASE, "make_report.py"), "--quiet"], check=True, capture_output=True, cwd=BASE)
    for n in names:
        pd.testing.assert_frame_equal(before[n], pd.read_csv(os.path.join(BASE, "exports", n)))
