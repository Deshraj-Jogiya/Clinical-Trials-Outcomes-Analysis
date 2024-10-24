"""De-identified analytics copy of the patient table.

Analysis and sharing should not need the raw patient identifier or exact age, so this builds `patients_deidentified`: the identifier is
replaced by a keyed SHA-256 pseudonym (stable across runs with the same key, not reversible without it) and age is generalised into
5-year bands. The raw `patients` table stays the system of record.
"""

import hashlib
import hmac
import os
import sqlite3

import pandas as pd

DEFAULT_KEY = "local-development-key"  # set CLINICAL_PSEUDONYM_KEY outside development


def pseudonym(patient_id: str, key: str) -> str:
    return hmac.new(key.encode(), patient_id.encode(), hashlib.sha256).hexdigest()[:16]


def age_band(age: int) -> str:
    low = (int(age) // 5) * 5
    return f"{low}-{low + 4}"


def deidentify(patients: pd.DataFrame, key: str) -> pd.DataFrame:
    out = pd.DataFrame({
        "patient_key": patients["patient_id"].map(lambda p: pseudonym(p, key)),
        "age_band": patients["age"].map(age_band),
        "gender": patients["gender"],
        "group_name": patients["group_name"],
        "baseline_vital": patients["baseline_vital"].round(0),
    })
    return out


def build(conn: sqlite3.Connection, key: str | None = None) -> int:
    key = key or os.environ.get("CLINICAL_PSEUDONYM_KEY", DEFAULT_KEY)
    patients = pd.read_sql_query("SELECT patient_id, age, gender, baseline_vital, group_name FROM patients", conn)
    deidentify(patients, key).to_sql("patients_deidentified", conn, if_exists="replace", index=False)
    return len(patients)


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with sqlite3.connect(os.path.join(base, "data", "clinical_trials.db")) as c:
        print(f"De-identified {build(c)} patients into patients_deidentified")
