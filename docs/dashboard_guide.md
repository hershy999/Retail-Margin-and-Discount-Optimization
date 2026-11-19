# Power BI Dashboard Implementation Guide

**Project:** Retail Margin Dynamics & Discount Optimization  
**File:** `powerbi/retail_margin_dashboard.pbix`  
**Data Sources:** PostgreSQL 18 (`retail_margin_db`), `data/processed/association_rules.csv`  
**Canvas Resolution:** 1280 × 720 (16:9 widescreen)  
**Theme:** Light Theme (`powerbi/themes/light_theme.json`) & Dark Theme (`powerbi/themes/dark_theme.json`)  

---

## 1. Connecting Data Sources in Power BI Desktop

### A. PostgreSQL Analytical Views
1. Open **Power BI Desktop**.
2. Select **Get Data → PostgreSQL database**.
3. **Server:** `localhost:5432` | **Database:** `retail_margin_db`
4. **Data Connectivity mode:** Select **Import** (recommended for full DAX / What-If performance).
5. Enter credentials: User = `postgres`, Password = `postgres123`.
6. Select and check all 7 views:
   - `vw_retail_kpis`
   - `vw_discount_profitability`
   - `vw_category_profitability`
   - `vw_product_performance`
   - `vw_region_profitability`
   - `vw_monthly_performance`
   - `vw_yoy_performance`
7. Click **Load**.

### B. Association Rules Flat File
1. Select **Get Data → Text/CSV**.
2. Browse to `data/processed/association_rules.csv`.
3. Verify headers: `antecedents`, `consequents`, `support`, `confidence`, `lift`.
4. Click **Load**.

---

## 2. Dedicated Measures Table & DAX Definitions

Create a new blank table named `_Measures` to house all explicit business calculations:

```dax
_Measures = ROW("Setup", 1)
```

### Core Financial & Operational Measures

```dax
Total Sales = 
SUM(fact_sales[sales])
```

```dax
Total Profit = 
SUM(fact_sales[profit])
```

```dax
Profit Margin % = 
DIVIDE([Total Profit], [Total Sales], 0) * 100
```

```dax
Avg Discount = 
AVERAGE(fact_sales[discount])
```

```dax
Total Orders = 
DISTINCTCOUNT(fact_sales[order_id])
```

```dax
Total Quantity = 
SUM(fact_sales[quantity])
```

---

## 3. What-If Discount Simulation DAX Measures

### What-If Parameter Setup
1. In the Power BI ribbon, navigate to **Modeling → New parameter → Numeric range**.
2. **Name:** `What-If Discount`
3. **Data type:** Decimal number
4. **Minimum:** `0.00` | **Maximum:** `0.85` | **Increment:** `0.01`
5. **Default:** `0.14` (reflecting historical mean discount of 14.3%)
6. Ensure **"Add slicer to this page"** is checked.

### Simulation DAX Measures

```dax
Estimated Cost = 
[Total Sales] - [Total Profit]
```

```dax
Est Pre-discount Sales = 
DIVIDE([Total Sales], 1 - [Avg Discount], 0)
```

```dax
Sim Sales = 
VAR DiscountRate = [What-If Discount Value]
RETURN
[Est Pre-discount Sales] * (1 - DiscountRate)
```

```dax
Sim Profit = 
[Sim Sales] - [Estimated Cost]
```

```dax
Sim Profit Margin % = 
DIVIDE([Sim Profit], [Sim Sales], 0) * 100
```

```dax
Profit Delta = 
[Sim Profit] - [Total Profit]
```

```dax
Profit Delta Color = 
IF([Profit Delta] >= 0, "#3C4763", "#573A34")
```

---

## 4. Five-Page Dashboard Layout & Visual Specifications

### Navigation Header (Replicated across all 5 pages)
- **Top Panel:** Height = 60px, Fill = `#18273E` (Deep Navy).
- **Title Text:** "Retail Margin Dynamics & Discount Optimization" (16pt, `#FBFBF9`).
- **5 Action Buttons:** Page Navigation type targeting Pages 1 through 5.
- **Theme Toggle Button:** Top right icon triggering bookmarks `Theme_Light` and `Theme_Dark`.

---

### Page 1 — Executive Overview
*Business Question: How are total sales and profit margins performing over time, by region, and by customer segment?*

1. **Top KPI Cards (Row 1):**
   - Card 1: `Total Sales` (\$12.64M)
   - Card 2: `Total Profit` (\$1.47M)
   - Card 3: `Profit Margin %` (11.61%)
   - Card 4: `Total Orders` (25,035)
   - Card 5: `Avg Discount` (14.29%)
2. **Monthly Revenue & Profit Trend (Left Area):**
   - Visual: Line chart from `vw_monthly_performance`.
   - X-axis: `month_start` (or `year_month`).
   - Y-axis: `monthly_sales` and `monthly_profit`.
   - Tooltip: Custom tooltip showing `profit_margin_pct`.
