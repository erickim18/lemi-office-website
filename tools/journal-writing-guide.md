# Lemi Journal: weekly writing guide

Instructions for the weekly writer. Each week, write **two short articles** about
current hair and beauty trends for the Lemi Journal, then open a pull request for
review. Never merge it yourself: a person approves every article before it goes live.

## Who we are

LEMI Office is a private boutique hair salon at 160 Madison Ave, Suite 12, New York,
founded by Lena Yeo. Services: haircuts, Korean digital and cold perms, color,
scalp-focused Korean head spa, make-up, and wedding hair and make-up. Read the menu
pages (hair.html, head-spa.html, make-up.html, wedding.html) before writing; they are
the only source for what LEMI offers and what it costs.

Readers are current and future clients in New York: style-conscious, busy, and
interested in Korean techniques. They want to know what is trending and whether it
would suit them.

## Voice

- Calm, warm, precise. Write like an experienced stylist talking to a client in the chair.
- No hype, no exclamation marks, no emoji, no "you won't believe".
- Sentence-case headings. American spelling. Spell it "make-up" and "LEMI".
- Short paragraphs. Plain words over jargon; explain a technique in one line when you name it.

## What to write each week

1. Research what is trending in hair and beauty **this season**, using at least two
   reputable, recent sources (for example Vogue, Allure, Harper's Bazaar, Byrdie, Elle,
   or Korean beauty publications). Prefer trends from the last few months.
2. Pick two different trends. Skip any topic already covered in `content/journal/`
   in the last eight weeks (check titles and dates).
3. Where it fits naturally, connect the trend to something LEMI does, and link to the
   right page with a relative link, e.g. `[our perm menu](hair.html)`. Don't force it.
4. Each article: **300 to 550 words**, an opening paragraph, two to four `##` sections,
   and an optional short list. End with a single practical line (who it suits, how to
   ask for it, or how to keep it looking good).

## Accuracy rules

- No medical or health claims: nothing about curing hair loss, regrowing hair,
  treating scalp conditions, or "detoxing" the body.
- No made-up facts, statistics, quotes, clients, or celebrity endorsements.
- Only mention LEMI services that appear on the menu pages. Only quote prices copied
  exactly from those pages, or leave prices out.
- Write in your own words. Do not copy sentences from sources. When a specific claim
  comes from a source, link to it inline.
- If you are unsure a statement is true, leave it out.

## File format

Save each article as `content/journal/YYYY-MM-DD-short-title.md`, using today's date
and a short lowercase hyphenated title:

```
---
title: Headline in sentence case, under 70 characters
date: YYYY-MM-DD
category: one of Hair trends, Color, Perms, Scalp care, Make-up, Bridal
summary: One or two sentences, under 180 characters, for the Journal list.
---
Article body in Markdown: paragraphs, ## and ### headings, - lists,
**bold**, *italic*, [links](https://example.com).
```

Do not use the category "From Instagram"; it is reserved for Lena's posts.

## Before opening the pull request

1. Run `python3 tools/build_journal.py`. It must finish with "Built the Journal".
2. Commit the two new `.md` files and everything the build changed
   (`journal.html`, `journal/`, `sitemap.xml`).
3. Open a pull request titled `Journal: 2 new articles for <date>`. In the description,
   list each article's title and summary, and the sources you used for each.
