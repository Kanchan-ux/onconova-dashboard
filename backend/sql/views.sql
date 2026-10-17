-- Onconova STEP 2A: derived-field views (SQLite)
-- Source of business-rule values: assumptions table populated from config.py.
-- PostgreSQL note: SQLite julianday() should be replaced with date subtraction/EXTRACT;
-- SQLite scalar CAST/subqueries work in PostgreSQL with minor syntax adjustments.

DROP VIEW IF EXISTS v_patients_recomputed;
CREATE VIEW v_patients_recomputed AS
WITH params AS (
  SELECT
    CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='AS_OF_DATE') AS TEXT) AS as_of_date,
    CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='SWITCH_BASE_PROB') AS REAL) AS switch_base,
    CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='SWITCH_PER_OVERDUE_DAY') AS REAL) AS switch_per_day,
    CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='SWITCH_CAP') AS REAL) AS switch_cap,
    CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='CAREPATH_FACTOR') AS REAL) AS carepath_factor,
    CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='RISK_HIGH_CUT') AS REAL) AS risk_high_cut,
    CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='RISK_MEDIUM_CUT') AS REAL) AS risk_medium_cut
), derived AS (
  SELECT p.*,
         MAX(0, CAST(julianday((SELECT as_of_date FROM params)) - julianday(p.last_fill_date) AS INTEGER) - p.days_supply) AS calc_days_overdue,
         CASE p.indication
           WHEN 'NSCLC' THEN CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='PRICE_PER_MONTH.NSCLC') AS REAL)
           WHEN 'CRC' THEN CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='PRICE_PER_MONTH.CRC') AS REAL)
           WHEN 'mBC' THEN CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='PRICE_PER_MONTH.mBC') AS REAL)
           WHEN 'Melanoma' THEN CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='PRICE_PER_MONTH.Melanoma') AS REAL)
           ELSE NULL END AS calc_monthly_revenue_usd,
         CASE WHEN MIN((SELECT switch_cap FROM params),
                       (SELECT switch_base FROM params) +
                       (SELECT switch_per_day FROM params) *
                       MAX(0, CAST(julianday((SELECT as_of_date FROM params)) - julianday(p.last_fill_date) AS INTEGER) - p.days_supply)
                      ) < 0 THEN 0
              ELSE MIN((SELECT switch_cap FROM params),
                       (SELECT switch_base FROM params) +
                       (SELECT switch_per_day FROM params) *
                       MAX(0, CAST(julianday((SELECT as_of_date FROM params)) - julianday(p.last_fill_date) AS INTEGER) - p.days_supply)
                      )
         END AS prob_before_carepath
  FROM patients p
)
SELECT d.*,
       CASE WHEN d.carepath_enrolled='Yes'
            THEN d.prob_before_carepath * (SELECT carepath_factor FROM params)
            ELSE d.prob_before_carepath END AS calc_switch_prob,
       CASE WHEN (CASE WHEN d.carepath_enrolled='Yes'
                       THEN d.prob_before_carepath * (SELECT carepath_factor FROM params)
                       ELSE d.prob_before_carepath END) >= (SELECT risk_high_cut FROM params) THEN 'High'
            WHEN (CASE WHEN d.carepath_enrolled='Yes'
                       THEN d.prob_before_carepath * (SELECT carepath_factor FROM params)
                       ELSE d.prob_before_carepath END) >= (SELECT risk_medium_cut FROM params) THEN 'Medium'
            ELSE 'Low' END AS calc_risk_level,
       d.calc_monthly_revenue_usd *
       (CASE WHEN d.carepath_enrolled='Yes'
             THEN d.prob_before_carepath * (SELECT carepath_factor FROM params)
             ELSE d.prob_before_carepath END) AS calc_expected_monthly_loss_usd
FROM derived d;

