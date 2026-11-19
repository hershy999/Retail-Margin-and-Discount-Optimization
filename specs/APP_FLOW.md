# APP_FLOW.md — End-to-End Data Workflow

**Version:** 1.1  
**Status:** Draft — awaiting approval  
**Last updated:** Dashboard navigation, theme switching, chart/table toggle, drill-through, tooltip, and What-If interaction flows added

This document describes the complete data flow from the raw source file to the final Power BI dashboard. Each stage lists its inputs, process, outputs, and validation checks.

---

## Overview

```
Stage 1 → Stage 2 → Stage 3 → Stage 4 → Stage 6
                 ↘                        ↗
                  Stage 5 (MBA) ──────────
```

Stages 3–4 (database) and Stage 5 (MBA) run independently after Stage 2 and both feed Stage 6 (Power BI).

---

## Stage 1 — Dataset Inspection & Profiling

**Trigger:** First time working with the dataset, or when the source file changes.

**Input:** `Dataset/Global_Superstore2.csv` (Latin-1 encoding, 51,290 rows, 24 columns)

**Process:**
1. Load the CSV with `encoding='latin1'`.
2. Confirm all 24 column names and their dtypes.
3. Identify the row grain: one product line within one order (Order ID is not unique per row).
4. Profile key numeric fields: Sales, Profit, Quantity, Discount.
5. Document nulls, duplicates, date ranges, and categorical value sets.
6. Record findings in `docs/data_quality_report.md`.

**Key findings from actual dataset:**
- 51,290 rows, 25,035 distinct Order IDs (avg 2.05 lines per order)
- Date range: 2011-01-01 to 2014-12-31
- `Postal Code`: 41,296 nulls — excluded from geographic analysis
- `Profit`: 12,544 negative values (~24.5%) — legitimate loss-making transactions
- `Discount`: 0.00–0.85; non-round values (0.002, 0.202, etc.) present
- Zero exact duplicate rows

**Outputs:**
- Profiling summary in `docs/data_quality_report.md`
- No files modified; raw data untouched

**Validation:**
- Confirm row count = 51,290
- Confirm all 24 expected columns are present with correct names

---

## Stage 2 — Python Data Cleaning

**Trigger:** After Stage 1 profiling is complete and reviewed.

**Input:** `Dataset/Global_Superstore2.csv`

**Script:** `src/clean_data.py`

**Process:**
1. Read source file (`encoding='latin1'`).
2. Strip whitespace from all column names; rename to `snake_case`.
3. Parse `order_date` and `ship_date` as datetime with `dayfirst=True` (DD-MM-YYYY format).
4. Confirm `sales`, `profit`, `quantity`, `discount` are numeric; coerce and log any failures.
5. **Null handling:**
   - Reject rows where `order_id`, `order_date`, `product_id`, or `sales` is null.
   - Log and document decisions for other nullable fields (e.g., `postal_code`).
6. **Duplicates:** Check for and remove exact duplicate rows (0 expected; safety check).
7. **Negative profit:** Retain all negative-profit rows with a note in the cleaning log.
8. **Discount non-round values:** Flag rows with values like 0.002 and 0.202; retain pending approval.
9. Write cleaned data to `data/processed/superstore_cleaned.csv`.
10. Write rejected rows (if any) to `data/rejected/rejected_records.csv` with a `rejection_reason` column.
11. Print and save cleaning log: input rows, cleaned rows, rejected rows, action summary.

**Outputs:**
- `data/processed/superstore_cleaned.csv`
- `data/rejected/rejected_records.csv` (if any rows rejected)
- Cleaning log (console + `docs/data_quality_report.md` update)

**Validation:**
- `input_rows = cleaned_rows + rejected_rows`
- No nulls in `order_id`, `order_date`, `product_id`, `sales`
- `data/raw/` or `Dataset/` source file hash unchanged

---

## Stage 3 — PostgreSQL Schema Design & Data Loading

**Trigger:** After Stage 2 produces a validated cleaned CSV.

**Input:** `data/processed/superstore_cleaned.csv`

**Scripts / SQL files:**
- `sql/01_create_schema.sql` — creates tables
- `src/load_to_postgres.py` — loads cleaned CSV into staging
- `sql/02_data_validation.sql` — post-load reconciliation

**Process:**
1. Run `sql/01_create_schema.sql` to create the database schema:
   - `stg_superstore_sales`: staging table (direct load, all columns)
   - `fact_sales`: validated fact table with correct types and NOT NULL constraints on key fields
   - `dim_date` (optional): calendar dimension if useful for YoY queries
