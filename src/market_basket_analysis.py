import sys
import logging
from pathlib import Path
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_FILE = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"
OUTPUT_RULES = PROJECT_ROOT / "data" / "processed" / "association_rules.csv"

logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def format_itemset(itemset) -> str:
    return ", ".join(sorted(list(itemset)))


def run_mba() -> int:
    df = pd.read_csv(CLEANED_FILE, low_memory=False)

    top_products = set(df["product_name"].value_counts()[lambda x: x >= 25].index)

    baskets = (
        df[df["product_name"].isin(top_products)]
        .groupby("order_id")["product_name"]
        .apply(lambda s: list(set(s)))
        .tolist()
    )
    baskets = [b for b in baskets if len(b) >= 2]
    n_effective_baskets = len(baskets)

    te = TransactionEncoder()
    te_ary = te.fit(baskets).transform(baskets)
    basket_df = pd.DataFrame(te_ary, columns=te.columns_)

    min_support = 2 / n_effective_baskets
    frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True, max_len=3)

    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
    filtered_rules = rules[
        (rules["confidence"] >= 0.10) &
        (rules["lift"] > 1.0)
    ].copy()
    filtered_rules = filtered_rules.sort_values(by=["lift", "confidence"], ascending=[False, False])

    export_df = pd.DataFrame({
        "antecedents": filtered_rules["antecedents"].apply(format_itemset),
        "consequents": filtered_rules["consequents"].apply(format_itemset),
        "support": filtered_rules["support"].round(6),
        "confidence": filtered_rules["confidence"].round(4),
        "lift": filtered_rules["lift"].round(2),
    })

    OUTPUT_RULES.parent.mkdir(parents=True, exist_ok=True)
    export_df.to_csv(OUTPUT_RULES, index=False, encoding="utf-8")
    log.info(f"Exported {len(export_df):,} rules to: {OUTPUT_RULES}")

    v_support = (export_df["support"] >= 0).all() and (export_df["support"] <= 1).all()
    v_conf = (export_df["confidence"] >= 0).all() and (export_df["confidence"] <= 1).all()
    v_lift = (export_df["lift"] > 1.0).all()
    v_non_empty = len(export_df) > 0

    return 0 if (v_support and v_conf and v_lift and v_non_empty) else 1


if __name__ == "__main__":
    sys.exit(run_mba())
