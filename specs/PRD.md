# PRD — Retail Margin Dynamics & Discount Optimization

**Version:** 1.1  
**Status:** Draft — awaiting approval  
**Source of truth:** `retail_margin_optimization_brainstorming.md`  
**Last updated:** UI/UX, Functional & Non-Functional Requirements added

---

## 1. Project Overview

An end-to-end retail analytics portfolio project using the Global Superstore dataset (51,290 transaction lines, 2011–2014). The project investigates how discount levels relate to sales and profitability, discovers frequently co-purchased products, and communicates findings through an interactive Power BI dashboard.

This is an **observational analysis**. It identifies associations and patterns in historical data. It does not prove causation, predict future demand, or make automated pricing decisions.

---

## 2. Business Problem

The business lacks evidence on how discounts affect margin across product categories, sub-categories, and regions. Specifically:

1. How do sales, profit, and profit margin vary across discount levels?
2. Which categories and sub-categories perform well or poorly after discounts?
3. Which regions generate healthy profit and which show weaker profitability?
4. Which products are frequently purchased together (cross-sell/bundle opportunities)?
5. How would estimated profit change under alternative discount assumptions?

**Main question:** Are the retailer's discount levels supporting profitability, or are some discounts reducing profit without sufficient business value?

---

## 3. Target Users

| User | Context |
|---|---|
| **Business analyst / stakeholder** | Uses the dashboard to explore discount and margin patterns; interacts with slicers and What-If simulator |
| **Portfolio reviewer / interviewer** | Evaluates the end-to-end technical implementation and analytical rigor |

---

## 4. Objectives & Expected Outcomes

- Provide a cleaned, validated dataset suitable for reproducible analysis.
- Deliver SQL-based business analysis covering KPIs, discount bands, category and regional performance, and time trends.
- Discover product association rules using Market Basket Analysis.
- Build an interactive Power BI dashboard (five pages) with a What-If discount simulator.
- Produce evidence-based findings; do not pre-decide conclusions.

---

## 5. Dataset

**File:** `Dataset/Global_Superstore2.csv`  
**Encoding:** Latin-1  
**Rows:** 51,290  
**Columns:** 24  
**Date coverage:** 2011-01-01 to 2014-12-31 (Order Date)  
**Row grain:** One transaction line (one product within one order)  

### Confirmed columns

| Column | Type | Notes |
|---|---|---|
| `Row ID` | int | Unique row identifier |
| `Order ID` | string | 25,035 distinct orders; one order has 1–14 lines |
| `Order Date` | string (DD-MM-YYYY) | No nulls; must be parsed to date |
| `Ship Date` | string (DD-MM-YYYY) | No nulls |
| `Ship Mode` | string | 4 values: First Class, Same Day, Second Class, Standard Class |
| `Customer ID` | string | No nulls |
| `Customer Name` | string | — |
| `Segment` | string | Consumer, Corporate, Home Office |
| `City` | string | — |
| `State` | string | — |
| `Country` | string | 147 distinct countries |
| `Postal Code` | float | **41,296 nulls** — missing for most international rows; not usable as a key |
| `Market` | string | 7 values: APAC, Africa, Canada, EMEA, EU, LATAM, US |
| `Region` | string | 13 values (sub-market regions) |
| `Product ID` | string | No nulls |
| `Category` | string | Furniture, Office Supplies, Technology |
| `Sub-Category` | string | 17 values |
| `Product Name` | string | — |
| `Sales` | float | No nulls; min 0.44, max 22,638; no negatives |
| `Quantity` | int | No nulls; range 1–14 |
| `Discount` | float | No nulls; range 0.00–0.85; 56.6% of rows have 0 discount |
| `Profit` | float | No nulls; min −6,599.98, max 8,399.98; **12,544 negative rows** |
| `Shipping Cost` | float | No nulls |
| `Order Priority` | string | Critical, High, Medium, Low (not confirmed in profile — to verify) |

### Key data observations

- **No exact duplicate rows** (0 found).
- **Postal Code is largely missing** (41,296 of 51,290 rows). Do not use it as a geographic identifier.
- **Negative Profit is real and significant**: 12,544 rows (~24.5%). These likely represent loss-making transactions, not data errors. Must be retained and investigated.
- **Discount distribution is non-uniform**: values cluster at 0, 0.1, 0.2, 0.4, 0.5, 0.6, 0.7 — suggesting preset discount tiers rather than a continuous range. A few non-round values (e.g., 0.002, 0.202) exist and should be noted.
- **Sales is always positive**; Profit can be negative. Estimated cost = Sales − Profit will always be computable.
- **Order ID is not unique per row**: average 2.05 lines per order; this affects the basket matrix for MBA and the definition of "Total Orders."

