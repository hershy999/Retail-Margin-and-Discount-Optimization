# TECH_STACK.md — Retail Margin Dynamics & Discount Optimization

**Version:** 1.1  
**Status:** Draft — awaiting approval  
**Last updated:** Power BI UI/UX implementation approach added

---

## 1. Final Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Data profiling & cleaning | Python 3.x, pandas | Inspect, clean, validate, and export the dataset |
| Market Basket Analysis | Python 3.x, pandas, mlxtend | Build basket matrix, run Apriori, generate association rules |
| Analytical database | PostgreSQL | Store cleaned data; run all business analysis queries |
| SQL analysis | PostgreSQL SQL (CTEs, window functions, views) | Produce KPIs, discount analysis, category/regional breakdowns, time trends |
| Dashboard & simulation | Power BI Desktop, Power Query, DAX | Interactive reporting, What-If discount simulation |
| Automation | Python scripts, shell run order | Repeatable pipeline execution without enterprise orchestration |

No technologies beyond this list are introduced.

---

## 2. High-Level Architecture & Data Flow

```
Dataset/Global_Superstore2.csv  (Latin-1, 51,290 rows, 24 columns)
        │
        ▼
[Stage 1] Python profiling
        → data quality report
        │
        ▼
[Stage 2] src/clean_data.py  (pandas)
        → data/processed/superstore_cleaned.csv
        → data/rejected/  (if applicable)
        → cleaning log
        │
        ├──────────────────────────────────────────┐
        ▼                                          ▼
[Stage 3] src/load_to_postgres.py          [Stage 5] notebooks/02_market_basket_analysis.ipynb
        → PostgreSQL: stg_superstore_sales          → binary basket matrix (25,035 orders × N products)
        → PostgreSQL: fact_sales                    → Apriori frequent itemsets
        │                                           → association rules
        ▼                                           → data/processed/association_rules.csv
[Stage 4] sql/03_business_analysis.sql              │
        → sql/04_create_views.sql                   │
        → 7 vw_ views                               │
        │                                           │
        └───────────────────┬───────────────────────┘
                            ▼
                 [Stage 6] Power BI Desktop
                         → PostgreSQL connector (vw_ views)
                         → association_rules.csv import
                         → 5-page dashboard
                         → What-If discount simulator
```

Data flows in one direction: raw → cleaned → database → views → dashboard. The raw source file is never modified.

---

## 3. Python: Cleaning & Automation

**Runtime:** Python 3.x  
**Key library:** pandas  
**Scripts:**

| Script | Responsibility |
|---|---|
| `src/clean_data.py` | Load raw CSV, normalize columns, parse dates, handle nulls/duplicates/negatives, write cleaned output |
| `src/validate_data.py` | Post-cleaning checks: row counts, null scan, range checks |
| `src/load_to_postgres.py` | Load cleaned CSV into PostgreSQL; validate after load |
| `src/run_pipeline.py` | Optional orchestrator: runs clean → validate → load in sequence |

**Key decisions grounded in the actual dataset:**
- Source file uses Latin-1 encoding; must be specified at read time.
- `Order Date` and `Ship Date` are stored as strings in DD-MM-YYYY format; `pd.to_datetime(..., dayfirst=True)` is required.
- `Postal Code` has 80.5% nulls. It is read but excluded from analysis and not loaded as a key field.
- Negative `Profit` rows (12,544) are retained; they represent loss-making transactions.
- No exact duplicate rows exist in the source; deduplication is a safety check, not an expected action.
- Discount ranges from 0.00 to 0.85 with no nulls. Non-round values (e.g., 0.002, 0.202) are documented and retained pending approval.

**Idempotency rule:** Scripts must overwrite output files rather than appending, so reruns produce the same result.

---

## 4. PostgreSQL: Schema & SQL Analysis

**Version:** PostgreSQL (any recent stable release)  
**Connection:** Local instance; credentials stored in environment variables or a `.env` file never committed to version control.

### Schema design

Based on the confirmed dataset grain (one row = one product line within one order):

```
stg_superstore_sales   -- staging: direct load from cleaned CSV; all columns as-is
fact_sales             -- validated: typed columns, NOT NULL constraints on key fields
dim_date               -- optional: calendar attributes if useful for YoY queries
```

**Primary / composite key for `fact_sales`:** `row_id` (unique integer from source) serves as surrogate key. `order_id + product_id` is not guaranteed unique if the same product appears twice in an order; `row_id` avoids this assumption.

