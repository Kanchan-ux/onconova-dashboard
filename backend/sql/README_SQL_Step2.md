# Onconova LOE SQL Layer — Steps A–F

All data is simulated. This package builds and tests a SQLite analysis layer on the supplied Onconova database.

## Contents

- `schema.sql` — source table definitions.
- `load_onconova.py` — loads `reps.csv`, `hcps.csv`, `patients.csv` and assumptions from `config.py` into SQLite.
- `onconova_sqlite.db` — supplied/tested database snapshot.
- `views.sql` — Step A: recomputed patient, HCP and rep fields. The rep performance score is rounded once in a CTE before the destination rule uses it.
- `reconciliation.sql` — Step B: mismatch counts for all 19 recomputed fields. HCP trend tolerance is `0.000001`.
- `carepath_analysis.sql` — Step C: CarePath vs non-CarePath switch probabilities by overdue bucket and payor.
- `business_queries.sql` — Step D: executive KPIs, waterfall, patient, HCP, rep and ROI dashboard questions.
- `advanced_queries.sql` — Step E: regional rep rankings, running totals, HCP revenue deciles and HCP rankings by indication.
- `run_checks.py` — Step F: runs the views, reconciliation and C–E queries, then compares the requested core KPIs.
- `config.py` and the three CSVs — source assumptions and simulated data.
- `generate_data.py`, `waterfall.py`, `roi.py`, `checks.py` — original Python logic supplied for reference.
- `run_output.txt` — captured console output from the tested run. Long detail lists are truncated in this console log, but queries return complete results.

## Run

Use Python 3.9+ and a SQLite build with JSON1 enabled (JSON functions are included in standard modern Python SQLite builds). No third-party packages are required for the SQL layer.

1. Extract this ZIP to one folder.
2. Open a terminal in that folder.
3. Run:

   ```bash
   python run_checks.py
   ```

   Or point to another database:

   ```bash
   python run_checks.py path/to/onconova_sqlite.db
   ```

The script creates/refreshes the three views in the selected database, runs `reconciliation.sql`, runs every query in `carepath_analysis.sql`, `business_queries.sql` and `advanced_queries.sql`, and prints the results. It exits with an error if any of the 19 reconciliation fields has a mismatch.

To rebuild the database from the source CSVs and assumptions, run:

```bash
python load_onconova.py
python run_checks.py
```

**Warning:** `load_onconova.py` rebuilds the configured database file; keep a backup if you have made manual changes to the DB.

## Query guide (viva-friendly)

- **Views:** recalculate the derived fields from source columns and values in the `assumptions` table. This helps demonstrate that the model's formula columns are reproducible.
- **Reconciliation:** compares each recalculated value with its stored value. Numeric fields use a tolerance of `0.000001`; the `trx_trend` comparison was tightened to that same tolerance.
- **CarePath analysis:** compares enrolled and non-enrolled patients inside the same overdue bucket and payor. This separates the direct probability adjustment from the fact that CarePath patients are less likely to be overdue in the simulated data.
- **Waterfall:** applies each configured scenario driver sequentially to remaining revenue, then applies the switching percentage calculated from patient data. It does not add losses against the original baseline, so losses are not double-counted.
- **ROI:** follows `roi.py`: monthly revenue at risk × effectiveness × uptake × realisation × effective months × contribution margin; costs include fixed cost plus engaged units × unit cost × months to LOE.
- **Window functions:** `RANK()` compares reps within region, `SUM() OVER` creates a running loss total, and `NTILE(10)` identifies the top revenue decile of HCPs.

## Results and important caveats

Tested against the supplied database snapshot:

- 13,400 patients, 6,000 HCPs and 200 reps.
- Monthly revenue: `$133,740,000`.
- High-risk patients: `1,883`.
- Tier 1 HCP call gaps: `154`.
- Reconciliation: all 19 fields have `0` mismatches at the specified tolerance.
- CarePath analysis returns 30 payor/bucket/enrolment groups. There are no patients in the `31+` overdue bucket in this snapshot, because the simulated overdue values top out at 30 days.
- The revenue waterfall's Base post-LOE revenue is approximately `$714.88M` from the current snapshot and assumptions.
- ROI query output is calculated from the assumptions and derived views, not from typed result values.

The provided `config.py` also contains an `EXCEL_KEY` with older benchmark values (for example, 1,834 high-risk patients and 170 Tier 1 call gaps). Those differ from the actual uploaded database and from the explicit Step F targets in the request (1,883 and 154). The SQL matches the current database and the requested targets; the older `EXCEL_KEY` should be treated as a separately calibrated benchmark, not as the live database truth.

## SQLite / PostgreSQL

This package targets standard SQLite. `julianday()` is SQLite-specific; PostgreSQL should use date subtraction or interval arithmetic. The scenario and ROI queries use SQLite JSON functions (`json_extract`, `json_each`); PostgreSQL would use its JSON/JSONB operators and set-returning functions. The queries use CTEs and window functions supported by modern SQLite and PostgreSQL.
