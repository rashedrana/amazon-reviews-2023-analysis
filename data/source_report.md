# Amazon Reviews 2023 — Source Verification Report

Stage 1 verification, run 2026-11-23. Every figure below was read from the live sources listed — not from memory.

## Source

- **Dataset:** "Amazon Reviews 2023", collected in 2023 by **McAuley Lab, UC San Diego (UCSD)** — an academic research lab. It is NOT an official Amazon release; the reviews are from **amazon.com (USA)**.
- **Project page:** https://amazon-reviews-2023.github.io/
- **Hugging Face:** https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023 (161,362 hub downloads at time of check)
- **APIs used for this report:**
  - https://huggingface.co/api/datasets/McAuley-Lab/Amazon-Reviews-2023
  - https://huggingface.co/api/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main?recursive=true (file sizes)
  - https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/raw/main/README.md (dataset card)
- **Original UCSD host** (linked from the lab page): https://datarepo.eng.ucsd.edu/mcauley_group/data/amazon_2023/ — files there are `.jsonl.gz`; the HF mirror stores the same review files uncompressed as `.jsonl`.

## Published corpus figures (lab page, "Compared to Previous Versions")

| Measure | Published figure |
|---|---|
| Reviews | **571.54M** |
| Users | **54.51M** |
| Items | **48.19M** (counted from the reviews; some items lack metadata) |
| Categories | **33** named categories (+ an "Unknown" bucket, a 34th file) |
| Timespan | **May 1996 – Sep 2023** |
| Review-text tokens | 30.14B |

## Licence / usage terms — as actually stated

- The Hugging Face dataset card declares **no licence**: no `license:` field in the card metadata and no licence tag (verified via the HF API, 2026-11-23). Neither the card nor the project page states formal terms of use.
- The one expectation both sources state is **citation** of the accompanying paper: Hou, Li, He, Yan, Chen & McAuley, *"Bridging Language and Items for Retrieval and Recommendation"*, arXiv:2403.03952 (2024).
- Working rule for this project: credit McAuley Lab / UCSD everywhere, cite the paper, and publish only aggregate statistics plus a bounded sample of derived fields — no bulk redistribution of review text.

## Files on Hugging Face — measured via the tree API (2026-11-23)

Raw review files total **275.40 GB** (uncompressed JSONL); metadata files total **101.40 GB**. Sorted by review-file size:

| Category | Review file size (HF) | Meta file size (HF) | Published review count (lab page, rounded) |
|---|---:|---:|---:|
| Home_and_Kitchen | 31,408.9 MB | 11,788.8 MB | 67.4M |
| Unknown | 29,933.8 MB | 674.8 MB | 63.8M |
| Clothing_Shoes_and_Jewelry | 27,810.1 MB | 17,960.5 MB | 66.0M |
| Electronics | 22,616.2 MB | 5,246.1 MB | 43.9M |
| Books | 20,121.2 MB | 14,697.6 MB | 29.5M |
| Kindle_Store | 15,800.6 MB | 6,865.2 MB | 25.6M |
| Tools_and_Home_Improvement | 12,779.1 MB | 4,850.7 MB | 27.0M |
| Health_and_Household | 11,395.4 MB | 2,468.5 MB | 25.6M |
| Beauty_and_Personal_Care | 11,021.5 MB | 2,835.2 MB | 23.9M |
| Cell_Phones_and_Accessories | 9,342.6 MB | 4,015.2 MB | 20.8M |
| Sports_and_Outdoors | 9,256.9 MB | 4,132.3 MB | 19.6M |
| Automotive | 8,727.7 MB | 5,345.6 MB | 20.0M |
| Movies_and_TV | 8,391.4 MB | 1,285.7 MB | 17.3M |
| Pet_Supplies | 8,350.8 MB | 1,571.3 MB | 16.8M |
| Patio_Lawn_and_Garden | 7,748.2 MB | 2,714.1 MB | 16.5M |
| Toys_and_Games | 7,316.1 MB | 2,637.9 MB | 16.3M |
| Grocery_and_Gourmet_Food | 5,974.0 MB | 1,382.1 MB | 14.3M |
| Office_Products | 5,776.8 MB | 2,146.5 MB | 12.8M |
| Arts_Crafts_and_Sewing | 3,945.1 MB | 2,170.2 MB | 9.0M |
| CDs_and_Vinyl | 3,287.2 MB | 948.9 MB | 4.8M |
| Baby_Products | 2,947.8 MB | 691.0 MB | 6.0M |
| Video_Games | 2,682.9 MB | 437.4 MB | 4.6M |
| Industrial_and_Scientific | 2,347.0 MB | 1,130.0 MB | 5.2M |
| Software | 1,869.2 MB | 256.2 MB | 4.9M |
| Musical_Instruments | 1,557.8 MB | 631.9 MB | 3.0M |
| Amazon_Fashion | 1,051.3 MB | 1,422.4 MB | 2.5M |
| Appliances | 929.5 MB | 285.3 MB | 2.1M |
| All_Beauty | 326.6 MB | 213.0 MB | 701.5K |
| Handmade_Products | 289.0 MB | 399.3 MB | 664.2K |
| Health_and_Personal_Care | 227.0 MB | 118.0 MB | 494.1K |
| Digital_Music | 78.8 MB | 67.1 MB | 130.4K |
| Gift_Cards | 50.2 MB | 2.0 MB | 152.4K |
| Magazine_Subscriptions | 33.3 MB | 4.1 MB | 71.5K |
| Subscription_Boxes | 9.0 MB | 1.4 MB | 16.2K |
| **TOTAL (34 files)** | **275.40 GB** | **101.40 GB** | **571.54M (all categories)** |

Notes:
- Review-record fields this project extracts: `rating`, `timestamp` (ms since epoch), `verified_purchase`, `helpful_vote`, `parent_asin`, `asin`, `user_id`. (The lab's example record spells the helpfulness field `helpful_votes`; the pipeline accepts both spellings and records which one a file actually uses.)
- Exact per-category review counts are NOT taken from the rounded lab table — each category's count is verified by counting the stream itself when that category is processed (see `data/processed/<Category>/stats.json`).

## Machine / disk at Stage 1

- Workspace filesystem (`df -h`, 2026-11-23): 150 GB total, **146 GB free** (3% used).
- Working rule for all stages: never more than ~4 GB of raw downloads on disk at once; each category file is stream-processed and its raw file deleted immediately afterwards.
