# Amazon Reviews 2023 — Analysis Question Bank

The question bank for this project, organised around the owner's themes:
best vs worst products and categories, when customers are most and least
satisfied, which kinds of customers review the most, verified vs unverified
behaviour, and helpfulness.

**Status legend**

- ✅ **Answerable now** — from the categories processed so far (Stage 1–2:
  11 categories, 14,757,532 verified reviews). Answers extend automatically
  as more categories are processed.
- 🔶 **Sample-based** — answerable now from `fact_sample.csv` (first 50,000
  reviews per category, in file order — a stated, bounded sample, not the
  full category).
- ⏳ **Later stage** — needs the remaining categories, the metadata files
  (titles, price, brand), or a small pipeline extension noted per question.

**Data files referenced** (per category `C` in `data/processed/C/`):
`monthly_aggregates.csv`, `rating_distribution.csv`, `fact_sample.csv`,
`products_C.csv`, `verified_split.csv`, `reviewer_concentration.csv`,
`yearly_satisfaction.csv`, `stats.json`, `stats_v2.json`, plus the combined
`analysis/category_summary.csv`.

---

## A. Best & worst products and categories

| # | Question | Answered by | Chart | Status |
|---|---|---|---|---|
| 1 | Which categories are rated highest and lowest overall (average rating, 5★ share, 1★ share)? | `analysis/category_summary.csv` → `avg_rating`, `share_5star`, `share_1star` | Sorted bar / lollipop | ✅ (11 of 33 categories so far; e.g. Gift_Cards 4.55 avg vs Subscription_Boxes 3.77) |
| 2 | Within a category, which products (≥100 reviews) are the best- and worst-rated? | `products_C.csv` → `parent_asin`, `reviews`, `avg_rating` (filter `reviews ≥ 100`) | Bar (top/bottom 20) | ✅ |
| 3 | Which products are the most polarising — loved and hated at once (high 5★ AND high 1★ shares)? | `products_C.csv` → `share_5star`, `share_1star` | Scatter (1★ share × 5★ share) | ✅ |
| 4 | Which products attract the most reviews in each category? | `products_C.csv` → `reviews` (sorted desc) | Bar | ✅ |
| 5 | Do heavily-reviewed products rate better or worse than niche products? | `products_C.csv` → `reviews` binned × `avg_rating` | Scatter / hexbin, or binned column | ✅ |
| 6 | What is the shape of each category's rating distribution — how J-shaped is it? | `rating_distribution.csv` → `rating`, `share` | Small-multiple columns | ✅ |
| 7 | Which product titles and brands earn the best ratings? | `products_C.csv` joined to **meta files** (`title`, `store`) on `parent_asin` | Bar | ⏳ meta stage |
| 8 | Does price predict rating — do expensive products satisfy more? | `products_C.csv` joined to **meta files** (`price`) on `parent_asin` | Scatter / binned line | ⏳ meta stage |

## B. Satisfaction over time — when are customers happiest?

| # | Question | Answered by | Chart | Status |
|---|---|---|---|---|
| 9 | How has the average rating evolved year by year, per category and overall? | `yearly_satisfaction.csv` → `year`, `avg_rating` | Multi-line | ✅ |
| 10 | Which years and months were customers most and least satisfied? | `yearly_satisfaction.csv` → `avg_rating`; `monthly_aggregates.csv` → `year_month`, `avg_rating` | Line + heatmap (year × month) | ✅ |
| 11 | Is there seasonality — which calendar months get the happiest (and angriest) reviews? | `monthly_aggregates.csv` aggregated by month-of-year → `avg_rating`, `stars_1`…`stars_5` | Column / radial | ✅ |
| 12 | How did review volume grow over time, and did the COVID years (2020–21) change ratings? | `monthly_aggregates.csv` → `reviews`, `avg_rating` | Dual-axis line | ✅ |
| 13 | Are customers getting harsher — has the 1★ share risen over time? | `monthly_aggregates.csv` → `stars_1` / `reviews` per year; `yearly_satisfaction.csv` → `share_5star` | Line | ✅ |
| 14 | Which category's satisfaction is improving fastest, and whose is declining? | `yearly_satisfaction.csv` → slope of `avg_rating` by `year`, compared across categories | Slope chart | ✅ |

## C. Who reviews — reviewer types and concentration

| # | Question | Answered by | Chart | Status |
|---|---|---|---|---|
| 15 | What share of reviewers write only a single review in a category? | `reviewer_concentration.csv` → bucket `1`, `share_of_reviewers` | Bar / donut | ✅ (67–95% depending on category) |
| 16 | How concentrated is reviewing — what share of all reviews comes from repeat reviewers (buckets 3–5 and up)? | `reviewer_concentration.csv` → `share_of_reviews` by bucket | Stacked bar | ✅ |
| 17 | Which categories have a real reviewer community vs mostly one-time drive-by reviewers? | `reviewer_concentration.csv` compared across categories (e.g. Software: 1-review users are 67% of reviewers but only 36% of reviews; Subscription_Boxes: 95% / 89%) | Stacked bar, categories × buckets | ✅ |
| 18 | Do prolific reviewers rate more harshly or more generously than one-time reviewers? | Needs rating sums per concentration bucket — pipeline extension (v2.1 output `reviewer_rating_by_bucket.csv`) | Grouped bar | ⏳ pipeline extension |
| 19 | Who are the single most prolific reviewers in the corpus? | Needs a per-user output (currently only bucketed counts are kept, by design) | Table | ⏳ pipeline extension |

## D. Verified vs unverified behaviour

| # | Question | Answered by | Chart | Status |
|---|---|---|---|---|
| 20 | Do verified purchasers rate higher or lower than unverified reviewers — and does the direction change by category? | `verified_split.csv` → `segment`, `avg_rating` | Grouped bar | ✅ (Direction really does flip: Appliances verified 4.25 vs unverified 3.53, but All_Beauty verified 3.95 vs unverified 4.08) |
| 21 | What share of reviews is verified, per category, and how has it changed over time? | `verified_split.csv` → `share_of_reviews`; `monthly_aggregates.csv` → `verified_share` by `year_month` | Bar + line | ✅ |
| 22 | Are unverified reviews more extreme (more 1★ and 5★) than verified ones? | Needs star counts split by verified flag — pipeline extension (v2.1) | Stacked bar | ⏳ pipeline extension |

## E. Helpfulness

| # | Question | Answered by | Chart | Status |
|---|---|---|---|---|
| 23 | Do higher-rated reviews earn more helpful votes? | `fact_sample.csv` → `rating` × `helpful_vote` | Box / binned column | 🔶 sample-based |
| 24 | Which products accumulate the most helpful votes? | `products_C.csv` → `helpful_votes` (sorted desc) | Bar | ✅ |
| 25 | Has helpful-vote engagement changed over time? | `monthly_aggregates.csv` → `helpful_votes` / `reviews` by `year_month` | Line | ✅ |
| 26 | Do verified reviews earn more helpful votes than unverified ones? | `fact_sample.csv` → `verified_purchase` × `helpful_vote` | Grouped bar | 🔶 sample-based |

---

## Coverage note

Every ✅ answer above is computed from the 11 categories processed in
Stages 1–2 (14,757,532 reviews, each counted from its own stream and
cross-checked against the lab's published counts). The remaining
22 categories + Unknown (~557M reviews) are processed in later stages;
the meta-file questions (7, 8) open once the metadata stage runs, and
questions 18, 19, 22 need the small v2.1 pipeline extension described in
their rows. No number in this bank is estimated — statuses say exactly
what the data on disk can and cannot answer today.
