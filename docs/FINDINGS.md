# Findings

Measured results from this pipeline. All 250 patient records are simulated with a fixed seed by `etl/clinical_etl.py`; no real
patient data is used.

## Does a higher dosage change survival?

**How it was tested.** Kaplan-Meier survival curves were fitted for the three treatment arms over 365 days, and every pair of arms
was compared with a log-rank test.

| Arm | Survival at day 365 | Median survival (days) | Mortality |
|---|---|---|---|
| Control | 0.1582 | 118.0 | 69.47% |
| Low-dosage | 0.3327 | 175.0 | 60.0% |
| High-dosage | 0.5320 | 295.5 | 42.5% |

| Log-rank comparison | Test statistic | p-value |
|---|---|---|
| Control vs High-dosage | 23.78 | 1.08e-06 |
| Control vs Low-dosage | 7.04 | 0.00796 |
| High-dosage vs Low-dosage | 5.11 | 0.0238 |

**Conclusion.** Survival differs between every pair of arms at p < 0.05, and the high-dosage arm survives longest.

**Source.** `exports/km_curves.csv` and `exports/logrank_tests.csv` (written by the pipeline); median survival and mortality from the
"Clinical significance summary" printed by `analytics/statistical_tests.py`.

**Skills shown.** lifelines (KaplanMeierFitter, pairwise log-rank test), pandas, SQL on SQLite.

## Does the high dosage bring more adverse events?

**How it was tested.** Adverse events per arm were compared with a chi-square test of independence.

| Arm | Adverse event rate |
|---|---|
| Control | 8.42% |
| Low-dosage | 10.67% |
| High-dosage | 23.75% |

| Chi-square statistic | p-value | Degrees of freedom |
|---|---|---|
| 9.4644 | 0.008807 | 2 |

**Conclusion.** Adverse-event rates differ significantly across arms (p < 0.05): the arm that survives longest also has the highest
adverse-event rate, so the survival gain comes with a safety cost to weigh.

**Source.** Output of `analytics/statistical_tests.py` ("Adverse events chi-square test" and "Clinical significance summary").

**Skills shown.** SciPy (`chi2_contingency`), pandas, SQL on SQLite.

## Should the report refresh run as one process or as separate scripts?

**How it was tested.** The four refresh steps (ETL, statistics, Tableau extracts, dashboard) were timed as separate scripts and as one
process (`python make_report.py --benchmark`, best of 3). A test checks that both ways write identical extracts.

| Separate scripts | One process | Time saved |
|---|---|---|
| 15.45 s | 6.25 s | 0.5954 |

**Decision.** `make_report.py` refreshes the whole report in one process; `tests/test_make_report.py` asserts the extracts are the
same as the separate scripts produce.

**Source.** `exports/report_refresh_benchmark.csv`, `tests/test_make_report.py`.

**Skills shown.** Python, pandas, pytest, Matplotlib, Tableau extracts.