2. Run `src/load_to_postgres.py`:
   - Truncate staging before each load (idempotent).
   - Use `COPY` or bulk insert from cleaned CSV.
   - Insert validated rows into `fact_sales`.
3. Run `sql/02_data_validation.sql`:
   - Row count in `fact_sales` = row count in cleaned CSV
   - `SUM(sales)` and `SUM(profit)` match between CSV and database
   - No nulls in key columns
   - No duplicate `row_id` values

**Outputs:**
- Populated `stg_superstore_sales` and `fact_sales` tables in PostgreSQL
- Validation query results

**Validation:** All checks in `sql/02_data_validation.sql` must pass before proceeding.

---

## Stage 4 — SQL Business Analysis

**Trigger:** After Stage 3 load is validated.

**Input:** `fact_sales` (and `dim_date` if created)

**SQL files:**
- `sql/03_business_analysis.sql` — all analysis queries
- `sql/04_create_views.sql` — creates the seven Power BI views

**Analyses produced:**

| Analysis | Method |
|---|---|
| Overall KPIs | Simple aggregations on `fact_sales` |
| Discount-band analysis | `CASE` statement to group discount into bands; aggregate per band |
| Category & sub-category profitability | `GROUP BY category, sub_category` |
| Product performance | `GROUP BY product_id, product_name`; sort by profit asc/desc |
| Regional analysis | `GROUP BY market, region, country` |
| Monthly/yearly trends | `DATE_TRUNC` to month/year; aggregate |
| Running totals | `SUM(sales) OVER (ORDER BY month)` |
| Year-over-year comparison | `LAG(total_sales, 1) OVER (PARTITION BY month ORDER BY year)` |

**Views created:**

| View | Contents |
|---|---|
| `vw_retail_kpis` | Total sales, profit, quantity, avg discount, profit margin % |
| `vw_discount_profitability` | Sales, profit, margin per discount band |
| `vw_category_profitability` | Sales, profit, margin per category and sub-category |
| `vw_product_performance` | Sales, profit, margin per product; flags high-sales/low-profit |
| `vw_region_profitability` | Sales, profit, margin per market and region |
| `vw_monthly_performance` | Monthly sales, profit, running totals |
| `vw_yoy_performance` | Year-over-year sales and profit comparison |

**Outputs:**
- `sql/03_business_analysis.sql` with documented queries
- Seven `vw_` views queryable in PostgreSQL

**Validation:**
- Spot-check KPI totals against cleaned CSV (`pandas` aggregation as reference)
- Run each view; confirm non-empty results
- Verify window function output on a known single-year slice

---

## Stage 5 — Market Basket Analysis

**Trigger:** After Stage 2 cleaned CSV is available. Runs independently of Stages 3–4.

**Input:** `data/processed/superstore_cleaned.csv`

**Notebook:** `notebooks/02_market_basket_analysis.ipynb`

**Process:**
1. Load cleaned CSV; confirm `order_id` and `product_name` columns are present and non-null.
2. Group `product_name` values by `order_id` → list of products per order.
3. Build binary basket matrix using `mlxtend.preprocessing.TransactionEncoder` or `pd.get_dummies`.
4. Confirm matrix row count = 25,035 (distinct Order IDs).
5. Run `apriori(basket_matrix, min_support=<threshold>, use_colnames=True)`.
   - Choose threshold by inspecting item frequency; document the choice.
6. Generate association rules with `association_rules(frequent_itemsets, metric='lift', min_threshold=1)`.
7. Filter: confidence ≥ chosen threshold; lift > 1; remove trivially weak rules.
8. Sort by lift descending.
9. Spot-check a top rule manually against the raw order data.
10. Write plain-language interpretation of the top 10–20 rules.
11. Export to `data/processed/association_rules.csv`.

**Outputs:**
- `notebooks/02_market_basket_analysis.ipynb`
- `data/processed/association_rules.csv` (columns: antecedents, consequents, support, confidence, lift)
- Short interpretation in `docs/market_basket_analysis.md`

**Validation:**
- Basket matrix row count = 25,035
- Support values: 0 ≤ support ≤ 1
- Confidence values: 0 ≤ confidence ≤ 1
- Lift values: lift > 0 (filtered to > 1 for export)
- Rules file is non-empty before Power BI import

**Known constraint:** Many orders contain only one product line (single-item baskets). These orders cannot generate multi-item association rules. The fraction of multi-item orders will be reported; support thresholds will be calibrated accordingly.

---

## Stage 6 — Power BI Dashboard