---

## 6. Functional Requirements

### FR-1 — Dataset ingestion and profiling

- FR-1.1: Load `Dataset/Global_Superstore2.csv` using Latin-1 encoding without modifying the source file.
- FR-1.2: Profile all 24 columns: dtype, null count, distinct values, min/max, and distributions for `Sales`, `Profit`, `Quantity`, and `Discount`.
- FR-1.3: Identify the row grain (one product line per order) and confirm Order ID is not unique per row.
- FR-1.4: Document findings in `docs/data_quality_report.md` before cleaning begins.
- FR-1.5: Confirm all expected fields exist. If a field is missing or named differently, stop and report — do not invent substitutes.

### FR-2 — Data cleaning and validation

- FR-2.1: Normalize all column names to `snake_case`; strip leading/trailing whitespace.
- FR-2.2: Parse `order_date` and `ship_date` from string (DD-MM-YYYY) to `datetime` using `dayfirst=True`. Log any unparseable rows as rejected.
- FR-2.3: Reject rows where `order_id`, `order_date`, `product_id`, or `sales` is null; write rejected rows to `data/rejected/rejected_records.csv` with a `rejection_reason` column.
- FR-2.4: Retain all negative `profit` rows with a note in the cleaning log — these are loss-making transactions, not data errors.
- FR-2.5: Do not impute `sales`, `profit`, `discount`, or `quantity` with derived or assumed values.
- FR-2.6: Flag non-round discount values (e.g., 0.002, 0.202); retain them pending approval of a rounding rule.
- FR-2.7: Check for exact duplicate rows and remove any found; log the count.
- FR-2.8: Write the cleaned dataset to `data/processed/superstore_cleaned.csv`. The script must be safe to rerun (overwrite, not append).
- FR-2.9: Log input rows, cleaned rows, rejected rows, and each type of action taken.
- FR-2.10: Validate: `input_rows = cleaned_rows + rejected_rows` (accounting for duplicates removed).

### FR-3 — PostgreSQL schema and data loading

- FR-3.1: Create a `stg_superstore_sales` staging table matching the cleaned CSV structure.
- FR-3.2: Create a `fact_sales` table with correct PostgreSQL types, NOT NULL constraints on key fields, and `row_id` as the surrogate primary key.
- FR-3.3: Optionally create `dim_date` for calendar-based queries if it simplifies YoY analysis.
- FR-3.4: Load from `data/processed/superstore_cleaned.csv` using an idempotent process (truncate staging before reload).
- FR-3.5: After every load, validate: PostgreSQL row count = cleaned CSV row count; `SUM(sales)` and `SUM(profit)` reconcile; no duplicate `row_id`; no unexpected nulls in key columns.
- FR-3.6: Store DB credentials in environment variables or a `.env` file — never hardcoded in SQL or Python files.

### FR-4 — SQL business analysis and views

- FR-4.1: **Overall KPIs** — `SUM(sales)`, `SUM(profit)`, `SUM(quantity)`, `AVG(discount)`, profit margin % using `SUM(profit) / NULLIF(SUM(sales), 0) * 100`.
- FR-4.2: **Discount-band analysis** — group transactions into defined bands (No Discount, Low, Medium, High, Very High); aggregate sales, profit, and margin per band. Confirm band boundaries from actual distribution before finalising.
- FR-4.3: **Category & sub-category analysis** — sales, profit, and margin grouped by `category` and `sub_category`.
- FR-4.4: **Product performance** — sales, profit, and margin per product; identify high-sales/low-profit and high-profit outliers.
- FR-4.5: **Regional analysis** — sales, profit, and margin grouped by `market`, `region`, and `country`. Exclude `postal_code`.
- FR-4.6: **Time trends** — monthly and yearly sales and profit using `DATE_TRUNC`.
- FR-4.7: **Running totals** — cumulative sales or profit over time using `SUM() OVER (ORDER BY month)`.
- FR-4.8: **Year-over-year comparison** — compare equivalent monthly periods across years using `LAG()`.
- FR-4.9: **Data validation queries** — reconcile database totals with the cleaned CSV reference values.
- FR-4.10: Create seven reusable views (`vw_retail_kpis`, `vw_discount_profitability`, `vw_category_profitability`, `vw_product_performance`, `vw_region_profitability`, `vw_monthly_performance`, `vw_yoy_performance`) confirmed to return results before Power BI connection.

