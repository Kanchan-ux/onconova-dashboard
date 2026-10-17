"""
checks.py  -  proves the Python data is trustworthy.

Run:  python checks.py       (after generate_data.py, waterfall.py and roi.py)

PART A compares the Python results with the numbers from my Excel model (the "answer key").
          The key is calibrated to SEED 42; with another seed small differences are normal random variation.
PART B runs internal consistency checks (the same kind of OK/CHECK cells I built in Excel). These must ALWAYS pass.
Every line prints OK or CHECK. A CHECK means something needs investigating.
"""
import os
import sys
import pandas as pd
import config

out = lambda name: os.path.join(config.OUTPUT_DIR, name)
reps, hcps, patients = pd.read_csv(out("reps.csv")), pd.read_csv(out("hcps.csv")), pd.read_csv(out("patients.csv"))
waterfall, roi = pd.read_csv(out("waterfall.csv")), pd.read_csv(out("roi.csv"))
overlap = pd.read_csv(out("roi_overlap.csv")).iloc[0]

as_of = pd.Timestamp(config.AS_OF_DATE)
failures = 0          # internal consistency failures (these must always be zero)
key_differences = 0   # differences from the Excel answer key (expected if SEED or sizes are changed)


def report(label, ok, detail=""):
    global failures
    failures += 0 if ok else 1
    print(f"  {'OK   ' if ok else 'CHECK'}  {label:<58}{detail}")


# ------------------------------------------------------------------ PART A: Excel answer key
python_values = {
    "Reps": len(reps), "HCPs": len(hcps), "Patients": len(patients),
    "Monthly revenue ($)": patients["monthly_revenue_usd"].sum(),
    "Tier 1 HCPs": (hcps["tier"] == "Tier 1").sum(), "Tier 2 HCPs": (hcps["tier"] == "Tier 2").sum(),
    "Tier 3 HCPs": (hcps["tier"] == "Tier 3").sum(),
    "High-risk patients": (patients["risk_level"] == "High").sum(),
    "Expected monthly loss ($)": patients["expected_monthly_loss_usd"].sum(),
    "High-risk patients not in CarePath": ((patients["risk_level"] == "High") & (patients["carepath_enrolled"] == "No")).sum(),
    "Patients overdue >= GraceDays": (patients["days_overdue"] >= config.GRACE_DAYS).sum(),
    "High-risk HCPs (Tier 1, falling)": (hcps["trx_risk"] == "High").sum(),
    "Tier 1 call gaps": (hcps["call_gap_tier1"] == "Yes").sum(),
    "Rep exits": (reps["destination"] == "Exit / Separation").sum(),
    "Reps retained on Onconova": (reps["destination"] == "Retain on Onconova").sum(),
    "Revenue per TRx ($)": patients["monthly_revenue_usd"].sum() / hcps["trx_m0"].sum(),
    "Post-LOE revenue, Base ($)": waterfall[(waterfall["scenario"] == "Base") & (waterfall["step"] == "Post-LOE Revenue")]["revenue"].iloc[0],
}
roi_by_name = roi.set_index("intervention")["roi_multiple"]
python_values.update({
    "ROI CarePath (x)": roi_by_name["CarePath enrolment push"], "ROI Refill (x)": roi_by_name["Refill-reminder outreach"],
    "ROI Call gaps (x)": roi_by_name["Close Tier 1 call gaps"], "ROI HCP retention (x)": roi_by_name["Retention plan: declining Tier 1 HCPs"],
})

print("\nPART A - Python vs Excel answer key")
print(f"  {'':5}  {'Metric':<42}{'Excel':>16}{'Python':>16}{'Diff':>8}{'Allowed':>9}")
for name, (excel_value, tolerance) in config.EXCEL_KEY.items():
    py = float(python_values[name])
    diff = (py - excel_value) / excel_value
    ok = abs(diff) <= tolerance + 1e-12
    key_differences += 0 if ok else 1
    print(f"  {'OK   ' if ok else 'CHECK'}  {name:<42}{excel_value:>16,.1f}{py:>16,.1f}{diff:>8.1%}{tolerance:>9.0%}")

# ------------------------------------------------------------------ PART B: internal consistency
print("\nPART B - internal consistency checks")
print(" Sizes and IDs")
report("Row counts match config", (len(reps), len(hcps), len(patients)) == (config.NUM_REPS, config.NUM_HCPS, config.NUM_PATIENTS))
report("IDs are unique", reps.rep_id.is_unique and hcps.hcp_id.is_unique and patients.patient_id.is_unique)
report("ID formats match Excel (REP001, HCP00001, PAT000001)",
       reps.rep_id[0] == "REP001" and hcps.hcp_id[0] == "HCP00001" and patients.patient_id[0] == "PAT000001")
report("Every patient's HCP exists", patients.hcp_id.isin(hcps.hcp_id).all())
report("Every HCP's rep exists", hcps.rep_id.isin(reps.rep_id).all())

