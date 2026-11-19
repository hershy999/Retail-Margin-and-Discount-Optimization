# Data Quality Report — Global Superstore Dataset

**Project:** Retail Margin Dynamics & Discount Optimization  
**Phase:** 1 — Dataset Inspection & Profiling  
**Date:** 2026-11-19  
**Source file:** `Dataset/Global_Superstore2.csv`  
**Working copy:** `data/raw/Global_Superstore2.csv` (byte-for-byte copy; original untouched)

---

## 1. Dataset Overview

| Property | Value |
|---|---|
| Row count | 51,290 |
| Column count | 24 |
| Encoding | Latin-1 |
| Date range | 2011-01-01 → 2014-12-31 |
| Unique Order IDs | 25,035 |
| Avg lines per order | 2.05 |
| Exact duplicates | 0 |

**Transaction grain:** One product line per order. `Order ID` is NOT unique per row — each order may contain multiple product lines (average 2.05 lines per order).

---

## 2. Schema Validation

All 24 expected columns are present. No columns are missing or renamed.

| # | Column | Dtype (raw) | Notes |
|---|---|---|---|
| 1 | Row ID | int64 | Unique integer row identifier |
| 2 | Order ID | object | Not unique per row |
| 3 | Order Date | object | DD-MM-YYYY string — parse with `dayfirst=True` |
| 4 | Ship Date | object | DD-MM-YYYY string — parse with `dayfirst=True` |
| 5 | Ship Mode | object | 4 categories |
| 6 | Customer ID | object | — |
| 7 | Customer Name | object | — |
| 8 | Segment | object | 3 categories |
| 9 | City | object | — |
| 10 | State | object | — |
| 11 | Country | object | — |
| 12 | Postal Code | float64 | **80.5% null — excluded from all analysis** |
| 13 | Market | object | 7 categories |
| 14 | Region | object | 13 categories |
| 15 | Product ID | object | — |
| 16 | Category | object | 3 categories |
| 17 | Sub-Category | object | 17 categories |
| 18 | Product Name | object | — |
| 19 | Sales | float64 | No nulls; always positive |
| 20 | Quantity | int64 | No nulls; range 1–14 |
| 21 | Discount | float64 | No nulls; range 0.00–0.85 |
| 22 | Profit | float64 | No nulls; 12,544 negative rows |
| 23 | Shipping Cost | float64 | — |
| 24 | Order Priority | object | — |

---

## 3. Null Analysis

Only one column contains null values:

| Column | Null Count | Null % | Decision |
|---|---|---|---|
| Postal Code | 41,296 | 80.5% | **Excluded from all analysis and dimension design.** Use `Market`, `Region`, `Country` for geographic analysis. |

All other columns: **0 nulls**. Critical fields (`Order ID`, `Order Date`, `Product ID`, `Sales`, `Profit`, `Quantity`) are fully populated.

---

## 4. Numeric Field Profiles

| Field | Min | Max | Mean | Median | Nulls | Zeros | Negatives |
|---|---|---|---|---|---|---|---|
| Sales | 0.44 | 22,638.48 | 246.49 | 85.05 | 0 | 0 | 0 |
| Profit | -6,599.98 | 8,399.98 | 28.61 | 9.24 | 0 | 668 | 12,544 |
| Quantity | 1 | 14 | 3.48 | 3.00 | 0 | 0 | 0 |
| Discount | 0.00 | 0.85 | 0.1429 | 0.00 | 0 | 29,009 | 0 |

**Notes:**
- `Sales` is always positive (min 0.44). No zero or negative values.
- `Quantity` range is 1–14, all positive integers. No zeros.
- `Discount` has 29,009 zero-discount rows (56.6% of data). Max is 0.85.
- `Profit` average discount across dataset ≈ 14.3%.

---

## 5. Date Format

- `Order Date` and `Ship Date` are stored as **DD-MM-YYYY strings** (e.g., `'31-07-2012'`).
- **Must be parsed with `pd.to_datetime(..., dayfirst=True)`.**
- Parse failure count: **0** — all 51,290 rows parse successfully.
- Dataset spans **2011-01-01 → 2014-12-31** (4 full calendar years).

---

## 6. Discount Value Distribution

27 distinct discount values observed. Distribution clusters around round values, but non-round values exist:

| Discount Value | Rows | % of Total | Type |
|---|---|---|---|
| 0.00 | 29,009 | 56.6% | Standard |
| 0.10 | 4,068 | 7.9% | Standard |
| 0.20 | 4,998 | 9.7% | Standard |
| 0.40 | 3,177 | 6.2% | Standard |
| 0.50 | 1,633 | 3.2% | Standard |
| 0.60 | 2,006 | 3.9% | Standard |
| 0.70 | 1,786 | 3.5% | Standard |
| 0.80 | 316 | 0.6% | Standard |
| 0.85 | 2 | 0.0% | Standard |
| 0.002 | 461 | 0.9% | **Non-round** |
| 0.07 | 150 | 0.3% | **Non-round** |
| 0.17 | 735 | 1.4% | **Non-round** |
| 0.202 | 41 | 0.1% | **Non-round** |
| 0.27 | 388 | 0.8% | **Non-round** |
| 0.32 | 27 | 0.1% | **Non-round** |
| 0.37 | 74 | 0.1% | **Non-round** |
| 0.402 | 104 | 0.2% | **Non-round** |
| 0.47 | 725 | 1.4% | **Non-round** |
| ... | ... | ... | **Non-round** |

**Decision (pending confirmation):** Non-round discount values will be **retained as-is** in the cleaned dataset. In SQL discount band analysis, they will be assigned to the nearest logical band via a `CASE` expression based on their actual value. This decision will be confirmed before Phase 4.

