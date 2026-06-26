"""Check the label balance of the final annotated dataset.

Reads data/soccer_posts.csv, prints the per-label count and percentage, the
total number of examples, and warns if any label is over-represented (>70%) or
under-represented (<20%).

Usage:
    python check_balance.py
"""

import csv
import os
import sys
from collections import Counter

INPUT_PATH = os.path.join("data", "soccer_posts.csv")
HIGH_THRESHOLD = 0.70
LOW_THRESHOLD = 0.20


def main():
    if not os.path.exists(INPUT_PATH):
        sys.exit(f"File not found: {INPUT_PATH}")

    with open(INPUT_PATH, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("label") or "").strip()]

    total = len(rows)
    if total == 0:
        sys.exit(f"No labeled rows found in {INPUT_PATH}.")

    counts = Counter(r["label"].strip() for r in rows)

    print(f"Total labeled examples: {total}\n")
    print("Label distribution:")
    for label, count in counts.most_common():
        pct = count / total
        print(f"  {label:<10} {count:>4}  ({pct:6.1%})")

    print()
    warned = False
    for label, count in counts.items():
        pct = count / total
        if pct > HIGH_THRESHOLD:
            print(f"WARNING: '{label}' is {pct:.1%} of the data (over {HIGH_THRESHOLD:.0%}).")
            warned = True
        if pct < LOW_THRESHOLD:
            print(f"WARNING: '{label}' is {pct:.1%} of the data (under {LOW_THRESHOLD:.0%}).")
            warned = True

    if not warned:
        print("Balance looks OK: every label is within 20%-70% of the dataset.")


if __name__ == "__main__":
    main()
