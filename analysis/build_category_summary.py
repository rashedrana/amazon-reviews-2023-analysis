#!/usr/bin/env python3
"""Build analysis/category_summary.csv from the processed categories' own
output files (stats.json + stats_v2.json). Nothing is typed by hand: every
number is read from the pipeline outputs.

Columns: category, verified_reviews, unique_users, unique_items, avg_rating,
share_5star, share_1star, verified_share, date_min, date_max.
Sorted by verified_reviews, descending.
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "analysis", "category_summary.csv")


def main():
    rows = []
    for cat in sorted(os.listdir(PROCESSED)):
        d = os.path.join(PROCESSED, cat)
        stats_path = os.path.join(d, "stats.json")
        if not os.path.isfile(stats_path):
            continue
        with open(stats_path) as fh:
            s = json.load(fh)
        total = s["total_reviews_counted"]
        dist = {float(k): v for k, v in s["rating_distribution"].items()}
        verified_share = ""
        v2_path = os.path.join(d, "stats_v2.json")
        if os.path.isfile(v2_path):
            with open(v2_path) as fh:
                s2 = json.load(fh)
            if isinstance(s2.get("verified"), dict):
                verified_share = round(s2["verified"]["reviews"] / total, 4) if total else ""
        rows.append({
            "category": cat,
            "verified_reviews": total,
            "unique_users": s["unique_users"],
            "unique_items": s["unique_items_parent_asin"],
            "avg_rating": s["avg_rating"],
            "share_5star": round(dist.get(5.0, 0) / total, 4) if total else "",
            "share_1star": round(dist.get(1.0, 0) / total, 4) if total else "",
            "verified_share": verified_share,
            "date_min": s["date_range"]["min"],
            "date_max": s["date_range"]["max"],
        })
    rows.sort(key=lambda r: -r["verified_reviews"])
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    total_all = sum(r["verified_reviews"] for r in rows)
    print(f"wrote {OUT}: {len(rows)} categories, {total_all:,} verified reviews total")
    for r in rows:
        print(f"  {r['category']:<28} {r['verified_reviews']:>10,}")


if __name__ == "__main__":
    main()
