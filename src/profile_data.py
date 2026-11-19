from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = PROJECT_ROOT / "data" / "raw" / "Global_Superstore2.csv"

EXPECTED_COLUMNS = [
    "Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode",
    "Customer ID", "Customer Name", "Segment", "City", "State",
    "Country", "Postal Code", "Market", "Region", "Product ID",
    "Category", "Sub-Category", "Product Name", "Sales", "Quantity",
    "Discount", "Profit", "Shipping Cost", "Order Priority"
]


def main():
    df = pd.read_csv(SOURCE_FILE, encoding="latin1")

    actual_cols = list(df.columns)
    assert len(actual_cols) == len(EXPECTED_COLUMNS)
    assert [c for c in EXPECTED_COLUMNS if c not in actual_cols] == []

    parsed_od = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
    parsed_sd = pd.to_datetime(df["Ship Date"], dayfirst=True, errors="coerce")
    assert parsed_od.isna().sum() == 0
    assert parsed_sd.isna().sum() == 0

    assert df.duplicated().sum() == 0
    assert df["Postal Code"].isna().sum() == 41296
    assert (df["Profit"] < 0).sum() == 12544

    for c in ["Order ID", "Order Date", "Product ID", "Sales", "Profit", "Quantity"]:
        assert df[c].isna().sum() == 0

    print("Profiling checks passed.")


if __name__ == "__main__":
    main()
