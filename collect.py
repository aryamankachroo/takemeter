"""Manual collection helper for the TakeMeter dataset.

Lets you paste r/soccer posts/comments straight from your browser into
data/soccer_posts_raw.csv without using the Reddit API. Writes the same schema
the rest of the pipeline expects (text, source, url) so annotate.py and
check_balance.py keep working unchanged.

Usage:
    python collect.py

For each example you:
  1. Paste the text (it can span multiple lines), then type END on its own line.
  2. Choose whether it's a post or a comment.
  3. Paste the URL (optional - press Enter to skip).
Type 'q' as the first line of the text to quit.
"""

import csv
import os

OUTPUT_PATH = os.path.join("data", "soccer_posts_raw.csv")
MIN_WORDS = 15
FIELDNAMES = ["text", "source", "url"]


def clean(text: str) -> str:
    """Collapse whitespace so multi-line pastes stay on a single CSV cell."""
    return " ".join(text.split())


def existing_count() -> int:
    if not os.path.exists(OUTPUT_PATH):
        return 0
    with open(OUTPUT_PATH, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def load_existing_texts() -> set:
    if not os.path.exists(OUTPUT_PATH):
        return set()
    with open(OUTPUT_PATH, newline="", encoding="utf-8") as f:
        return {row["text"] for row in csv.DictReader(f)}


def read_multiline() -> str:
    """Read lines until the user types END (or 'q' to quit) on its own line."""
    print("\nPaste the post/comment text. Type END on its own line when done.")
    print("(Type 'q' on the first line to quit.)")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not lines and line.strip().lower() == "q":
            return "q"
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def read_source() -> str:
    while True:
        choice = input("Source - [p]ost or [c]omment? (default p): ").strip().lower()
        if choice in ("", "p", "post"):
            return "post"
        if choice in ("c", "comment"):
            return "comment"
        print("  Please enter 'p' or 'c'.")


def append_row(row: dict):
    file_exists = os.path.exists(OUTPUT_PATH)
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    print("TakeMeter manual collection helper")
    print(f"Appending to: {OUTPUT_PATH}")
    count = existing_count()
    seen = load_existing_texts()
    print(f"Existing examples in file: {count}")

    while True:
        raw = read_multiline()
        if raw.strip().lower() == "q":
            break

        text = clean(raw)
        if not text:
            print("  (empty - skipped)")
            continue

        words = len(text.split())
        if words < MIN_WORDS:
            keep = input(
                f"  Only {words} words (< {MIN_WORDS}). Add anyway? [y/N]: "
            ).strip().lower()
            if keep != "y":
                print("  Skipped.")
                continue

        if text in seen:
            print("  Duplicate of something already in the file - skipped.")
            continue

        source = read_source()
        url = input("URL (optional, press Enter to skip): ").strip()

        append_row({"text": text, "source": source, "url": url})
        seen.add(text)
        count += 1
        print(f"  Saved. Total examples: {count}\n")

    print(f"\nDone. {count} examples in {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()
