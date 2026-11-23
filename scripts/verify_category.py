#!/usr/bin/env python3
"""Verify one or more processed categories for internal consistency.

Checks per category (all numbers read from the category's own output files):
  monthly_aggregates reviews sum        == stats.json total
  monthly_aggregates star columns sum   == rating_distribution counts
  rating_distribution reviews sum       == stats.json total
  yearly_satisfaction reviews sum       == stats.json total        (v2)
  verified_split reviews sum            == stats.json total        (v2)
  reviewer_concentration reviews sum    == stats.json total        (v2)
  reviewer_concentration reviewers sum  == stats.json unique_users (v2)
  products_<Cat> reviews sum            == stats.json total        (v2)
and cross-checks the counted total against the lab's published (rounded)
count from data/source_report.md, flagging differences beyond rounding.

Usage: python verify_category.py Category [Category ...]
Exit code 0 if every check passes (rounding cross-check warnings allowed
only when flagged as WARN, not FAIL — see tolerance below).
"""

import csv
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")

# Lab-published counts (rounded, from data/source_report.md) and the size of
# one rounding unit, used only for the cross-check tolerance.
LAB_COUNTS = {
    "Subscription_Boxes": (16_200, 100),
    "Magazine_Subscriptions": (71_500, 100),
    "Gift_Cards": (152_400, 100),
    "Digital_Music": (130_400, 100),
    "Health_and_Personal_Care": (494_100, 100),
    "Handmade_Products": (664_200, 100),
    "All_Beauty": (701_500, 100),
    "Appliances": (2_100_000, 100_000),
    "Amazon_Fashion": (2_500_000, 100_000),
    "Musical_Instruments": (3_000_000, 100_000),
    "Software": (4_900_000, 100_000),
    "Industrial_and_Scientific": (5_200_000, 100_000),
    "Video_Games": (4_600_000, 100_000),
    "Baby_Products": (6_000_000, 100_000),
    "CDs_and_Vinyl": (4_800_000, 100_000),
}


def read_csv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def check(cat):
    d = os.path.join(PROCESSED, cat)
    ok = True

    def report(label, passed, detail=""):
        nonlocal ok
        print(f"  [{'PASS' if passed else 'FAIL'}] {label} {detail}")
        ok = ok and passed

    with open(os.path.join(d, "stats.json")) as fh:
        stats = json.load(fh)
    total = stats["total_reviews_counted"]
    print(f"{cat}: counted total = {total:,}")

    monthly = read_csv(os.path.join(d, "monthly_aggregates.csv"))
    m_sum = sum(int(r["reviews"]) for r in monthly)
    report("monthly reviews sum == total", m_sum == total, f"({m_sum:,})")

    dist = read_csv(os.path.join(d, "rating_distribution.csv"))
    d_sum = sum(int(r["reviews"]) for r in dist)
    report("rating distribution sum == total", d_sum == total, f"({d_sum:,})")

    star_cols = {f"{i}.0": sum(int(r[f"stars_{i}"]) for r in monthly) for i in range(1, 6)}
    dist_map = {r["rating"]: int(r["reviews"]) for r in dist}
    report("monthly star columns == rating distribution", star_cols == dist_map,
           "" if star_cols == dist_map else f"({star_cols} vs {dist_map})")

    v2_files = ["yearly_satisfaction.csv", "verified_split.csv",
                "reviewer_concentration.csv", f"products_{cat}.csv"]
    if all(os.path.exists(os.path.join(d, f)) for f in v2_files):
        yearly = read_csv(os.path.join(d, "yearly_satisfaction.csv"))
        y_sum = sum(int(r["reviews"]) for r in yearly)
        report("yearly reviews sum == total", y_sum == total, f"({y_sum:,})")

        vsplit = read_csv(os.path.join(d, "verified_split.csv"))
        v_sum = sum(int(r["reviews"]) for r in vsplit)
        report("verified split sum == total", v_sum == total, f"({v_sum:,})")

        conc = read_csv(os.path.join(d, "reviewer_concentration.csv"))
        c_sum = sum(int(r["reviews"]) for r in conc)
        report("concentration reviews sum == total", c_sum == total, f"({c_sum:,})")
        r_sum = sum(int(r["reviewers"]) for r in conc)
        report("concentration reviewers == unique_users",
               r_sum == stats["unique_users"], f"({r_sum:,} vs {stats['unique_users']:,})")

        prods = read_csv(os.path.join(d, f"products_{cat}.csv"))
        p_sum = sum(int(r["reviews"]) for r in prods)
        report("products reviews sum == total", p_sum == total, f"({p_sum:,})")
    else:
        print("  [SKIP] v2 outputs not present")

    if cat in LAB_COUNTS:
        published, unit = LAB_COUNTS[cat]
        diff = total - published
        # Published figures are rounded to `unit`; allow one full unit plus
        # 0.1% slack before calling it a mismatch.
        tol = unit + 0.001 * published
        status = "OK" if abs(diff) <= tol else "MISMATCH"
        print(f"  [{status}] lab cross-check: counted {total:,} vs published "
              f"{published:,} (diff {diff:+,}, tolerance ±{tol:,.0f})")
        if status == "MISMATCH":
            ok = False
    return ok


def main():
    cats = sys.argv[1:]
    if not cats:
        print(__doc__)
        return 2
    all_ok = True
    for cat in cats:
        all_ok = check(cat) and all_ok
    print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