### FR-5 — Market Basket Analysis

- FR-5.1: Use only `data/processed/superstore_cleaned.csv` as input.
- FR-5.2: Group `product_name` by `order_id` to form order-level baskets. Confirm `order_id` and `product_name` are non-null before building the matrix.
- FR-5.3: Build a binary basket matrix; validate that row count = 25,035 (distinct Order IDs).
- FR-5.4: Run Apriori (`mlxtend`) with a minimum support threshold chosen by inspecting item frequency — not an arbitrary fixed value. Document the chosen threshold and the reason.
- FR-5.5: Generate association rules; filter by a justified confidence threshold and `lift > 1`.
- FR-5.6: Validate: support ∈ [0, 1]; confidence ∈ [0, 1]; lift > 0. Spot-check at least one top rule against the raw order data manually.
- FR-5.7: Export filtered rules to `data/processed/association_rules.csv` with columns: `antecedents`, `consequents`, `support`, `confidence`, `lift`.
- FR-5.8: Write a plain-language interpretation of the top 10–20 rules in `docs/market_basket_analysis.md`. Do not over-claim; note that association is not causation.

### FR-6 — Power BI dashboard

- FR-6.1: Connect Power BI Desktop to PostgreSQL and import the seven `vw_` views. Import `association_rules.csv` as a flat table.
- FR-6.2: Create a dedicated **Measures** table containing all DAX measures. Use no implicit aggregations.
- FR-6.3: Implement the five-page dashboard structure. Each page must address a specific business question listed in Section 7 (UI/UX).
- FR-6.4: Provide consistent slicers across pages for at least: year, market/region, category, segment.
- FR-6.5: Enable cross-filtering between visuals on the same page.
- FR-6.6: Provide drill-through from summary to product-level detail on Page 3.
- FR-6.7: Provide report-page tooltips on key visuals to show contextual detail without cluttering the main layout.
- FR-6.8: Implement a **chart/table toggle** on pages where tabular detail adds value (Pages 2, 3, 4). Use Power BI bookmarks and the Selection pane to show/hide the alternate view.
- FR-6.9: Implement a **light/dark theme toggle** using bookmarks and a custom Power BI theme JSON file. Both themes must use the approved colour palette defined in Section 7 (UI/UX). Theme state must persist across page navigation.
- FR-6.10: Implement **page navigation** using consistent button-based navigation visible on all five pages.

### FR-7 — What-If discount simulation

- FR-7.1: Implement a Power BI What-If parameter (numeric range slider) for an alternative discount rate.
- FR-7.2: Compute scenario measures using only derived values — no modification of historical data:
  - `Estimated Cost = Sales − Profit`
  - `Estimated Pre-discount Sales = Sales / (1 − Discount)` — guard against `Discount = 1.0` with `DIVIDE()` or `IF`.
  - `Sim Sales = Estimated Pre-discount Sales × (1 − What-If Discount)`
  - `Sim Profit = Sim Sales − Estimated Cost`
  - `Sim Profit Margin % = DIVIDE([Sim Profit], [Sim Sales], 0) * 100`
- FR-7.3: Display baseline vs. scenario KPIs side by side on Page 5.
- FR-7.4: Display a prominent disclaimer on Page 5: *"This simulation holds quantity and estimated cost constant. It does not forecast customer demand or guarantee real-world outcomes."*
- FR-7.5: All simulation measures must be clearly prefixed (`Sim_`) and never co-mingled with historical actuals in the same visual without explicit labelling.

---

## 7. Non-Functional Requirements

### NFR-1 — Data accuracy & consistency
- NFR-1.1: Cleaned CSV must reconcile exactly with the source: `input_rows = cleaned_rows + rejected_rows`.
- NFR-1.2: PostgreSQL `SUM(sales)` and `SUM(profit)` must match the cleaned CSV to within floating-point rounding tolerance.
- NFR-1.3: All KPI definitions must be numerically identical between SQL views and DAX measures for the same date range and filters.
- NFR-1.4: Historical actuals and simulated scenario outputs must never share a column or visual without clear labelling.

