# SQL Business Analysis & Views Documentation

**Project:** Retail Margin Dynamics & Discount Optimization  
**Database:** PostgreSQL 18 (`retail_margin_db`)  
**Phase:** 4 — SQL Business Analysis & Views  
**Date:** 2026-11-19  

---

## 1. Overview & Objectives

Phase 4 translates the cleaned line-item transaction data in `fact_sales` into structured analytical queries and reusable database views (`vw_`). These views serve as the direct data source for the Power BI reporting layer.

### Key Metrics Defined:
- **Total Sales:** `ROUND(SUM(sales)::NUMERIC, 2)`
- **Total Profit:** `ROUND(SUM(profit)::NUMERIC, 2)`
- **Total Orders:** `COUNT(DISTINCT order_id)`
- **Total Units Sold:** `SUM(quantity)`
- **Average Discount:** `ROUND(AVG(discount)::NUMERIC, 4)`
- **Profit Margin %:** `ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2)`

---

## 2. Discount Band Analysis

### Distribution & Band Boundaries:
Analysis of the 27 distinct discount values in `fact_sales` revealed that discount rates span from 0.00 to 0.85. The relationship with profitability demonstrates severe margin degradation at higher discount levels:

| Discount Band | Discount Range | Row Count | Orders | Total Sales ($) | Total Profit ($) | Profit Margin % | Avg Discount |
|---|---|---|---|---|---|---|---|
| **No Discount** | `= 0.00` | 29,009 | 15,211 | 6,992,410.95 | 1,770,695.27 | **+25.32%** | 0.0000 |
| **Low** | `> 0.00 and < 0.20` | 5,955 | 3,833 | 2,516,047.89 | 393,728.24 | **+15.65%** | 0.1048 |
| **Medium** | `0.20 to < 0.40` | 6,188 | 4,222 | 1,728,204.94 | 74,193.26 | **+4.29%** | 0.2170 |
| **High** | `0.40 to < 0.60` | 5,988 | 3,541 | 1,048,666.92 | -368,042.04 | **-35.10%** | 0.4391 |
| **Very High** | `>= 0.60` | 4,150 | 2,347 | 357,171.20 | -403,117.44 | **-112.86%** | 0.6586 |

### Empirical Insights:
1. **Breakeven Threshold:** Profitability turns sharply negative when discount rates reach **40% or higher**.
2. **Profit Erosion:** High and Very High discount bands account for \$771,159.48 in combined net losses across 10,138 transactions.
3. **No Discount Outperformance:** Zero-discount orders generate \$1.77M in profit at a healthy 25.32% margin, representing the vast majority of net company profit.

---

## 3. Category & Sub-Category Performance

| Category | Sub-Category | Total Sales ($) | Total Profit ($) | Profit Margin % | Avg Discount | Total Units |
|---|---|---|---|---|---|---|
| **Technology** | Copiers | 1,509,436.27 | 258,567.55 | **17.13%** | 0.1171 | 7,454 |
| **Technology** | Accessories | 749,237.02 | 129,626.31 | **17.30%** | 0.1205 | 10,946 |
| **Technology** | Phones | 1,706,824.14 | 216,717.01 | **12.70%** | 0.1458 | 11,870 |
| **Technology** | Machines | 779,060.07 | 58,867.87 | **7.56%** | 0.1696 | 4,906 |
| **Office Supplies**| Paper | 244,291.72 | 59,207.68 | **24.24%** | 0.1095 | 12,822 |
| **Office Supplies**| Labels | 73,404.03 | 15,010.51 | **20.45%** | 0.1204 | 9,322 |
| **Office Supplies**| Envelopes | 170,904.30 | 29,601.12 | **17.32%** | 0.1317 | 8,380 |
| **Office Supplies**| Binders | 461,911.51 | 72,449.85 | **15.68%** | 0.1792 | 21,429 |
| **Office Supplies**| Art | 372,091.97 | 57,953.91 | **15.58%** | 0.1174 | 16,301 |
| **Office Supplies**| Appliances | 1,011,064.31 | 141,680.59 | **14.01%** | 0.1417 | 6,078 |
| **Office Supplies**| Fasteners | 83,242.32 | 11,525.42 | **13.85%** | 0.1406 | 8,390 |
| **Office Supplies**| Storage | 1,127,085.86 | 108,461.49 | **9.62%** | 0.1385 | 16,917 |
| **Office Supplies**| Supplies | 243,074.22 | 22,583.26 | **9.29%** | 0.1279 | 8,543 |
| **Furniture** | Furnishings | 385,578.26 | 46,967.43 | **12.18%** | 0.1511 | 11,225 |
| **Furniture** | Bookcases | 1,466,572.24 | 161,924.42 | **11.04%** | 0.1538 | 8,310 |
| **Furniture** | Chairs | 1,501,681.76 | 140,396.27 | **9.35%** | 0.1631 | 12,336 |
| **Furniture** | Tables | 757,041.92 | -64,083.39 | **-8.46%** | 0.2907 | 3,083 |

**Critical Observation:** **Tables** is the only sub-category with a net negative profit margin (-8.46%, -\$64,083.39), directly coinciding with the highest average discount rate (29.07%) across all sub-categories.

---

## 4. PostgreSQL Views Specification

All seven views have been deployed and verified in `retail_margin_db`:

| View Name | Schema Description | Intended Power BI Visuals |
|---|---|---|
| `vw_retail_kpis` | Aggregated overall revenue, profit, units, orders, margin %, avg discount | Executive Overview KPI summary cards |
| `vw_discount_profitability` | Sales, profit, margin %, orders grouped by 5 standardized discount bands | Discount vs. Margin clustered bar chart, band distribution table |
| `vw_category_profitability` | Performance grouped by category and sub-category | Category Margin bar chart, Sub-category matrix |
| `vw_product_performance` | Product-level metrics sorted by profitability descending | Top 10 profitable products, bottom 10 margin products, drill-through |
| `vw_region_profitability` | Performance grouped by Market, Region, and Country | Geographic heatmaps, regional sales/profit charts |
| `vw_monthly_performance` | Monthly metrics (2011–2014) with running cumulative totals | 4-year trend line charts, cumulative sales growth |
| `vw_yoy_performance` | Monthly metrics compared to prior year via `LAG(12)` with YoY growth % | Year-over-year revenue & profit comparison charts |

---

## 5. Verification & Spot-Check Results

Spot-check validation script `src/spotcheck_views.py` confirmed 100% numerical consistency between PostgreSQL views and cleaned CSV:
- **`vw_retail_kpis`:**
  - Sales: \$12,642,501.91 (Match: `True`)
  - Profit: \$1,467,457.29 (Match: `True`)
  - Row Count: 51,290 (Match: `True`)
- **`vw_discount_profitability`:**
  - Sum of band sales equals total sales (Match: `True`)
  - Sum of band profit equals total profit (Match: `True`)
- **`vw_monthly_performance`:**
  - 2011 Sales slice: \$2,259,450.90 (Match: `True`)
  - 2011 Profit slice: \$248,940.81 (Match: `True`)

Phase 4 status: **COMPLETE ✓**