**`Postal Code` handling:** Column loaded as nullable text; excluded from dimension design and analysis queries.

### SQL analysis approach

All business queries use CTEs for multi-step logic and inline comments for non-obvious steps. Window functions (`SUM() OVER`, `LAG()`) handle running totals and YoY comparisons.

**Profit margin formula (consistent throughout):**
```sql
SUM(profit) / NULLIF(SUM(sales), 0) * 100
```

**Discount bands (illustrative — confirm thresholds after inspecting distributions):**

| Band label | Discount range |
|---|---|
| No discount | 0% |
| Low | 0.1%–19.9% |
| Medium | 20%–39.9% |
| High | 40%–59.9% |
| Very high | 60%+ |

Exact band boundaries must be confirmed from the actual distribution; the above is a starting point.

### Views for Power BI

| View | Feeds dashboard page |
|---|---|
| `vw_retail_kpis` | Page 1 — Executive Overview |
| `vw_discount_profitability` | Page 2 — Discount & Margin Analysis |
| `vw_category_profitability` | Page 2 & 3 |
| `vw_product_performance` | Page 3 — Product & Category Performance |
| `vw_region_profitability` | Page 1 & 2 |
| `vw_monthly_performance` | Page 1 & 2 |
| `vw_yoy_performance` | Page 1 |

---

## 5. Market Basket Analysis

**Libraries:** pandas, `mlxtend.frequent_patterns.apriori`, `mlxtend.frequent_patterns.association_rules`

**Approach:**
1. Load `data/processed/superstore_cleaned.csv`.
2. Group `product_name` by `order_id` → list of products per order.
3. Build binary basket matrix using `pd.get_dummies` or `mlxtend TransactionEncoder`.
4. Matrix dimensions: 25,035 rows (distinct orders) × N columns (distinct product names).
5. Run `apriori()` with a minimum support threshold chosen after inspecting item frequency.
6. Generate rules; filter by `confidence` threshold and `lift > 1`.
7. Export columns: `antecedents`, `consequents`, `support`, `confidence`, `lift`.

**Known constraint:** ~56.6% of orders have zero discount and potentially only one item, limiting multi-item basket coverage. The effective basket pool for multi-item rules is the subset of orders with two or more product lines. This will be quantified and documented before setting thresholds.

**Output file:** `data/processed/association_rules.csv`

---

## 6. Power BI, DAX & What-If Simulation

**Tool:** Power BI Desktop  
**Data sources:** PostgreSQL `vw_` views + `association_rules.csv`  
**Connection mode:** To be confirmed (Import recommended for portfolio use; DirectQuery for live data).

### DAX measures (core set)

| Measure | Formula |
|---|---|
| `Total Sales` | `SUM(fact_sales[sales])` |
| `Total Profit` | `SUM(fact_sales[profit])` |
| `Profit Margin %` | `DIVIDE([Total Profit], [Total Sales], 0) * 100` |
| `Avg Discount` | `AVERAGE(fact_sales[discount])` |
| `Total Orders` | `DISTINCTCOUNT(fact_sales[order_id])` |
| `Sim Profit` | Scenario calculation using What-If parameter |
| `Sim Profit Margin %` | `DIVIDE([Sim Profit], [Sim Sales], 0) * 100` |

### What-If simulation logic

The simulation holds quantity and estimated cost constant; only the discount rate changes.

```
Estimated Cost = Sales - Profit                              (derived from dataset)
Estimated Pre-discount Sales = Sales / (1 - Discount)       (guard: Discount ≠ 1.0)
Sim Sales = Estimated Pre-discount Sales × (1 - What-If Discount)
Sim Profit = Sim Sales - Estimated Cost
```

This is a simplified scenario model. It assumes no demand response to price change. This assumption must be stated prominently on Page 5.

### Theme implementation

Two Power BI theme JSON files define the light and dark variants using the approved colour palette.

**Light theme key values:**
- Page background: `#FBFBF9`
- Card background: `#FFFFFF`
- Primary text: `#18273E`
- Accent: `#DEBAAC`
- Secondary background: `#EEEBE4`

**Dark theme key values:**
- Page background: `#18273E`
- Card background: `#3C4763`
- Primary text: `#FBFBF9`
- Accent: `#DEBAAC`
- Secondary background: `#5F6879`

Theme JSON files are stored in `powerbi/themes/`. The active theme is applied at the report level in Power BI Desktop (`View → Themes → Browse for themes`).