3. **Category Profit Margin (Upper Right):**
   - Visual: Clustered bar chart from `vw_category_profitability`.
   - Y-axis: `category`. X-axis: `profit_margin_pct`.
4. **Regional Sales Contribution (Lower Right):**
   - Visual: Bar chart from `vw_region_profitability`.
   - Category: `market`. Values: `total_sales`.
5. **Slicers:** Year (`yr`), Market (`market`), Segment (`segment`).

---

### Page 2 — Discount & Margin Analysis
*Business Question: At what discount levels does discounting erode profit margin, and how does this vary across categories?*

1. **Sales, Profit & Margin % by Discount Band (Main Visual):**
   - Visual: Clustered column and line chart from `vw_discount_profitability`.
   - X-axis: `discount_band` (sorted by `band_sort`).
   - Column values: `total_sales`, `total_profit`.
   - Line value: `profit_margin_pct`.
   - Toggle: Chart / Table view bookmarks (`ChartView_P2`, `TableView_P2`).
2. **Discount vs. Profit Margin by Sub-Category (Scatter Chart):**
   - Visual: Scatter chart from `vw_category_profitability`.
   - X-axis: `avg_discount`.
   - Y-axis: `profit_margin_pct`.
   - Legend / Details: `sub_category`.
   - Reference Line: Constant line at `Y = 0` (Breakeven).
3. **Slicers:** Year, Category, Market.

---

### Page 3 — Product & Category Analysis
*Business Question: Which specific products and sub-categories drive or destroy profit margin?*

1. **Sub-Category Sales vs. Profit Bubble/Bar Chart:**
   - Visual: Scatter or clustered bar from `vw_category_profitability`.
2. **Top 10 Most Profitable Products:**
   - Visual: Bar chart from `vw_product_performance` (Filter: Top 10 by `total_profit`).
3. **Bottom 10 Lowest Margin Products:**
   - Visual: Bar chart from `vw_product_performance` (Filter: Bottom 10 by `profit_margin_pct`, min 5 sales).
4. **Drill-Through Target:**
   - Right-click any product to drill through to **Product Detail** page showing historical order breakdown and discount levels.

---

### Page 4 — Market Basket Insights
*Business Question: What products are frequently co-purchased, and how can bundles protect margin?*

1. **Association Rules Matrix / Table:**
   - Columns: `antecedents`, `consequents`, `support`, `confidence`, `lift`.
   - Source: `association_rules.csv`.
2. **Top 15 Cross-Sell Pairs by Lift:**
   - Visual: Horizontal bar chart sorted by `lift` descending.
3. **Strategic Callout Cards:**
   - Plain-language callouts: e.g., "Office seating exhibits high affinity with storage carts and technology accessories."
4. **Prominent Observational Caveat:**
   - Static banner: *"Notice: Association rules reflect historical observational patterns; association does not imply causation."*

---

### Page 5 — Discount What-If Simulator
*Business Question: What would happen to total profit and margin if baseline discount rates were adjusted?*

1. **Interactive Discount Slider:**
   - Connected to `What-If Discount Value` (range: 0.00 to 0.85).
2. **Baseline vs. Simulated KPI Comparison Cards:**
   - Card 1: Baseline Sales (\$12.64M) vs. `Sim Sales`
   - Card 2: Baseline Profit (\$1.47M) vs. `Sim Profit`
   - Card 3: Baseline Margin (11.61%) vs. `Sim Profit Margin %`
3. **Variance Indicator:**
   - Card: `Profit Delta` (\$ change). Conditional color formatting with `[Profit Delta Color]`.
4. **Category Scenario Comparison:**
   - Clustered column chart: `Total Profit` vs. `Sim Profit` by `category`.
5. **Permanent Assumption Disclaimer Box (Required):**
   - *"Assumptions: This model assumes constant transaction volume, product mix, and unit costs. It does not forecast dynamic customer demand or price elasticity."*

---

## 5. Bookmark-Based Toggles

1. **Theme Toggle (`Theme_Light` vs. `Theme_Dark`):**
   - In the **Selection** pane, toggle visibility between light and dark background shapes and text colors.
   - Assign `Theme_Light` bookmark to the Sun/Light icon button.
   - Assign `Theme_Dark` bookmark to the Moon/Dark icon button.
2. **Chart/Table Toggles (Pages 2, 3, 4):**
   - Place table visual directly over chart visual.
   - Bookmark `ChartView_PX`: Chart visible = ON, Table visible = OFF.
   - Bookmark `TableView_PX`: Chart visible = OFF, Table visible = ON.
   - Wire buttons "Show Table" and "Show Chart" to these bookmarks.
