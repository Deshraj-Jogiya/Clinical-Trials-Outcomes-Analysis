import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etl.deidentify import age_band, deidentify, pseudonym  # noqa: E402


def test_identifier_and_exact_age_are_removed():
    raw = pd.DataFrame({"patient_id": ["PT-001", "PT-002"], "age": [64, 71], "gender": ["Male", "Female"],
                        "baseline_vital": [134.6, 120.2], "group_name": ["Control", "High-dosage"]})
    out = deidentify(raw, "k")
    assert "patient_id" not in out and "age" not in out
    assert not out["patient_key"].str.contains("PT-").any()
    assert list(out["age_band"]) == ["60-64", "70-74"]


def test_pseudonyms_are_stable_per_key_and_differ_across_keys():
    assert pseudonym("PT-001", "k") == pseudonym("PT-001", "k")
    assert pseudonym("PT-001", "k") != pseudonym("PT-001", "other")
    assert pseudonym("PT-001", "k") != pseudonym("PT-002", "k")


def test_age_band_edges():
    assert age_band(40) == "40-44" and age_band(44) == "40-44" and age_band(85) == "85-89"