**Trigger:** After Stages 4 (SQL views) and 5 (association rules CSV) are both complete and validated.

**Inputs:**
- PostgreSQL: seven `vw_` views
- `data/processed/association_rules.csv`

**Setup:**
1. Connect Power BI Desktop to PostgreSQL (Import or DirectQuery mode).
2. Import each `vw_` view as a separate table in the data model.
3. Import `association_rules.csv` as a flat table.
4. Create a dedicated **Measures** table (no data, only DAX measures).
5. Define relationships where needed (e.g., `dim_date` ↔ fact views on date key).
6. Apply the light theme JSON file from `powerbi/themes/` as the default report theme.

**DAX measures (minimum set):**

| Measure | Formula |
|---|---|
| `Total Sales` | `SUM(fact_sales[sales])` |
| `Total Profit` | `SUM(fact_sales[profit])` |
| `Profit Margin %` | `DIVIDE([Total Profit], [Total Sales], 0) * 100` |
| `Avg Discount` | `AVERAGE(fact_sales[discount])` |
| `Total Orders` | `DISTINCTCOUNT(fact_sales[order_id])` |
| `Estimated Cost` | `SUM(fact_sales[sales]) - SUM(fact_sales[profit])` |
| `Sim Sales` | `[Est Pre-discount Sales] * (1 - [What-If Discount])` |
| `Sim Profit` | `[Sim Sales] - [Estimated Cost]` |
| `Sim Profit Margin %` | `DIVIDE([Sim Profit], [Sim Sales], 0) * 100` |

**Dashboard pages:**

| Page | Business question answered |
|---|---|
| 1 — Executive Overview | What is the overall business performance (2011–2014)? |
| 2 — Discount & Margin Analysis | How does discounting relate to profit margin? |
| 3 — Product & Category Analysis | Which products and categories drive or erode profit? |
| 4 — Market Basket Insights | Which products are frequently bought together? |
| 5 — Discount What-If Simulator | How would profit change under a different discount rate? |

---

## Dashboard Interaction Flows

### Navigation between pages

```
User opens the dashboard (lands on Page 1 — Executive Overview)
        │
        ├─ Header navigation bar visible on all pages
        │   Buttons: [Executive Overview] [Discount & Margin] [Product & Category]
        │             [Market Basket] [What-If Simulator]
        │
        ├─ Active page button is highlighted (filled background or accent border)
        ├─ Clicking any button navigates directly to that page (Power BI Page Navigation action)
        └─ No browser back/forward — navigation is always through the button bar
```

Navigation buttons are implemented as Power BI button visuals with the **Page navigation** action. All five buttons are present on every page in the same position.

---

### Slicer and cross-filter interaction

```
User selects a slicer value (e.g., Year = 2013, Category = Technology)
        │
        ├─ All visuals on the current page filter to the selection
        ├─ Slicers are synced across pages where the same field appears
        │   (use Power BI Sync Slicers to propagate Year, Market, Segment selections)
        │
        ├─ User clicks a bar in a chart
        │   → Cross-filter: other visuals on the page highlight/filter to that value
        │   → Click the same bar again to deselect
        │
        └─ "Clear filters" button (or native slicer eraser) resets all selections on the page
```

Cross-filtering is enabled between visuals on the same page. Document any intentional exceptions (e.g., KPI summary cards that should not be filtered by chart clicks on Page 1).

---

### Light / dark theme toggle

```
User clicks the theme toggle button (top-right corner, all pages)
        │
        ├─ Light → Dark:
        │   Power BI triggers bookmark "Theme_Dark"
        │   Page background switches to #18273E
        │   Card backgrounds switch to #3C4763
        │   Text switches to #FBFBF9
        │   Accent colour (#DEBAAC) remains consistent
        │
        └─ Dark → Light:
            Power BI triggers bookmark "Theme_Light"
            Page background switches to #FBFBF9 / #EEEBE4
            Card backgrounds switch to #FFFFFF
            Text switches to #18273E
```

The toggle button updates the bookmark state. Because bookmarks in Power BI do not natively apply a different theme JSON file at runtime, the theme implementation uses one of two approaches (confirm during implementation):
- **Option A:** A single theme JSON that covers both states using report-level colour overrides, controlled via bookmarks and conditional formatting.
- **Option B:** Two separate `.pbix` versions (not ideal for a portfolio; document if chosen).

The chosen approach and any limitations must be documented in `docs/dashboard_guide.md`.

---

### Chart / table toggle (Pages 2, 3, 4)

