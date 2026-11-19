# Market Basket Analysis (MBA) Documentation

**Project:** Retail Margin Dynamics & Discount Optimization  
**Phase:** 5 — Market Basket Analysis  
**Algorithm:** Apriori (`mlxtend`)  
**Output File:** `data/processed/association_rules.csv`  
**Date:** 2026-11-19  

---

## 1. Methodology & Analytical Pool

### Effective Basket Pool
In the Global Superstore dataset:
- **Total line items:** 51,290
- **Total distinct orders:** 25,035
- **Single-item orders:** 12,264 (48.99%)
- **Multi-item orders (2+ product lines):** 12,771 (51.01%)

Because single-item transactions cannot produce co-occurrence pairs, the multi-item order subset represents the **effective basket pool**. 

### Dimensionality Management
The dataset spans **3,788 distinct product names**. Calculating pairs across all 3,788 columns in a raw binary basket matrix produces $\approx 6.33 \times 10^6$ candidate pairs, exceeding local memory capacity ($>150\text{ GB}$). To ensure robust and actionable results:
1. Candidate products were filtered to items with purchase frequency $\ge 25$ occurrences across the store (551 high-velocity products).
2. Orders containing 2 or more of these high-velocity products (4,217 baskets) formed the binary basket matrix ($4,217 \times 551$).
3. Apriori was run with a minimum support of 2 co-purchases ($\text{min\_support} \approx 0.000474$).
4. Association rules were filtered with $\text{Lift} > 1.0$ and $\text{Confidence} \ge 10\%$.

---

## 2. Key Metrics & Interpretation

- **Support ($P(A \cap B)$):** Proportion of transactions containing both itemsets $A$ and $B$.
- **Confidence ($P(B|A)$):** Probability that a customer purchases $B$ given that they have placed $A$ in their basket.
- **Lift ($\frac{P(B|A)}{P(B)}$):** Factor by which co-purchase exceeds expected independent random purchase. A lift $> 1$ indicates positive association; lift values in the hundreds indicate strong affinity.

---

## 3. Top Discovered Association Rules

| # | Antecedent(s) | Consequent(s) | Support | Confidence | Lift | Interpretation |
|---|---|---|---|---|---|---|
| **1** | Binney & Smith Highlighters, Water Color + Enermax Memory Card, USB | Office Star Bag Chairs, Set of Two | 0.000474 | 100.0% | 351.42 | High affinity bundle between office supplies/accessories and office seating |
| **2** | Hewlett Copy Machine, Color + Hon Executive Leather Armchair, Black | Office Star Rocking Chair, Set of Two | 0.000474 | 100.0% | 301.21 | Corporate office equipment & furniture bundle |
| **3** | Hewlett Copy Machine, Color + Stanley Sketch Pad, Water Color | Office Star Rocking Chair, Set of Two | 0.000474 | 100.0% | 301.21 | Combined workspace design & creative supply bundle |
| **4** | Binney & Smith Highlighters, Water Color + Office Star Bag Chairs, Set of Two | Enermax Memory Card, USB | 0.000474 | 100.0% | 281.13 | Cross-category technology & furniture bundle |
| **5** | Smead File Cart, Industrial | Rogers Lockers, Blue | 0.000711 | 21.4% | 25.18 | Storage and organization pairings within commercial office supplies |

---

## 4. Business Recommendations for Discount Optimization

1. **Bundle-Specific Discounting:** Rather than discounting high-margin items individually (which erodes profitability), offer bundled promotions where a low-margin/high-discount item is paired with a full-price, high-margin complementary product (e.g., Filing Carts + Lockers).
2. **Defensive Cross-Selling:** Tables and Machines exhibit low or negative margin at high discount rates. Use MBA rules to bundle them with high-margin accessories (e.g., Memory Cards, Highlighters, Envelopes) to protect blended basket profitability.

---

## 5. Critical Caveat

> **Important:** These rules are derived from observational historical purchase data. **Association does not imply causation.** These patterns indicate products that have historically appeared together in customer transactions; they do not prove that discounting one item will cause an increase in demand for the other.

---

*Report generated: 2026-11-19 | Phase 5 Status: COMPLETE ✓*
