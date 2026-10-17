"""
roi.py  -  intervention ROI model (Python version of the Excel ROI sheet).

Run:  python roi.py        (needs generate_data.py to have been run first)
Output: output/roi.csv, output/roi_sensitivity.csv, output/roi_overlap.csv, output/roi_summary.txt

Benefit = revenue at risk x effectiveness x uptake x realisation x effective months x margin
Cost    = fixed cost + (engaged units x unit cost per month x months to LOE)
ROI     = (benefit - cost) / cost
"""
import os
import pandas as pd
import config


def build_roi(patients, hcps):
    as_of, loe = pd.Timestamp(config.AS_OF_DATE), pd.Timestamp(config.LOE_DATE)
    months_to_loe = (loe - as_of).days / config.DAYS_PER_MONTH
    effective_months = max(0.0, months_to_loe - config.RAMP_MONTHS)
    rev_per_trx = patients["monthly_revenue_usd"].sum() / hcps["trx_m0"].sum()   # bridge from HCP TRx to revenue

    # target groups
    carepath_target = (patients["risk_level"] == "High") & (patients["carepath_enrolled"] == "No")
    overdue = patients["days_overdue"] >= config.GRACE_DAYS
    refill_target = overdue & ~carepath_target             # overlap removed: those patients are credited to CarePath
    callgap_target = hcps["call_gap_tier1"] == "Yes"
    declining_target = (hcps["tier"] == "Tier 1") & (hcps["trx_risk"] == "High")

    loss = patients["expected_monthly_loss_usd"]
    trx = hcps["trx_m0"]
    targets = {
        "CarePath enrolment push": (int(carepath_target.sum()), loss[carepath_target].sum(), "Patients"),
        "Refill-reminder outreach": (int(refill_target.sum()), loss[refill_target].sum(), "Patients"),
        "Close Tier 1 call gaps": (int(callgap_target.sum()), trx[callgap_target].sum() * rev_per_trx, "HCPs"),
        "Retention plan: declining Tier 1 HCPs": (int(declining_target.sum()), trx[declining_target].sum() * rev_per_trx, "HCPs"),
    }

    rows = []
    for name, (units, at_risk, unit_type) in targets.items():
        a = config.ROI_INTERVENTIONS[name]
        effectiveness = (1 - config.CAREPATH_FACTOR) if a["effectiveness"] is None else a["effectiveness"]
        monthly_protected = at_risk * effectiveness * a["uptake"] * config.REALISATION_FACTOR
        revenue_protected = monthly_protected * effective_months
        benefit = revenue_protected * config.CONTRIBUTION_MARGIN
        engaged = units * a["uptake"]
        variable = engaged * a["unit_cost"] * months_to_loe          # we pay from day one, including ramp-up
        total_cost = variable + a["fixed_cost"]
        net = benefit - total_cost
        monthly_margin = monthly_protected * config.CONTRIBUTION_MARGIN
        rows.append({
            "intervention": name, "unit_type": unit_type, "target_units": units,
            "monthly_revenue_at_risk": at_risk, "effectiveness": effectiveness, "uptake": a["uptake"],
            "realisation": config.REALISATION_FACTOR, "monthly_revenue_protected": monthly_protected,
            "effective_months": effective_months, "revenue_protected": revenue_protected,
            "contribution_margin": config.CONTRIBUTION_MARGIN, "benefit": benefit,
            "engaged_units": engaged, "unit_cost_per_month": a["unit_cost"], "variable_cost": variable,
            "fixed_cost": a["fixed_cost"], "total_cost": total_cost, "net_benefit": net,
            "roi_multiple": net / total_cost if total_cost > 0 else None,
            "payback_months": total_cost / monthly_margin if monthly_margin > 0 else None,
        })
    roi = pd.DataFrame(rows)
    roi["rank_by_roi"] = roi["roi_multiple"].rank(ascending=False).astype(int)
    roi["rank_by_net_benefit"] = roi["net_benefit"].rank(ascending=False).astype(int)

    # sensitivity: uptake lower, realisation lower, both lower, and break-even realisation
    h = config.SENSITIVITY_HAIRCUT
    sens = []
    for _, r in roi.iterrows():
        cost_up = r["fixed_cost"] + r["variable_cost"] * (1 - h)
        sens.append({
            "intervention": r["intervention"],
            "base_roi": r["roi_multiple"],
            "uptake_lower_roi": (r["benefit"] * (1 - h) - cost_up) / cost_up,
            "realisation_lower_roi": (r["benefit"] * (1 - h) - r["total_cost"]) / r["total_cost"],
            "both_lower_roi": (r["benefit"] * (1 - h) ** 2 - cost_up) / cost_up,
            "break_even_realisation": r["total_cost"] * r["realisation"] / r["benefit"],
        })
    sens = pd.DataFrame(sens)

    # overlap between CarePath and Refill groups
    union = int((carepath_target | overdue).sum())
    overlap = pd.DataFrame([{
        "patients_in_both_carepath_and_overdue": int((carepath_target & overdue).sum()),
        "refill_target_before_removing_overlap": int(overdue.sum()),
        "distinct_patients_in_either_group": union,
        "carepath_plus_refill_targets": int(carepath_target.sum() + refill_target.sum()),
        "hcps_in_both_callgap_and_declining": int((callgap_target & declining_target).sum()),
        "combined_carepath_refill_roi": (roi["benefit"][:2].sum() - roi["total_cost"][:2].sum()) / roi["total_cost"][:2].sum(),
        "months_to_loe": months_to_loe, "revenue_per_trx": rev_per_trx,
    }])
    return roi, sens, overlap


def so_what(roi):
    top = roi.loc[roi["rank_by_roi"] == 1].iloc[0]
    return (f"Start with {top['intervention']}: ROI {top['roi_multiple']:.1f}x, payback {top['payback_months']:.1f} months, "
            f"net benefit ${top['net_benefit'] / 1e6:.1f}M.")


def main():
    patients = pd.read_csv(os.path.join(config.OUTPUT_DIR, "patients.csv"))
    hcps = pd.read_csv(os.path.join(config.OUTPUT_DIR, "hcps.csv"))
    roi, sens, overlap = build_roi(patients, hcps)
    roi.to_csv(os.path.join(config.OUTPUT_DIR, "roi.csv"), index=False)
    sens.to_csv(os.path.join(config.OUTPUT_DIR, "roi_sensitivity.csv"), index=False)
    overlap.to_csv(os.path.join(config.OUTPUT_DIR, "roi_overlap.csv"), index=False)
    text = so_what(roi)
    with open(os.path.join(config.OUTPUT_DIR, "roi_summary.txt"), "w") as f:
        f.write(text + "\n")
    print("ROI saved.")
    print(roi[["intervention", "target_units", "benefit", "total_cost", "roi_multiple", "payback_months"]].round(2).to_string(index=False))
    print(text)
    return roi, sens, overlap


if __name__ == "__main__":
    main()
