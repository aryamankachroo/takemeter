"""Build the TakeMeter candidate corpus from a public r/soccer dataset.

Instead of scraping Reddit (which now requires an OAuth app) or copy-pasting by
hand, this pulls from the public Hugging Face dataset `singhala/reddit_soccer`
(~98k real r/soccer posts and comments), applies the planning.md filters, and
samples a diverse set of candidates into data/soccer_posts_raw.csv.

Output schema matches the rest of the pipeline: text, source, url. So
annotate.py -> hand review -> check_balance.py all work unchanged.

Usage:
    python fetch_dataset.py            # default ~300 candidates
    python fetch_dataset.py --n 250    # custom target
"""

import argparse
import csv
import io
import os
import sys

import pandas as pd
import requests

PARQUET_URL = (
    "https://huggingface.co/datasets/singhala/reddit_soccer/"
    "resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet"
)
OUTPUT_PATH = os.path.join("data", "soccer_posts_raw.csv")
MIN_WORDS = 15
DEFAULT_TARGET = 300
SEED = 42
# Roughly how much of the sample should be standalone posts vs. comments.
POST_FRACTION = 0.35
DELETED_MARKERS = {"", "[deleted]", "[removed]", "[deleted by user]", "nan", "none"}


def clean(text) -> str:
    """Collapse whitespace; treat NaN/None as empty."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    return " ".join(str(text).split())


def word_count(text: str) -> int:
    return len(text.split())


def is_usable(text: str) -> bool:
    if text.lower() in DELETED_MARKERS:
        return False
    # Skip bodies that are essentially just a URL with no commentary.
    if text.lower().startswith(("http://", "https://", "www.")) and word_count(text) < MIN_WORDS:
        return False
    return word_count(text) >= MIN_WORDS


def download_dataframe() -> pd.DataFrame:
    print("Downloading r/soccer dataset (~10 MB)...")
    resp = requests.get(PARQUET_URL, timeout=120)
    resp.raise_for_status()
    df = pd.read_parquet(io.BytesIO(resp.content))
    print(f"Loaded {len(df):,} raw rows.")
    return df


def build_posts(df: pd.DataFrame) -> pd.DataFrame:
    """One row per unique submission: title + submission_text."""
    posts = df.drop_duplicates(subset=["name"]).copy()
    posts["text"] = (
        posts["title"].map(clean) + " " + posts["submission_text"].map(clean)
    ).str.strip()
    posts["source"] = "post"
    posts["url"] = posts["submission_url"].map(clean)
    posts = posts[posts["text"].map(is_usable)]
    return posts[["text", "source", "url"]]


def build_comments(df: pd.DataFrame) -> pd.DataFrame:
    comments = df.copy()
    comments["text"] = comments["comment"].map(clean)
    comments["source"] = "comment"
    comments["url"] = comments["submission_url"].map(clean)
    comments = comments[comments["text"].map(is_usable)]
    comments = comments.drop_duplicates(subset=["text"])
    return comments[["text", "source", "url"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=DEFAULT_TARGET, help="target number of candidates")
    args = parser.parse_args()
    target = args.n

    df = download_dataframe()

    posts = build_posts(df)
    comments = build_comments(df)
    print(f"Usable posts: {len(posts):,} | usable comments: {len(comments):,}")

    n_posts = min(len(posts), int(round(target * POST_FRACTION)))
    n_comments = min(len(comments), target - n_posts)
    # If one pool is short, backfill from the other to still hit the target.
    if n_posts + n_comments < target:
        n_posts = min(len(posts), target - n_comments)

    sampled_posts = posts.sample(n=n_posts, random_state=SEED)
    sampled_comments = comments.sample(n=n_comments, random_state=SEED)

    out = pd.concat([sampled_posts, sampled_comments], ignore_index=True)
    out = out.drop_duplicates(subset=["text"]).sample(frac=1, random_state=SEED).reset_index(drop=True)

    os.makedirs("data", exist_ok=True)
    out.to_csv(OUTPUT_PATH, index=False, quoting=csv.QUOTE_MINIMAL)

    print(f"\nWrote {len(out)} candidates to {OUTPUT_PATH}")
    print(f"  posts:    {(out['source'] == 'post').sum()}")
    print(f"  comments: {(out['source'] == 'comment').sum()}")
    print("\nNext: pre-label with `python annotate.py`, then hand-review every label.")


if __name__ == "__main__":
    main()
