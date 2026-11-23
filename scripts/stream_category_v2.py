#!/usr/bin/env python3
"""Stream-process ONE category of the McAuley Lab "Amazon Reviews 2023" dataset — v2.

Superset of scripts/stream_category.py (v1, kept untouched). One streaming
pass produces ALL v1 outputs (identical formats):

  data/processed/<Category>/monthly_aggregates.csv
  data/processed/<Category>/rating_distribution.csv
  data/processed/<Category>/fact_sample.csv          (first-N, see --sample)
  data/processed/<Category>/stats.json

plus the v2 outputs:

  data/processed/<Category>/products_<Category>.csv  per-product (parent_asin)
                                                     aggregates: reviews, avg
                                                     rating, 5-star / 1-star
                                                     shares, verified share,
                                                     helpful votes
  data/processed/<Category>/verified_split.csv       verified vs unverified:
                                                     reviews, share, avg rating
  data/processed/<Category>/reviewer_concentration.csv
                                                     reviews-per-user counts in
                                                     buckets 1, 2, 3-5, 6-10,
                                                     11-50, 51+
  data/processed/<Category>/yearly_satisfaction.csv  per year: reviews, avg
                                                     rating, 5-star share
  data/processed/<Category>/stats_v2.json            the v2 headline numbers

Usage mirrors v1:
  python stream_category_v2.py Subscription_Boxes --download-to data/raw_tmp/Subscription_Boxes.jsonl --delete-raw

Per-product and per-user structures are held in memory as hashed/plain dicts;
if either exceeds --max-tracked entries, tracking for that structure stops
and stats_v2.json reports "not_tracked" instead of a guessed number. (In
Stage 2 v2 is only run on categories whose raw file is <= 2 GB, where the
structures stay well below the cap.)
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stream_category import open_stream, year_month, HF_BASE, PROJECT_ROOT  # noqa: E402

CONCENTRATION_BUCKETS = [(1, 1, "1"), (2, 2, "2"), (3, 5, "3-5"),
                         (6, 10, "6-10"), (11, 50, "11-50"), (51, None, "51+")]


def bucket_label(n):
    for lo, hi, label in CONCENTRATION_BUCKETS:
        if n >= lo and (hi is None or n <= hi):
            return label
    return "51+"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("category")
    ap.add_argument("--file", help="local raw file (.jsonl or .jsonl.gz)")
    ap.add_argument("--url", help="remote raw file URL (streamed, not saved)")
    ap.add_argument("--download-to", help="download to this local path first, then process the file")
    ap.add_argument("--delete-raw", action="store_true", help="delete the local raw file after processing")
    ap.add_argument("--sample", type=int, default=50000, help="max rows in fact_sample.csv (first-N method)")
    ap.add_argument("--max-uniques", type=int, default=4_000_000,
                    help="stop unique item tracking above this many distinct ids (v1 behaviour)")
    ap.add_argument("--max-tracked", type=int, default=8_000_000,
                    help="stop per-user / per-product tracking above this many distinct keys")
    args = ap.parse_args()

    category = args.category
    out_dir = os.path.join(PROJECT_ROOT, "data", "processed", category)
    os.makedirs(out_dir, exist_ok=True)

    source = args.file or args.url
    local_raw = args.file
    if args.download_to:
        url = args.url or f"{HF_BASE}/raw/review_categories/{category}.jsonl"
        os.makedirs(os.path.dirname(args.download_to), exist_ok=True)
        print(f"downloading {url} -> {args.download_to}", flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "amazon-reviews-pipeline/2.0"})
        with urllib.request.urlopen(req) as r, open(args.download_to, "wb") as fh:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
        source = local_raw = args.download_to
        print(f"downloaded {os.path.getsize(local_raw):,} bytes", flush=True)
    if not source:
        source = f"{HF_BASE}/raw/review_categories/{category}.jsonl"

    # --- v1 accumulators ---------------------------------------------------
    monthly = defaultdict(lambda: {"count": 0, "rating_sum": 0.0, "verified": 0,
                                   "helpful": 0, "stars": defaultdict(int)})
    rating_dist = defaultdict(int)
    items = set()
    track_items = True
    sample_rows = []

    # --- v2 accumulators ---------------------------------------------------
    user_counts = {}            # md5(user_id)[:8] -> reviews in this category
    track_users = True
    products = {}               # parent_asin -> [count, rating_sum, n5, n1, verified, helpful]
    track_products = True
    verified_acc = {0: [0, 0.0], 1: [0, 0.0]}   # flag -> [reviews, rating_sum]
    yearly = defaultdict(lambda: [0, 0.0, 0])    # year -> [reviews, rating_sum, n5]

    total = 0
    min_ts, max_ts = None, None
    helpful_field_seen = None

    print(f"streaming {source}", flush=True)
    with open_stream(source) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            rating = rec.get("rating")
            rating_f = float(rating) if rating is not None else None
            ts = rec.get("timestamp")
            verified = 1 if rec.get("verified_purchase") else 0
            if "helpful_vote" in rec:
                helpful = rec.get("helpful_vote") or 0
                helpful_field_seen = helpful_field_seen or "helpful_vote"
            else:
                helpful = rec.get("helpful_votes") or 0
                helpful_field_seen = helpful_field_seen or "helpful_votes"
            helpful = int(helpful)
            y, m = year_month(ts)
            if ts is not None:
                min_ts = ts if min_ts is None else min(min_ts, ts)
                max_ts = ts if max_ts is None else max(max_ts, ts)
            if y is not None:
                cell = monthly[(y, m)]
                cell["count"] += 1
                cell["verified"] += verified
                cell["helpful"] += helpful
                if rating_f is not None:
                    cell["rating_sum"] += rating_f
                    cell["stars"][rating_f] += 1
                yr = yearly[y]
                yr[0] += 1
                if rating_f is not None:
                    yr[1] += rating_f
                    if rating_f == 5.0:
                        yr[2] += 1
            if rating_f is not None:
                rating_dist[rating_f] += 1

            # verified / unverified split
            vacc = verified_acc[verified]
            vacc[0] += 1
            if rating_f is not None:
                vacc[1] += rating_f

            # unique items (v1 behaviour)
            pid = rec.get("parent_asin")
            if track_items:
                if pid:
                    items.add(hashlib.md5(str(pid).encode()).digest()[:8])
                if len(items) > args.max_uniques:
                    track_items = False
                    items.clear()

            # reviewer concentration (hashed user ids)
            uid = rec.get("user_id")
            if track_users and uid:
                key = hashlib.md5(str(uid).encode()).digest()[:8]
                user_counts[key] = user_counts.get(key, 0) + 1
                if len(user_counts) > args.max_tracked:
                    track_users = False
                    user_counts.clear()

            # per-product aggregates
            if track_products and pid:
                p = products.get(pid)
                if p is None:
                    p = products[pid] = [0, 0.0, 0, 0, 0, 0]
                p[0] += 1
                p[4] += verified
                p[5] += helpful
                if rating_f is not None:
                    p[1] += rating_f
                    if rating_f == 5.0:
                        p[2] += 1
                    elif rating_f == 1.0:
                        p[3] += 1
                if len(products) > args.max_tracked:
                    track_products = False
                    products.clear()

            if len(sample_rows) < args.sample:
                sample_rows.append({
                    "user_id": rec.get("user_id"),
                    "parent_asin": rec.get("parent_asin"),
                    "asin": rec.get("asin"),
                    "rating": rating,
                    "year_month": f"{y:04d}-{m:02d}" if y else "",
                    "verified_purchase": verified,
                    "helpful_vote": helpful,
                })
            if total % 500_000 == 0:
                print(f"  {total:,} reviews...", flush=True)

    # --- v1 outputs ----------------------------------------------------------
    with open(os.path.join(out_dir, "monthly_aggregates.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year_month", "reviews", "avg_rating", "verified_share",
                    "helpful_votes", "stars_1", "stars_2", "stars_3", "stars_4", "stars_5"])
        for (yy, mm) in sorted(monthly):
            c = monthly[(yy, mm)]
            w.writerow([f"{yy:04d}-{mm:02d}", c["count"],
                        round(c["rating_sum"] / c["count"], 4) if c["count"] else "",
                        round(c["verified"] / c["count"], 4) if c["count"] else "",
                        c["helpful"],
                        c["stars"].get(1.0, 0), c["stars"].get(2.0, 0), c["stars"].get(3.0, 0),
                        c["stars"].get(4.0, 0), c["stars"].get(5.0, 0)])

    with open(os.path.join(out_dir, "rating_distribution.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rating", "reviews", "share"])
        for r in sorted(rating_dist):
            w.writerow([r, rating_dist[r], round(rating_dist[r] / total, 4) if total else ""])

    with open(os.path.join(out_dir, "fact_sample.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["user_id", "parent_asin", "asin", "rating",
                                           "year_month", "verified_purchase", "helpful_vote"])
        w.writeheader()
        w.writerows(sample_rows)

    def iso(t):
        if t is None:
            return None
        seconds = t / 1000.0 if t > 10_000_000_000 else float(t)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()

    stats = {
        "category": category,
        "source": source if not local_raw else os.path.basename(local_raw),
        "total_reviews_counted": total,
        "date_range": {"min": iso(min_ts), "max": iso(max_ts)},
        "rating_distribution": {str(k): v for k, v in sorted(rating_dist.items())},
        "avg_rating": round(sum(k * v for k, v in rating_dist.items()) / total, 4) if total else None,
        "unique_users": len(user_counts) if track_users else "not_tracked",
        "unique_items_parent_asin": len(items) if track_items else "not_tracked",
        "helpful_field_name_in_file": helpful_field_seen,
        "fact_sample_rows": len(sample_rows),
        "fact_sample_method": "first-N rows of the file, in file order",
        "monthly_cells": len(monthly),
        "pipeline": "stream_category_v2.py (v1-compatible outputs)",
    }
    with open(os.path.join(out_dir, "stats.json"), "w") as fh:
        json.dump(stats, fh, indent=2)

    # --- v2 outputs ----------------------------------------------------------
    if track_products:
        prod_path = os.path.join(out_dir, f"products_{category}.csv")
        with open(prod_path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["parent_asin", "reviews", "avg_rating", "share_5star",
                        "share_1star", "verified_share", "helpful_votes"])
            for asin, p in sorted(products.items(), key=lambda kv: (-kv[1][0], kv[0])):
                n = p[0]
                w.writerow([asin, n, round(p[1] / n, 4),
                            round(p[2] / n, 4), round(p[3] / n, 4),
                            round(p[4] / n, 4), p[5]])
    else:
        prod_path = None

    with open(os.path.join(out_dir, "verified_split.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["segment", "reviews", "share_of_reviews", "avg_rating"])
        for flag, label in ((1, "verified"), (0, "unverified")):
            n, s = verified_acc[flag]
            w.writerow([label, n, round(n / total, 4) if total else "",
                        round(s / n, 4) if n else ""])

    concentration_rows = []
    if track_users:
        buckets = {label: [0, 0] for _, _, label in CONCENTRATION_BUCKETS}
        for c in user_counts.values():
            b = buckets[bucket_label(c)]
            b[0] += 1
            b[1] += c
        n_reviewers = len(user_counts)
        with open(os.path.join(out_dir, "reviewer_concentration.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["reviews_per_user_bucket", "reviewers", "share_of_reviewers",
                        "reviews", "share_of_reviews"])
            for _, _, label in CONCENTRATION_BUCKETS:
                reviewers, reviews = buckets[label]
                row = [label, reviewers,
                       round(reviewers / n_reviewers, 4) if n_reviewers else "",
                       reviews, round(reviews / total, 4) if total else ""]
                w.writerow(row)
                concentration_rows.append(row)
    else:
        n_reviewers = "not_tracked"

    with open(os.path.join(out_dir, "yearly_satisfaction.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "reviews", "avg_rating", "share_5star"])
        for yy in sorted(yearly):
            n, s, n5 = yearly[yy]
            w.writerow([yy, n, round(s / n, 4) if n else "", round(n5 / n, 4) if n else ""])

    def seg(flag):
        n, s = verified_acc[flag]
        return {"reviews": n, "avg_rating": round(s / n, 4) if n else None}

    stats_v2 = {
        "category": category,
        "total_reviews_counted": total,
        "products_tracked": len(products) if track_products else "not_tracked",
        "products_file": os.path.basename(prod_path) if prod_path else None,
        "verified": seg(1),
        "unverified": seg(0),
        "reviewers_tracked": n_reviewers,
        "reviewer_concentration": [
            {"bucket": r[0], "reviewers": r[1], "share_of_reviewers": r[2],
             "reviews": r[3], "share_of_reviews": r[4]} for r in concentration_rows
        ] if track_users else "not_tracked",
        "years_covered": [min(yearly), max(yearly)] if yearly else None,
    }
    with open(os.path.join(out_dir, "stats_v2.json"), "w") as fh:
        json.dump(stats_v2, fh, indent=2)

    if args.delete_raw and local_raw and os.path.exists(local_raw):
        os.remove(local_raw)
        print(f"deleted raw file {local_raw}", flush=True)

    print(json.dumps(stats, indent=2))
    print(json.dumps(stats_v2, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
