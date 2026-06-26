"""Pre-label the raw r/soccer corpus with Groq to speed up annotation.

Reads data/soccer_posts_raw.csv, asks llama-3.3-70b-versatile to assign one of
{analysis, hot_take, reaction} to each post, and writes the result to
data/soccer_posts_prelabeled.csv.

IMPORTANT: These labels are a STARTING POINT only. Every label must be reviewed
and corrected by hand afterwards. The pre_labeled column is set to True so the
AI-assisted rows can be tracked and disclosed in the README.

Credentials are read from the environment and never hardcoded:
    GROQ_API_KEY

Usage:
    python annotate.py
"""

import csv
import os
import sys
import time
from collections import Counter

from groq import Groq

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

MODEL = "llama-3.3-70b-versatile"
INPUT_PATH = os.path.join("data", "soccer_posts_raw.csv")
OUTPUT_PATH = os.path.join("data", "soccer_posts_prelabeled.csv")
VALID_LABELS = {"analysis", "hot_take", "reaction"}

SYSTEM_PROMPT = (
    "You are labeling r/soccer posts for a text classification dataset.\n"
    "Assign exactly one label from: analysis, hot_take, reaction.\n"
    "- analysis: structured argument using tactics, stats, or evidence. Reasoning holds "
    "without the emotional framing.\n"
    "- hot_take: bold opinion asserted without meaningful evidence. Confident but "
    "doesn't argue.\n"
    "- reaction: immediate emotional response to a match/event. Primary content is "
    "feeling, not argument.\n"
    "Respond with ONLY the label name, nothing else."
)


def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        sys.exit(
            "Missing required environment variable: GROQ_API_KEY\n"
            "See .env.example for the expected values."
        )
    return Groq(api_key=api_key)


def normalize_label(raw: str) -> str:
    """Map a model response to a valid label, or '' if it can't be parsed."""
    cleaned = (raw or "").strip().lower().strip(".\"' ")
    if cleaned in VALID_LABELS:
        return cleaned
    # Be forgiving if the model wraps the label in a short sentence.
    for label in VALID_LABELS:
        if label in cleaned:
            return label
    return ""


def classify(client, text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        max_tokens=10,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return normalize_label(response.choices[0].message.content)


def load_rows():
    if not os.path.exists(INPUT_PATH):
        sys.exit(f"Input file not found: {INPUT_PATH}\nRun scrape_reddit.py first.")
    with open(INPUT_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    client = get_client()
    rows = load_rows()
    total = len(rows)
    print(f"Pre-labeling {total} examples with {MODEL}...")

    out_rows = []
    counts = Counter()

    for i, row in enumerate(rows, start=1):
        text = row.get("text", "")
        try:
            label = classify(client, text)
        except Exception as exc:  # noqa: BLE001 - keep going on transient errors
            print(f"  [{i}/{total}] error: {exc}; retrying once...")
            time.sleep(2)
            try:
                label = classify(client, text)
            except Exception as exc2:  # noqa: BLE001
                print(f"  [{i}/{total}] failed again: {exc2}; leaving blank.")
                label = ""

        counts[label or "UNPARSED"] += 1
        out_rows.append(
            {
                "text": text,
                "label": label,
                "notes": "",
                "pre_labeled": "True",
                "url": row.get("url", ""),
            }
        )

        if i % 25 == 0:
            print(f"  {i}/{total} done")

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["text", "label", "notes", "pre_labeled", "url"]
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"\nWrote {len(out_rows)} rows to {OUTPUT_PATH}")
    print("\nLabel distribution (pre-review):")
    for label, count in counts.most_common():
        print(f"  {label:<10} {count}")
    print("\nReminder: review and correct EVERY label by hand before training.")


if __name__ == "__main__":
    main()
