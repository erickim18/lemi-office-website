# LEMI Office website

Static site for www.lemioffice.com, hosted on Netlify. Every change merged into
`main` goes live automatically.

## Lemi Journal

- **Articles** live in `content/journal/` as Markdown files (format at the top of
  `tools/build_journal.py`). After adding, editing or deleting one, run
  `python3 tools/build_journal.py` to regenerate `journal.html`, `journal/` and
  `sitemap.xml`. Never edit those generated files by hand.
- **Weekly articles** are drafted by a scheduled Claude routine that follows
  `tools/journal-writing-guide.md` and opens a pull request. Netlify adds a preview
  link to the pull request; merging it publishes the articles.
- **Instagram posts** tagged `#lemijournal` on @lemioffice are added every 3 hours by
  `.github/workflows/instagram.yml`, which runs `tools/import_instagram.py`. It needs
  the `INSTAGRAM_TOKEN` repository secret.

`_redirects` keeps `content/`, `tools/`, `.github/` and this file off the public site.
