import os
import sqlite3
import sys

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from viz import tableau_export as te  # noqa: E402


def _outcomes():
    with sqlite3.connect(te.DB_PATH) as conn:
        return te.patient_outcomes(conn, "test-key")


def test_export_carries_no_raw_identifiers_or_exact_ages():
    df = _outcomes()
    assert "patient_id" not in df.columns and "age" not in df.columns
    assert df["patient_key"].str.fullmatch(r"[0-9a-f]{16}").all()
    assert df["age_band"].str.fullmatch(r"\d+-\d+").all()


def test_one_row_per_patient_and_curves_start_at_full_survival():
    df = _outcomes()
    assert len(df) == df["patient_key"].nunique() == 250
    km = te.km_curves(df)
    first = km.sort_values("day").groupby("group_name").head(1)
    assert set(first["group_name"]) == {"Control", "Low-dosage", "High-dosage"}
    assert (first["survival_probability"] == 1.0).all()
    assert km["survival_probability"].between(0, 1).all()


def test_logrank_covers_every_pair_of_arms():
    res = te.logrank(_outcomes())
    assert len(res) == 3 and res["p_value"].between(0, 1).all()
