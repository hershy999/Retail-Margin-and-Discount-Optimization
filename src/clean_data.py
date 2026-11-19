import sys
import re
import logging
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "Dataset" / "Global_Superstore2.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"
REJECTED_FILE = PROJECT_ROOT / "data" / "rejected" / "rejected_records.csv"

DISCOUNT_MIN = 0.00
DISCOUNT_MAX = 0.85

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def to_snake_case(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[\s\-]+", "_", name)
    name = re.sub(r"[^\w]", "", name)
    name = re.sub(r"_+", "_", name)
    return name.lower().strip("_")


def load_source(filepath: Path) -> pd.DataFrame:
    log.info(f"Loading: {filepath}")
    df = pd.read_csv(filepath, encoding="latin1", dtype=str)
    log.info(f"Loaded {len(df):,} rows, {len(df.columns)} columns.")
    return df


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    original = list(df.columns)
    df.columns = [to_snake_case(c) for c in df.columns]
    renamed = {o: n for o, n in zip(original, df.columns) if o != n}
    if renamed:
        log.info(f"Renamed {len(renamed)} columns.")
    return df


def parse_dates(df: pd.DataFrame, rejected: list) -> pd.DataFrame:
    for date_col in ["order_date", "ship_date"]:
        parsed = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        failures = parsed.isna() & df[date_col].notna()
        n_fail = failures.sum()
        if n_fail > 0:
            failed_rows = df[failures].copy()
            failed_rows["rejection_reason"] = f"unparseable_{date_col}"
            rejected.append(failed_rows)
            df = df[~failures].copy()
            parsed = parsed[~failures]
        df[date_col] = parsed

    null_dates = df["order_date"].isna() | df["ship_date"].isna()
    n_null_dates = null_dates.sum()
    if n_null_dates > 0:
        failed_rows = df[null_dates].copy()
        failed_rows["rejection_reason"] = "null_date_after_parse"
        rejected.append(failed_rows)
        df = df[~null_dates].copy()

    return df


def cast_numerics(df: pd.DataFrame, rejected: list) -> pd.DataFrame:
    float_cols = ["sales", "profit", "discount", "shipping_cost"]
    int_cols = ["quantity", "row_id"]

    for col in float_cols:
        if col not in df.columns:
            continue
        original_str = df[col].copy()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        failures = df[col].isna() & original_str.notna()
        n_fail = failures.sum()
        if n_fail > 0:
            failed_rows = df[failures].copy()
            failed_rows["rejection_reason"] = f"non_numeric_{col}"
            rejected.append(failed_rows)
            df = df[~failures].copy()

    for col in int_cols:
        if col not in df.columns:
            continue
        original_str = df[col].copy()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        failures = df[col].isna() & original_str.notna()
        n_fail = failures.sum()
        if n_fail > 0:
            failed_rows = df[failures].copy()
            failed_rows["rejection_reason"] = f"non_numeric_{col}"
            rejected.append(failed_rows)
            df = df[~failures].copy()
        df[col] = df[col].astype("Int64")

    return df


def reject_critical_nulls(df: pd.DataFrame, rejected: list) -> pd.DataFrame:
    critical_cols = ["order_id", "order_date", "product_id", "sales"]
    for col in critical_cols:
        if col not in df.columns:
            continue
        null_mask = df[col].isna()
        n_null = null_mask.sum()
        if n_null > 0:
            failed_rows = df[null_mask].copy()
            failed_rows["rejection_reason"] = f"null_{col}"
            rejected.append(failed_rows)
            df = df[~null_mask].copy()
    return df


def handle_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    n_before = len(df)
    df = df.drop_duplicates()
    return df, n_before - len(df)


def save_outputs(df: pd.DataFrame, rejected_rows: list) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REJECTED_FILE.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    log.info(f"Cleaned CSV written: {OUTPUT_FILE} ({len(df):,} rows)")

    if rejected_rows:
        rejected_df = pd.concat(rejected_rows, ignore_index=True)
        cols = ["rejection_reason"] + [c for c in rejected_df.columns if c != "rejection_reason"]
        rejected_df[cols].to_csv(REJECTED_FILE, index=False, encoding="utf-8")
        log.info(f"Rejected CSV written: {REJECTED_FILE} ({len(rejected_df):,} rows)")
    else:
        pd.DataFrame(columns=["rejection_reason"]).to_csv(REJECTED_FILE, index=False)
        log.info(f"No rejected rows: {REJECTED_FILE}")


def main():
    df = load_source(SOURCE_FILE)
    input_rows = len(df)

    df = normalize_column_names(df)

    rejected = []
    df = parse_dates(df, rejected)
    df = cast_numerics(df, rejected)
    df = reject_critical_nulls(df, rejected)
    df, dupes_removed = handle_duplicates(df)

    total_rejected = sum(len(r) for r in rejected)
    cleaned_rows = len(df)

    log.info(f"Input: {input_rows:,} | Cleaned: {cleaned_rows:,} | Rejected: {total_rejected:,} | Duplicates: {dupes_removed:,}")
    log.info(f"Reconciled: {input_rows == cleaned_rows + total_rejected + dupes_removed}")

    save_outputs(df, rejected)
    return cleaned_rows, total_rejected, input_rows, dupes_removed


if __name__ == "__main__":
    main()
