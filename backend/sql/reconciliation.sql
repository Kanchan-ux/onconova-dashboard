-- Onconova STEP 2B: stored-versus-recomputed mismatch counts (SQLite)
-- Numeric fields use a 1e-6 absolute tolerance; categorical/integer fields compare exactly.
WITH mismatch_counts AS (
 SELECT 'patients.days_overdue' AS field, COUNT(*) AS mismatches
 FROM patients p JOIN v_patients_recomputed v USING(patient_id)
 WHERE p.days_overdue IS NULL OR ABS(p.days_overdue-v.calc_days_overdue)>0.000001
 UNION ALL
 SELECT 'patients.monthly_revenue_usd', COUNT(*)
 FROM patients p JOIN v_patients_recomputed v USING(patient_id)
 WHERE p.monthly_revenue_usd IS NULL OR ABS(p.monthly_revenue_usd-v.calc_monthly_revenue_usd)>0.000001
 UNION ALL
 SELECT 'patients.switch_prob', COUNT(*)
 FROM patients p JOIN v_patients_recomputed v USING(patient_id)
 WHERE p.switch_prob IS NULL OR ABS(p.switch_prob-v.calc_switch_prob)>0.000001
 UNION ALL
 SELECT 'patients.risk_level', COUNT(*)
 FROM patients p JOIN v_patients_recomputed v USING(patient_id)
 WHERE p.risk_level IS NOT v.calc_risk_level
 UNION ALL
 SELECT 'patients.expected_monthly_loss_usd', COUNT(*)
 FROM patients p JOIN v_patients_recomputed v USING(patient_id)
 WHERE p.expected_monthly_loss_usd IS NULL OR ABS(p.expected_monthly_loss_usd-v.calc_expected_monthly_loss_usd)>0.000001
 UNION ALL
 SELECT 'hcps.avg_trx_6m', COUNT(*)
 FROM hcps h JOIN v_hcps_recomputed v USING(hcp_id)
 WHERE h.avg_trx_6m IS NULL OR ABS(h.avg_trx_6m-v.calc_avg_trx_6m)>0.000001
 UNION ALL
 SELECT 'hcps.tier', COUNT(*)
 FROM hcps h JOIN v_hcps_recomputed v USING(hcp_id)
 WHERE h.tier IS NOT v.calc_tier
 UNION ALL
 SELECT 'hcps.trx_trend', COUNT(*)
 FROM hcps h JOIN v_hcps_recomputed v USING(hcp_id)
 WHERE h.trx_trend IS NULL OR ABS(h.trx_trend-v.calc_trx_trend)>0.000001
 UNION ALL
 SELECT 'hcps.trx_risk', COUNT(*)
 FROM hcps h JOIN v_hcps_recomputed v USING(hcp_id)
 WHERE h.trx_risk IS NOT v.calc_trx_risk
 UNION ALL
 SELECT 'hcps.days_since_call', COUNT(*)
 FROM hcps h JOIN v_hcps_recomputed v USING(hcp_id)
 WHERE h.days_since_call IS NULL OR h.days_since_call IS NOT v.calc_days_since_call
 UNION ALL
 SELECT 'hcps.call_gap_tier1', COUNT(*)
 FROM hcps h JOIN v_hcps_recomputed v USING(hcp_id)
 WHERE h.call_gap_tier1 IS NOT v.calc_call_gap_tier1
 UNION ALL
 SELECT 'reps.quota_attainment', COUNT(*)
 FROM reps r JOIN v_reps_recomputed v USING(rep_id)
 WHERE r.quota_attainment IS NULL OR ABS(r.quota_attainment-v.calc_quota_attainment)>0.000001
 UNION ALL
 SELECT 'reps.attainment_score', COUNT(*)
 FROM reps r JOIN v_reps_recomputed v USING(rep_id)
 WHERE r.attainment_score IS NULL OR ABS(r.attainment_score-v.calc_attainment_score)>0.000001
 UNION ALL
 SELECT 'reps.months_hit', COUNT(*)
 FROM reps r JOIN v_reps_recomputed v USING(rep_id)
 WHERE r.months_hit IS NULL OR r.months_hit IS NOT v.calc_months_hit
 UNION ALL
 SELECT 'reps.consistency_score', COUNT(*)
 FROM reps r JOIN v_reps_recomputed v USING(rep_id)
 WHERE r.consistency_score IS NULL OR ABS(r.consistency_score-v.calc_consistency_score)>0.000001
 UNION ALL
 SELECT 'reps.growth_percentage', COUNT(*)
 FROM reps r JOIN v_reps_recomputed v USING(rep_id)
 WHERE r.growth_percentage IS NULL OR ABS(r.growth_percentage-v.calc_growth_percentage)>0.000001
 UNION ALL
 SELECT 'reps.growth_score', COUNT(*)
 FROM reps r JOIN v_reps_recomputed v USING(rep_id)
 WHERE r.growth_score IS NULL OR ABS(r.growth_score-v.calc_growth_score)>0.000001
 UNION ALL
 SELECT 'reps.performance_score', COUNT(*)
 FROM reps r JOIN v_reps_recomputed v USING(rep_id)
 WHERE r.performance_score IS NULL OR ABS(r.performance_score-v.calc_performance_score)>0.000001
 UNION ALL
 SELECT 'reps.destination', COUNT(*)
 FROM reps r JOIN v_reps_recomputed v USING(rep_id)
 WHERE r.destination IS NOT v.calc_destination
)
SELECT field, mismatches FROM mismatch_counts ORDER BY field;
