# Clinical Trials Patient Outcomes Analysis

[![ci](https://github.com/Deshraj-Jogiya/Clinical-Trials-Outcomes-Analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/Deshraj-Jogiya/Clinical-Trials-Outcomes-Analysis/actions/workflows/ci.yml) ![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)

A clinical-trial analysis pipeline on simulated data: SQL and Python ingestion of patient survival, vitals and dosage records, Kaplan-Meier
survival curves and log-rank tests across three treatment arms, and a de-identified copy of the patient table for analysis.

## Highlights

- **Ingestion and cleaning** of patient survival, vital signs and dosage records into SQLite.
- **Survival analysis:** Kaplan-Meier curves and log-rank test statistics (SciPy) compare treatment efficacy across 3 cohorts.
- **De-identification:** `etl/deidentify.py` builds `patients_deidentified`, replacing patient IDs with keyed SHA-256 pseudonyms and exact
  ages with 5-year bands; covered by `tests/test_deidentify.py`.
- **Reporting:** an outcomes dashboard (matplotlib preview below).

## Architecture

```mermaid
flowchart LR
    E[etl/clinical_etl.py<br/>250 simulated patients] --> DB[(SQLite)]
    DB --> D[etl/deidentify.py<br/>pseudonyms, age bands] --> DB
    DB --> S[analytics/statistical_tests.py<br/>Kaplan-Meier, log-rank]
    S --> V[viz/dashboard_export.py]
```

![Dashboard preview](viz/matplotlib_dashboard_preview.png)

## Stack

Python, SQL, SQLite, pandas, SciPy, Matplotlib, pytest, GitHub Actions.

## Run it

```bash
pip install -r requirements.txt
python etl/clinical_etl.py
python etl/deidentify.py
python analytics/statistical_tests.py
python viz/dashboard_export.py
python -m pytest tests/ -v
```

## Data

The 250 patient records are simulated (seeded); no real patient data is used.