### NFR-2 — Reproducibility & maintainability
- NFR-2.1: All Python scripts must be safe to rerun from scratch and produce identical outputs.
- NFR-2.2: The database load process must truncate staging before reloading; no silent data accumulation.
- NFR-2.3: Every cleaning decision, rejection reason, and formula assumption must appear in the cleaning log or `docs/data_quality_report.md`.
- NFR-2.4: SQL files must be numbered sequentially and self-contained. A new developer must be able to run them in order on a clean database.
- NFR-2.5: The raw source file (`Dataset/Global_Superstore2.csv`) must remain byte-for-byte identical throughout the project.

### NFR-3 — Performance
- NFR-3.1: Power BI Import mode is preferred for this dataset size (~51k rows). Dashboard pages should load within a reasonable time on a standard development machine.
- NFR-3.2: SQL views must not use full-table cartesian joins or unindexed cross-joins. Add indexes only where query patterns justify them.
- NFR-3.3: The What-If slider must respond without noticeable lag when moving across its range; keep DAX scenario calculations lightweight.

### NFR-4 — Usability & readability
- NFR-4.1: The dashboard must be interpretable by a business user with no knowledge of the technical pipeline. Each page must have a clear title and business question.
- NFR-4.2: All KPI cards must display units (currency symbol, % sign, or count label) and have consistent formatting across all pages.
- NFR-4.3: Chart titles, axis labels, and tooltip text must be written in plain business language — no raw column names or technical identifiers.
- NFR-4.4: Slicers must behave consistently across all five pages. A selection made on one page must carry over or be clearly scoped.
- NFR-4.5: Visuals must remain readable at 1920×1080 (16:9) without horizontal scrolling or overlapping labels.

### NFR-5 — Accessibility & contrast
- NFR-5.1: Text on coloured backgrounds must meet a minimum contrast ratio of 4.5:1 (WCAG AA) for body text.
- NFR-5.2: Do not rely on colour alone to convey meaning — use labels, icons, or patterns alongside colour for critical distinctions.
- NFR-5.3: KPI card values and chart labels must use a font size of at least 11pt at the report's native canvas size.

### NFR-6 — Documentation & assumptions
- NFR-6.1: Every assumption must be documented before implementation — not discovered during review.
- NFR-6.2: The simulation disclaimer must be permanently visible on Page 5, not hidden behind a tooltip or info button.
- NFR-6.3: The MBA interpretation must note that association rules are observational and do not imply causation.

---

## 8. Power BI UI/UX Requirements

### 8.1 Colour palette

All dashboard colours must be drawn from this approved palette. Do not introduce unrelated colours.

**Primary colours**

| Name | Hex | Typical use |
|---|---|---|
| Deep Navy | `#18273E` | Page headers, navigation bar, dark backgrounds |
| Slate Indigo | `#3C4763` | Card backgrounds, section headers |
| Warm Ivory | `#EEEBE4` | Light theme page background |
| Dusty Blush | `#DEBAAC` | Accent bars, highlights, positive KPI indicators |
| Dark Brown | `#573A34` | Strong accent text, borders on light backgrounds |
| White | `#FFFFFF` | Card and visual backgrounds in light theme |

**Supporting colours**

| Name | Hex | Typical use |
|---|---|---|
| Slate | `#777F92` | Secondary text, axis labels |
| Grey Blue | `#8C929E` | Gridlines, borders |
| Muted Blue Grey | `#9DA3B1` | Inactive navigation items |
| Dark Slate | `#5F6879` | Tooltips, secondary chart elements |
| Pale Lavender Grey | `#D9D9E3` | Slicer backgrounds, dividers |
| Light Grey | `#D1D4D9` | Table row alternation, subtle separators |
| Pale Blush | `#EFDCD6` | Hover states, soft highlights |
| Soft Peach | `#E9CEC5` | Chart fill for secondary series |
| Muted Taupe | `#AB9C99` | Inactive state, disabled controls |
| Dusty Mauve | `#8A7574` | Tertiary text |
| Off White | `#F2F1EC` | Alternate card background |
| Light Ivory | `#F5F4F0` | Subtle background areas |
| Pale Pink | `#FAF0EF` | Light theme secondary background |
| Warm Grey | `#DDD8D5` | Input borders, light separators |
| Soft White | `#FBFBF9` | Near-white areas, page canvas in light theme |