DROP VIEW IF EXISTS v_hcps_recomputed;
CREATE VIEW v_hcps_recomputed AS
WITH params AS (
 SELECT
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='HCP_TIER1_CUT') AS REAL) AS tier1_cut,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='HCP_TIER2_CUT') AS REAL) AS tier2_cut,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='HCP_HIGH_CUT') AS REAL) AS high_cut,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='HCP_MED_CUT') AS REAL) AS med_cut,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='AS_OF_DATE') AS TEXT) AS as_of_date,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='CALL_GAP_DAYS') AS INTEGER) AS call_gap_days
), avgd AS (
 SELECT h.*,
        (COALESCE(h."trx_m-5",0)+COALESCE(h."trx_m-4",0)+COALESCE(h."trx_m-3",0)+
         COALESCE(h."trx_m-2",0)+COALESCE(h."trx_m-1",0)+COALESCE(h."trx_m0",0))/6.0 AS calc_avg_trx_6m,
        (COALESCE(h."trx_m-5",0)+COALESCE(h."trx_m-4",0)+COALESCE(h."trx_m-3",0))/3.0 AS first3_avg,
        (COALESCE(h."trx_m-2",0)+COALESCE(h."trx_m-1",0)+COALESCE(h."trx_m0",0))/3.0 AS last3_avg,
        CAST(julianday((SELECT as_of_date FROM params))-julianday(h.last_call_date) AS INTEGER) AS calc_days_since_call
 FROM hcps h
), trends AS (
 SELECT a.*,
        CASE WHEN first3_avg>0 THEN last3_avg/first3_avg-1.0 ELSE 0.0 END AS calc_trx_trend
 FROM avgd a
)
SELECT t.*,
       CASE WHEN calc_avg_trx_6m >= (SELECT tier1_cut FROM params) THEN 'Tier 1'
            WHEN calc_avg_trx_6m >= (SELECT tier2_cut FROM params) THEN 'Tier 2'
            ELSE 'Tier 3' END AS calc_tier,
       CASE WHEN calc_trx_trend <= (SELECT high_cut FROM params)
              THEN CASE WHEN (CASE WHEN calc_avg_trx_6m >= (SELECT tier1_cut FROM params) THEN 'Tier 1'
                                   WHEN calc_avg_trx_6m >= (SELECT tier2_cut FROM params) THEN 'Tier 2' ELSE 'Tier 3' END)='Tier 1'
                        THEN 'High' ELSE 'Medium' END
            WHEN calc_trx_trend <= (SELECT med_cut FROM params) THEN 'Medium'
            ELSE 'Low' END AS calc_trx_risk,
       CASE WHEN (CASE WHEN calc_avg_trx_6m >= (SELECT tier1_cut FROM params) THEN 'Tier 1'
                       WHEN calc_avg_trx_6m >= (SELECT tier2_cut FROM params) THEN 'Tier 2' ELSE 'Tier 3' END)='Tier 1'
                  AND CAST(julianday((SELECT as_of_date FROM params))-julianday(last_call_date) AS INTEGER) > (SELECT call_gap_days FROM params)
            THEN 'Yes' ELSE 'No' END AS calc_call_gap_tier1
FROM trends t;

