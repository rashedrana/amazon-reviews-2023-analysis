#!/usr/bin/env python3
"""Stream-process ONE category of the McAuley Lab "Amazon Reviews 2023" dataset.

Reads a raw review file (.jsonl or .jsonl.gz) line by line — from a local path
or an http(s) URL — without ever loading it into memory, and writes small
aggregate outputs:

  data/processed/<Category>/monthly_aggregates.csv   year-month x rating counts,
                                                     avg rating, verified share,
                                                     helpful votes
  data/processed/<Category>/rating_distribution.csv  counts per star rating
  data/processed/<Category>/fact_sample.csv          bounded sample of per-review
                                                     rows (first-N, see --sample)
  data/processed/<Category>/stats.json               verified totals counted from
                                                     the stream itself

Usage:
  python stream_category.py Digital_Music --url https://.../Digital_Music.jsonl
  python stream_category.py Digital_Music --file data/raw_tmp/Digital_Music.jsonl --delete-raw

Unique user/item counting uses in-memory sets of hashed ids and is only kept
while the sets stay under --max-uniques entries; beyond that the counts are
reported as "not_tracked" in stats.json rather than guessed.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

HF_BASE = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def open_stream(source):
    """Return a text stream over a local file or URL, gzip-aware."""
    if source.startswith("http://") or source.startswith("https://"):
        req = urllib.request.Request(source, headers={"User-Agent": "amazon-reviews-pipeline/1.0"})
        raw = urllib.request.urlopen(req)
        is_gz = source.endswith(".gz")
    else:
        raw = open(source, "rb")
        with open(source, "rb") as fh:
            is_gz = fh.read(2) == b"\x1f\x8b"
    if is_gz:
        raw = gzip.GzipFile(fileobj=raw)
    return io.TextIOWrapper(raw, encoding="utf-8", errors="replace")


def year_month(ts):
    """Amazon Reviews 2023 timestamps are ms since epoch (some early ones s)."""
    if ts is None:
        return None, None
    seconds = ts / 1000.0 if ts > 10_000_000_000 else float(ts)
    try:
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None, None
    return dt.year, dt.month


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("category")
    ap.add_argument("--file", help="local raw file (.jsonl or .jsonl.gz)")
    ap.add_argument("--url", help="remote raw file URL (streamed, not saved)")
    ap.add_argument("--download-to", help="download to this local path first, then process the file")
    ap.add_argument("--delete-raw", action="store_true", help="delete the local raw file after processing")
    ap.add_argument("--sample", type=int, default=50000, help="max rows in fact_sample.csv (first-N method)")
    ap.add_argument("--max-uniques", type=int, default=4_000_000,
                    help="stop unique user/item tracking above this many distinct ids")
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
        req = urllib.request.Request(url, headers={"User-Agent": "amazon-reviews-pipeline/1.0"})
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

    monthly = defaultdict(lambda: {"count": 0, "rating_sum": 0.0, "verified": 0,
                                   "helpful": 0, "stars": defaultdict(int)})
    rating_dist = defaultdict(int)
    users, items = set(), set()
    track_uniques = True
    total = 0
    min_ts, max_ts = None, None
    helpful_field_seen = None
    sample_rows = []

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
            ts = rec.get("timestamp")
            verified = 1 if rec.get("verified_purchase") else 0
            if "helpful_vote" in rec:
                helpful = rec.get("helpful_vote") or 0
                helpful_field_seen = helpful_field_seen or "helpful_vote"
            else:
                helpful = rec.get("helpful_votes") or 0
                helpful_field_seen = helpful_field_seen or "helpful_votes"
            y, m = year_month(ts)
            if ts is not None:
                min_ts = ts if min_ts is None else min(min_ts, ts)
                max_ts = ts if max_ts is None else max(max_ts, ts)
            if y is not None:
                cell = monthly[(y, m)]
                cell["count"] += 1
                cell["verified"] += verified
                cell["helpful"] += int(helpful)
                if rating is not None:
                    cell["rating_sum"] += float(rating)
                    cell["stars"][float(rating)] += 1
            if rating is not None:
                rating_dist[float(rating)] += 1
            if track_uniques:
                uid, pid = rec.get("user_id"), rec.get("parent_asin")
                if uid:
                    users.add(hashlib.md5(str(uid).encode()).digest()[:8])
                if pid:
                    items.add(hashlib.md5(str(pid).encode()).digest()[:8])
                if len(users) > args.max_uniques or len(items) > args.max_uniques:
                    track_uniques = False
                    users.clear(); items.clear()
            if len(sample_rows) < args.sample:
                sample_rows.append({
                    "user_id": rec.get("user_id"),
                    "parent_asin": rec.get("parent_asin"),
                    "asin": rec.get("asin"),
                    "rating": rating,
                    "year_month": f"{y:04d}-{m:02d}" if y else "",
                    "verified_purchase": verified,
                    "helpful_vote": int(helpful),
                })
            if total % 500_000 == 0:
                print(f"  {total:,} reviews...", flush=True)

    # --- outputs -----------------------------------------------------------
    with open(os.path.join(out_dir, "monthly_aggregates.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year_month", "reviews", "avg_rating", "verified_share",
                    "helpful_votes", "stars_1", "stars_2", "stars_3", "stars_4", "stars_5"])
        for (y, m) in sorted(monthly):
            c = monthly[(y, m)]
            w.writerow([f"{y:04d}-{m:02d}", c["count"],
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

    def iso(ts):
        if ts is None:
            return None
        seconds = ts / 1000.0 if ts > 10_000_000_000 else float(ts)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()

    stats = {
        "category": category,
        "source": source if not local_raw else os.path.basename(local_raw),
        "total_reviews_counted": total,
        "date_range": {"min": iso(min_ts), "max": iso(max_ts)},
        "rating_distribution": {str(k): v for k, v in sorted(rating_dist.items())},
        "avg_rating": round(sum(k * v for k, v in rating_dist.items()) / total, 4) if total else None,
        "unique_users": len(users) if track_uniques else "not_tracked",
        "unique_items_parent_asin": len(items) if track_uniques else "not_tracked",
        "helpful_field_name_in_file": helpful_field_seen,
        "fact_sample_rows": len(sample_rows),
        "fact_sample_method": "first-N rows of the file, in file order",
        "monthly_cells": len(monthly),
    }
    with open(os.path.join(out_dir, "stats.json"), "w") as fh:
        json.dump(stats, fh, indent=2)

    if args.delete_raw and local_raw and os.path.exists(local_raw):
        os.remove(local_raw)
        print(f"deleted raw file {local_raw}", flush=True)

    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
