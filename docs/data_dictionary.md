# Data Dictionary — fact_sales

**Project:** Retail Margin Dynamics & Discount Optimization  
**Table:** `fact_sales` in `retail_margin_db`  
**Source:** `data/processed/superstore_cleaned.csv` → `stg_superstore_sales` → `fact_sales`  
**Row grain:** One product line per order. `row_id` is the primary key.

---

| Column | Type | Constraints | Source Column | Business Definition |
|---|---|---|---|---|
| `row_id` | INTEGER | PRIMARY KEY | Row ID | Unique integer row identifier from the source dataset. Used as the fact table surrogate key because `order_id + product_id` is not guaranteed unique. |
| `order_id` | TEXT | NOT NULL | Order ID | Identifier shared across all product lines within a single customer order. One order may contain multiple rows. |
| `order_date` | DATE | NOT NULL | Order Date | Date the order was placed. Original format: DD-MM-YYYY (parsed with `dayfirst=True`). Range: 2011-01-01 – 2014-12-31. |
| `ship_date` | DATE | NOT NULL | Ship Date | Date the order was shipped. Always ≥ `order_date`. |
| `ship_mode` | TEXT | — | Ship Mode | Shipping speed tier: First Class, Same Day, Second Class, Standard Class. |
| `customer_id` | TEXT | — | Customer ID | Unique customer identifier. |
| `customer_name` | TEXT | — | Customer Name | Full name of the customer. |
| `segment` | TEXT | — | Segment | Customer market segment: Consumer, Corporate, Home Office. |
| `city` | TEXT | — | City | City of the shipping destination. |
| `state` | TEXT | — | State | State or province of the shipping destination. |
| `country` | TEXT | — | Country | Country of the shipping destination. Used in geographic analysis. |
| `market` | TEXT | — | Market | High-level geographic market: APAC, Africa, Canada, EMEA, EU, LATAM, US. Used in geographic analysis. |
| `region` | TEXT | — | Region | Sub-market region (13 values): Africa, Canada, Caribbean, Central, Central Asia, EMEA, East, North, North Asia, Oceania, South, Southeast Asia, West. |
| `product_id` | TEXT | NOT NULL | Product ID | Unique product identifier. |
| `category` | TEXT | — | Category | Top-level product category: Furniture, Office Supplies, Technology. |
| `sub_category` | TEXT | — | Sub-Category | Product sub-category (17 values): Accessories, Appliances, Art, Binders, Bookcases, Chairs, Copiers, Envelopes, Fasteners, Furnishings, Labels, Machines, Paper, Phones, Storage, Supplies, Tables. |
| `product_name` | TEXT | — | Product Name | Full product name. Used as the basket item identifier in Market Basket Analysis. |
| `sales` | NUMERIC(12,4) | NOT NULL | Sales | Revenue from this line item in USD. Always positive (min observed: 0.44). |
| `quantity` | INTEGER | NOT NULL | Quantity | Number of units ordered. Range: 1–14. Always positive. |
| `discount` | NUMERIC(6,4) | NOT NULL | Discount | Fractional discount applied to this line (0.00 = no discount, 0.85 = 85% discount). Range: 0.00–0.85. Contains both round values (e.g., 0.20, 0.40) and non-round values (e.g., 0.002, 0.202). |
| `profit` | NUMERIC(12,4) | NOT NULL | Profit | Net profit from this line item in USD. Can be negative (12,544 rows, 24.5%) — these are legitimate loss-making transactions, not data errors. |
| `shipping_cost` | NUMERIC(12,4) | — | Shipping Cost | Cost of shipping this line item in USD. |
| `order_priority` | TEXT | — | Order Priority | Fulfillment priority level: Critical, High, Medium, Low. |

---

## Excluded Columns

| Source Column | Reason for Exclusion |
|---|---|
| `Postal Code` | 80.5% null (41,296 of 51,290 rows). Provides no analytical value. Geographic analysis uses `country`, `market`, and `region` instead. |

---

## Key Metric Definitions

| Metric | Formula | Notes |
|---|---|---|
| Profit Margin % | `SUM(profit) / NULLIF(SUM(sales), 0) * 100` | Always computed on aggregated sums — never averaged across row-level margins. |
| Estimated Cost | `sales - profit` | Derived approximation; not independently recorded in the source data. |
| Est. Pre-discount Sales | `sales / NULLIF(1 - discount, 0)` | Used in What-If simulation. Guard against `discount = 1.0`. |

---

*Created: 2026-11-19 | Phase 3 — PostgreSQL Schema & Data Loading*
