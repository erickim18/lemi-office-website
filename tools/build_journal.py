#!/usr/bin/env python3
"""Build the Lemi Journal.

Reads articles from content/journal/*.md and writes:
  journal.html          the Journal index
  journal/<slug>.html   one page per article
  sitemap.xml           every site page plus every article

Header, menu and footer are copied from about.html, so menu changes on the
main pages carry over to the Journal the next time this runs.

Run from anywhere:  python3 tools/build_journal.py

Article format (content/journal/2026-10-12-some-title.md):

  ---
  title: The headline
  date: 2026-10-12
  category: Hair trends
  summary: One or two sentences shown on the Journal index.
  image: assets/img/journal/photo.jpg      (optional)
  image_alt: Describe the photo             (optional)
  instagram: https://www.instagram.com/p/…  (optional, for Instagram posts)
  ---
  Body in simple Markdown: paragraphs, ## and ### headings, - lists,
  > quotes, **bold**, *italic*, [links](https://…).
"""
import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "content", "journal")
OUT_DIR = os.path.join(ROOT, "journal")
SITE = "https://www.lemioffice.com"
BOOK = "https://lemioffice.glossgenius.com/book"
ARROW = '<svg viewBox="0 0 24 10" aria-hidden="true"><path d="M0 5h23M19 1l4 4-4 4" fill="none" stroke="currentColor"/></svg>'
PAGES = ["", "about.html", "team.html", "hair.html", "head-spa.html", "make-up.html", "wedding.html", "journal.html"]
REQUIRED = ("title", "date", "category", "summary")


# ---------- Reading articles ----------

