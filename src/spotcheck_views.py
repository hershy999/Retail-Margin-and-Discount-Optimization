import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv(".env")
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

df = pd.read_csv("data/processed/superstore_cleaned.csv", low_memory=False)

db = pd.read_sql("SELECT * FROM vw_retail_kpis", conn)
csv_sales = round(df["sales"].sum(), 2)
csv_profit = round(df["profit"].sum(), 2)
csv_rows = len(df)
db_sales = float(db["total_sales"][0])
db_profit = float(db["total_profit"][0])
db_rows = int(db["total_rows"][0])

assert abs(csv_sales - db_sales) < 0.01
assert abs(csv_profit - db_profit) < 0.01
assert csv_rows == db_rows

db2 = pd.read_sql("SELECT discount_band, total_sales, total_profit, profit_margin_pct FROM vw_discount_profitability", conn)
db2_total_sales = round(float(db2["total_sales"].sum()), 2)
db2_total_profit = round(float(db2["total_profit"].sum()), 2)

assert abs(db2_total_sales - csv_sales) < 0.01
assert abs(db2_total_profit - csv_profit) < 0.01
assert len(db2) == 5

db3 = pd.read_sql("SELECT year_month, monthly_sales, monthly_profit FROM vw_monthly_performance WHERE yr = 2011", conn)
df_2011 = df[pd.to_datetime(df["order_date"]).dt.year == 2011]
csv_2011_sales = round(df_2011["sales"].sum(), 2)
csv_2011_profit = round(df_2011["profit"].sum(), 2)
db_2011_sales = round(float(db3["monthly_sales"].sum()), 2)
db_2011_profit = round(float(db3["monthly_profit"].sum()), 2)

assert abs(csv_2011_sales - db_2011_sales) < 0.01
assert abs(csv_2011_profit - db_2011_profit) < 0.01

conn.close()
print("All view spot-checks passed.")
