import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from lifelines import KaplanMeierFitter
from lifelines.statistics import pairwise_logrank_test
from scipy.stats import chi2_contingency

def load_data(db_path):
    """Loads patients, outcomes, and treatment log from SQLite database."""
    print(f"Loading data from database at {db_path}...")
    conn = sqlite3.connect(db_path)
    
    # Query to get patients and outcomes
    query_outcomes = """
        SELECT p.patient_id, p.age, p.gender, p.baseline_vital, p.group_name,
               o.survival_days, o.event_observed, o.efficacy_score
        FROM patients p
        JOIN trial_outcomes o ON p.patient_id = o.patient_id
    """
    df_outcomes = pd.read_sql_query(query_outcomes, conn)
    
    # Query to get treatment log
    query_logs = "SELECT * FROM treatment_log"
    df_logs = pd.read_sql_query(query_logs, conn)
    
    conn.close()
    return df_outcomes, df_logs

def analyze_survival(df):
    """Performs Kaplan-Meier Survival Analysis and log-rank tests."""
    print("\n=== KAPLAN-MEIER SURVIVAL ANALYSIS ===")
    
    kmf = KaplanMeierFitter()
    groups = df['group_name'].unique()
    
    # Run Pairwise Log-Rank Test to compare survival distributions
    log_rank_results = pairwise_logrank_test(df['survival_days'], df['group_name'], df['event_observed'])
    print("\nPairwise Log-Rank Test Results:")
    print(log_rank_results.summary)
    
    # Return survival analysis data for plotting or reference
    return log_rank_results

def analyze_adverse_events(df_outcomes, df_logs):
    """
    Defines adverse events using longitudinal vitals:
    Adverse event defined as experiencing severe hypertension (SBP > 155)
    or severe hypotension (SBP < 105) at any point during treatment.
    Conducts Chi-square test across groups.
    """
    print("\n=== ADVERSE EVENTS CHI-SQUARE TEST ===")
    
    # Determine which patients had an adverse event
    # Group by patient and check if any vital was outside [105, 155]
    adverse_patients = df_logs.groupby('patient_id')['vitals_measured'].apply(
        lambda x: ((x < 105) | (x > 155)).any()
    ).reset_index(name='had_adverse_event')
    
    # Merge back to outcomes to get group info
    df_analysis = df_outcomes.merge(adverse_patients, on='patient_id', how='left')
    # If a patient has no logs (died on day 1), assume no adverse event measured
    df_analysis['had_adverse_event'] = df_analysis['had_adverse_event'].fillna(False).astype(int)
    
    # Create contingency table
    contingency_table = pd.crosstab(df_analysis['group_name'], df_analysis['had_adverse_event'])
    print("\nContingency Table (Adverse Events by Treatment Group):")
    print(contingency_table)
    
    # Chi-square test
    chi2, p_val, dof, expected = chi2_contingency(contingency_table)
    print(f"\nChi-Square Statistic: {chi2:.4f}")
    print(f"p-value: {p_val:.4g}")
    print(f"Degrees of Freedom: {dof}")
    
    if p_val < 0.05:
        print("Result: Statistically significant differences in adverse event rates across treatment arms (p < 0.05).")
    else:
        print("Result: No statistically significant differences in adverse event rates across treatment arms (p >= 0.05).")
        
    return df_analysis, contingency_table

def print_clinical_significance(df_analysis):
    """Summarizes clinical endpoints, efficacy, and safety across groups."""
    print("\n=== CLINICAL SIGNIFICANCE SUMMARY ===")
    
    summary = df_analysis.groupby('group_name').agg(
        total_patients=('patient_id', 'count'),
        mean_survival_days=('survival_days', 'mean'),
        median_survival_days=('survival_days', 'median'),
        mortality_rate=('event_observed', 'mean'),
        mean_efficacy_pct=('efficacy_score', 'mean'),
        adverse_event_rate=('had_adverse_event', 'mean')
    ).reset_index()
    
    # Format percentages
    summary['mortality_rate'] = (summary['mortality_rate'] * 100).round(2).astype(str) + '%'
    summary['adverse_event_rate'] = (summary['adverse_event_rate'] * 100).round(2).astype(str) + '%'
    summary['mean_survival_days'] = summary['mean_survival_days'].round(1)
    summary['mean_efficacy_pct'] = summary['mean_efficacy_pct'].round(2)
    
    print(summary.to_string(index=False))

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'data', 'clinical_trials.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}. Please run clinical_etl.py first.")
        return
        
    df_outcomes, df_logs = load_data(db_path)
    
    # Survival analysis
    analyze_survival(df_outcomes)
    
    # Adverse events chi-sq test
    df_analysis, contingency_table = analyze_adverse_events(df_outcomes, df_logs)
    
    # Print clinical results
    print_clinical_significance(df_analysis)

if __name__ == '__main__':
    main()
