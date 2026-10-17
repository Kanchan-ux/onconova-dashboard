-- BIZ 1: Executive KPIs: population counts, current monthly revenue, high-risk patients and expected monthly loss.
SELECT
  (SELECT COUNT(*) FROM patients) AS total_patients,
  (SELECT COUNT(*) FROM hcps) AS total_hcps,
  (SELECT COUNT(*) FROM reps) AS total_reps,
  (SELECT ROUND(SUM(calc_monthly_revenue_usd), 2) FROM v_patients_recomputed) AS monthly_revenue_usd,
  (SELECT COUNT(*) FROM v_patients_recomputed WHERE calc_risk_level='High') AS high_risk_patients,
  (SELECT ROUND(SUM(calc_expected_monthly_loss_usd), 2) FROM v_patients_recomputed) AS expected_monthly_loss_usd;

-- BIZ 2: Revenue waterfall by Base, Bear and Bull. Each driver applies to the revenue remaining after the prior step.
WITH RECURSIVE
assum AS (SELECT parameter_key, parameter_value FROM assumptions),
scenarios AS (
 SELECT 'Base' scenario, json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Base'),'$.generic_entry') generic_entry,
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Base'),'$.price_gtn') price_gtn,
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Base'),'$.formulary') formulary,
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Base'),'$.competitor_launch') competitor_launch
 UNION ALL
 SELECT 'Bear', json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Bear'),'$.generic_entry'),
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Bear'),'$.price_gtn'),
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Bear'),'$.formulary'),
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Bear'),'$.competitor_launch')
 UNION ALL
 SELECT 'Bull', json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Bull'),'$.generic_entry'),
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Bull'),'$.price_gtn'),
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Bull'),'$.formulary'),
        json_extract((SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL.Bull'),'$.competitor_launch')
),
base AS (SELECT SUM(calc_monthly_revenue_usd)*12.0 baseline FROM v_patients_recomputed),
switching AS (SELECT SUM(calc_expected_monthly_loss_usd)/NULLIF(SUM(calc_monthly_revenue_usd),0) pct FROM v_patients_recomputed),
steps AS (
 SELECT scenario, 0 step_no, 'Baseline Revenue' step, NULL pct FROM scenarios
 UNION ALL SELECT scenario,1,(SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL_LABELS.generic_entry'),generic_entry FROM scenarios
 UNION ALL SELECT scenario,2,(SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL_LABELS.price_gtn'),price_gtn FROM scenarios
 UNION ALL SELECT scenario,3,(SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL_LABELS.formulary'),formulary FROM scenarios
 UNION ALL SELECT scenario,4,(SELECT parameter_value FROM assum WHERE parameter_key='WATERFALL_LABELS.competitor_launch'),competitor_launch FROM scenarios
 UNION ALL SELECT scenario,5,'Patient Switching',(SELECT pct FROM switching) FROM scenarios
 UNION ALL SELECT scenario,6,'Post-LOE Revenue',NULL FROM scenarios
),
walk(scenario,step_no,step,pct,loss,revenue) AS (
 SELECT s.scenario,0,s.step,NULL,0.0,b.baseline FROM steps s CROSS JOIN base b WHERE s.step_no=0
 UNION ALL
 SELECT s.scenario,s.step_no,s.step,s.pct,
        CASE WHEN s.step_no=6 THEN 0.0 ELSE w.revenue*s.pct END,
        CASE WHEN s.step_no=6 THEN w.revenue ELSE w.revenue*(1.0-s.pct) END
 FROM walk w JOIN steps s ON s.scenario=w.scenario AND s.step_no=w.step_no+1
)
SELECT scenario, step, pct, ROUND(loss,2) AS loss_usd, ROUND(revenue,2) AS revenue_usd
FROM walk ORDER BY CASE scenario WHEN 'Base' THEN 1 WHEN 'Bear' THEN 2 ELSE 3 END, step_no;

-- BIZ 3A: High-risk patients and expected monthly loss by payor.
SELECT payor, COUNT(*) AS high_risk_patients,
       ROUND(SUM(calc_expected_monthly_loss_usd),2) AS expected_monthly_loss_usd
FROM v_patients_recomputed WHERE calc_risk_level='High'
GROUP BY payor ORDER BY expected_monthly_loss_usd DESC;

-- BIZ 3B: High-risk patients and expected monthly loss by indication.
SELECT indication, COUNT(*) AS high_risk_patients,
       ROUND(SUM(calc_expected_monthly_loss_usd),2) AS expected_monthly_loss_usd
FROM v_patients_recomputed WHERE calc_risk_level='High'
GROUP BY indication ORDER BY expected_monthly_loss_usd DESC;

-- BIZ 4: Target list: patients overdue at least GRACE_DAYS and not enrolled in CarePath.
SELECT v.patient_id, v.hcp_id, v.indication, v.payor, v.days_supply,
       v.calc_days_overdue AS days_overdue, v.calc_switch_prob AS switch_probability,
       v.calc_monthly_revenue_usd AS monthly_revenue_usd,
       v.calc_expected_monthly_loss_usd AS expected_monthly_loss_usd
FROM v_patients_recomputed v
WHERE v.calc_days_overdue >= CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='GRACE_DAYS') AS INTEGER)
  AND v.carepath_enrolled='No'
ORDER BY v.calc_expected_monthly_loss_usd DESC, v.calc_days_overdue DESC;

-- BIZ 5A: HCP tier distribution by indication.
SELECT indication, calc_tier AS tier, COUNT(*) AS hcp_count
FROM v_hcps_recomputed GROUP BY indication, calc_tier
ORDER BY indication, calc_tier;

-- BIZ 5B: Tier 1 HCPs with falling TRx classified High risk.
SELECT hcp_id, hcp_name, indication, rep_id, calc_avg_trx_6m AS avg_trx_6m,
       calc_trx_trend AS trx_trend, calc_trx_risk AS trx_risk
FROM v_hcps_recomputed
WHERE calc_tier='Tier 1' AND calc_trx_risk='High'
ORDER BY calc_trx_trend ASC;

-- BIZ 6: Tier 1 HCPs with call gaps longer than CALL_GAP_DAYS.
SELECT hcp_id, hcp_name, indication, rep_id, last_call_date, calc_days_since_call AS days_since_call
FROM v_hcps_recomputed
WHERE calc_call_gap_tier1='Yes'
ORDER BY calc_days_since_call DESC;

-- BIZ 7: Rep destination counts and average performance score by destination.
SELECT calc_destination AS destination, COUNT(*) AS rep_count,
       ROUND(AVG(calc_performance_score),2) AS avg_performance_score
FROM v_reps_recomputed GROUP BY calc_destination
ORDER BY rep_count DESC, destination;

-- BIZ 8: Revenue handled by exiting reps, by region. Annual sales are in $ millions in the source table.
SELECT r.region, COUNT(DISTINCT r.rep_id) AS exiting_reps,
       ROUND(SUM(r.annual_sales_achieved_usd_m),3) AS annual_sales_handled_usd_m,
       ROUND(SUM(r.annual_sales_achieved_usd_m)*1000000.0,2) AS annual_sales_handled_usd
FROM v_reps_recomputed v JOIN reps r USING(rep_id)
WHERE v.calc_destination='Exit / Separation'
GROUP BY r.region ORDER BY annual_sales_handled_usd_m DESC;

-- BIZ 9: ROI for four interventions using Python roi.py's formula and config-backed inputs.
WITH
p AS (
 SELECT CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='AS_OF_DATE') AS TEXT) as as_of_date,
        CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='LOE_DATE') AS TEXT) as loe_date,
        CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='DAYS_PER_MONTH') AS REAL) as days_per_month,
        CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='RAMP_MONTHS') AS REAL) as ramp_months,
        CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='REALISATION_FACTOR') AS REAL) as realisation,
        CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='CONTRIBUTION_MARGIN') AS REAL) as margin,
        CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='CAREPATH_FACTOR') AS REAL) as carepath_factor,
        CAST((SELECT parameter_value FROM assumptions WHERE parameter_key='GRACE_DAYS') AS INTEGER) as grace_days
), horizon AS (
 SELECT (julianday(loe_date)-julianday(as_of_date))/days_per_month AS months_to_loe,
        MAX(0.0,(julianday(loe_date)-julianday(as_of_date))/days_per_month-ramp_months) AS effective_months,
        realisation,margin,carepath_factor,grace_days FROM p
), patient_targets AS (
 SELECT v.*,
        (v.calc_risk_level='High' AND v.carepath_enrolled='No') AS is_carepath_target,
        (v.calc_days_overdue >= (SELECT grace_days FROM horizon)) AS is_overdue
 FROM v_patients_recomputed v
), revtrx AS (
 SELECT SUM(calc_monthly_revenue_usd)/NULLIF((SELECT SUM("trx_m0") FROM hcps),0) AS revenue_per_trx FROM v_patients_recomputed
), targets AS (
 SELECT 'CarePath enrolment push' intervention, 'Patients' unit_type,
        SUM(CASE WHEN is_carepath_target THEN 1 ELSE 0 END) target_units,
        SUM(CASE WHEN is_carepath_target THEN calc_expected_monthly_loss_usd ELSE 0 END) revenue_at_risk
 FROM patient_targets
 UNION ALL
 SELECT 'Refill-reminder outreach','Patients',
        SUM(CASE WHEN is_overdue AND NOT is_carepath_target THEN 1 ELSE 0 END),
        SUM(CASE WHEN is_overdue AND NOT is_carepath_target THEN calc_expected_monthly_loss_usd ELSE 0 END)
 FROM patient_targets
 UNION ALL
 SELECT 'Close Tier 1 call gaps','HCPs',COUNT(*),SUM(h."trx_m0")*(SELECT revenue_per_trx FROM revtrx)
 FROM v_hcps_recomputed v JOIN hcps h USING(hcp_id) WHERE v.calc_call_gap_tier1='Yes'
 UNION ALL
 SELECT 'Retention plan: declining Tier 1 HCPs','HCPs',COUNT(*),SUM(h."trx_m0")*(SELECT revenue_per_trx FROM revtrx)
 FROM v_hcps_recomputed v JOIN hcps h USING(hcp_id) WHERE v.calc_tier='Tier 1' AND v.calc_trx_risk='High'
), inputs AS (
 SELECT t.*,
        json_extract(a.parameter_value,'$.uptake') AS uptake,
        COALESCE(json_extract(a.parameter_value,'$.effectiveness'),1.0-(SELECT carepath_factor FROM horizon)) AS effectiveness,
        json_extract(a.parameter_value,'$.unit_cost') AS unit_cost,
        json_extract(a.parameter_value,'$.fixed_cost') AS fixed_cost
 FROM targets t JOIN assumptions a ON a.parameter_key='ROI_INTERVENTIONS.'||t.intervention
), calc AS (
 SELECT i.*, h.months_to_loe,h.effective_months,h.realisation,h.margin,
        revenue_at_risk*effectiveness*uptake*realisation AS monthly_revenue_protected,
        (revenue_at_risk*effectiveness*uptake*realisation)*effective_months*margin AS benefit,
        target_units*uptake*unit_cost*months_to_loe+fixed_cost AS total_cost
 FROM inputs i CROSS JOIN horizon h
)
SELECT intervention,unit_type,target_units,ROUND(revenue_at_risk,2) AS monthly_revenue_at_risk_usd,
       ROUND(total_cost,2) AS total_cost_usd,ROUND(benefit,2) AS benefit_usd,
       ROUND(benefit-total_cost,2) AS net_benefit_usd,
       ROUND((benefit-total_cost)/NULLIF(total_cost,0),4) AS roi_multiple,
       ROUND(total_cost/NULLIF(monthly_revenue_protected*margin,0),2) AS payback_months
FROM calc ORDER BY roi_multiple DESC;
