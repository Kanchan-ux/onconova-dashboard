PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS assumptions (
    parameter_key TEXT PRIMARY KEY,
    parameter_value TEXT NOT NULL,
    value_type TEXT NOT NULL CHECK (value_type IN ('number','string','boolean','null','json')),
    source_section TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reps (
    "rep_id" TEXT PRIMARY KEY NOT NULL,
    "rep_name" TEXT,
    "region" TEXT,
    "state" TEXT,
    "indication" TEXT,
    "annual_sales_achieved_usd_m" REAL,
    "annual_sales_target_usd_m" REAL,
    "sales_Jul-2025" REAL,
    "sales_Aug-2025" REAL,
    "sales_Sep-2025" REAL,
    "sales_Oct-2025" REAL,
    "sales_Nov-2025" REAL,
    "sales_Dec-2025" REAL,
    "sales_Jan-2026" REAL,
    "sales_Feb-2026" REAL,
    "sales_Mar-2026" REAL,
    "sales_Apr-2026" REAL,
    "sales_May-2026" REAL,
    "sales_Jun-2026" REAL,
    "quota_attainment" REAL,
    "attainment_score" REAL,
    "months_hit" INTEGER,
    "consistency_score" REAL,
    "growth_percentage" REAL,
    "growth_score" REAL,
    "performance_score" REAL,
    "destination" TEXT
);

CREATE TABLE IF NOT EXISTS hcps (
    "hcp_id" TEXT PRIMARY KEY NOT NULL,
    "hcp_name" TEXT,
    "specialty" TEXT,
    "indication" TEXT,
    "state" TEXT,
    "trx_m-5" INTEGER,
    "trx_m-4" INTEGER,
    "trx_m-3" INTEGER,
    "trx_m-2" INTEGER,
    "trx_m-1" INTEGER,
    "trx_m0" INTEGER,
    "is_kol" TEXT CHECK ("is_kol" IN ('Yes', 'No')),
    "avg_trx_6m" REAL,
    "tier" TEXT,
    "trx_trend" REAL,
    "trx_risk" TEXT,
    "last_call_date" TEXT NOT NULL,
    "days_since_call" INTEGER,
    "call_gap_tier1" TEXT CHECK ("call_gap_tier1" IN ('Yes', 'No')),
    "rep_id" TEXT NOT NULL,
    FOREIGN KEY ("rep_id") REFERENCES reps("rep_id")
);

CREATE TABLE IF NOT EXISTS patients (
    "patient_id" TEXT PRIMARY KEY NOT NULL,
    "indication" TEXT,
    "payor" TEXT,
    "carepath_enrolled" TEXT CHECK ("carepath_enrolled" IN ('Yes', 'No')),
    "hcp_id" TEXT NOT NULL,
    "state" TEXT,
    "age" INTEGER CHECK ("age" BETWEEN 0 AND 120),
    "monthly_copay_usd" REAL,
    "therapy_start_date" TEXT NOT NULL,
    "last_fill_date" TEXT NOT NULL,
    "days_supply" INTEGER CHECK ("days_supply" > 0),
    "days_overdue" INTEGER,
    "monthly_revenue_usd" REAL,
    "switch_prob" REAL CHECK ("switch_prob" >= 0 AND "switch_prob" <= 1),
    "risk_level" TEXT,
    "expected_monthly_loss_usd" REAL,
    FOREIGN KEY ("hcp_id") REFERENCES hcps("hcp_id")
);