```
User is on Page 2 — Discount & Margin Analysis, viewing the discount-band bar chart
        │
        ├─ Clicks "Show Table" button
        │   → Bookmark "TableView_P2" is triggered
        │   → Chart visual visibility: OFF (hidden in Selection pane)
        │   → Table/matrix visual visibility: ON
        │   → Button label changes to "Show Chart"
        │
        └─ Clicks "Show Chart"
            → Bookmark "ChartView_P2" is triggered
            → Table visibility: OFF
            → Chart visibility: ON
            → Button label returns to "Show Table"
```

The table view shows the same underlying data as the chart, formatted as a readable matrix. It includes the same filters and slicer context. This pattern repeats on Pages 3 and 4 with page-specific bookmarks.

---

### Drill-through (Page 3 — Product & Category Analysis)

```
User right-clicks a product bar on the product ranking visual (Page 3)
        │
        ├─ Power BI shows the drill-through context menu
        ├─ User selects "Drill through → Product Detail"
        │
        └─ Product Detail page loads, filtered to that product
            Shows: full order history, sales/profit trend, discount distribution,
                   order quantities by region
            Back button (auto-generated by Power BI) returns to Page 3
```

The Product Detail page is a drill-through page — it is not part of the five main pages and does not appear in the navigation bar. It is marked as a drill-through page in its Power BI page settings.

---

### Report-page tooltips

```
User hovers over a data point on a trend chart (Pages 1, 2)
        │
        └─ A tooltip page appears showing:
               - Total Sales for that period
               - Total Profit for that period
               - Profit Margin %
               - Avg Discount for that period
           The tooltip disappears when the cursor moves away.
```

Tooltip pages are small report pages (e.g., 320×240 canvas) set as tooltip pages in Power BI page settings. They are not part of the five main pages and do not appear in the navigation bar.

---

### What-If simulator interaction (Page 5)

```
User navigates to Page 5 — Discount What-If Simulator
        │
        ├─ Page loads showing Baseline KPIs (actual historical values)
        │   Cards: Total Sales, Total Profit, Profit Margin %
        │
        ├─ User moves the What-If Discount slider (e.g., from 14% to 25%)
        │   → DAX measures recalculate:
        │       Sim Sales = Estimated Pre-discount Sales × (1 - 0.25)
        │       Sim Profit = Sim Sales - Estimated Cost
        │       Sim Profit Margin % = Sim Profit / Sim Sales * 100
        │   → Sim KPI cards update: Sim Profit, Sim Profit Margin %
        │   → Variance card updates: Sim Profit - Baseline Profit (colour-coded)
        │   → Combo chart updates: Sim Sales vs Sim Profit by category
        │
        ├─ Disclaimer text box is always visible below the KPI cards:
        │   "This simulation holds quantity and estimated cost constant.
        │    It does not forecast customer demand or guarantee real-world outcomes."
        │
        └─ User moves slider back to match actual avg discount (~14%)
            → Sim values converge toward baseline (small differences due to rounding)
```

No slicers on Page 5 that would conflict with the What-If parameter logic. If category-level filtering is desired on Page 5, evaluate whether a category slicer produces meaningful results with the simulation formula before adding it.

---

**Outputs:**
- `powerbi/retail_margin_dashboard.pbix`
- `powerbi/themes/light_theme.json`
- `powerbi/themes/dark_theme.json`

**Validation:**
- DAX KPI totals match SQL view totals for the same period.
- What-If slider updates all scenario measures correctly across the full slider range.
- All slicers cross-filter consistently across all pages.
- Theme toggle switches all visual backgrounds, text colours, and accents correctly on every page.
- Chart/table toggle works on Pages 2, 3, and 4 without breaking cross-filter context.
- Drill-through opens the correct product detail context from Page 3.
- Tooltip pages display on hover for the main trend charts.
- Association rules data displays correctly on Page 4.
- All currency and percentage formats are applied consistently in both themes.

---

## Expected Outputs by Stage

| Stage | Output file(s) |
|---|---|
| 1 | `docs/data_quality_report.md` (profile section) |
| 2 | `data/processed/superstore_cleaned.csv`, `data/rejected/` (if applicable), cleaning log |
| 3 | PostgreSQL tables: `stg_superstore_sales`, `fact_sales` |
| 4 | `sql/03_business_analysis.sql`, `sql/04_create_views.sql`, seven `vw_` views |
| 5 | `notebooks/02_market_basket_analysis.ipynb`, `data/processed/association_rules.csv`, `docs/market_basket_analysis.md` |
| 6 | `powerbi/retail_margin_dashboard.pbix` |
