# Writing a blog post

One post is one Markdown file in `src/blog/posts/<slug>.md`. Run `python3 build.py` and the post appears on the
listing, its category and tag pages, in search, the RSS feed and the sitemap.

## Front matter

Start the file with this block (between the two `---` lines):

```
---
title: "What makes a file print-ready? A practical guide"
slug: what-makes-a-file-print-ready
excerpt: "One or two sentences for cards and search results. Max 160 characters."
category: print-prep
tags: [printing, design, tips]
author: daniel-okafor
date: 2026-09-30
updated: 2026-10-05
featured: false
thumbnail: what-makes-a-file-print-ready.webp
thumbnail_alt: "A white T-shirt on a soft orange background"
summary:
  - "Three to five short takeaways, written by us."
  - "Each one a single, plain sentence."
  - "They appear in the Key takeaways box."
seo_title: "Optional: a different <title> for search engines"
seo_description: "Optional: a different meta description"
---
```

Rules the build checks (it stops with a clear message if one is broken):
- `category` must be a slug in `src/blog/categories.json`; every tag a slug in `src/blog/tags.json`;
  `author` a slug in `src/blog/authors.json`. Add new ones there first.
- `slug` is unique; `excerpt` is 160 characters or fewer; `thumbnail_alt` is always filled in.
- `date` and `updated` are `YYYY-MM-DD`. `updated` is optional. `featured: true` puts the post in the featured row
  (the newest one or two featured posts are shown).

## Thumbnail

- Put the image in `src/assets/blog/`. Use **16:10**, ideally 1600 x 1000 pixels (the build warns if the ratio is
  different, and the image then shows at its own ratio; it is never cropped).
- The build makes 640, 960 and 1440 pixel wide WebP versions automatically.
- `thumbnail_alt` describes the image for people who cannot see it. Keep it short and literal.

## The summary

`summary` holds 3 to 5 bullets: the key points a busy reader should take away. Write them yourself, in plain
sentences. They are part of the page from the start (good for search engines and screen readers); the "Summarize this
article" button only reveals them with a short animation. Never call them AI-generated.

## Writing the body

Plain Markdown. Use `##` for sections and `###` for sub-sections: they build the "On this page" contents list and get
copy-link anchors. Keep paragraphs short; the page is set for comfortable reading.

- **Tables**: normal Markdown tables. They scroll sideways on phones.
- **Callouts**: a quote that starts with a type, like this:

  ```
  > [!NOTE]
  > The thing customers do not know: ...
  ```

  Types: `NOTE`, `TIP`, `WARNING`.
- **Quotes** (for a merchant or a pull quote): a normal `>` quote; put the name on its own line in bold.
- **Images with a caption**: `![What the image shows](path/to/image.webp "The caption")`.
- **Checklists**: `- [x] Done item` and `- [ ] Open item`.
- No em dashes (use a comma or a full stop), no exclamation marks, sentence case for headings.

## Preview

Run `python3 build.py`, then `python3 -m http.server -d site` and open
http://localhost:8000/resources/blog/ (search needs the local server; opening the files directly works for the rest).
