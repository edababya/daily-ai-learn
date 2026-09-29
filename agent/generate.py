#!/usr/bin/env python3
"""Daily AI learning post generator.

Picks today's topic, asks an OpenAI-compatible model for one X-ready post
(<=280 chars) plus a short markdown explainer, and writes posts/YYYY-MM-DD.md.

Env:
    AI_API_KEY    required (unless --dry-run)
    AI_API_BASE   default https://api.deepseek.com
    AI_MODEL      default deepseek-chat
"""

import datetime
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent.parent
TOPICS_FILE = ROOT / "agent" / "topics.txt"
POSTS_DIR = ROOT / "posts"

SYSTEM_PROMPT = """You are an AI educator writing for a technically literate audience \
of founders, engineers, and investors on X. Your style: sharp, concrete, no hype, \
no filler. Teach one genuinely non-obvious insight — the kind of thing a smart \
person gets wrong. Never be vague, never moralize, never use clickbait."""

USER_TEMPLATE = """Topic: {topic}

Write TWO things, exactly in this format:

TWEET:
(one X post, English, at most 280 characters including hashtags. 1-2 hashtags max, \
no emoji. Must teach one sharp insight about the topic, not just define it. \
No hype words like "revolutionary", "game-changer".)

EXPLAINER:
(a 120-180 word markdown explainer for a smart reader: what it is, why it works \
this way, and one line on why it matters. Plain markdown, no title line.)
"""


def pick_topic(today: datetime.date) -> str:
    topics = [line.strip() for line in TOPICS_FILE.read_text().splitlines() if line.strip()]
    if not topics:
        raise SystemExit("topics.txt is empty")
    return topics[today.timetuple().tm_yday % len(topics)]


def call_model(topic: str) -> tuple[str, str]:
    api_key = os.environ.get("AI_API_KEY")
    if not api_key:
        raise SystemExit("AI_API_KEY is not set")
    base = os.environ.get("AI_API_BASE", "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("AI_MODEL", "deepseek-chat")

    def complete(prompt: str) -> str:
        resp = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 800,
            },
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    text = complete(USER_TEMPLATE.format(topic=topic))
    tweet, explainer = parse(text)

    if len(tweet) > 280:
        # one retry: ask the model to compress its own tweet
        text = complete(
            f"Shorten this X post to at most 280 characters, keeping the insight. "
            f"Reply with ONLY the post, no preamble:\n\n{tweet}"
        )
        tweet = text.strip()
    if len(tweet) > 280:  # hard guard: cut at last space
        tweet = tweet[:277].rsplit(" ", 1)[0] + "..."
    return tweet, explainer


def parse(text: str) -> tuple[str, str]:
    if "TWEET:" not in text or "EXPLAINER:" not in text:
        raise SystemExit(f"Model output missing TWEET:/EXPLAINER: markers:\n{text}")
    tweet = text.split("TWEET:", 1)[1].split("EXPLAINER:", 1)[0].strip()
    explainer = text.split("EXPLAINER:", 1)[1].strip()
    if not tweet or not explainer:
        raise SystemExit(f"Model output had empty sections:\n{text}")
    return tweet, explainer


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    today = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()
    topic = pick_topic(today)

    if dry_run:
        print(SYSTEM_PROMPT)
        print()
        print(USER_TEMPLATE.format(topic=topic))
        return

    tweet, explainer = call_model(topic)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    out = POSTS_DIR / f"{today.isoformat()}.md"
    out.write_text(
        f"# {today.isoformat()} — {topic}\n\n## X-ready post\n\n{tweet}\n\n"
        f"## Explainer\n\n{explainer}\n"
    )
    print(f"Wrote {out}")
    print()
    print("----- X post (copy/paste to publish manually) -----")
    print(tweet)
    print(f"----- ({len(tweet)}/280 chars) -----")


if __name__ == "__main__":
    main()
