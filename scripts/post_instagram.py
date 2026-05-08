#!/usr/bin/env python3
"""Post the next queued entry from private/instagram-queue.yaml to Instagram.

Run with:
    uv run --with instagrapi --with python-dotenv --with pyyaml \
        python scripts/post_instagram.py [--publish]

By default this is a dry-run preview. Pass --publish to actually post.

Posts at most one entry per run. If any entry was posted in the last 24
hours, the script refuses to post (recurring-account safety cap). After a
successful post, updates the queue file in place with `posted_at` and
`posted_url`.

Setup is documented in private/instagram-setup.md.
"""

import argparse
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
QUEUE_PATH = ROOT / "private" / "instagram-queue.yaml"
SESSION_PATH = ROOT / "private" / "instagram-session.json"
ENV_PATH = ROOT / "private" / ".env"

DAY_CAP_HOURS = 24
DELAY_MIN_S = 30
DELAY_MAX_S = 90

CAPTION_LIMIT = 2200
HASHTAG_LIMIT = 30


def _str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _str_representer, Dumper=yaml.SafeDumper)


def load_env():
    if not ENV_PATH.exists():
        sys.exit(f"Missing {ENV_PATH}. See private/instagram-setup.md.")
    from dotenv import dotenv_values
    values = dotenv_values(ENV_PATH)
    username = values.get("IG_USERNAME")
    password = values.get("IG_PASSWORD")
    if not username or not password:
        sys.exit("IG_USERNAME and IG_PASSWORD must both be set in private/.env.")
    return username, password


def load_queue():
    if not QUEUE_PATH.exists():
        sys.exit(f"Missing {QUEUE_PATH}. See private/instagram-setup.md.")
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data or "posts" not in data:
        sys.exit(f"{QUEUE_PATH} has no `posts` key.")
    return data


def save_queue(data):
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=1000)


def find_next_unposted(queue):
    for i, post in enumerate(queue["posts"]):
        if not post.get("posted_at"):
            return i, post
    return None, None


def latest_posted_within(queue, hours):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    latest = None
    for post in queue["posts"]:
        ts = post.get("posted_at")
        if not ts:
            continue
        try:
            posted = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            continue
        if posted > cutoff and (latest is None or posted > latest):
            latest = posted
    return latest


def build_caption(post):
    parts = [post["caption"].strip()]
    tags = post.get("hashtags") or []
    if tags:
        parts.append("")
        parts.append(" ".join(tags))
    return "\n".join(parts)


def validate(post, caption):
    issues = []
    image = ROOT / post["image"]
    if not image.exists():
        issues.append(f"Image not found: {image}")
    if len(caption) > CAPTION_LIMIT:
        issues.append(f"Caption is {len(caption)} chars (IG limit: {CAPTION_LIMIT})")
    tags = post.get("hashtags") or []
    if len(tags) > HASHTAG_LIMIT:
        issues.append(f"{len(tags)} hashtags (IG limit: {HASHTAG_LIMIT})")
    return issues


def preview(post, caption):
    image = ROOT / post["image"]
    print(f"Next post: {post['id']}")
    print(f"  Image:        {post['image']}")
    print(f"  Image exists: {image.exists()}")
    if image.exists():
        print(f"  Image size:   {image.stat().st_size // 1024} KB")
    print(f"  Caption:      {len(caption)} chars, "
          f"{len(post.get('hashtags') or [])} hashtags")
    print()
    for line in caption.splitlines():
        print(f"    {line}" if line else "")
    print()


def login(username, password):
    from instagrapi import Client
    from instagrapi.exceptions import (
        ChallengeRequired, BadPassword, PleaseWaitAFewMinutes,
    )

    cl = Client()
    cl.delay_range = [1, 3]

    if SESSION_PATH.exists():
        try:
            cl.load_settings(SESSION_PATH)
            cl.login(username, password)
            cl.get_timeline_feed()
            print("Logged in via cached session.")
            return cl
        except Exception as e:
            print(f"Cached session unusable ({type(e).__name__}); trying fresh login.")
            cl = Client()
            cl.delay_range = [1, 3]

    try:
        cl.login(username, password)
    except ChallengeRequired:
        code = input(
            "\nInstagram challenge required.\n"
            "Check the email/SMS for this account, then enter the code here: "
        ).strip()
        cl.login(username, password, verification_code=code)
    except BadPassword:
        sys.exit("Bad password. Check IG_PASSWORD in private/.env.")
    except PleaseWaitAFewMinutes:
        sys.exit("Instagram is rate-limiting this account. Wait a few hours and retry.")

    cl.dump_settings(SESSION_PATH)
    print("Logged in fresh; session cached to private/instagram-session.json.")
    return cl


def main():
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument(
        "--publish", action="store_true",
        help="Actually post to Instagram. Without this, prints a dry-run preview.",
    )
    args = parser.parse_args()

    queue = load_queue()
    _, post = find_next_unposted(queue)

    if post is None:
        print(f"Queue empty. Add new entries to {QUEUE_PATH}.")
        return

    caption = build_caption(post)
    preview(post, caption)

    issues = validate(post, caption)
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

    if not args.publish:
        print("Dry run. Pass --publish to actually post.")
        return

    last = latest_posted_within(queue, DAY_CAP_HOURS)
    if last is not None:
        sys.exit(
            f"Day cap: last script post was at {last.isoformat()} "
            f"(< {DAY_CAP_HOURS}h ago). Try again tomorrow."
        )

    image = ROOT / post["image"]
    username, password = load_env()
    cl = login(username, password)

    delay = random.uniform(DELAY_MIN_S, DELAY_MAX_S)
    print(f"Waiting {delay:.0f}s before upload (looks more human)...")
    time.sleep(delay)

    media = cl.photo_upload(image, caption=caption)

    post["posted_at"] = datetime.now(timezone.utc).isoformat()
    post["posted_url"] = f"https://www.instagram.com/p/{media.code}/"
    save_queue(queue)

    print()
    print(f"Posted: {post['posted_url']}")


if __name__ == "__main__":
    main()
