#!/usr/bin/env python3
"""Run the Onconova SQLite views, reconciliation and C-F query suites.

Usage: python run_checks.py [path/to/onconova_sqlite.db]
Uses only Python's standard library. The selected database is updated with views.
"""
from pathlib import Path
import re
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent
DB = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "onconova_sqlite.db"


def query_blocks(sql_text: str, marker: str):
    """Return named SQL blocks separated by marker comments, preserving CTEs."""
    chunks = re.split(rf"(?m)(?=^-- {re.escape(marker)} )", sql_text)
    out = []
    for chunk in chunks:
        m = re.match(rf"(?m)^-- {re.escape(marker)} ([^:\n]+):?\s*(.*)$", chunk)
        if not m:
            continue
        name = m.group(1).strip()
        sql = chunk[m.end():].strip()
        # Remove any trailing semicolon only; leading comments within SQL are okay.
        if sql:
            out.append((name, sql))
    return out


def execute_one(conn, sql):
    # SQL blocks are authored as one query each; execute() accepts comments before SELECT.
    return conn.execute(sql.rstrip().rstrip(';'))


def print_result(conn, name, sql, max_rows=12):
    cur = execute_one(conn, sql)
    cols = [d[0] for d in cur.description or []]
    rows = cur.fetchall()
    print(f"\n{name} — {len(rows)} row(s)")
    if cols:
        print(" | ".join(cols))
    for row in rows[:max_rows]:
        print(" | ".join("NULL" if v is None else str(v) for v in row))
    if len(rows) > max_rows:
        print(f"... {len(rows)-max_rows} additional row(s) omitted from console; query returns the full result.")
    return cols, rows


def main():
    if not DB.exists():
        raise SystemExit(f"Database not found: {DB}")
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.executescript((ROOT / "views.sql").read_text(encoding="utf-8"))
        print(f"Database: {DB}")
        print("Views created/refreshed.")

        mismatch_rows = conn.execute((ROOT / "reconciliation.sql").read_text(encoding="utf-8")).fetchall()
        total_mismatches = sum(int(r[1]) for r in mismatch_rows)
        print("\nA/B reconciliation (tolerance: 0.000001 for numeric fields, including HCP trend):")
        for field, count in mismatch_rows:
            print(f"  {field}: {count}")
        print(f"TOTAL MISMATCHES: {total_mismatches}")

        care_sql = (ROOT / "carepath_analysis.sql").read_text(encoding="utf-8")
        care_rows = conn.execute(care_sql).fetchall()
        print(f"\nC CarePath comparison — {len(care_rows)} grouped rows")
        print("payor | overdue_bucket | carepath_enrolled | patient_count | avg_switch_probability | avg_switch_probability_pct")
        for row in care_rows:
            print(" | ".join(str(x) for x in row))

        business_sql = (ROOT / "business_queries.sql").read_text(encoding="utf-8")
        for name, sql in query_blocks(business_sql, "BIZ"):
            max_rows = 10 if name.startswith("4") or name.startswith("5B") or name.startswith("6") else 30
            print_result(conn, f"D {name}", sql, max_rows=max_rows)

        advanced_sql = (ROOT / "advanced_queries.sql").read_text(encoding="utf-8")
        for name, sql in query_blocks(advanced_sql, "ADV"):
            print_result(conn, f"E {name}", sql, max_rows=10)

        # Compare core KPIs to user-provided targets. The targets are checks, not SQL assumptions.
        kpi = conn.execute("""SELECT
          (SELECT COUNT(*) FROM patients),
          (SELECT COUNT(*) FROM hcps),
          (SELECT COUNT(*) FROM reps),
          (SELECT SUM(calc_monthly_revenue_usd) FROM v_patients_recomputed),
          (SELECT COUNT(*) FROM v_patients_recomputed WHERE calc_risk_level='High'),
          (SELECT COUNT(*) FROM v_hcps_recomputed WHERE calc_call_gap_tier1='Yes')
        """).fetchone()
        checks = [
            ("Patients", kpi[0], 13400, 0),
            ("HCPs", kpi[1], 6000, 0),
            ("Reps", kpi[2], 200, 0),
            ("Monthly revenue ($)", kpi[3], 133_740_000, 0.005),
            ("High-risk patients", kpi[4], 1883, 0),
            ("Tier 1 call-gap HCPs", kpi[5], 154, 0),
        ]
        print("\nF User-requested target comparison (high-risk and call-gap targets are supplied checks, not assumptions):")
        for label, actual, target, tol in checks:
            if tol == 0:
                passed = actual == target
                diff = actual - target
                print(f"  {'PASS' if passed else 'DIFF'} {label}: actual={actual}, target={target}, difference={diff}")
            else:
                pct = (actual-target)/target if target else 0.0
                passed = abs(pct) <= tol
                print(f"  {'PASS' if passed else 'DIFF'} {label}: actual={actual:,.2f}, target={target:,.2f}, difference={pct:.3%}, tolerance={tol:.3%}")
        print("\nRun status:", "PASS" if total_mismatches == 0 else "CHECK — reconciliation mismatches exist")
        if total_mismatches:
            raise SystemExit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
