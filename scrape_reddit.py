"""Scrape r/soccer posts and top-level comments for the TakeMeter dataset.

Pulls titles + selftext from the past month's top posts and the top-level
comments on those posts, filters out low-signal items, and writes the raw
(unlabeled) corpus to data/soccer_posts_raw.csv.

Credentials are read from environment variables and are never hardcoded:
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

Usage:
    python scrape_reddit.py
"""

import csv
import os
import sys

import praw

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

SUBREDDIT = "soccer"
TIME_FILTER = "month"
TARGET_EXAMPLES = 300
MIN_WORDS = 15
# Pull comments from this many of the top posts (the rest of the budget is
# filled by post bodies). Tuned so we comfortably reach TARGET_EXAMPLES.
POST_LIMIT = 200
COMMENTS_PER_POST = 5

OUTPUT_PATH = os.path.join("data", "soccer_posts_raw.csv")


def get_reddit_client():
    """Build a read-only PRAW client from environment variables."""
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT")

    missing = [
        name
        for name, value in (
            ("REDDIT_CLIENT_ID", client_id),
            ("REDDIT_CLIENT_SECRET", client_secret),
            ("REDDIT_USER_AGENT", user_agent),
        )
        if not value
    ]
    if missing:
        sys.exit(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + "\nSee .env.example for the expected values."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        check_for_async=False,
    )


def word_count(text: str) -> int:
    return len(text.split())


def clean(text: str) -> str:
    """Collapse whitespace so multi-line bodies stay on a single CSV cell."""
    return " ".join((text or "").split())


def is_low_signal_post(submission) -> bool:
    """Skip link-only posts and anything without enough body text."""
    # A link post with no self text is "just a link with no body".
    if not submission.is_self and not (submission.selftext or "").strip():
        return True
    return False


def collect():
    reddit = get_reddit_client()
    subreddit = reddit.subreddit(SUBREDDIT)

    rows = []
    seen = set()

    for submission in subreddit.top(time_filter=TIME_FILTER, limit=POST_LIMIT):
        if len(rows) >= TARGET_EXAMPLES:
            break

        if is_low_signal_post(submission):
            continue

        title = clean(submission.title)
        selftext = clean(submission.selftext)
        post_text = (title + " " + selftext).strip()

        if word_count(post_text) >= MIN_WORDS and post_text not in seen:
            seen.add(post_text)
            rows.append(
                {
                    "text": post_text,
                    "source": "post",
                    "url": f"https://www.reddit.com{submission.permalink}",
                }
            )

        # Top-level comments only.
        submission.comments.replace_more(limit=0)
        for comment in submission.comments[:COMMENTS_PER_POST]:
            if len(rows) >= TARGET_EXAMPLES:
                break
            body = clean(getattr(comment, "body", ""))
            if body in ("", "[deleted]", "[removed]"):
                continue
            if word_count(body) < MIN_WORDS or body in seen:
                continue
            seen.add(body)
            rows.append(
                {
                    "text": body,
                    "source": "comment",
                    "url": f"https://www.reddit.com{comment.permalink}",
                }
            )

    return rows


def main():
    os.makedirs("data", exist_ok=True)
    rows = collect()

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "source", "url"])
        writer.writeheader()
        writer.writerows(rows)

    posts = sum(1 for r in rows if r["source"] == "post")
    comments = sum(1 for r in rows if r["source"] == "comment")
    print(f"Wrote {len(rows)} examples to {OUTPUT_PATH}")
    print(f"  posts:    {posts}")
    print(f"  comments: {comments}")


if __name__ == "__main__":
    main()