### 8.2 Typography

- Use a single consistent sans-serif font throughout (Segoe UI or the Power BI default; do not mix fonts).
- Page titles: bold, 18–22pt equivalent.
- Section headers: semi-bold, 13–15pt.
- KPI card values: bold, 24–32pt.
- KPI card labels and axis text: regular, 10–12pt.
- Do not use decorative fonts or more than two weight variants.

### 8.3 Layout & spacing

- Canvas size: 1280×720 (16:9) or 1920×1080 — confirm and lock before building.
- Apply consistent padding: 12–16px inside cards; 8–12px between visual groups.
- Align all elements to an invisible grid. Avoid uneven spacing or orphaned visuals.
- Keep a consistent header band across all five pages (navigation, page title, theme toggle).
- Keep a consistent footer or disclaimer band on Page 5 for the simulation assumption text.

### 8.4 Five-page structure

#### Page 1 — Executive Overview
*Business question: What is the overall business performance across 2011–2014?*
- KPI cards: Total Sales, Total Profit, Profit Margin %, Total Orders, Avg Discount.
- Sales and profit trend line chart (by month or year).
- Profitability overview by category (bar or column chart).
- Market/region summary (map or bar chart — use whichever renders correctly without additional licensing).
- Slicers: Year, Market, Segment.

#### Page 2 — Discount & Margin Analysis
*Business question: How do discount levels relate to profit margin?*
- Sales, profit, and margin by discount band (clustered bar or column).
- Scatter or combo chart: discount rate vs. profit margin per sub-category or product.
- Category and sub-category breakdown filtered by discount band.
- Slicers: Year, Market, Category.
- Chart/table toggle for the main discount-band visual.

#### Page 3 — Product & Category Analysis
*Business question: Which products and categories drive or erode profit?*
- Category and sub-category performance: sales vs. profit (dual-axis or scatter).
- Top N and bottom N products by profit margin (bar charts).
- Drill-through: click a product to reach a detail page showing its full order history.
- Slicers: Year, Category, Sub-Category.
- Chart/table toggle for product ranking visuals.

#### Page 4 — Market Basket Analysis
*Business question: Which products are frequently purchased together?*
- Table or matrix showing top association rules: antecedents, consequents, support, confidence, lift.
- Bar chart of top rules ranked by lift.
- Plain-language callout card for the top 3–5 rules.
- Note: *"These rules are based on historical co-purchase patterns. Association does not imply causation."*
- Slicers: minimum confidence, minimum lift.
- Chart/table toggle for the rules table.

#### Page 5 — Discount What-If Simulator
*Business question: How would profit change under a different discount rate?*
- What-If parameter slider: discount rate range (e.g., 0%–80%, step 1%).
- Side-by-side KPI cards: Baseline Profit vs. Sim Profit; Baseline Margin % vs. Sim Profit Margin %.
- Variance card: Profit delta (Sim minus Baseline), formatted with colour coding (positive = favourable).
- Combo chart: Sim Sales vs. Sim Profit across selected categories.
- Prominent disclaimer text box — always visible, not collapsible.
- No slicers that would conflict with the What-If parameter logic.

### 8.5 Navigation

- A consistent navigation panel or tab bar must appear on every page.
- Navigation buttons must be clearly labelled with page names (not just numbers).
- The active page button must be visually distinct (filled vs. outline, or different background).
- Navigation must work in both light and dark themes without layout changes.

### 8.6 Light and dark theme

- **Light theme (default):** page background `#FBFBF9` / `#EEEBE4`; card backgrounds `#FFFFFF`; primary text `#18273E`; accent `#DEBAAC`.
- **Dark theme:** page background `#18273E`; card backgrounds `#3C4763`; primary text `#FBFBF9`; accent `#DEBAAC`.
- Implement using two Power BI theme JSON files and a bookmark-based toggle button.
- The toggle button must be visible on every page in the same position.
- Both themes must maintain sufficient contrast (NFR-5.1).

### 8.7 Chart/table toggle

- Pages 2, 3, and 4 must offer a toggle button that switches between the chart view and a table view for the primary visual.
- Implement using Power BI bookmarks and the Selection pane (show/hide layers).
- The toggle button must be clearly labelled ("Show Table" / "Show Chart").
- The table view must include the same data as the chart but formatted as a readable matrix or table visual.