DROP VIEW IF EXISTS v_reps_recomputed;
CREATE VIEW v_reps_recomputed AS
WITH params AS (
 SELECT
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='ATTAINMENT_FULL_MARKS') AS REAL) AS attainment_full_marks,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='HIT_PCT') AS REAL) AS hit_pct,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='GROWTH_SCORE_CENTRE') AS REAL) AS growth_score_centre,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='GROWTH_SCORE_SCALE') AS REAL) AS growth_score_scale,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='SCORE_WEIGHTS.attainment') AS REAL) AS weight_attainment,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='SCORE_WEIGHTS.consistency') AS REAL) AS weight_consistency,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='SCORE_WEIGHTS.growth') AS REAL) AS weight_growth,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='EXIT_BELOW') AS REAL) AS exit_below,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='RETAIN_MIN') AS REAL) AS retain_min,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='PIPELINE_MIN') AS REAL) AS pipeline_min,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='MARKET_ACCESS_MIN') AS REAL) AS market_access_min,
  CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='QUOTA_FLOOR') AS REAL) AS quota_floor,
  (SELECT parameter_value FROM assumptions WHERE parameter_key='RETAIN_INDICATIONS') AS retain_indications_json
), raw_scores AS (
 SELECT r.*,
        r.annual_sales_achieved_usd_m / NULLIF(r.annual_sales_target_usd_m,0) AS calc_quota_attainment,
        MIN(10.0, (r.annual_sales_achieved_usd_m / NULLIF(r.annual_sales_target_usd_m,0)) /
             (SELECT attainment_full_marks FROM params) * 10.0) AS calc_attainment_score_raw,
        (SELECT COUNT(*) FROM (
          SELECT 'sales_Jul-2025' AS c, r."sales_Jul-2025" AS sales UNION ALL
          SELECT 'sales_Aug-2025', r."sales_Aug-2025" UNION ALL
          SELECT 'sales_Sep-2025', r."sales_Sep-2025" UNION ALL
          SELECT 'sales_Oct-2025', r."sales_Oct-2025" UNION ALL
          SELECT 'sales_Nov-2025', r."sales_Nov-2025" UNION ALL
          SELECT 'sales_Dec-2025', r."sales_Dec-2025" UNION ALL
          SELECT 'sales_Jan-2026', r."sales_Jan-2026" UNION ALL
          SELECT 'sales_Feb-2026', r."sales_Feb-2026" UNION ALL
          SELECT 'sales_Mar-2026', r."sales_Mar-2026" UNION ALL
          SELECT 'sales_Apr-2026', r."sales_Apr-2026" UNION ALL
          SELECT 'sales_May-2026', r."sales_May-2026" UNION ALL
          SELECT 'sales_Jun-2026', r."sales_Jun-2026"
        ) months WHERE months.sales >= (SELECT hit_pct FROM params) * r.annual_sales_target_usd_m / 12.0) AS calc_months_hit,
        (r."sales_Jul-2025"+r."sales_Aug-2025"+r."sales_Sep-2025"+r."sales_Oct-2025"+r."sales_Nov-2025"+r."sales_Dec-2025") AS first_half_sales,
        (r."sales_Jan-2026"+r."sales_Feb-2026"+r."sales_Mar-2026"+r."sales_Apr-2026"+r."sales_May-2026"+r."sales_Jun-2026") AS second_half_sales
 FROM reps r
), scores AS (
 SELECT s.*,
        ROUND(calc_attainment_score_raw,2) AS calc_attainment_score,
        ROUND(calc_months_hit / 12.0 * 10.0,2) AS calc_consistency_score,
        ROUND(second_half_sales / NULLIF(first_half_sales,0)-1.0,3) AS calc_growth_percentage
 FROM raw_scores s
), scored AS (
 SELECT s.*,
        MAX(0.0, MIN(10.0, (SELECT growth_score_centre FROM params) +
                    calc_growth_percentage * (SELECT growth_score_scale FROM params))) AS calc_growth_score
 FROM scores s
), final_scores AS (
 SELECT s.*,
        ((SELECT weight_attainment FROM params)*calc_attainment_score +
         (SELECT weight_consistency FROM params)*calc_consistency_score +
         (SELECT weight_growth FROM params)*calc_growth_score) AS raw_performance_score
 FROM scored s
)
SELECT f.*,
       CASE
         -- Python's round(x, 2) uses ties-to-even; SQLite ROUND uses ties-away-from-zero.
         WHEN ABS(raw_performance_score*100.0 - CAST(raw_performance_score*100.0 AS INTEGER)) = 0.5
           THEN CASE WHEN CAST(raw_performance_score*100.0 AS INTEGER) % 2 = 0
                     THEN CAST(raw_performance_score*100.0 AS INTEGER)/100.0
                     ELSE (CAST(raw_performance_score*100.0 AS INTEGER)+1)/100.0 END
         ELSE ROUND(raw_performance_score,2)
       END AS calc_performance_score,
       CASE
        WHEN (CASE
         WHEN ABS(raw_performance_score*100.0 - CAST(raw_performance_score*100.0 AS INTEGER)) = 0.5
           THEN CASE WHEN CAST(raw_performance_score*100.0 AS INTEGER) % 2 = 0
                     THEN CAST(raw_performance_score*100.0 AS INTEGER)/100.0
                     ELSE (CAST(raw_performance_score*100.0 AS INTEGER)+1)/100.0 END
         ELSE ROUND(raw_performance_score,2)
       END) < (SELECT exit_below FROM params) THEN 'Exit / Separation'
        WHEN (CASE
         WHEN ABS(raw_performance_score*100.0 - CAST(raw_performance_score*100.0 AS INTEGER)) = 0.5
           THEN CASE WHEN CAST(raw_performance_score*100.0 AS INTEGER) % 2 = 0
                     THEN CAST(raw_performance_score*100.0 AS INTEGER)/100.0
                     ELSE (CAST(raw_performance_score*100.0 AS INTEGER)+1)/100.0 END
         ELSE ROUND(raw_performance_score,2)
       END) >= (SELECT retain_min FROM params)
          THEN CASE WHEN indication IN (SELECT value FROM json_each((SELECT retain_indications_json FROM params)))
                    THEN 'Retain on Onconova' ELSE 'Pipeline NP-309' END
        WHEN (CASE WHEN ABS(raw_performance_score*100.0 - CAST(raw_performance_score*100.0 AS INTEGER)) = 0.5 THEN CASE WHEN CAST(raw_performance_score*100.0 AS INTEGER) % 2 = 0 THEN CAST(raw_performance_score*100.0 AS INTEGER)/100.0 ELSE (CAST(raw_performance_score*100.0 AS INTEGER)+1)/100.0 END ELSE ROUND(raw_performance_score,2) END) >= (SELECT pipeline_min FROM params) THEN 'Pipeline NP-412'
        WHEN (CASE WHEN ABS(raw_performance_score*100.0 - CAST(raw_performance_score*100.0 AS INTEGER)) = 0.5 THEN CASE WHEN CAST(raw_performance_score*100.0 AS INTEGER) % 2 = 0 THEN CAST(raw_performance_score*100.0 AS INTEGER)/100.0 ELSE (CAST(raw_performance_score*100.0 AS INTEGER)+1)/100.0 END ELSE ROUND(raw_performance_score,2) END) >= (SELECT market_access_min FROM params) THEN 'Market Access'
        WHEN calc_quota_attainment < (SELECT quota_floor FROM params) THEN 'TBD - manager review'
        ELSE 'Other BU Transfer'
       END AS calc_destination
FROM final_scores f;
