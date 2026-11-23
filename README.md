# Amazon Reviews 2023 — Analysis of a 571-Million-Review Corpus

A staged, category-by-category analysis of the largest public Amazon review
dataset, built with a streaming pipeline that never holds more than one
category file on disk at a time.

## Data source & credit

- **Dataset:** *Amazon Reviews 2023*, collected by **McAuley Lab, UC San Diego**
- **Project page:** https://amazon-reviews-2023.github.io/
- **Hugging Face:** https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
- **Citation:** Hou, Li, He, Yan, Chen & McAuley, *Bridging Language and Items
  for Retrieval and Recommendation*, arXiv:2403.03952 (2024)
- The dataset card declares no formal licence; this project credits the lab,
  cites the paper, and publishes aggregate statistics plus a bounded sample of
  derived fields only — no bulk review text is redistributed.
- Note: this is an academic dataset of **amazon.com (USA)** reviews. It is not
  an official Amazon release, and it is not amazon.de data.

## Honest scope

- The **full corpus** is **571.54M reviews** (54.51M users, 48.19M items,
  33 categories, May 1996 – Sep 2023) — these are the lab's *published*
  figures; see `data/source_report.md` for the measured per-category file
  sizes (275.4 GB of raw review files in total).
- This project processes the corpus **category by category, in stages**. Every
  "processed" number in this repo comes from a `stats.json` produced by
  counting that category's stream directly — never from the rounded published
  tables.

## Progress

**14,757,532 reviews verified so far** across 11 of 34 category files
(each counted from its own stream; see Verification below). Combined
per-category numbers live in `analysis/category_summary.csv` (built by
`analysis/build_category_summary.py` from the pipeline outputs), and the
analysis question bank is in `analysis/QUESTIONS.md`.

| Category | Reviews counted (verified) | Avg rating | Date range | Status |
|---|---:|---:|---|---|
| Software | 4,880,181 | 3.94 | 1999-03 – 2023-09 | ✅ Stage 2 |
| Musical_Instruments | 3,017,439 | 4.26 | 1999-08 – 2023-09 | ✅ Stage 2 |
| Amazon_Fashion | 2,500,939 | 3.97 | 2002-05 – 2023-09 | ✅ Stage 2 |
| Appliances | 2,128,605 | 4.22 | 2000-10 – 2023-09 | ✅ Stage 2 |
| All_Beauty | 701,528 | 3.96 | 2000-11 – 2023-09 | ✅ Stage 2 |
| Handmade_Products | 664,162 | 4.50 | 2007-05 – 2023-09 | ✅ Stage 2 |
| Health_and_Personal_Care | 494,121 | 4.00 | 2001-02 – 2023-09 | ✅ Stage 2 |
| Gift_Cards | 152,410 | 4.55 | 2008-08 – 2023-09 | ✅ Stage 2 |
| Digital_Music | 130,434 | 4.53 | 1997-09 – 2023-09 | ✅ Stage 1 proof run (v2 outputs added in Stage 2) |
| Magazine_Subscriptions | 71,497 | 4.04 | 2001-10 – 2023-08 | ✅ Stage 2 |
| Subscription_Boxes | 16,216 | 3.77 | 2017-01 – 2023-08 | ✅ Stage 2 |
| …23 more categories + Unknown | — | — | — | planned, one stage each |

## Pipeline

`scripts/stream_category.py` streams one category file (local or HTTP,
plain or gzipped JSONL) line by line and writes, per category, into
`data/processed/<Category>/`:

- `monthly_aggregates.csv` — reviews per year-month with rating counts,
  average rating, verified-purchase share and helpful votes
- `rating_distribution.csv` — counts and share per star rating
- `fact_sample.csv` — bounded sample (max 50,000 rows, first-N in file order)
  of per-review derived fields: user, item, rating, month, verified flag,
  helpful votes
- `stats.json` — the category's verified totals, counted from the stream

`scripts/stream_category_v2.py` (Stage 2; v1 kept untouched) produces all
of the above in the same formats, plus, per category:

- `products_<Category>.csv` — per-product aggregates (review count, average
  rating, 5★/1★ shares, verified share, helpful votes) for every product
  in the category — up to 825,869 products for Amazon_Fashion
- `verified_split.csv` — verified vs unverified review counts and average
  ratings
- `reviewer_concentration.csv` — reviews-per-user distribution in buckets
  (1, 2, 3–5, 6–10, 11–50, 51+): how much of a category is written by
  one-time reviewers vs a repeat-reviewer community
- `yearly_satisfaction.csv` — per-year review volume, average rating and
  5★ share
- `stats_v2.json` — the v2 headline numbers

`scripts/verify_category.py` re-checks every processed category: monthly
aggregates, rating distribution, yearly, verified-split, concentration
and product tables must all sum exactly to the counted total, and the
total is cross-checked against the lab's published count.

Raw downloads are deleted immediately after processing (never more than
~4 GB of raw data on disk at once).

## Verification

Stage 1 (Digital_Music): the stream counted **130,434** reviews, **100,952**
unique users and **70,511** unique items — matching the lab's published
130.4K / 101.0K / 70.5K for this category. Monthly aggregates and the rating
distribution each sum exactly to the counted total.

Stage 2 (10 more categories, 14,627,098 further reviews): every category
passes all internal consistency checks in `scripts/verify_category.py`,
and every counted total agrees with the lab's published (rounded) count
within rounding — the largest absolute difference is Appliances
(2,128,605 counted vs 2.1M published, i.e. inside the published figure's
own rounding unit). Combined verified total after Stage 2:
**14,757,532 reviews**.