### 8.8 Interactivity

- Cross-filtering: visuals on the same page must cross-filter each other by default, except where it would produce misleading results (document any exceptions).
- Drill-through: Page 3 product visuals must support drill-through to a product detail context.
- Tooltips: use report-page tooltips on the main trend charts and discount-band visuals to show additional KPIs on hover without cluttering the canvas.
- Slicers must reset cleanly using a "Clear filters" button or the native slicer reset.

### 8.9 Animations & transitions

- Use native Power BI conditional formatting and visual-level animations where available.
- Bookmark transitions use Power BI's built-in transition; keep them instant or use a very brief fade — do not add delays that slow the user experience.
- Consider **Deneb** (a custom visual based on Vega-Lite) only if a specific chart type genuinely cannot be achieved with native visuals and adds clear analytical value. If introduced, document the visual name, its purpose, and why a native visual is insufficient.
- Do not use animations that move chart elements continuously or add decorative motion with no informational value.

### 8.10 Mobile layout

- After completing the desktop layout, create a Power BI mobile layout for key pages (prioritise Pages 1 and 5).
- Stack KPI cards vertically; ensure slicer labels remain readable.
- Mobile layout is secondary; it must not compromise the desktop design.
- Document any visuals that do not render well in mobile and the workaround used.

---

## 9. Scope

### In scope
- Python profiling, cleaning, and validation (pandas)
- PostgreSQL schema, data loading, SQL analysis, and views
- Market Basket Analysis (mlxtend Apriori)
- Power BI five-page dashboard with What-If discount simulation
- Lightweight automation: reusable scripts with logging and a documented run order

### Out of scope
- Real-time pipelines, streaming, or cloud infrastructure
- Enterprise orchestration (Airflow, Prefect, etc.)
- Machine learning beyond Apriori association rules
- Automated pricing decisions
- Demand forecasting

---

## 10. Acceptance Criteria

The project is complete when:

- [ ] Original dataset files are unchanged.
- [ ] Cleaning script runs reproducibly and logs all actions.
- [ ] Cleaned CSV row count reconciles with input minus rejected rows.
- [ ] PostgreSQL row counts and SUM totals match the cleaned CSV.
- [ ] SQL views cover all seven required analyses and return correct results.
- [ ] MBA produces interpretable association rules with validated metrics.
- [ ] Power BI KPIs match SQL view totals for the same period and filters.
- [ ] What-If slider recalculates scenario measures and displays assumptions.
- [ ] A new user can follow the README to reproduce the full workflow.

---

## 11. Dataset Limitations & Assumptions

| Item | Detail |
|---|---|
| `Postal Code` | Unusable as a geographic key (80.5% null). Geography analysis relies on `Country`, `Region`, and `Market`. |
| Negative Profit | 12,544 rows (~24.5%). Treated as legitimate loss-making transactions, not errors. Must be investigated before final decision. |
| `Estimated Cost` | Derived as `Sales − Profit`. Not an independently supplied cost figure. |
| What-If formula | Assumes quantity and cost are constant when discount changes. This is a simplification; it does not model demand elasticity. |
| MBA unit | Basket = Order ID. Product granularity = Product Name. 56% of baskets are single-item orders, which limits rule generation; this is expected and not a data error. |
| Discount non-round values | Values like 0.002 and 0.202 exist alongside the main tier values. Likely rounding artefacts. Document and retain unless a business rule justifies exclusion. |
| Date format | `Order Date` and `Ship Date` are stored as strings in DD-MM-YYYY format. Must be explicitly parsed. |

---

## 12. Open Questions (require approval before implementation)

1. **Postal Code:** Confirm that all geographic analysis should use `Country`, `Market`, and `Region` only — not `Postal Code`.
2. **Negative Profit rows:** Confirm that all 12,544 negative-profit rows should be retained in the fact table (not rejected), and that negative profit represents loss-making sales rather than data errors.
3. **Discount non-round values:** Confirm whether values like 0.002 and 0.202 should be rounded to the nearest tier, flagged, or retained as-is.
4. **MBA product identifier:** Confirm whether association rules should use `Product Name` or `Product ID` as the basket item identifier.
5. **Power BI connection mode:** Confirm Import vs. DirectQuery preference for the PostgreSQL connection in Power BI.
