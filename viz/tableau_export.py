"""Export the trial results as flat CSV files for the Tableau Public dashboard.

Only de-identified fields leave the database: the patient identifier becomes the same keyed pseudonym used by
etl/deidentify.py, and age is reported as a 5-year band. Writes three files to exports/:

- patient_outcomes.csv: one row per patient (arm, age band, gender, baseline vital, survival, event, efficacy, adverse event)
- km_curves.csv: Kaplan-Meier survival probability and patients at risk per arm and day
- logrank_tests.csv: pairwise log-rank statistics and p-values between arms
"""

import os
import sqlite3
import sys

import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines.statistics import pairwise_logrank_test

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from etl.deidentify import DEFAULT_KEY, age_band, pseudonym  # noqa: E402

DB_PATH = os.path.join(BASE, "data", "clinical_trials.db")
OUT_DIR = os.path.join(BASE, "exports")
# Same definition as analytics/statistical_tests.py: a systolic reading outside [105, 155] at any point during treatment
VITAL_LOW, VITAL_HIGH = 105, 155


def patient_outcomes(conn, key):
    df = pd.read_sql_query(
        """
        SELECT p.patient_id, p.age, p.gender, p.baseline_vital, p.group_name,
               o.survival_days, o.event_observed, o.efficacy_score
        FROM patients p JOIN trial_outcomes o ON p.patient_id = o.patient_id
        """,
        conn,
    )
    logs = pd.read_sql_query("SELECT patient_id, vitals_measured FROM treatment_log", conn)
    adverse = logs.groupby("patient_id")["vitals_measured"].apply(lambda v: bool(((v < VITAL_LOW) | (v > VITAL_HIGH)).any()))
    df["had_adverse_event"] = df["patient_id"].map(adverse).fillna(False).astype(int)
    df.insert(0, "patient_key", df["patient_id"].map(lambda p: pseudonym(str(p), key)))
    df["age_band"] = df["age"].map(age_band)
    df["baseline_vital"] = df["baseline_vital"].round(0)
    return df.drop(columns=["patient_id", "age"])[
        ["patient_key", "group_name", "age_band", "gender", "baseline_vital", "survival_days", "event_observed",
         "efficacy_score", "had_adverse_event"]
    ]


def km_curves(df):
    rows = []
    for arm, g in df.groupby("group_name"):
        kmf = KaplanMeierFitter().fit(g["survival_days"], g["event_observed"], label=arm)
        table = kmf.event_table.join(kmf.survival_function_)
        for day, r in table.iterrows():
            rows.append({"group_name": arm, "day": int(day), "survival_probability": round(float(r[arm]), 4),
                         "at_risk": int(r["at_risk"])})
    return pd.DataFrame(rows)


def logrank(df):
    res = pairwise_logrank_test(df["survival_days"], df["group_name"], df["event_observed"]).summary.reset_index()
    res.columns = ["arm_a", "arm_b"] + list(res.columns[2:])
    return pd.DataFrame({
        "comparison": res["arm_a"] + " vs " + res["arm_b"],
        "test_statistic": res["test_statistic"].round(2),
        "p_value": res["p"].map(lambda p: float(f"{p:.3g}")),
    })


def main():
    key = os.environ.get("CLINICAL_PSEUDONYM_KEY", DEFAULT_KEY)
    os.makedirs(OUT_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        outcomes = patient_outcomes(conn, key)
    outcomes.to_csv(os.path.join(OUT_DIR, "patient_outcomes.csv"), index=False)
    km_curves(outcomes).to_csv(os.path.join(OUT_DIR, "km_curves.csv"), index=False)
    logrank(outcomes).to_csv(os.path.join(OUT_DIR, "logrank_tests.csv"), index=False)
    print(f"Wrote {len(outcomes)} patients, Kaplan-Meier curves and log-rank tests to {OUT_DIR}")


if __name__ == "__main__":
    main()