### Bookmark-based interactions

Power BI bookmarks (via the **Bookmarks pane** and **Selection pane**) drive two types of toggle:

**Light/dark theme toggle:**
- Two bookmarks: `Theme_Light` and `Theme_Dark`.
- Each bookmark captures the report theme state and visibility of a theme-toggle button overlay.
- A toggle button on every page switches between the two bookmarks.
- Button position and size must be identical across all pages so the toggle never jumps.

**Chart/table toggle (Pages 2, 3, 4):**
- For each toggleable visual, two overlapping layers exist in the Selection pane: a chart visual and a table/matrix visual.
- Two bookmarks per page: `ChartView_P2` / `TableView_P2`, etc.
- A labelled button ("Show Table" / "Show Chart") switches between the two bookmarks.
- Only one layer is visible at a time; the hidden layer has visibility turned off in the Selection pane.

### Navigation implementation

- Use **Power BI button visuals** (not page tabs) for navigation so appearance can be fully controlled.
- All five page navigation buttons are grouped in a consistent header panel replicated across pages.
- The active page button uses `#DEBAAC` fill or `#18273E` border to distinguish it from inactive buttons (`#9DA3B1` text, transparent background).
- Navigation buttons use the **Page navigation** action type (built-in Power BI feature) — no macros or external tools required.

### Native visuals (preferred)

Prefer native Power BI visuals for all standard chart types:

| Visual type | Native equivalent |
|---|---|
| KPI cards | Card or New Card visual |
| Trend lines | Line chart |
| Bar/column charts | Clustered bar / clustered column |
| Scatter (discount vs. margin) | Scatter chart |
| Map (regional) | Map or Filled Map (confirm rendering without ArcGIS licence) |
| Matrix / table | Matrix or Table visual |
| Slicer | Slicer visual (dropdown or tile style) |
| Combo chart | Line and clustered column chart |

### Custom visuals

Introduce a custom visual only if a native visual cannot meet a clearly defined need. Any custom visual must be:
1. Available from the Microsoft AppSource marketplace.
2. Justified with a specific reason a native visual is insufficient.
3. Documented here before introduction.

**Currently planned custom visual:**

| Visual | Source | Justification | Status |
|---|---|---|---|
| **Deneb** (Vega-Lite renderer) | AppSource | Considered for advanced scatter or small-multiple charts if native scatter is insufficient for sub-category comparisons | Optional — evaluate during implementation |

If Deneb or any other custom visual is not needed during implementation, do not introduce it.

### Drill-through & tooltips

- **Drill-through:** Implemented as a Power BI drill-through page. The target page is a product detail context page (not counted in the five main pages). It is reached by right-clicking a product visual on Page 3 and selecting "Drill through."
- **Report-page tooltips:** A small tooltip report page is created for the main trend chart and discount-band visual. It shows contextual KPIs (sales, profit, margin) on hover. Tooltip pages are not part of the five main pages; they are marked as tooltip pages in the page settings.

### Mobile layout

- After the desktop design is finalised, create a Power BI mobile layout for Pages 1 and 5 using the **Mobile layout editor** (View → Mobile layout).
- Stack KPI cards in a 2-column grid; stack charts vertically below.
- Slicers must remain usable on a touch interface (tile or dropdown style preferred over list slicers).
- Mobile layout is secondary; desktop quality takes priority.
- Document any visual that does not render correctly in mobile and the workaround.

---

## 7. Dependencies & Integration Points

| Dependency | Version / Notes |
|---|---|
| Python | 3.9+ recommended |
| pandas | Latest stable |
| mlxtend | Latest stable (for `apriori` and `association_rules`) |
| psycopg2 or SQLAlchemy | For Python–PostgreSQL connection |
| PostgreSQL | Local instance; tested with 14+ |
| Power BI Desktop | Windows only; free version sufficient |
| `python-dotenv` | Optional; for loading DB credentials from `.env` |

**Integration points:**
- `src/load_to_postgres.py` → PostgreSQL: requires a live local PostgreSQL connection.
- Power BI → PostgreSQL: requires the `npgsql` or native PostgreSQL connector.
- Power BI → `association_rules.csv`: flat file import; no live database dependency for MBA results.

---

## 8. Environment & Security

- DB credentials stored in a `.env` file; never committed to version control.
- Raw data files (`Dataset/`) not committed to a public repository.
- No cloud services, API keys, or external data sources required.
- All processing runs locally on the developer's machine.
