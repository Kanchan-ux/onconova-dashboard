-- C: Like-for-like CarePath comparison.
-- Within each overdue bucket and payor, compare enrolled vs non-enrolled patients.
-- The probability itself is recomputed in v_patients_recomputed from config-backed assumptions.
WITH bucketed AS (
  SELECT
    patient_id, payor, carepath_enrolled,
    CASE
      WHEN calc_days_overdue = 0 THEN '0'
      WHEN calc_days_overdue BETWEEN 1 AND 7 THEN '1-7'
      WHEN calc_days_overdue BETWEEN 8 AND 30 THEN '8-30'
      ELSE '31+'
    END AS overdue_bucket,
    calc_switch_prob
  FROM v_patients_recomputed
)
SELECT
  payor,
  overdue_bucket,
  carepath_enrolled,
  COUNT(*) AS patient_count,
  ROUND(AVG(calc_switch_prob), 6) AS avg_switch_probability,
  ROUND(AVG(calc_switch_prob) * 100.0, 3) AS avg_switch_probability_pct
FROM bucketed
GROUP BY payor, overdue_bucket, carepath_enrolled
ORDER BY payor,
  CASE overdue_bucket WHEN '0' THEN 1 WHEN '1-7' THEN 2 WHEN '8-30' THEN 3 ELSE 4 END,
  carepath_enrolled;
