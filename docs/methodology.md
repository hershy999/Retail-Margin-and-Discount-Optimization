# Project Methodology & Pipeline Architecture

**Project:** Retail Margin Dynamics & Discount Optimization  
**Dataset:** Global Superstore (2011–2014)  
**Author / Analyst:** Antigravity Data Analytics  
**Date:** 2026-11-19  

---

## 1. Executive Summary

This project conducts an empirical, observational investigation into the relationship between commercial discounting practices, sales volume, and bottom-line profitability for a multi-regional retailer.

The core question addressed: **Do aggressive discounts drive sufficient incremental gross profit, or do they destroy margin without proportional business value?**

Through Python data cleaning, PostgreSQL data warehousing, Apriori association rule mining, and Power BI What-If simulation, we demonstrate that discount levels above 20% severely erode margin, with discounts $\ge 40\%$ generating massive net operational losses (-\$771K net deficit).

---

## 2. End-to-End Pipeline Architecture

```
                       [ RAW SOURCE ]
                 Dataset/Global_Superstore2.csv
                (51,290 rows · Latin-1 encoding)
                                │
                                ▼
                      [ STAGE 1: PROFILING ]
                    src/profile_data.py
                docs/data_quality_report.md
                                │
                                ▼
                     [ STAGE 2: DATA CLEANING ]
                       src/clean_data.py
                      src/validate_data.py
                                │
              ┌─────────────────┴─────────────────┐
              ▼                                   ▼
    [ STAGE 3: WAREHOUSING ]            [ STAGE 5: BASKET MINING ]
      src/load_to_postgres.py             src/market_basket_analysis.py
       PostgreSQL 18 database              mlxtend Apriori algorithm
     (stg_superstore_sales & fact_sales)   data/processed/association_rules.csv
              │                                   │
              ▼                                   │
    [ STAGE 4: SQL VIEWS ]                        │
      sql/03_business_analysis.sql                │
      sql/04_create_views.sql                     │
      (7 reusable analytical views)               │
              │                                   │
              └─────────────────┬─────────────────┘
                                ▼
                      [ STAGE 6: REPORTING ]
                         Power BI Desktop
                  5-Page Interactive Dashboard
                     What-If Discount Slider
```

---

## 3. Data Engineering Decisions & Integrity Rules

1. **Transaction Grain:** One row represents an individual product line item within an order. Because a single order can contain multiple items, `order_id` is non-unique (average 2.05 lines per order). `row_id` serves as the fact table surrogate primary key.
2. **Negative Profit Retention:** 12,544 rows (24.5% of total records) exhibit negative profit values. These records reflect genuine loss-making commercial transactions where discounting and delivery costs exceeded net revenue. Filtering them out would bias the study; all 12,544 rows are retained.
3. **Postal Code Exclusion:** `Postal Code` contains 41,296 missing values (80.5% null). It is explicitly omitted from analytical dimensions; geography is modeled through `Market` (7 values), `Region` (13 values), and `Country`.
4. **Idempotent Execution:** Database loading truncates target staging and fact tables prior to bulk insertion, ensuring zero duplicate records upon rerun.

---

## 4. Key Analytical Formulas

- **Profit Margin %:**
  $$\text{Profit Margin \%} = \frac{\sum \text{Profit}}{\sum \text{Sales}} \times 100$$
  *Rule:* Must always be calculated using aggregated totals; never averaged across row-level percentages.
- **Derived Estimated Cost:**
  $$\text{Estimated Cost} = \text{Sales} - \text{Profit}$$
- **Estimated Pre-Discount Sales:**
  $$\text{Est. Pre-Discount Sales} = \frac{\text{Sales}}{1 - \text{Discount}} \quad (\text{guarding against } \text{Discount} = 1.0)$$
- **What-If Simulated Profit:**
  $$\text{Sim. Profit} = [\text{Est. Pre-Discount Sales} \times (1 - \text{What-If Discount})] - \text{Estimated Cost}$$

---

## 5. Analytical Limitations

- **Observational Nature:** All analyses reflect historical observational correlations. They do not prove causal relationships or customer price elasticity.
- **Fixed-Cost Simulation Assumption:** The What-If simulation assumes unit volumes and supplier acquisition costs remain static when discount sliders move.
