-- Clinical Trial Analytical Queries

-- 1. Average baseline and treatment vitals by treatment group
-- Helps verify if baseline vitals were balanced and how vitals changed during treatment.
SELECT 
    p.group_name,
    COUNT(DISTINCT p.patient_id) AS patient_count,
    ROUND(AVG(p.baseline_vital), 2) AS avg_baseline_vital,
    ROUND(AVG(tl.vitals_measured), 2) AS avg_treatment_vital,
    ROUND(AVG(tl.vitals_measured) - AVG(p.baseline_vital), 2) AS avg_vital_change
FROM patients p
LEFT JOIN treatment_log tl ON p.patient_id = tl.patient_id
GROUP BY p.group_name;


-- 2. Average dosage and survival time by treatment group
-- Examines the association between dosage levels, efficacy, and survival.
SELECT 
    p.group_name,
    ROUND(AVG(tl.dosage_mg), 2) AS avg_dosage_administered_mg,
    ROUND(AVG(o.survival_days), 1) AS avg_survival_days,
    ROUND(AVG(o.efficacy_score), 2) AS avg_efficacy_score
FROM patients p
JOIN trial_outcomes o ON p.patient_id = o.patient_id
LEFT JOIN treatment_log tl ON p.patient_id = tl.patient_id
GROUP BY p.group_name;


-- 3. Event (mortality) rates and censor rates by treatment group and gender
-- Analyzes subgroup outcomes and event rates.
SELECT 
    p.group_name,
    p.gender,
    COUNT(p.patient_id) AS total_patients,
    SUM(o.event_observed) AS event_deaths,
    ROUND(100.0 * SUM(o.event_observed) / COUNT(p.patient_id), 2) AS mortality_rate_pct,
    COUNT(p.patient_id) - SUM(o.event_observed) AS censored_count,
    ROUND(100.0 * (COUNT(p.patient_id) - SUM(o.event_observed)) / COUNT(p.patient_id), 2) AS censor_rate_pct
FROM patients p
JOIN trial_outcomes o ON p.patient_id = o.patient_id
GROUP BY p.group_name, p.gender
ORDER BY p.group_name, p.gender;


-- 4. Dosage correlation with survival time for patients who completed treatment logs
-- Calculates Pearson-like correlation metrics using SQLite aggregation (simplified covariance analysis).
SELECT 
    p.group_name,
    ROUND(AVG(tl.dosage_mg * o.survival_days) - AVG(tl.dosage_mg) * AVG(o.survival_days), 4) AS covariance_dosage_survival,
    ROUND(AVG(o.efficacy_score), 2) AS mean_efficacy
FROM patients p
JOIN trial_outcomes o ON p.patient_id = o.patient_id
JOIN treatment_log tl ON p.patient_id = tl.patient_id
GROUP BY p.group_name;


-- 5. Outlier Detection: Patients with high baseline vitals but below-average survival
-- Identifies high-risk patients who might have had poor tolerance.
WITH GroupAverages AS (
    SELECT 
        group_name,
        AVG(survival_days) AS group_avg_survival
    FROM trial_outcomes o
    JOIN patients p ON o.patient_id = p.patient_id
    GROUP BY group_name
)
SELECT 
    p.patient_id,
    p.group_name,
    p.age,
    p.baseline_vital,
    o.survival_days,
    ROUND(ga.group_avg_survival, 1) AS group_avg_survival,
    o.event_observed
FROM patients p
JOIN trial_outcomes o ON p.patient_id = o.patient_id
JOIN GroupAverages ga ON p.group_name = ga.group_name
WHERE o.survival_days < ga.group_avg_survival * 0.7
  AND p.baseline_vital > (SELECT AVG(baseline_vital) FROM patients)
ORDER BY o.survival_days ASC;


-- 6. Longitudinal patient summary
-- Pulls a complete summary of baseline, treatment, and outcome metrics per patient.
SELECT 
    p.patient_id,
    p.group_name,
    p.age,
    p.gender,
    ROUND(p.baseline_vital, 2) AS baseline_vital,
    COUNT(tl.record_id) AS total_treatment_days,
    ROUND(AVG(tl.vitals_measured), 2) AS mean_treatment_vital,
    o.survival_days,
    o.event_observed,
    ROUND(o.efficacy_score, 2) AS efficacy_score
FROM patients p
JOIN trial_outcomes o ON p.patient_id = o.patient_id
LEFT JOIN treatment_log tl ON p.patient_id = tl.patient_id
GROUP BY p.patient_id
ORDER BY o.survival_days DESC
LIMIT 10;
