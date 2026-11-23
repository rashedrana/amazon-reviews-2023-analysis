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

| Category | Reviews counted (verified) | Date range | Status |
|---|---:|---|---|
| Digital_Music | 130,434 | 1997-09 – 2023-09 | ✅ Stage 1 proof run |
| …33 more categories + Unknown | — | — | planned, one stage each |

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

Raw downloads are deleted immediately after processing (never more than
~4 GB of raw data on disk at once).

## Verification

Stage 1 (Digital_Music): the stream counted **130,434** reviews, **100,952**
unique users and **70,511** unique items — matching the lab's published
130.4K / 101.0K / 70.5K for this category. Monthly aggregates and the rating
distribution each sum exactly to the counted total.
