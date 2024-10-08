import os
import sqlite3
import numpy as np
import pandas as pd

def init_db(db_path, schema_path):
    """Initializes the SQLite database with the schema from schema.sql."""
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Executing schema from {schema_path}...")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    cursor.executescript(schema_sql)
    conn.commit()
    return conn

def simulate_data(num_patients=250, seed=42):
    """Simulates clinical trial data for 250 patients across 3 arms."""
    np.random.seed(seed)
    
    # 1. Generate patients
    groups = ['Control', 'Low-dosage', 'High-dosage']
    patient_groups = np.random.choice(groups, size=num_patients, p=[1/3, 1/3, 1/3])
    
    patients_list = []
    outcomes_list = []
    treatment_logs_list = []
    
    study_duration = 365 # 1 year study duration limit
    
    for i in range(num_patients):
        patient_id = f"PT-{i+1:03d}"
        group = patient_groups[i]
        
        # Demographics
        age = int(np.clip(np.random.normal(64, 8), 40, 85))
        gender = np.random.choice(['Male', 'Female'], p=[0.52, 0.48])
        
        # Baseline vital: Systolic Blood Pressure (mmHg)
        # Normal distribution with mean 135 and std 12
        baseline_vital = np.random.normal(135, 12)
        
        patients_list.append({
            'patient_id': patient_id,
            'age': age,
            'gender': gender,
            'baseline_vital': round(baseline_vital, 2),
            'group_name': group
        })
        
        # 2. Simulate outcomes based on group
        # Efficacy score: tumor shrinkage percentage
        if group == 'Control':
            # Placebo: minimal change or disease progression (negative shrinkage = growth)
            efficacy_score = np.random.normal(2.0, 8.0)
            # Higher hazard rate -> shorter survival
            survival_days = np.random.exponential(150)
            dosage_mg = 0.0
        elif group == 'Low-dosage':
            # Moderate shrinkage
            efficacy_score = np.random.normal(28.0, 12.0)
            survival_days = np.random.exponential(290)
            dosage_mg = 50.0
        else: # High-dosage
            # High shrinkage
            efficacy_score = np.random.normal(58.0, 15.0)
            survival_days = np.random.exponential(450)
            dosage_mg = 150.0
            
        # Clip efficacy score (max 100% shrinkage, min -50% progression)
        efficacy_score = np.clip(efficacy_score, -50.0, 100.0)
        
        # Cap survival days at study duration (365 days)
        # If survival time exceeds 365, the event is censored (event_observed = 0)
        if survival_days >= study_duration:
            survival_days = study_duration
            event_observed = 0
        else:
            # Let's add a random censoring probability (e.g. 15% drop-out rate)
            if np.random.random() < 0.15:
                # Censored due to drop-out before event
                survival_days = np.random.uniform(30, survival_days)
                event_observed = 0
            else:
                event_observed = 1
                
        # Ensure survival days is at least 1
        survival_days = max(1, int(survival_days))
        
        outcome_id = f"OC-{i+1:03d}"
        outcomes_list.append({
            'outcome_id': outcome_id,
            'patient_id': patient_id,
            'survival_days': survival_days,
            'event_observed': event_observed,
            'efficacy_score': round(efficacy_score, 2)
        })
        
        # 3. Simulate treatment logs / longitudinal vitals
        # Standard follow-up schedule: Day 1, then every 30 days
        follow_up_days = [1, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
        
        for day in follow_up_days:
            if day > survival_days:
                break
                
            # Physiological response:
            # Active drug (Low/High dosage) reduces blood pressure (vitals) over time
            # Placebo (Control) SBP stays high or increases slightly due to progression
            time_factor = min(1.0, day / 180.0)
            if group == 'Control':
                vital_drift = np.random.normal(2.0, 4.0) * time_factor
            elif group == 'Low-dosage':
                vital_drift = np.random.normal(-8.0, 5.0) * time_factor
            else: # High-dosage
                vital_drift = np.random.normal(-15.0, 6.0) * time_factor
                
            vital_measured = baseline_vital + vital_drift + np.random.normal(0, 3.0)
            
            treatment_logs_list.append({
                'patient_id': patient_id,
                'dosage_mg': dosage_mg,
                'vitals_measured': round(vital_measured, 2),
                'trial_day': day
            })
            
    df_patients = pd.DataFrame(patients_list)
    df_outcomes = pd.DataFrame(outcomes_list)
    df_logs = pd.DataFrame(treatment_logs_list)
    
    return df_patients, df_logs, df_outcomes

def save_to_sqlite(conn, df_patients, df_logs, df_outcomes):
    """Saves dataframes to SQLite tables."""
    print("Writing data to SQLite database...")
    # Write to SQL tables
    df_patients.to_sql('patients', conn, if_exists='append', index=False)
    df_logs.to_sql('treatment_log', conn, if_exists='append', index=False)
    df_outcomes.to_sql('trial_outcomes', conn, if_exists='append', index=False)
    print("Database populate successful!")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'data', 'clinical_trials.db')
    schema_path = os.path.join(base_dir, 'db', 'schema.sql')
    
    # Check if database already exists and delete to ensure clean run
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing database for a fresh run.")
        
    conn = init_db(db_path, schema_path)
    
    df_patients, df_logs, df_outcomes = simulate_data(num_patients=250, seed=42)
    
    save_to_sqlite(conn, df_patients, df_logs, df_outcomes)
    
    # Print summary statistics to verify simulation sanity
    print("\n--- Simulation Summary ---")
    print(f"Total Patients: {len(df_patients)}")
    print(df_patients['group_name'].value_counts())
    print("\nAverage Survival Days by Group:")
    merged = df_patients.merge(df_outcomes, on='patient_id')
    print(merged.groupby('group_name')['survival_days'].mean())
    print("\nMortality (Event) Rates by Group:")
    print(merged.groupby('group_name')['event_observed'].mean())
    print("\nAverage Efficacy Score (Tumor Shrinkage %) by Group:")
    print(merged.groupby('group_name')['efficacy_score'].mean())
    
    conn.close()

if __name__ == '__main__':
    main()
