-- ADV 1: Rank reps within each region by recalculated performance score.
WITH ranked AS (
 SELECT reps.rep_id,reps.rep_name,reps.region,calc_destination AS destination,calc_performance_score AS performance_score,
        RANK() OVER (PARTITION BY reps.region ORDER BY calc_performance_score DESC) AS region_rank
 FROM v_reps_recomputed JOIN reps USING(rep_id)
)
SELECT * FROM ranked WHERE region_rank <= 5 ORDER BY region,region_rank,rep_id;

-- ADV 2: Running total of expected monthly loss by patient, largest loss first.
WITH ranked_loss AS (
 SELECT patient_id,payor,indication,calc_expected_monthly_loss_usd AS expected_loss,
        SUM(calc_expected_monthly_loss_usd) OVER (
          ORDER BY calc_expected_monthly_loss_usd DESC, patient_id
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_expected_loss
 FROM v_patients_recomputed
)
SELECT * FROM ranked_loss ORDER BY expected_loss DESC,patient_id LIMIT 20;

-- ADV 3: Top 10% of HCPs by estimated monthly revenue. NTILE(10) puts HCPs into ten ranked groups.
WITH revenue_per_trx AS (
 SELECT SUM(calc_monthly_revenue_usd)/NULLIF((SELECT SUM("trx_m0") FROM hcps),0) AS amount FROM v_patients_recomputed
), hcp_revenue AS (
 SELECT h.hcp_id,h.hcp_name,h.indication,h.rep_id,h."trx_m0" AS current_trx,
        h."trx_m0"*(SELECT amount FROM revenue_per_trx) AS estimated_monthly_revenue,
        NTILE(10) OVER (ORDER BY h."trx_m0" DESC,h.hcp_id) AS revenue_decile
 FROM hcps h
)
SELECT * FROM hcp_revenue WHERE revenue_decile=1 ORDER BY estimated_monthly_revenue DESC,hcp_id;

-- ADV 4: Rank HCPs within indication by average six-month TRx and show the top five per indication.
WITH ranked AS (
 SELECT hcp_id,hcp_name,indication,calc_avg_trx_6m AS avg_trx_6m,calc_tier AS tier,
        RANK() OVER (PARTITION BY indication ORDER BY calc_avg_trx_6m DESC) AS indication_rank
 FROM v_hcps_recomputed
)
SELECT * FROM ranked WHERE indication_rank<=5 ORDER BY indication,indication_rank,hcp_id;