print(" HCP and patient link (one source of truth)")
patients_per_hcp = patients.groupby("hcp_id").size().reindex(hcps.hcp_id).fillna(0).astype(int).to_numpy()
report("Each HCP's current TRx equals its number of patients", (hcps["trx_m0"].to_numpy() == patients_per_hcp).all())
report("Sum of HCP current TRx equals number of patients", hcps["trx_m0"].sum() == len(patients), f"{hcps['trx_m0'].sum():,}")
trx_cols = [c for c in hcps.columns if c.startswith("trx_m")]
report("TRx are whole numbers and not negative", ((hcps[trx_cols] % 1 == 0).all().all()) and (hcps[trx_cols] >= 0).all().all())
tier1_share = patients.hcp_id.isin(hcps[hcps.tier == "Tier 1"].hcp_id).mean()
report("Tier 1 HCPs hold 70-85% of patients", 0.70 <= tier1_share <= 0.85, f"{tier1_share:.1%}")
report("Patient indication matches its HCP's indication",
       (patients.indication.to_numpy() == hcps.set_index("hcp_id").indication.reindex(patients.hcp_id).to_numpy()).all())

print(" Patient dates and risk")
fill, start = pd.to_datetime(patients.last_fill_date), pd.to_datetime(patients.therapy_start_date)
report("Last fill is on or before the snapshot date", (fill <= as_of).all())
report("Therapy start is on or before last fill", (start <= fill).all())
report("Therapy start is not before launch", (start >= pd.Timestamp(config.FIRST_MONTH)).all())
report("Days overdue are not negative", (patients.days_overdue >= 0).all())
report("Switch probability is between 0 and the cap", patients.switch_prob.between(0, config.SWITCH_CAP).all())
report("High + Medium + Low risk patients = all patients", patients.risk_level.isin(["High", "Medium", "Low"]).all())
report("Tier 1 + 2 + 3 HCPs = all HCPs", hcps.tier.isin(["Tier 1", "Tier 2", "Tier 3"]).all())

print(" Reps")
month_cols = [c for c in reps.columns if c.startswith("sales_")]
report("Monthly sales add up to annual sales for every rep",
       ((reps[month_cols].sum(axis=1) - reps.annual_sales_achieved_usd_m).abs() < 1e-6).all())
expected_pool = patients.monthly_revenue_usd.sum() * 12 * config.REP_REVENUE_SHARE / 1e6
report("Rep sales total = revenue share x annual revenue", abs(reps.annual_sales_achieved_usd_m.sum() - expected_pool) < 1e-6,
       f"${reps.annual_sales_achieved_usd_m.sum():,.1f}M")
report("Rep destinations add up to total reps", reps.destination.notna().all())
report("No rep exits with a high score (rule is enforced)",
       (reps[reps.destination == "Exit / Separation"].performance_score < config.EXIT_BELOW).all())

print(" Waterfall")
ok = True
for scenario, g in waterfall.groupby("scenario", sort=False):
    start_rev = g[g.step == "Baseline Revenue"].revenue.iloc[0]
    end_rev = g[g.step == "Post-LOE Revenue"].revenue.iloc[0]
    ok = ok and abs(start_rev - g.loss.sum() - end_rev) < 1
report("Baseline minus all losses = post-LOE revenue (every scenario)", ok)
end = waterfall[waterfall.step == "Post-LOE Revenue"].set_index("scenario").revenue
report("Bear < Base < Bull", end["Bear"] < end["Base"] < end["Bull"])

print(" ROI sanity checks")
report("1. Target populations are positive and within the population",
       ((roi.target_units > 0) & (roi.target_units[:2] <= len(patients)).reindex(roi.index, fill_value=True)).all()
       and (roi.target_units[2:] <= len(hcps)).all())
report("2. Revenue at risk does not exceed the source total",
       roi.monthly_revenue_at_risk[:2].sum() <= patients.expected_monthly_loss_usd.sum() + 1
       and (roi.monthly_revenue_at_risk[2:] <= patients.monthly_revenue_usd.sum()).all())
report("3. Revenue protected is at most revenue at risk x months",
       (roi.revenue_protected <= roi.monthly_revenue_at_risk * roi.effective_months + 1e-6).all())
report("4. Costs are positive", (roi.total_cost > 0).all())
report("5. Effective months are not negative", (roi.effective_months >= 0).all())
report("6. ROI and payback calculate (no errors)", roi.roi_multiple.notna().all() and roi.payback_months.notna().all())
report("7. Overlap flagged and CarePath + Refill count each patient once",
       overlap.carepath_plus_refill_targets == overlap.distinct_patients_in_either_group,
       f"{int(overlap.patients_in_both_carepath_and_overdue):,} patients credited to CarePath")

print("\nSUMMARY")
print("  Internal consistency checks:", "ALL PASSED" if failures == 0 else f"{failures} FAILED - investigate before using the data")
print("  Excel answer-key comparison:", "ALL WITHIN TOLERANCE" if key_differences == 0 else
      f"{key_differences} outside tolerance (expected if you changed SEED or sizes: the key is calibrated to SEED 42)")
sys.exit(0 if failures == 0 else 1)
