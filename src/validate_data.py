import sys
import logging
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "Dataset" / "Global_Superstore2.csv"
CLEANED_FILE = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"
REJECTED_FILE = PROJECT_ROOT / "data" / "rejected" / "rejected_records.csv"

SOURCE_ROW_COUNT = 51_290
DISCOUNT_MIN = 0.00
DISCOUNT_MAX = 0.85

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def run_assertions(results: list[tuple[str, bool, str]]) -> bool:
    all_passed = True
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        log.info(f"{status} | {name}")
        if detail:
            log.info(f"       | {detail}")
        if not passed:
            all_passed = False
    return all_passed


def main() -> int:
    for f in [SOURCE_FILE, CLEANED_FILE, REJECTED_FILE]:
        if not f.exists():
            log.error(f"Missing file: {f}")
            return 1

    with open(SOURCE_FILE, encoding="latin1") as fh:
        source_rows = sum(1 for _ in fh) - 1

    df_cleaned = pd.read_csv(CLEANED_FILE, encoding="utf-8", low_memory=False)
    cleaned_rows = len(df_cleaned)

    df_rejected = pd.read_csv(REJECTED_FILE, encoding="utf-8")
    rejected_rows = len(df_rejected) if "rejection_reason" in df_rejected.columns and len(df_rejected) > 0 else 0

    results = []

    results.append(("Source row count", source_rows == SOURCE_ROW_COUNT, f"Actual: {source_rows:,}"))

    n_cleaned_dupes = df_cleaned.duplicated().sum()
    b_pass = source_rows == cleaned_rows + rejected_rows + n_cleaned_dupes
    results.append(("Reconciliation", b_pass, f"Sum: {cleaned_rows + rejected_rows + n_cleaned_dupes:,}"))

    for col in ["order_id", "order_date", "product_id", "sales"]:
        if col not in df_cleaned.columns:
            results.append((f"Column {col} exists", False, "Missing column"))
            continue
        n_null = df_cleaned[col].isna().sum()
        results.append((f"No nulls in {col}", n_null == 0, f"Null count: {n_null}"))

    if "discount" in df_cleaned.columns:
        disc_num = pd.to_numeric(df_cleaned["discount"], errors="coerce")
        out_of_range = ((disc_num < DISCOUNT_MIN) | (disc_num > DISCOUNT_MAX)).sum()
        results.append(("Discount range valid", out_of_range == 0, f"Out of range: {out_of_range}"))
    else:
        results.append(("Discount column present", False, "Missing column"))

    expected_cleaned = source_rows - rejected_rows - n_cleaned_dupes
    results.append(("Cleaned row count expected", cleaned_rows == expected_cleaned, f"Actual: {cleaned_rows:,}"))
    results.append(("No exact duplicates", n_cleaned_dupes == 0, f"Duplicates: {n_cleaned_dupes}"))

    for date_col in ["order_date", "ship_date"]:
        if date_col in df_cleaned.columns:
            parsed = pd.to_datetime(df_cleaned[date_col], errors="coerce")
            results.append((f"Date parseable: {date_col}", parsed.isna().sum() == 0, f"Failures: {parsed.isna().sum()}"))

    if "sales" in df_cleaned.columns:
        sales_num = pd.to_numeric(df_cleaned["sales"], errors="coerce")
        non_positive = (sales_num <= 0).sum()
        results.append(("Sales positive", non_positive == 0, f"Non-positive: {non_positive}"))

    all_passed = run_assertions(results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
