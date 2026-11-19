import os
import sys
import logging
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_FILE = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"
SCHEMA_FILE = PROJECT_ROOT / "sql" / "01_create_schema.sql"
VIEWS_FILE = PROJECT_ROOT / "sql" / "04_create_views.sql"
ENV_FILE = PROJECT_ROOT / ".env"

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def get_connection(dbname: str = None):
    load_dotenv(ENV_FILE)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=dbname or os.getenv("DB_NAME", "retail_margin_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )


def ensure_database():
    load_dotenv(ENV_FILE)
    db_name = os.getenv("DB_NAME", "retail_margin_db")
    conn = get_connection(dbname="postgres")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if not cur.fetchone():
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        log.info(f"Created database: {db_name}")
    else:
        log.info(f"Database exists: {db_name}")
    cur.close()
    conn.close()


def create_schema(conn):
    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()


def load_staging(conn, df: pd.DataFrame) -> int:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE stg_superstore_sales")

        cols = [
            "row_id", "order_id", "order_date", "ship_date", "ship_mode",
            "customer_id", "customer_name", "segment", "city", "state",
            "country", "postal_code", "market", "region", "product_id",
            "category", "sub_category", "product_name", "sales", "quantity",
            "discount", "profit", "shipping_cost", "order_priority",
        ]

        records = [
            tuple(None if pd.isna(v) else v for v in row)
            for row in df[cols].itertuples(index=False, name=None)
        ]

        insert_sql = "INSERT INTO stg_superstore_sales (" + ", ".join(cols) + ") VALUES %s"
        execute_values(cur, insert_sql, records, page_size=1000)

    conn.commit()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM stg_superstore_sales")
        count = cur.fetchone()[0]
    return count


def load_fact(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE fact_sales")
        cur.execute("""
            INSERT INTO fact_sales (
                row_id, order_id, order_date, ship_date, ship_mode,
                customer_id, customer_name, segment, city, state, country,
                market, region, product_id, category, sub_category,
                product_name, sales, quantity, discount, profit,
                shipping_cost, order_priority
            )
            SELECT
                row_id, order_id, order_date, ship_date, ship_mode,
                customer_id, customer_name, segment, city, state, country,
                market, region, product_id, category, sub_category,
                product_name, sales, quantity, discount, profit,
                shipping_cost, order_priority
            FROM stg_superstore_sales
            WHERE order_id IS NOT NULL
              AND order_date IS NOT NULL
              AND product_id IS NOT NULL
              AND sales IS NOT NULL
              AND profit IS NOT NULL
              AND quantity IS NOT NULL
        """)
    conn.commit()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM fact_sales")
        count = cur.fetchone()[0]
    return count


def create_views(conn):
    views_sql = VIEWS_FILE.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(views_sql)
    conn.commit()


def validate_load(conn, df: pd.DataFrame, stg_count: int, fact_count: int) -> bool:
    csv_rows = len(df)
    csv_sum_sales = round(float(df["sales"].sum()), 2)
    csv_sum_profit = round(float(df["profit"].sum()), 2)

    with conn.cursor() as cur:
        cur.execute("SELECT ROUND(SUM(sales)::NUMERIC, 2), ROUND(SUM(profit)::NUMERIC, 2) FROM fact_sales")
        db_sum_sales, db_sum_profit = cur.fetchone()

    db_sum_sales = float(db_sum_sales)
    db_sum_profit = float(db_sum_profit)

    checks = [
        ("Row count", csv_rows == fact_count),
        ("SUM(sales)", abs(csv_sum_sales - db_sum_sales) < 0.01),
        ("SUM(profit)", abs(csv_sum_profit - db_sum_profit) < 0.01),
        ("Staging == Fact", stg_count == fact_count),
    ]

    all_pass = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        log.info(f"{status} | {name}")
        if not passed:
            all_pass = False

    return all_pass


def main() -> int:
    df = pd.read_csv(CLEANED_FILE, encoding="utf-8", low_memory=False, parse_dates=["order_date", "ship_date"])

    ensure_database()
    conn = get_connection()

    create_schema(conn)
    stg_count = load_staging(conn, df)
    fact_count = load_fact(conn)
    create_views(conn)

    all_pass = validate_load(conn, df, stg_count, fact_count)
    conn.close()

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
