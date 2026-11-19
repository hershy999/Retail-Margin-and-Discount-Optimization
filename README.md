# Retail Margin Dynamics & Discount Optimization

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-blue.svg)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://www.python.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-yellow.svg)](https://powerbi.microsoft.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end retail data analytics and business intelligence project investigating how commercial discounting strategies impact profitability across product categories, sub-categories, and geographic regions using historical transactions from the Global Superstore dataset (51,290 lines, 2011–2014).

---

## Business Objective & Problem Solved

Retailers frequently use discounts to accelerate top-line revenue, but aggressive promotions often erode margins or result in outright operating losses. This project provides empirical evidence showing:
- Discount rates above 20% dramatically degrade margins.
- Discount rates $\ge 40\%$ generate severe losses (-\$771K net deficit across 10,138 orders).
- The "Tables" sub-category produces a negative profit margin (-8.46%) due to an excessive average discount rate of 29.07%.
- Strategic product bundling via Market Basket Analysis (Apriori) can protect blended margins by cross-selling high-margin consumables alongside heavily discounted equipment.

---

## Architecture & Technology Stack

| Layer | Tools | Key Artifacts |
|---|---|---|
| **Data Cleaning & Pipeline** | Python 3, pandas | `src/clean_data.py`, `src/validate_data.py` |
| **Data Warehousing** | PostgreSQL 18, psycopg2 | `sql/01_create_schema.sql`, `sql/02_data_validation.sql` |
| **SQL Business Analysis** | PostgreSQL CTEs, Window Functions | `sql/03_business_analysis.sql`, `sql/04_create_views.sql` |
| **Market Basket Analysis** | Python, pandas, mlxtend | `src/market_basket_analysis.py`, `association_rules.csv` |
| **Reporting & Simulation** | Power BI Desktop, DAX | 5-Page Dashboard, What-If Parameter Simulator |

---

## Step-by-Step Execution Guide

### 1. Prerequisites
- Python 3.9+ installed
- PostgreSQL 14+ running locally (default port: `5432`)
- Power BI Desktop (Windows)

Install Python dependencies:
```bash
pip install -r requirements.txt
```

Configure your `.env` file with database credentials:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_margin_db
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### 2. Run the Data Pipeline
Execute the automated sequential pipeline:
```bash
python src/run_pipeline.py
```
This automatically runs:
1. `src/clean_data.py`: Generates `data/processed/superstore_cleaned.csv`
2. `src/validate_data.py`: Validates 12 data assertions
3. `src/load_to_postgres.py`: Creates `retail_margin_db`, builds tables, and loads all 51,290 records

### 3. Run Business Views & SQL Validation
Deploy all 7 analytical views in PostgreSQL:
```bash
psql -U postgres -d retail_margin_db -f sql/04_create_views.sql
```

### 4. Run Market Basket Analysis
Generate association rules:
```bash
python src/market_basket_analysis.py
```
Outputs filtered association rules to `data/processed/association_rules.csv`.

### 5. Open Power BI Dashboard
1. Open Power BI Desktop and import views from PostgreSQL (`localhost:5432/retail_margin_db`).
2. Import `data/processed/association_rules.csv`.
3. Follow the visual layout and DAX measure setup in `docs/dashboard_guide.md`.

---

## Project Structure

```
Retail Margin DA Project/
├── AGENTS.md                          # Coding guidelines & engineering standards
├── IMPLEMENTATION_PLAN.md             # 7-phase execution roadmap
├── README.md                          # Project documentation and quickstart
├── requirements.txt                   # Python dependencies
├── .env                               # Database credentials (ignored in git)
│
├── Dataset/                           # Untouched original raw source files
│   └── Global_Superstore2.csv         # 51,290 lines, 24 columns
│
├── data/
│   ├── raw/                           # Verified byte-for-byte copy
│   ├── processed/                     # superstore_cleaned.csv, association_rules.csv
│   └── rejected/                      # rejected_records.csv (if any)
│
├── docs/                              # Supporting documentation
│   ├── data_quality_report.md         # Schema, nulls, distributions, decisions
│   ├── data_dictionary.md             # Column constraints and definitions
│   ├── methodology.md                 # End-to-end architecture & equations
│   ├── sql_analysis.md                # SQL business analysis findings
│   ├── market_basket_analysis.md      # Apriori rules interpretation
│   └── dashboard_guide.md             # Power BI layout & DAX measures guide
│
├── notebooks/                         # Interactive Jupyter notebooks
│   ├── 01_data_exploration.ipynb      # Phase 1 dataset profiling
│   └── 02_market_basket_analysis.ipynb# Phase 5 MBA modeling
│
├── src/                               # Reusable Python scripts
│   ├── clean_data.py                  # Cleaning pipeline
│   ├── validate_data.py               # Post-cleaning validation assertions
│   ├── load_to_postgres.py            # PostgreSQL table loader
│   ├── run_pipeline.py                # Automated orchestrator
│   └── market_basket_analysis.py      # Apriori association mining
│
├── sql/                               # Sequenced SQL scripts
│   ├── 01_create_schema.sql           # Tables and indexes
│   ├── 02_data_validation.sql         # 7 validation checks
│   ├── 03_business_analysis.sql       # Analytical CTEs & window queries
│   └── 04_create_views.sql            # 7 views for Power BI
│
└── powerbi/
    └── themes/
        ├── light_theme.json           # Approved corporate light palette
        └── dark_theme.json            # Approved corporate dark palette
```

---

## Known Analytical Limitations

- **Observational:** Identifies empirical patterns; does not establish causality or predict future demand changes.
- **Postal Code:** Excluded due to 80.5% missing values; regional analysis relies on Market, Region, and Country.
- **What-If Assumptions:** Simulation holds order volume, product mix, and unit costs constant to isolate discount effects.
