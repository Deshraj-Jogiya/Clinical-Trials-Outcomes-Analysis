-- Clinical Trial Database Schema

-- Patients table: contains baseline demographic information
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(50) PRIMARY KEY,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    baseline_vital REAL NOT NULL, -- e.g., baseline blood pressure or heart rate
    group_name VARCHAR(20) NOT NULL -- Control, Low-dosage, High-dosage
);

-- Treatment Log table: tracking daily treatments and daily vitals
CREATE TABLE IF NOT EXISTS treatment_log (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id VARCHAR(50) NOT NULL,
    dosage_mg REAL NOT NULL,
    vitals_measured REAL NOT NULL, -- vitals measured on that day
    trial_day INT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

-- Trial Outcomes table: final outcomes of the trial for survival analysis
CREATE TABLE IF NOT EXISTS trial_outcomes (
    outcome_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    survival_days INT NOT NULL,
    event_observed INT NOT NULL, -- 1 if event (death) occurred, 0 if censored (survived/dropped out)
    efficacy_score REAL NOT NULL, -- primary efficacy endpoint (tumor shrinkage % or similar)
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);