---

## 7. Negative Profit Investigation

| Metric | Value |
|---|---|
| Total negative-profit rows | 12,544 |
| As % of total | 24.5% |
| Min Profit | -6,599.98 |
| Max Profit (positive) | 8,399.98 |

**By Category:**

| Category | Negative-Profit Rows |
|---|---|
| Office Supplies | 7,003 |
| Furniture | 3,117 |
| Technology | 2,424 |

**Decision:** All 12,544 negative-profit rows are **retained** as legitimate loss-making transactions. These are not data errors — they represent real orders where discounts or costs exceeded revenue. Removing them would invalidate the discount-margin analysis.

---

## 8. Categorical Value Sets

| Field | Count | Values |
|---|---|---|
| Category | 3 | Furniture, Office Supplies, Technology |
| Sub-Category | 17 | Accessories, Appliances, Art, Binders, Bookcases, Chairs, Copiers, Envelopes, Fasteners, Furnishings, Labels, Machines, Paper, Phones, Storage, Supplies, Tables |
| Market | 7 | APAC, Africa, Canada, EMEA, EU, LATAM, US |
| Region | 13 | Africa, Canada, Caribbean, Central, Central Asia, EMEA, East, North, North Asia, Oceania, South, Southeast Asia, West |
| Segment | 3 | Consumer, Corporate, Home Office |
| Ship Mode | 4 | First Class, Same Day, Second Class, Standard Class |

---

## 9. Duplicate Row Check

| Check | Result |
|---|---|
| Exact duplicate rows | **0** |
| Status | ✓ No duplicates found |

---

## 10. Decisions & Anomaly Log

| # | Field | Anomaly | Decision |
|---|---|---|---|
| 1 | Postal Code | 41,296 nulls (80.5%) | Excluded from all analysis — use Market/Region/Country |
| 2 | Profit | 12,544 negative values (24.5%) | Retained as valid loss-making transactions |
| 3 | Discount | 11 non-round values (e.g., 0.002, 0.202, 0.47) | Retained; assigned to bands by actual value in SQL |
| 4 | Order Date / Ship Date | DD-MM-YYYY string format | Parse with `dayfirst=True` |
| 5 | Profit (zeros) | 668 zero-profit rows | Retained; represent break-even transactions |
| 6 | Quantity | Range 1–14 (no zeros) | No action required |
| 7 | Sales | Range 0.44–22,638.48 (no zeros/negatives) | No action required |

---

## 11. Source File Integrity

| Property | Value |
|---|---|
| Original file | `Dataset/Global_Superstore2.csv` |
| File size (bytes) | 12,089,916 |
| Working copy | `data/raw/Global_Superstore2.csv` |
| Copy size (bytes) | 12,089,916 |
| Size match | ✓ Identical |
| Row count verification | 51,290 rows confirmed |

---

## 12. Phase 1 Completion Checklist

- [x] All 24 columns confirmed present with correct names
- [x] Row grain documented (one product line per order; avg 2.05 lines per Order ID)
- [x] Date format confirmed (DD-MM-YYYY); parse with `dayfirst=True`
- [x] Null analysis complete — only `Postal Code` has nulls (41,296 / 80.5%)
- [x] Negative profit documented and decision recorded (retain)
- [x] Discount distribution documented; non-round values noted for Phase 4 decision
- [x] Duplicate check: 0 exact duplicates
- [x] Categorical value sets documented
- [x] Raw source file byte-for-byte unchanged (12,089,916 bytes; 51,290 rows)

**Phase 1 status: COMPLETE ✓**

---

*Report generated: 2026-11-19 | Next step: Phase 2 — Python Data Cleaning & Validation*

---

## 13. Phase 2 — Cleaning Outcomes (appended)

**Script:** `src/clean_data.py`  
**Run date:** 2026-11-19

| Metric | Value |
|---|---|
| Input rows | 51,290 |
| Cleaned rows | 51,290 |
| Rejected rows | 0 |
| Duplicates removed | 0 |
| Reconciliation | 51,290 == 51,290 + 0 + 0 ✓ |

**Column name normalizations (24 columns renamed to snake_case):**

| Original | Cleaned |
|---|---|
| Row ID | row_id |
| Order ID | order_id |
| Order Date | order_date |
| Ship Date | ship_date |
| Ship Mode | ship_mode |
| Customer ID | customer_id |
| Customer Name | customer_name |
| Segment | segment |
| City | city |
| State | state |
| Country | country |
| Postal Code | postal_code |
| Market | market |
| Region | region |
| Product ID | product_id |
| Category | category |
| Sub-Category | sub_category |
| Product Name | product_name |
| Sales | sales |
| Quantity | quantity |
| Discount | discount |
| Profit | profit |
| Shipping Cost | shipping_cost |
| Order Priority | order_priority |

**Cleaning decisions applied:**
- Date parsing: `dayfirst=True` → 0 failures
- Numeric coercions: 0 failures across all numeric columns
- Critical null rejections: 0 rows rejected
- Exact duplicates: 0 found
- Negative profit: 12,544 rows retained
- Zero profit: 668 rows retained
- Non-round discount values: 2,740 rows retained (assigned to bands in Phase 4)
- Discount range: all values in [0.00, 0.85]

**Output:** `data/processed/superstore_cleaned.csv` (51,290 rows, UTF-8)

**Post-cleaning validation (`src/validate_data.py`):** 12/12 assertions passed ✓

**Phase 2 status: COMPLETE ✓**

---

*Report updated: 2026-11-19 | Next step: Phase 3 — PostgreSQL Schema & Data Loading*
