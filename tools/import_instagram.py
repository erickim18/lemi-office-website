#!/usr/bin/env python3
"""Add Lena's tagged Instagram posts to the Lemi Journal.

Looks at the most recent @lemioffice posts. Any post whose caption includes
#lemijournal becomes a Journal article (her photo and her caption), then the
Journal is rebuilt. Posts that were already added are skipped.

Needs INSTAGRAM_TOKEN: a Meta access token with instagram_basic and
pages_show_list for the Facebook Page connected to @lemioffice.
IG_USER_ID is optional; without it the account is looked up from the token.

Runs from .github/workflows/instagram.yml every few hours.
Try it without a token:  python3 tools/import_instagram.py --sample posts.json --dry-run
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "content", "journal")
IMG_DIR = os.path.join(ROOT, "assets", "img", "journal")
GRAPH = "https://graph.facebook.com/v25.0"
TAG = re.compile(r"#lemijournal\b", re.I)
FIELDS = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"
NEW_YORK = ZoneInfo("America/New_York")


def api(path, token, **params):
    params["access_token"] = token
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        sys.exit(f"Instagram API error {e.code} on {path}: {detail}")


def instagram_user_id(token):
    if os.environ.get("IG_USER_ID"):
        return os.environ["IG_USER_ID"]
    pages = api("me/accounts", token, fields="instagram_business_account{id,username}")["data"]
    accounts = [p["instagram_business_account"] for p in pages if p.get("instagram_business_account")]
    if not accounts:
        sys.exit("No Instagram business account is connected to the Facebook Page this token can see.")
    preferred = [a for a in accounts if a.get("username") == "lemioffice"]
    return (preferred or accounts)[0]["id"]


def recent_posts(token):
    return api(f"{instagram_user_id(token)}/media", token, fields=FIELDS, limit=25)["data"]


def imported_ids():
    ids = set()
    if os.path.isdir(POSTS_DIR):
        for f in os.listdir(POSTS_DIR):
            if f.endswith(".md"):
                m = re.search(r"^instagram_id:\s*(\S+)", open(os.path.join(POSTS_DIR, f), encoding="utf-8").read(), re.M)
                if m:
                    ids.add(m.group(1))
    return ids


def clean_caption(caption):
    text = re.sub(r"(?<!\w)#\w+", "", caption)          # hashtags, including #lemijournal
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in text.splitlines()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def shorten(text, limit):
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…"


def to_article(post):
    # The caption's first sentence becomes the title; everything after it is the article.
    caption = clean_caption(post.get("caption") or "")
    # Captions often end a sentence with an emoji instead of a full stop, so emoji count as a break too.
    head, _, tail = caption.partition("\n")
    sentence = re.match(r"(.+?(?:[.!?]|\s[\u2600-\u27BF\U0001F300-\U0001FAFF\uFE0F]+))\s+(.+)", head)
    first, more = (sentence.group(1), sentence.group(2)) if sentence else (head, "")
    first = re.sub(r"[\s\u2600-\u27BF\U0001F300-\U0001FAFF\uFE0F]+$", "", first)
    title = shorten(first, 80) or "From the salon"
    rest = (more + "\n" + tail).strip()
    lede = " ".join(rest.split("\n\n")[0].split())
    summary = shorten(lede, 180) if rest else title
    if rest and summary == lede:  # the summary already shows the first paragraph, so don't repeat it below
        rest = rest.split("\n\n", 1)[1].strip() if "\n\n" in rest else ""
    day = datetime.datetime.fromisoformat(post["timestamp"].replace("+0000", "+00:00")).astimezone(NEW_YORK).date()
    slug_words = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50].strip("-") or "post"
    return {
        "slug": f"{day.isoformat()}-ig-{slug_words}",
        "title": title,
        "date": day.isoformat(),
        "summary": summary,
        "body": rest,
        "image_url": post.get("thumbnail_url") if post.get("media_type") == "VIDEO" else post.get("media_url"),
        "permalink": post.get("permalink", ""),
        "id": post["id"],
    }


def save_image(url, name):
    os.makedirs(IMG_DIR, exist_ok=True)
    dest = os.path.join(IMG_DIR, name)
    if url.startswith("http"):
        with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
    else:  # local file, used by --sample
        shutil.copyfile(os.path.join(ROOT, url), dest)
    return f"assets/img/journal/{name}"


def write_article(a):
    image_lines = ""
    if a["image_url"]:
        image = save_image(a["image_url"], f"ig-{a['id']}.jpg")
        image_lines = f"image: {image}\nimage_alt: Photo from LEMI Office on Instagram\n"
    one_line = lambda s: " ".join(s.split())
    text = (
        "---\n"
        f"title: {one_line(a['title'])}\n"
        f"date: {a['date']}\n"
        "category: From Instagram\n"
        f"summary: {one_line(a['summary'])}\n"
        f"{image_lines}"
        f"instagram: {a['permalink']}\n"
        f"instagram_id: {a['id']}\n"
        "---\n"
        f"{a['body']}\n"
    )
    os.makedirs(POSTS_DIR, exist_ok=True)
    path = os.path.join(POSTS_DIR, f"{a['slug']}.md")
    n = 2
    while os.path.exists(path):  # two posts with the same opening line on the same day
        path = os.path.join(POSTS_DIR, f"{a['slug']}-{n}.md")
        n += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", help="read posts from this JSON file instead of Instagram")
    parser.add_argument("--dry-run", action="store_true", help="show what would be added, change nothing")
    args = parser.parse_args()

    if args.sample:
        posts = json.load(open(args.sample, encoding="utf-8"))["data"]
    else:
        token = os.environ.get("INSTAGRAM_TOKEN")
        if not token:
            sys.exit("INSTAGRAM_TOKEN is not set.")
        posts = recent_posts(token)

    done = imported_ids()
    new = [p for p in posts if TAG.search(p.get("caption") or "") and p["id"] not in done]
    if not new:
        print("No new #lemijournal posts.")
        return
    for post in reversed(new):  # oldest first
        article = to_article(post)
        if args.dry_run:
            print(f"Would add: {article['date']}  {article['title']}")
        else:
            print(f"Added {os.path.relpath(write_article(article), ROOT)}", flush=True)
    if not args.dry_run:
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_journal.py")], check=True)


if __name__ == "__main__":
    main()