def read_post(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        sys.exit(f"{path}: missing the --- header block")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    missing = [k for k in REQUIRED if not meta.get(k)]
    if missing:
        sys.exit(f"{path}: missing {', '.join(missing)}")
    meta["day"] = datetime.date.fromisoformat(meta["date"])
    meta["slug"] = os.path.splitext(os.path.basename(path))[0]
    meta["body"] = m.group(2)
    return meta


def load_posts():
    if not os.path.isdir(POSTS_DIR):
        return []
    posts = [read_post(os.path.join(POSTS_DIR, f)) for f in os.listdir(POSTS_DIR) if f.endswith(".md")]
    return sorted(posts, key=lambda p: (p["day"], p["slug"]), reverse=True)


# ---------- Markdown (the small subset articles use) ----------

def inline(text):
    text = html.escape(text, quote=False)

    def link(m):
        label, url = m.group(1), html.escape(m.group(2))
        if url.startswith("http"):
            return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        return f'<a href="{url}">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", text)
    return text


def markdown(src):
    out = []
    for block in re.split(r"\n\s*\n", src.strip()):
        lines = [l.rstrip() for l in block.strip().splitlines()]
        if not lines:
            continue
        first = lines[0]
        if first.startswith("### "):
            out.append(f"<h3>{inline(first[4:])}</h3>")
        elif first.startswith("## "):
            out.append(f"<h2>{inline(first[3:])}</h2>")
        elif all(l.startswith("- ") for l in lines):
            items = "".join(f"<li>{inline(l[2:])}</li>" for l in lines)
            out.append(f"<ul>{items}</ul>")
        elif all(l.startswith(">") for l in lines):
            quote = " ".join(l.lstrip("> ") for l in lines)
            out.append(f"<blockquote><p>{inline(quote)}</p></blockquote>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out)


# ---------- Page shell ----------

def nice_date(day):
    return day.strftime("%b %-d, %Y")


def shell(title, description, canonical, main, image=None, og_type="website", ld=None, depth=0):
    page = open(os.path.join(ROOT, "about.html"), encoding="utf-8").read()
    t, d = html.escape(title), html.escape(description)
    page = re.sub(r"<title>.*?</title>", f"<title>{t}</title>", page, count=1, flags=re.S)
    page = re.sub(r'(<meta name="description" content=")[^"]*', rf"\g<1>{d}", page, count=1)
    page = re.sub(r'(<meta property="og:title" content=")[^"]*', rf"\g<1>{t}", page, count=1)
    page = re.sub(r'(<meta property="og:description" content=")[^"]*', rf"\g<1>{d}", page, count=1)
    page = re.sub(r'(<meta property="og:type" content=")[^"]*', rf"\g<1>{og_type}", page, count=1)
    page = re.sub(r'(<link rel="canonical" href=")[^"]*', rf"\g<1>{canonical}", page, count=1)
    if image:
        page = re.sub(r'(<meta property="og:image" content=")[^"]*', rf"\g<1>{SITE}/{image}", page, count=1)
    if ld:
        page = re.sub(r'<script type="application/ld\+json">.*?</script>',
                      lambda _: f'<script type="application/ld+json">{json.dumps(ld)}</script>', page, count=1, flags=re.S)
    page = page.replace(' aria-current="page"', "")
    page = page.replace('<a href="journal.html">Journal</a>', '<a href="journal.html" aria-current="page">Journal</a>', 1)
    page = page.replace('<a href="journal.html" style="--i:6">', '<a href="journal.html" aria-current="page" style="--i:6">', 1)
    start, end = page.index('<main id="main">'), page.index("</main>")
    page = page[:start] + '<main id="main">\n' + main + "\n" + page[end:]
    if depth:
        # Article pages live one folder down, so local links need a "../" in front.
        prefix = "../" * depth
        page = re.sub(r'((?:href|src)=")(?!https?:|mailto:|tel:|sms:|#|data:|/|\.\./)',
                      rf"\g<1>{prefix}", page)
    return page


def card(p, base=""):
    summary = "" if p["summary"] == p["title"] else f'<span class="jpost__d">{html.escape(p["summary"])}</span>'
    pic = ""
    if p.get("image"):
        pic = (f'<span class="jpost__pic"><img src="{base}{html.escape(p["image"])}" alt="" '
               f'width="600" height="750" loading=lazy decoding="async"></span>')
    return f'''<a class="jpost{' jpost--pic' if pic else ''}" href="{base}journal/{p["slug"]}.html" data-r>
  <span class="jpost__meta"><time datetime="{p["date"]}">{nice_date(p["day"])}</time><span>{html.escape(p["category"])}</span></span>
  <span class="jpost__main"><span class="jpost__t">{html.escape(p["title"])}</span>{summary}</span>
  {pic}<span class="jpost__a">{ARROW}</span>
</a>'''


CTA = f'''<section class="cta light">
  <div class="wrap">
    <p class="eyebrow" data-r>Appointments</p>
    <h2 class="h2" data-r style="--d:1">Find your own <em>unique light.</em></h2>
    <div data-r style="--d:2"><a class="btn btn--solid" href="{BOOK}" target="_blank" rel="noopener">Book an appointment</a></div>
  </div>
</section>'''


def index_page(posts):
    if posts:
        items = "\n".join(card(p) for p in posts)
    else:
        items = '<p class="jempty">The first stories are on their way.</p>'
    main = f'''<section class="phead">
  <div class="wrap grid">
    <div class="phead__t">
      <p class="eyebrow" data-r>LEMI Office</p>
      <h1 class="display"><span class="ln"><span style="--i:0">Lemi</span></span><span class="ln"><span style="--i:1"><em>Journal</em></span></span></h1>
    </div>
    <div class="phead__d" data-r style="--d:3"><p>Notes on hair, scalp care and beauty from our chairs on Madison Avenue: the trends we are seeing, and what is new at LEMI.</p></div>
  </div>
</section>

<section class="journal">
  <div class="wrap"><div class="jlist">
{items}
  </div></div>
</section>

{CTA}'''
    return shell("Lemi Journal | Hair & Beauty Notes from LEMI Office, New York",
                 "Hair, scalp care and beauty trends from LEMI Office, a private boutique hair salon on Madison Avenue, New York.",
                 f"{SITE}/journal.html", main)


def post_page(p, posts):
    lede = "" if p["summary"] == p["title"] else f'<p class="post__lede" data-r style="--d:2">{html.escape(p["summary"])}</p>'
    figure = ""
    if p.get("image"):
        alt = html.escape(p.get("image_alt", ""))
        figure = f'<figure class="wrap post__fig" data-r><img src="{html.escape(p["image"])}" alt="{alt}" decoding="async"></figure>'
    ig = ""
    if p.get("instagram"):
        ig = (f'<p class="post__ig"><a class="more" href="{html.escape(p["instagram"])}" target="_blank" '
              f'rel="noopener">View on Instagram{ARROW}</a></p>')
    others = [o for o in posts if o["slug"] != p["slug"]][:2]
    more = ""
    if others:
        more = f'''<section class="sec sec--ivory post__more">
  <div class="wrap">
    <div class="idx-head" data-r><p class="eyebrow">More from the Journal</p><a class="more" href="journal.html">All stories{ARROW}</a></div>
    <div class="jlist">
{chr(10).join(card(o) for o in others)}
    </div>
  </div>
</section>'''
    main = f'''<article class="post">
  <header class="wrap post__head">
    <p class="eyebrow" data-r><a class="tlink" href="journal.html">Lemi Journal</a>&ensp;·&ensp;{html.escape(p["category"])}&ensp;·&ensp;<time datetime="{p["date"]}">{nice_date(p["day"])}</time></p>
    <h1 class="post__h" data-r style="--d:1">{html.escape(p["title"])}</h1>
    {lede}
  </header>
  {figure}
  <div class="wrap post__wrap"><div class="post__body" data-r>
{markdown(p["body"])}
{ig}
  </div></div>
</article>

{more}

{CTA}'''
    canonical = f"{SITE}/journal/{p['slug']}.html"
    ld = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "description": p["summary"],
        "datePublished": p["date"], "url": canonical,
        "author": {"@type": "Organization", "name": "LEMI Office", "url": SITE},
        "publisher": {"@type": "Organization", "name": "LEMI Office", "url": SITE},
    }
    if p.get("image"):
        ld["image"] = f"{SITE}/{p['image']}"
    page = shell(f"{p['title']} | Lemi Journal", p["summary"], canonical, main,
                 image=p.get("image"), og_type="article", ld=ld, depth=1)
    # Links inside the "More" cards and back links point at the site root; fix them for this folder.
    return page.replace('href="../journal/', 'href="')


def sitemap(posts):
    urls = [f"{SITE}/{p}" for p in PAGES] + [f"{SITE}/journal/{p['slug']}.html" for p in posts]
    rows = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    posts = load_posts()
    os.makedirs(OUT_DIR, exist_ok=True)
    keep = {f"{p['slug']}.html" for p in posts}
    for f in os.listdir(OUT_DIR):  # remove pages for articles that were deleted
        if f.endswith(".html") and f not in keep:
            os.remove(os.path.join(OUT_DIR, f))
    for p in posts:
        write(os.path.join(OUT_DIR, f"{p['slug']}.html"), post_page(p, posts))
    write(os.path.join(ROOT, "journal.html"), index_page(posts))
    write(os.path.join(ROOT, "sitemap.xml"), sitemap(posts))
    print(f"Built the Journal: {len(posts)} article(s).")


if __name__ == "__main__":
    main()
