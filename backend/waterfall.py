"""
waterfall.py  -  revenue-erosion waterfall (Python version of the Excel WaterFall sheet).

Run:  python waterfall.py        (needs generate_data.py to have been run first)
Output: output/waterfall.csv  (all three scenarios, one row per step)

Logic: start from annualised revenue, then apply each driver in turn to the revenue that is LEFT
(so drivers are never double counted). Patient switching comes from the Patients data, not a typed number.
"""
import os
import pandas as pd
import config


def build_waterfall(patients):
    monthly_revenue = patients["monthly_revenue_usd"].sum()
    baseline = monthly_revenue * 12
    switching_pct = patients["expected_monthly_loss_usd"].sum() / monthly_revenue   # derived from data

    rows = []
    for scenario, drivers in config.WATERFALL.items():
        remaining = baseline
        rows.append({"scenario": scenario, "step": "Baseline Revenue", "pct": None, "loss": 0.0, "revenue": remaining})
        steps = [(config.WATERFALL_LABELS[k], v) for k, v in drivers.items()] + [("Patient Switching", switching_pct)]
        for label, pct in steps:
            loss = remaining * pct            # each driver hits what is left after the previous one
            remaining = remaining - loss
            rows.append({"scenario": scenario, "step": label, "pct": pct, "loss": loss, "revenue": remaining})
        rows.append({"scenario": scenario, "step": "Post-LOE Revenue", "pct": None, "loss": 0.0, "revenue": remaining})
    return pd.DataFrame(rows)


def main():
    patients = pd.read_csv(os.path.join(config.OUTPUT_DIR, "patients.csv"))
    wf = build_waterfall(patients)
    wf.to_csv(os.path.join(config.OUTPUT_DIR, "waterfall.csv"), index=False)
    final = wf[wf["step"] == "Post-LOE Revenue"].set_index("scenario")["revenue"] / 1e6
    print("Waterfall saved. Post-LOE revenue ($M):", final.round(1).to_dict())
    return wf


if __name__ == "__main__":
    main()
