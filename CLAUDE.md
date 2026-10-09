# InkyBay website — Claude Code guide

## Rules for working in this repo (read first, every session)

1. CLAUDE.md is the source of truth. Any change to tokens, components,
   section behaviour, page structure, URLs, build or deploy MUST update
   CLAUDE.md in the same commit. A change without its doc update is not done.
2. Before starting, check that CLAUDE.md matches the code for the area you
   are about to touch. If they disagree, tell me before changing anything.
3. Content lives in JSON (src/features/*.json, _index.json). Never hardcode
   copy in templates or CSS.
4. Shared look lives in src/template.html and src/feature.css. Never add
   page-specific CSS; extend the shared template for all pages instead.
5. Run python3 build.py and python3 scripts/audit.py on what you changed
   before every commit. Never commit a failing audit.
6. One logical change per commit, authored as me. Never force-push.
7. After every task, add one line to the "Change log" section at the
   bottom of CLAUDE.md: date, what changed, and any decision behind it.
8. If a decision of mine changes an earlier rule in this file, update or
   remove the old rule; never leave two rules that contradict each other.

The homepage is **designed and locked**. `src/template.html` (built to `site/index.html`) is the source of truth for look
and behaviour. When building the full site, extract tokens and components from it first, rebuild the homepage in the
chosen stack until it matches the build, and only then create new pages. Do not reinvent the look on page 2.

## Repo layout

```
site/                     build output, not in git (.gitignore); python3 build.py regenerates it, Actions deploys it
  index.html              the homepage, one self-contained file
  features/<slug>/index.html  one page per src/features/<slug>.json (clean URL: features/<slug>/)
  404.html                the interactive 404 (every link starts from SITE_BASE)
src/template.html         the homepage with {{TOKENS}} for buttons, brand SVGs and images
src/feature.css           styles for the shared feature-page template
src/features/<slug>.json  content for one feature page (the schema every feature page follows)
src/nav.json              every navbar mega menu: items, groups, promos, footer columns (see Mega menu)
src/industries/_index.json  the eight industries (slug, title, short, icon): single source for the mega menu,
                          the wheel's industry order and future industry pages
render_feature.py         renders a feature page: homepage head/nav/CTA/footer/JS + JSON content
render_industry.py        renders an industry page (same shell) from src/industries/<slug>.json
src/industry.css          styles for the shared industry-page template
src/industries/<slug>.json  content for one industry page (hero deck, products, stats, merchants, FAQs)
docs/industry-hero-spec.md  the industry hero ("customizing deck") spec
docs/claude-code-industry-pages.md  the prompt the industry pages were built from
src/assets/               logos/, products/, people/, photos/, brand/ (SVG), heroes/ (feature hero photos), hero-editor.webp, cta-products.webp
src/products.json         product library: {"<name>": {"label", "industry"}} for every src/assets/products/<name>.webp
build.py                  python3 build.py  ->  regenerates site/ (homepage, 404, feature and industry pages); SITE_BASE lives here
render_404.py             renders the 404 from src/404.json (styles in src/404.css)
render_partners.py        renders site/partners/ from src/partners.json (copy) + src/partners-directory.json (the list)
render_contact.py         renders site/contact/ from src/contact.json (styles in src/contact.css)
render_blog.py            the blog: content model, validation, thumbnails, every blog page, search index, RSS
src/blog/                 posts/<slug>.md, categories.json, tags.json, authors.json, blog.json (page copy)
src/assets/blog/          post thumbnails (16:10); scripts/make_blog_covers.py makes the demo covers
requirements.txt          build dependencies: Markdown 3.7 and Pillow 11.3 (the Pages workflow installs them)
src/forms.css             shared form styles (Partners, Contact, newsletter); the form JS is shared in the template
scripts/audit.py          checks feature JSON and the built pages in site/ (see the playbook below)
.github/workflows/pages.yml  builds site/ and deploys it to GitHub Pages on every push to main
```

## Build and deploy

- Local: `python3 build.py`, then preview with `python3 -m http.server -d site` (open http://localhost:8000/).
  Opening the files directly works for single pages, but folder links like `features/<slug>/` need a server.
- Live: https://aowshad.github.io/inkybay-website/ (feature pages at `features/<slug>/`). Every push to `main` runs
  `.github/workflows/pages.yml`: checkout, Python 3.12, `python3 build.py`, upload `site/` with
  `actions/upload-pages-artifact`, deploy with `actions/deploy-pages` (concurrency group `pages`).
- Repo Settings > Pages > Source must be **GitHub Actions** (not "Deploy from a branch"). There is no root
  `index.html` or `.nojekyll` any more; the deployed artifact is `site/` only.

## Product images

`src/assets/products/<name>.webp`: transparent, 600x600, WebP quality ~82, the product trimmed and centred so it fills
82% of the frame (so every product reads at the same size). Exception: `tee.webp` is 1000x1000, because it is shown large (the 404
editor, industry decks, How it works); it is still only ~24 KB. Keys are lowercase and hyphenated (`water-bottle`). Every
image has an entry in `src/products.json` with its `label` (shown on product-wall cards, e.g. "Mug") and its
`industry` (a slug from `src/industries/_index.json`); every product with an industry gets a card on the homepage wheel.
Never delete an image that something still references.

## Locked kit (do not add new values; extend the scale only if a real need appears)

**Layout**: 1440 frame, 1248 container, `--margin` 96 (fluid, 20 min), 12 columns, `--gutter` 32 (fluid).
**Rhythm**: `--section-y` 120 desktop / 80 phones (every section's top and bottom padding).
`--head-gap` 64 / 40 (section heading block to its content).
**Type**: Geist for headings only, Inter for everything else. **No monospace anywhere**, including chip and mini-UI text:
a font-name roll uses "Display", never "Mono".
Display 64/72 (`--t-display`), H2 56 (`--t-h2`, 1.17 line-height, -0.025em), lead 18/24, body 16/24.
**Floor**: paragraph text never below 16px; section sub headings are 18px.
**Colour**: brand `#F58220` / `#FF7500` / `#E5380F` / red `#D42427`, brand gradient, frame gradient,
`--tint #FFF7F0`, `--editor-blue #1C8CF0` (only for editor-selection visuals). Neutrals are tokens with dark overrides.
**Theme**: follows the device (`prefers-color-scheme`). There is no toggle. Industries and the CTA+footer zone are always dark.
**Radius**: 8 / 12 / 16 / 20. **Motion**: `--ease-expo` cubic-bezier(.16,1,.3,1) for everything; `--ease-inout` for the button roll.

## Components

- **Button** (`.btn--primary`, `.btn--secondary`): 44px, radius 12. Hover: label rolls up, arrow exits right and re-enters left (0.5s).
- **Navbar**: full width at top; on scroll becomes a glass pill. Sizes never change (68px, logo 48, CTA 44); only spacing and
  width shrink (940px). Insets are formula-based: logo 10px on left/top/bottom, CTA 12px. Dark mode has top and bottom hairlines.
  All parts move on one ease-in-out (`--ease-nav`, 0.9s) so expanding never bounces; it compacts past 60px and only expands at
  scrollY <= 4 (ignores trackpad overscroll). At <= 960px it is always the compact pill, as wide as the container.
- **Smooth scroll**: dependency-free wheel glide (lerp 0.085). Touch, keyboard, scrollbar, pinch-zoom, sideways swipes and
  reduced motion stay native; any outside scroll cancels the glide; in-page anchors glide and stop below the navbar.
  Wheel input over the open mobile sheet is left native so the sheet can scroll.
- **Image swaps** (features, why): the new frame fades in on top while the old stays fully opaque until covered. No scale, no blink.
- **Comet ring** (`.has-ring` + `.ring` + `.ring-glow > i`): 1px light with a short trail (~60deg), 8s per lap. The glow is a 3px
  masked stroke inside a wrapper that blurs it (7px) AFTER masking, so the halo is soft and centred on the line. Never mask after blurring.
  Used on the homepage hero editor, the rating card and the CTA card. Feature-page heroes use the showcase stage instead
  (the ring appears there only in the `{"type": "image"}` fallback). Content that should sit above the light gets `z-index: 4`.
- **Mini UI** (`.mui-stage > .mui`): em-based product snippets used as section visuals; scale with the host via container
  queries; one quiet loop each; animate only while on screen (`.mui-live`).
- **Heading reveal**: plain-text h2s are split into words by JS and rise out of a blur once on entering the viewport.

## Section order and behaviour

1. **Hero**: proof pill (star icon, 4.6, 169 reviews; "App Store" hidden under 480px), word-by-word headline landing, editor screenshot with comet ring.
2. **Logos**: marquee inside the container with edge fades; second set cloned by JS; pauses on hover.
3. **Features**: "customization" is always a selected layer; swatches auto-cycle every 2s and are clickable; ring is the active swatch's own box-shadow (always concentric). Left list auto-advances (7s progress line). Mobile heading: "Everything you need / for product / customization + swatches".
4. **Industries** (always dark, "Custom products for every business"): the wheel is built by build.py from
   `src/products.json`: one static card per product that has an `industry`, each product exactly once. Card: the product
   image and its `label` (one line, never wraps, also at 390px; cards 232px with 22px titles, 210px at 960px and below),
   linking to `industries/<that product's industry>/`. Order: round-robin over the industries in `_index.json` order, so
   two cards from the same industry are never neighbours (also across the loop's wrap; build.py checks this). An industry
   with no products gets no card and appears once products are added. Geometry adapts to the card count: the step is
   9.5deg (smaller once 9.5 x cards would pass 340deg), and the radius is computed at the card's bottom edge so
   neighbours never touch (32.8px gap; 20px on the flat phone track); a card hides only right at the loop's wrap, so
   nothing pops on screen. 1.6 deg/s; pause eases to a stop. Pause/play plus prev/next steps. Flat track on phones.
5. **Reveal**: in-flow statement; words sharpen with a 5-word soft edge as it passes through the viewport.
6. **Feature rail** ("Customize without limits"): pinned; vertical scroll drives the horizontal track 1:1; cards always 16:10, one full plus half the next; title one line, description reserves two lines, so every media box is identical; progress bar, no numbers. Native swipe rail under 960px.
7. **Case study** (tint band shared with Reviews): story card plus three stats that count up once. The "See full case study"
   underline draws left to right on hover (0.8s ease-in-out).
8. **Reviews**: infinite loop with clones, autoplay 5s driven by a JS clock (not CSS animationend; that skipped under load), dots only, drag/swipe, pauses on hover, keyboard focus, drag or offscreen. All cards equal height.
9. **How it works**: heading left, CTA right. Each step card has its own flat colour (01 Install #F5F2E8, 02 Embed #F5EAE1, 03 Product setup #E7F1F4, 04 Start selling #F0EEE5) with a matching darker stroke of equal contrast (#E2DABD, #E9D0BC, #C2DCE3, #DBD7C1; 1.25 each), the same in both themes. Hovered step widens (JS-controlled active state so crossing gaps never collapses the row). Scenes scale to the card, centred geometrically before scaling.
10. **Why InkyBay** (tint): image left, stacked cards right (each tucks 18px under the next); active card gets a glow stroke only (no scaling or widening); each frame has its own nature photo (`photos/why-1..4`) with a frosted-glass mini UI on top (identical in light and dark mode: its text tokens are fixed to the light values) that fills ~79% of the frame with an equal margin on all sides (`--pad: 6cqmin`); its main area (canvas, chart, file list) grows to fill; chart bars are white with the last one brand; the active side tab is solid brand with white text; progress hairline is aligned to the card's edges and centred in its bottom margin; click or 6s auto-advance.
11. **FAQ** (heading "FAQs", same 56px H2 as every section): sticky intro left, single-open accordion right; white cards, orange only on the open one.
12. **Crowd marquee** (dark zone, between CTA and footer): "Built for merchants [4 round faces] and shoppers [4 soft-square faces]",
   Geist 120px, 48s loop, edge fades, pauses on hover. Faces sit on colour chips (warm for merchants, cool for shoppers) with a
   dark stroke so stacked avatars separate; crops are centred on the detected head; the star separator has equal word-sized space each side; a hovered face lifts. JS repeats the set until it overfills, then duplicates it for a gap-free -50% loop.
13. **CTA + footer** (one dark zone): static product collage above the ring; footer wordmark from Figma with a cursor spotlight (auto sweep on touch).

## Rules that must survive the rebuild

- Every section uses `--section-y` and `--head-gap`; no ad-hoc paddings.
- Respect `prefers-reduced-motion` everywhere (autoplay off, reveals static, rings hidden).
- Autoplay pauses on hover, on keyboard focus (`:focus-visible` only, so a mouse click never freezes it) and when offscreen.
- Sliders and progress indicators never show numbers (screen-reader labels may).
- Sentence case for headings and titles.
- Check light and dark mode, and 360 / 390 / 768 / 1440 / 1920 widths; no horizontal overflow.

## Open items (not blocking the lock)

- Draft content to replace: case study quote and store, five reviews marked "Draft review", FAQ answers (verify feature claims).
- Social links are text; drop in official icons from each platform's brand kit.
- Live chat links carry `data-action="live-chat"`; hook the chat widget to them when it is chosen.
- Stats (10,000+ merchants, 50,000+ products daily, 169 reviews) and the 4.6 rating must match the live App Store listing.
- There is no pricing page or section yet: the navbar's "Pricing" (`#pricing`) and the 404's "Pricing" link go nowhere.
- Fonts load from Google Fonts in the build; self-host Geist and Inter in production.

## Suggested next steps

1. Pick the stack (Next.js + CSS modules or Tailwind with these tokens as theme values).
2. Port tokens, then Button, Navbar, Ring, Mini UI, heading reveal.
3. Rebuild the homepage section by section and diff it visually against `site/index.html`.
4. Start the inner pages (Features, Industries, Pricing, Resources) with the same kit.


## Mega menu

One data-driven component. `src/nav.json` lists every menu (`{"menus": [...]}`) in navbar order; build.py renders the
desktop triggers (`{{NAV_TRIGGERS}}`), the panels (`{{MEGA_PANELS}}`) and the mobile sheet sub-lists (`{{SHEET_MENUS}}`)
into the shared template. Never hand-write a menu in the template.
- Menu: `{"id", "label", "layout": "grid" | "groups", "base", "promo", ...}`. A grid takes its items from
  `items_from` (an index file such as `src/features/_index.json`) or `items`; groups take `groups: [{"title", "items"}]`.
- Item: `{"slug" or "href", "title", "short", "icon", "external": bool}` (+ optional `"action"` for a `data-action`
  hook). `slug` links to `<base><slug>/`. External links open in a new tab (`rel="noopener"`) with a small arrow-out icon.
- Promo: `{"title", "text", "cta", "href", "image"}` (an `src/assets/` WebP, fading into the card; optional
  `"position"` sets its `object-position` when the subject is not centred in the 16:10 crop) or `"visual": "video"`.
- Footer: a menu's `"footer"` list renders its footer columns (`{{FOOT_COLS:<id>}}` in the template):
  `{"title", "groups"?, "limit"?, "more"?, "extra"?}`. Footer link copy comes from the same data as the menus.
- Menus: Features (grid, `src/features/_index.json`, base `features/`); Industries (grid, `src/industries/_index.json`,
  base `industries/`, promo `cta-products.webp` anchored to the top, footer: first five plus "All industries").
  Industry pages come later, so `industries/...` links 404 until they exist.
  Resources (groups: Learn, Grow with InkyBay, Get help; internal pages `resources/blog/`, `resources/case-studies/`,
  `resources/video-tutorials/`, `partners/`, `affiliate/` come later; Help center is external to docs.inkybay.com;
  promo is the video visual; footer: "Resources" = Learn + Grow, "Get help" = the Get help group: Help center, Live chat,
  Contact). Contact ("Write to our team.", icon mail) links to `contact/`.
- Groups layout: one column per group (`.mega__groups`, `grid-auto-columns: minmax(0, 1fr)`), each with a 14px muted
  title and a vertical list of items. Columns share the width evenly, so adding an item or a group needs no CSS change.
- Video promo (`"visual": "video"`): `hero-editor.webp` as a full-bleed thumbnail (anchored to the top) under a light
  dark wash, with a centred brand play button; same card, fade and dark-mode treatment as the image promos.
- Live chat is `href="#"` with `data-action="live-chat"` (menu, sheet and footer) so the chat widget can hook in later.
- Mobile sheet: an accordion (opening one section closes the others). Section rows are 52px, 18px text, with hairlines
  between sections; every row, label and sub-item shares one 12px left edge. Sub-items are 48px touch targets: the
  item's icon in a 32px tile plus its title in full ink (not muted); group titles are 14px muted labels; the current
  page is tinted brand. The open sheet is capped to the viewport and scrolls inside itself.
- Behaviour (every menu): opens on click, not hover; one open at a time; clicking another trigger swaps panels instantly
  (no close-then-open fade); outside click and Esc close (Esc returns focus to the trigger); every trigger has
  `aria-expanded` and `aria-controls`. The current page's own item is highlighted (`aria-current`).
- Look: left, the label and items (icon, title, `short`). `short` is menu copy: 14px, two lines max, about 40 characters,
  written so it never truncates. Right: a 280px dark promo card (`#121010`) with its image fading into it and a CTA.
  In dark mode the card lifts off the panel: warm surface `#1E1714` with a soft orange glow at the top (radial,
  `rgba(255,117,0,.18)`) and a 1px `rgba(255,255,255,.08)` border drawn on `::after` so it stays visible over the
  full-bleed image. Light mode is unchanged. The Features promo image (`mega-promo.webp`) is a 720px-wide WebP
  (quality ~82) shown as a 16:10 `object-fit: cover` crop; its subject (app icon and cursor) is centred, so it uses the
  default `object-position`. Below 1360px the promo hides (it would squeeze the items); below 1100px the grid drops to
  two columns; on phones the menu sheet shows each menu as a collapsible list.
- Links are relative to the page's own folder, because the site is served under `/inkybay-website/` (never start an
  internal link with `/`; the only exception is the 404 page, whose links start from `SITE_BASE`, see "404 page"): every link is `<root><path>`, where `<root>` is `""` on the homepage and `../../` on a
  feature page (e.g. `../../features/<slug>/`). The homepage logo is `#`; feature pages link home with `../../`
  (logos and breadcrumb, via `{{HOME}}`).

## Feature pages (one template, nine pages)

Every feature page has the same sections in the same order; only the JSON changes. The nine features, their
descriptions and two-line taglines live in `src/features/_index.json` (data only, not built as a page).

| # | Section | JSON key | Background |
|---|---|---|---|
| 1 | Hero: breadcrumb, H1, lead, two buttons, proof pill, showcase visual (no comet ring) | `hero`, `hero.visual` | white |
| 2 | Benefits: 4 open columns, a hairline on top that fills with brand on hover | `benefits` | white |
| 3 | How it works: two-tone heading (the feature's tagline), 3 zig-zag rows with a hairline checklist | `details_heading`, `details` | dark |
| 4 | Quote (same dark band) | `quote` | dark |
| 5 | Capabilities: 8 cards (heading one tone on tint) | `capabilities_heading`, `capabilities` | tint |
| 6 | Works with: text left, vertical product wall right (3 columns, middle runs the other way) | `products_heading`, `products_lead`, `products` | white |
| 7 | FAQs | `faqs` | tint |
| 8 | CTA, crowd marquee, footer | from the homepage | dark |

**Hero showcase** (`hero.visual`): `{"layout": "showcase", "image": "<slug>", "ui": "<mini-ui>", "chips": [up to 2]}`
(a chip is a string or `{"label", "roll"}`, as in the zig-zag). The photo is `src/assets/heroes/<slug>.webp` (1200x1200,
transparent). It must look clearly different from the zig-zag:
- Square showcase (`.fshow`), sized in `cqw`/`em` so it scales down as one unit. A framed stage fills the top-left 88%:
  radius 24, warm dark base `#150E09` with a static orange/red gradient mesh and grain, inset 1px `rgba(255,255,255,.08)`.
  The stage stays dark in light and dark mode (like the mega promo and CTA card).
- The photo is centred on the stage at 70% of its width and floats (0 to -10px, 7s, alternate). Its shadow is
  `filter: drop-shadow()` on the image, so it follows the product; no ground shadow or ellipse.
- Exactly one key mini UI, 18em wide at the zig-zag's text size, hanging over the stage's bottom-right corner and
  the photo's lower-right edge. It enters once (fade + rise, `.is-shown` stays) and then stays still; its own loops run.
- Chip 1 (white) across the photo's left edge, chip 2 (brand) across the stage's right edge; they enter after the UI and
  bob like the zig-zag chips.
- No glow blobs, no stacked cards: those belong to the zig-zag only. Loops pause off screen (`.mui-live`);
  reduced motion shows the final state.
- No `hero.visual`, or `{"type": "image"}`: the old editor screenshot with the comet ring (`hero.visual_alt` is its alt).

 `["First line.", "Second line."]` renders the first line in ink and the second muted; the
heading reveal animates both lines word by word. The homepage uses the inline variant (`.h-line.h-inline`) on
Industries, Rail, Case study, How it works and CTA ("Custom products / for every business."). On dark sections the
muted part is rgba(255,255,255,.42). Reviews, Why InkyBay, FAQs and the Features heading stay single-tone.

**Two-tone rule**: two-tone headings only on white and dark backgrounds. On the orange tint the muted tone loses
contrast, so headings there render in one tone automatically (`.fsec--tint`, `.case`, `.reviews`, `.why`).

**Zig-zag visuals**: no box; a soft brand glow (orange, red, amber) drifts behind the UI. Small parts (chips, badges,
option tiles) live inside the anchor (the main card's box) so they always overlap its edges. They animate on their
own while on screen: staggered entrance, a gentle bob, a cycling size value, rotating active colour. No pointer effects.
- `{"layout": "single", "ui": "<mini-ui>", "chip": "text", "badge": "text"}`: one card, chip top-left, brand badge bottom-right
- `{"layout": "product", "image": "<products/name>", "chips": [{"label": "Size", "roll": ["S","M","L","XL"]}, "text"], "colors": ["#hex", ...]}`:
  product photo, cycling chip top-left, colour tiles on the right edge, chip bottom-left
- `{"layout": "stack", "back": "<mini-ui>", "front": "<mini-ui>", "badge": "text"}`: two overlapping cards, badge on the front card
A chip is a string or `{"label", "roll"}` (the value cycles).
Mini-UI names: setup, design, files, options, methods, inventory, quote, addons, tiers, library, templates, sides, grow.

**Product wall**: the section has no vertical padding; the 560px wall meets its top and bottom edges and fades into them. Any number of products. Cards are rendered into three columns; JS spreads them over the visible
columns (two on phones, so none are lost), repeats them until each column overfills, then duplicates for a
seamless loop. Hover pauses the wall.

To add a feature page: copy `src/features/advanced-product-setup.json`, take the title, description and tagline
from `_index.json`, write the rest, run `python3 build.py`. Do not add page-specific CSS; if a feature needs a new
section type, add it to the template for all pages.


## 404 page ("the 404 is a design project")

`site/404.html`, built by `render_404.py` from `src/404.json` (copy, products, print areas, swatches) with
`src/404.css`. GitHub Pages serves it for any missing URL at any depth, so its links cannot be relative: build.py's
`SITE_BASE` ("/inkybay-website/" now; `SITE_BASE=/ python3 build.py` on a custom domain) is the root of every link on
this page. Images are inlined, so nothing else depends on the depth. It has `noindex` and nothing links to it. It has
no CTA section (render_404.py removes it from the shared tail); the crowd marquee and footer stay.
- Left (5 cols): H1 on two lines, "404" (ink) over "Page not found" (muted), at display size; the lead and "Back to
  homepage". No status label and no helpful links (your call).
- Right (7 cols): a mini InkyBay editor (glass card, light in both themes): product tabs (T-shirt, Mug, Tote bag; the
  tote replaced the cap because its flat front holds text well) and Reset;
  a canvas with the product, a dashed print area and the "404" text layer (Geist 700), selected with an editor-blue box,
  four corner handles and a rotate handle; a toolbar with six swatches, Regular/Bold and a size readout.
- Drag moves the layer; a corner resizes it (aspect kept); the top handle rotates (snaps to 45deg steps); double-click
  or double-tap edits the text (max 8 characters; empty restores "404"); tabs switch product (the layer keeps its place
  in the print area, products crossfade). If any corner leaves the print area, the box turns red and an "Outside print
  area" chip shows. Keyboard on the canvas: arrows 4px (Shift 16px), +/- resize, R rotates 15deg, Esc deselects, Enter
  edits; changes are announced politely. A 2.5s first-visit hint (cursor drags and resizes the layer, "Drag, resize or
  recolor me") never runs again after an interaction (localStorage). Reduced motion: no hint, no crossfades.
  Phones: the editor stacks under the text, handles have 32px touch targets, the toolbar wraps to two rows.
- The audit serves site/ like GitHub Pages (missing paths return 404.html) and checks three depths (same links, all
  from SITE_BASE, existing targets return 200, no relative asset paths), dragging, resizing, the warning showing and
  clearing, and no overflow at 390px.

## Forms (shared)

Every form is `form.form[data-form][data-endpoint]` with `.field`s (label, control, `.field__err` with aria-live), a
`.form__hp` honeypot and a `.form__status`; styles in `src/forms.css`, one handler in the template. Selects use our own
chevron with room on the right; checkboxes are a custom 22px box with a check mark; submit buttons are primary
buttons with the arrow (`{{BTN_ARROWS}}` inside the `<button>`). `.form__row` puts two fields side by side, `.form__one`
keeps one field per row.
- Endpoints come from the build config in build.py: `FORM_ENDPOINT` (Partners, Contact) and `NEWSLETTER_ENDPOINT`
  (newsletter), e.g. a Formspree or Basin URL, set with `FORM_ENDPOINT=... python3 build.py` (and the same in the
  Pages workflow when chosen). Both are empty for now. The "Form not connected yet" note (`.form__note`) is hidden
  for now (your call); a submit without an endpoint still says so in the status line and never pretends to send. No
  service has been picked.
- Client-side validation with inline errors (required fields, email, `https://` website fields), on blur once a field
  was touched and on submit, with aria-invalid and focus on the first error; hidden or disabled fields are skipped; a
  filled honeypot is dropped quietly; the submit button shows a loading state; the result appears in place via fetch
  (no reload). A `template.form__done` after the form replaces it on success (`{name}` becomes the first name; "Send
  another message" brings the form back); otherwise the status line says it. On failure the input stays and the
  status offers `data-fail-email` as a mailto link.
- Every "Talk to our team" button (homepage, feature, industry and partners FAQs) links to `contact/`.

## Partners page

`site/partners/`, built by `render_partners.py` from `src/partners.json` (all copy) and `src/partners-directory.json`
(the list), styles in `src/partners.css` + `src/forms.css`. Reached from the Resources mega menu and the footer.
1. Hero [white]: breadcrumb Home > Resources > Partners, a one-line H1 "Grow with the InkyBay partner network" (display
   size, no second line), lead, "Become a partner" (to the form) and "Browse partners" (to the directory); visual: the
   first six partners' logo tiles orbiting an InkyBay tile (90s, upright, the core and chips float; static with
   reduced motion).
2. Directory [tint]: tabs All / App / Service / Theme / Others with live counts, a search on name and description,
   3-up cards (logo tile, name, type badge, 2-line description, "Learn more" external with new tab and noopener); a
   `featured` partner is listed first but looks like every other card. Every card lifts with a brand edge on hover or
   keyboard focus. The first 9, then "Show more partners"; an empty state with "Clear filters". Filtering fades and
   slides cards in.
3. Why partner [white]: four benefit columns (feature-page benefit style).
4. Partner with InkyBay [tint]: one section, one heading. Left (5 cols): the heading, lead, "How it works" in small
   type (Apply, We review, Get listed; numbered circles joined by a thread; no time promises) and a one-line trust note.
   Right (7 cols): the form card: name and email side by side, then company website, partner type and message each on
   their own row, consent, and "Send message" (a primary button with the arrow). See Forms.
5. FAQs [white]. 6. CTA, crowd marquee, footer.
(There is no "Who we partner with" section any more; your call.)
- Logos: `src/assets/partners/logo-NN.webp` (192px), set per partner with `"logo"`; without one a monogram tile shows.
- Demo and draft: all 12 partners are fictional demo entries (`"demo": true`, links to example.com) wearing the 13
  supplied partner logos assigned at random, so names and logos do not belong together yet;
  the benefits and FAQ answers are `"draft": true`. The consent checkbox's privacy policy link is `#` (no privacy page
  yet). The audit checks tabs, search, counts, "Show more", the empty state, blocked empty submits, external links and
  overflow at 390px.

## Contact page

`site/contact/`, built by `render_contact.py` from `src/contact.json` (topics, fields, channels, offices, FAQs; nothing
hardcoded), styles in `src/contact.css` + `src/forms.css`. "It should feel like talking to a person."
1. Hero + form [white]. Left: breadcrumb, two-tone H1 "Have questions? / Let's Talk" (capital T is your call; the rest of the site uses sentence case), lead, three channel
   rows (Email support with a copy button, "Copied" for 2s, and a mailto link; Live chat with
   `data-action="live-chat"`; Help center, external) and the response note. Right: the form card (white, radius 24,
   soft shadow, 1px line, glass edge).
   - Topic chips (a radio group, arrow keys move; none selected by default, all fields shown). Book a demo: shows "Best
     time to talk"; Setup help: its own placeholder; Billing: hides "I'm using"; Partnerships: the form gives way to a
     note and a button to `partners/#partner-form`; Something else: its own placeholder. Each topic sets the message
     placeholder and the hidden `topic` field (sent with the payload). Fields come and go with height + fade (0.35s);
     hidden fields are disabled so they are neither validated nor sent. The wrappers are `.cfx` (`.fx` is the homepage
     features heading).
   - Fields: Full name, Email address, Phone (optional, tel), Store URL (https:// inside the field), I'm using, Message
     (counter, 1000 max), consent (privacy link `#` until a privacy page exists), honeypot, "Send message"; posts to
     FORM_ENDPOINT (see Forms). Success replaces the form: a drawn check, "Thanks, <first name>. We got your message.",
     what happens next, "Send another message". Error keeps the input and offers support@inkybay.com.
2. Offices [dark]: two cards (US HQ, Bangladesh development office) with a dashed brand-gradient arc between them and a
   dot travelling it (8s loop, only on screen; static with reduced motion; vertical on phones). Each card: live local
   time (Intl.DateTimeFormat in the office's time zone, every 30s), an Open now / Closed badge from the JSON hours,
   the address (Google Maps search, new tab) and a tel: link. No embedded maps.
3. FAQs [white]. 4. CTA, crowd marquee, footer.
Phones: form first, then the channels; topic chips scroll sideways with snap; office cards stack.
- Draft (to confirm): the response note and the success "what happens next" (both promise replies within 2 hours
  during business hours), the business hours (Mon-Fri 09:00-18:00 local) and the FAQ answers. The audit checks every
  topic's placeholder and fields, blocked empty submits, the copy button, both clocks and badges, links and overflow.

## Blog

Built by `render_blog.py` (Python-Markdown for posts, Pillow for thumbnails; both pinned in `requirements.txt`), styles
in `src/blog.css`, behaviour in the shared template. Writers' guide: `docs/writing-a-blog-post.md`.
- URLs (relative links like every page): `resources/blog/` (+ `page/<n>/`), `resources/blog/category/<slug>/`
  (+ `page/<n>/`), `resources/blog/tag/<slug>/` (+ `page/<n>/`), `resources/blog/search/?q=` (client-side),
  `resources/blog/<post-slug>/`. Also `resources/blog/search-index.json`, `resources/blog/feed.xml` (RSS 2.0) and
  `sitemap.xml` for the whole site (every page but the 404 and search). `SITE_URL` in build.py makes the absolute URLs.
- A post is `src/blog/posts/<slug>.md`: front matter (title, slug, excerpt max 160, one category, tags, author, date,
  updated, featured, thumbnail, thumbnail_alt, summary 3-5 bullets, optional seo_title / seo_description) + Markdown.
  The build stops with a clear message on an unknown category, tag or author, a missing thumbnail_alt, a duplicate
  slug, an excerpt over 160 characters or a bad date. Reading time is words / 225, rounded up.
- Categories (`categories.json`: slug, name, description) and tags (`tags.json`: slug, name) must exist before a post
  uses them. Authors in `authors.json` (name, role, bio, optional avatar).
- Thumbnails: `src/assets/blog/`, 16:10 recommended (1600x1000); the build makes 640/960/1440 WebP versions with
  width/height and srcset, warns (does not fail) on another ratio, and never crops: every thumbnail renders at its own
  ratio (`height: auto`, no `object-fit: cover`); grid rows align to the top.
- Listing: two-tone hero with a search field ("/" focuses it), the newest one or two featured posts, "Latest
  articles" on tint with a sticky category bar (All + categories with counts, real links; as many as fit, the rest in a
  "More" popover with a filter box; on phones it scrolls with snap) and a layout switch (grid 2/3/4 or list, grid 3 by
  default, remembered in localStorage; hidden on phones, which show one column), 12 posts per page with numbered
  pagination (rel prev/next), then the newsletter (dark).
- Result pages (category, tag, search) share one layout: breadcrumb, label, H1, count, description (categories),
  a removable filter chip, "Related tags" on tags, the same grid and pagination. Search matches title, excerpt,
  category and tags (case- and accent-insensitive), highlights matches with <mark>, updates as you type (150ms) and
  keeps `?q=` in the URL; empty state with popular categories and "Clear search"; search pages are noindex.
- Article: a 2px reading progress bar (body only); breadcrumb, category pill, H1, meta (author, date, updated,
  reading time); the thumbnail at its own ratio (eager, fetchpriority high); "Key takeaways" (the bullets are in the
  HTML; the button reveals them with a 0.6s shimmer and a typing effect; reduced motion shows them at once; without JS
  they are simply shown; never labelled AI); body at 19px / 1.7 / 68ch with copy-link anchors on h2/h3, scrolling
  tables, callouts (`> [!NOTE]`), quotes, captioned images and checklists; tags, share links (copy, X, LinkedIn,
  Facebook, email; plain URLs, no third-party scripts), author box, "Keep reading" (same category first, then shared
  tags), previous / next. Desktop sidebar (sticky): "On this page" (h2 + h3, the section in view highlighted), then
  the newsletter and "Sell custom products with InkyBay" promos; it scrolls inside itself when taller than the screen.
  Tablet and phone: the contents become a disclosure above the body and the promos follow the article.
- SEO: unique title and description (seo_* overrides), canonical, Open Graph and Twitter tags (thumbnail as image),
  JSON-LD BlogPosting (articles), BreadcrumbList (all blog pages) and CollectionPage (listings); one H1 per page.
- Small text: pills, tags, share buttons and the filter chip are 16px links; dates, reading times and labels are 14px
  metadata in non-paragraph elements.
- Audit (`scripts/audit.py`, part of `--all`): thumbnails at their natural ratio, category/tag pills and pagination
  resolve, search finds "print" and shows the empty state for "zzzz", the layout switch changes the columns, the
  contents follow the section in view, the summary reveals the bullets, JSON-LD parses, no overflow at 390px.
- Endpoints: the newsletter forms post to `NEWSLETTER_ENDPOINT` (see Forms); empty for now, so they say "Not connected
  yet". Draft / demo: the 14 posts and both authors are demo content; the promo cards and newsletter copy are draft.

## Industry pages (one template)

Built by `render_industry.py` from `src/industries/<slug>.json` to `site/industries/<slug>/` for every industry in
`_index.json` that has a JSON file. Same shell as the feature pages. Sections, in order:

| # | Section | JSON key | Background |
|---|---|---|---|
| 1 | Hero: breadcrumb Home > Industries > title, H1, lead, two buttons, proof pill, the customizing deck | `hero` (`stage`) | white |
| 2 | Products: two-tone heading (one tone on tint), 4-up cards (image + name), CTA text + primary button | `products_heading`, `products`, `products_cta` | tint |
| 3 | Stats: heading + lead left, three stats right with hairlines; whole numbers count up (shared `.stat__num`), decimals static; hover sweeps a light across the digits | `stats_heading`, `stats_lead`, `stats` | white |
| 4 | Merchants: two cards per row (one on phones): store preview, name + country, quote, "Visit store"; the first `merchants_visible`, then "Show more stores" (shared `[data-show-more]` JS) | `merchants_heading`, `merchants`, `merchants_visible` | dark |
| 5 | Testimonials: the homepage reviews section, same markup and shared JS | from the homepage | tint |
| 6 | FAQs | `faqs` | white |
| 7 | CTA, crowd marquee, footer | from the homepage | dark |

Primary buttons with a link use `{{BTN_PRIMARY:label|href}}`.

**JSON schema** (`src/industries/<slug>.json`, the single source of copy for the page):
- `slug`, `nav_label`, `meta {title, description}`
- `hero {title, lead, primary_cta, secondary_cta, stage}`; `stage {actions: [3 x {label, icon}], swatches: [hex],
  deck: [3-5 x {product, label, swatch (index into swatches), chip}]}`
- `products_heading` (2 lines), `products: [{name, image}]`, `products_cta {text, label, href}`
- `stats_heading` (2 lines), `stats_lead`, `stats: [3 x {value, suffix, label}]` (a value with a "." stays static)
- `merchants_heading` (2 lines), `merchants: [{name, country, quote, preview, url}]`, `merchants_visible`
- `faqs: [3-5 x {q, a}]` (answers max 200 chars); optional `needs_images` (what is missing; stand-ins are used)
Every `product`, `image` and `preview` is a key in `src/products.json`.

**Products**: cards show the product image and name only (no tags); the CTA under them links to the demo store.
**Merchants**: store preview window, store name and country, quote, "Visit store"; no avatar, no category. Two per row
(one on phones); the rest behind "Show more stores". Store names marked "Store name (draft)" and the `#demo-store` link
are placeholders until real ones are supplied.

**Industry hero: the customizing deck** (`docs/industry-hero-spec.md`, data in `hero.stage`): 3-5 product cards
(4:5, radius 24, white in both themes) stacked so each back card is 14px higher and 4% narrower; back cards show only
their top edge (no label, no progress line) and that edge is the button that brings the card forward. The front card
shows its label top-left, a large product photo (its box 96% of the card width, allowed to dip over the palette) and its
`chip`, static. The editor panel (right) and palette (bottom-left) are frosted glass, light in both themes (more opaque
on a dark page), and never move. The only animated customization is colour (no text step, no option step): each front
card's story runs 3.0s: the cursor glides to the card's swatch and clicks it, the product tints (a multiply overlay
masked by the image's own alpha, opacity .35), then the deck rotates (0.6s): the front card lifts 12px, tilts back,
blurs to 10px and fades while it moves to the back (each half of that animation eases on its own so it stays visible),
and the next card sharpens forward (back cards carry a slight 0.3px-per-step blur). Runs only while on screen (the
shared `.mui-live` observer) and pauses on hover or focus. Tabs (buttons, "Show <label>"), arrow keys and swipe change
cards; the deck is an `aria-roledescription="carousel"` with a polite live region. Phones: two back tabs, one palette
row. Reduced motion and no JS: no cursor, blur or rotation; the first card is shown coloured and tabs switch instantly.
The audit checks the JSON, that the panel, palette and chip overlap the front card, that the deck advances on its own
and that every visible tab brings its card to the front.

## Writing a feature page (playbook)

All nine feature pages are built from `src/features/<slug>.json`. For a new feature, add it to `_index.json`, copy an
existing page's JSON and rewrite it against these rules.

**Source of truth**: title, description and tagline come from `src/features/_index.json`. The hero lead is the
description; `details_heading` is the tagline, word for word. Never invent numbers, integrations or claims that the
description (or https://docs.inkybay.com) does not support.

**Voice**: plain, confident, short. Sentence case for every heading and title. No em dashes (use a comma or a full
stop). No exclamation marks. Write for a Shopify merchant, not a developer.

**Lengths** (enforced by `scripts/audit.py`):
| Field | Rule |
|---|---|
| `hero.lead` | max 260 chars |
| `benefits` | exactly 4; title max 3-4 words; text max 70 chars |
| `details` | exactly 3; title max 40 chars; text max 180 chars; exactly 3 `points`, each max 32 chars |
| `details[].visual` | use each layout once: `single`, `product`, `stack` |
| `capabilities` | exactly 8; title max 24 chars; text max 45 chars; heading lines max 36 chars |
| `products` | 6-14 names from `src/products.json`; heading lines max 24 chars (half-width column) |
| `faqs` | 3-5; answer max 200 chars |
| `_index.json short` | about 40 chars; must fit two lines in the mega menu |

**Visuals**: pick mini UIs that show the feature itself (quotes: `quote`; library: `library`; inventory: `inventory`;
discounts: `tiers`; pricing: `addons`; printing: `methods`; templates: `templates`; options: `options`). Chips and
badges are short labels a real UI would show ("Tier unlocked", "Quote sent"); a rolling chip cycles through 4 values. Chip text
follows the docs wording, in the hero and the zig-zag alike: inventory at its stop-sell threshold is "Unavailable"
(not "Auto-paused").

**Checks before every commit**:
```
python3 build.py
python3 scripts/audit.py <slug>        # must print PASS (use --all for every page and the homepage)
```
The audit checks the JSON rules above, then opens the built page at 390, 768 and 1440px in light and dark mode:
no JS errors, no horizontal overflow, no text under 16px, every heading reveals, every chip and badge overlaps its
card's edge, the product wall shows every product, no two-tone heading line wraps at 1440px, no mega-menu
description is cut off, and (for a hero showcase) the photo loads and the hero UI and chips overlap the photo's or the
stage's edge at every width and mode. On every page it also opens each mega menu from `nav.json` at 1366 and 1440px:
exactly one open at a time (switching directly), `aria-expanded`/`aria-controls` set, no description cut off, every
promo image loads, Esc and an outside click close it; and at 390px every menu's sheet sub-list opens fully with the
same number of links as `nav.json`. Setup once: `python3 -m pip install --user playwright && python3 -m playwright install chromium`.

**Commits**: one commit per page, e.g. `Add feature page: Custom quote requests`. Never batch pages together.


## Change log

Newest first. One line per commit: date, what changed, and any decision behind it.

- 2026-10-09: Contact heading is now "Have questions? / Let's Talk" (your wording)
- 2026-10-09: 404 simplified (your changes): heading "404 / Page not found", no "Status 404" label, no helpful links, no CTA section; the cap becomes a tote bag (flat front, print area 31-69% across, 48-84% down) so the text sits balanced
- 2026-10-09: Partners and forms polish (your changes): one-line hero heading; "Who we partner with" removed; How it works and the form merged into one "Partner with InkyBay" section (steps small on the left, form card on the right; name + email in one row, website, type and message each on their own row); every partner card has the same hover lift instead of the first one looking permanently hovered; shared form fixes on every form: a proper select chevron, a custom checkbox, the primary arrow on submit buttons, and the "Form not connected yet" note hidden
- 2026-10-08: Blog links, audit and docs: audit check_blog (thumbnail ratios, pill/tag/pagination links, search results and empty state, layout switch, contents highlight, summary reveal, JSON-LD, overflow at 390px) and four blog pages in --all; docs/writing-a-blog-post.md for writers. The Resources mega menu and footer already point to resources/blog/
- 2026-10-08: Blog demo content: four categories (Print prep, Pricing and operations, Shopify and growth, InkyBay product), eight tags, two demo authors, 14 demo posts (302 to 702 words; two featured) including the flagship "What makes a file print-ready? A practical guide" with the resolution table, colour section, callout, merchant quote, lists, checklist and FAQ; 16:10 covers (soft brand gradient + one product, no text) made by scripts/make_blog_covers.py. Figma frames were not readable, so titles are our own
- 2026-10-08: Blog content model and build (render_blog.py: front matter, validation, Python-Markdown, reading time, contents, responsive thumbnails, listing / category / tag / search / article pages, SEO tags and JSON-LD, search-index.json, feed.xml; sitemap.xml for the whole site; SITE_URL; requirements.txt pinned Markdown 3.7 + Pillow 11.3, installed by the Pages workflow; blog.css and blog JS). The brief's listing, result-page and article commits land here because one renderer builds them all. Decisions: Python-Markdown (small, well known, tables and heading ids built in); a small built-in front matter reader instead of a YAML library; the sticky sidebar scrolls inside itself when taller than the screen; pills, tags and share buttons are 16px, metadata 14px in non-paragraph elements; screen-reader-only headings are skipped by the heading reveal
- 2026-10-08: New tee image (your 1600px photo; the old tee was a 400px source enlarged to 600 and looked soft). Same treatment as the library (trimmed, centred, 82% fill) but 1000x1000 because the tee is shown large; ~24 KB, so page weight barely changes. It replaces the tee everywhere it is used (mini UIs, How it works, zig-zags, decks, wheel, walls, 404)
- 2026-10-08: Partners: real partner logos (13 supplied logos in src/assets/partners/, 192px WebP, assigned at random to the 12 demo partners and the hero orbit; monogram tiles stay as the fallback). Flagged: the logos are real apps while the names are still fictional demo names
- 2026-10-08: Contact page (render_contact.py, src/contact.json, src/contact.css, contact JS in the template, audit check_contact); the shared form handler gains blur validation, a success template that replaces the form, and an email fallback on errors; Resources > Get help gets a Contact item and every "Talk to our team" button links to contact/. Fixes found while building: the field wrappers were renamed .cfx because .fx is the homepage features heading (its script crashed the page), and .form[hidden] now really hides the form on success. Figma not readable; copy from the brief
- 2026-10-08: Partners page (render_partners.py, src/partners.json, src/partners-directory.json, src/partners.css) and the shared form setup (src/forms.css, one form handler in the template, FORM_ENDPOINT and NEWSLETTER_ENDPOINT in build.py, both empty: forms say "Form not connected yet"). Also {{BTN_SECONDARY:label|href}}. Decisions: the hero title uses the H2 size (two long lines at display size ran to seven lines); demo partners and draft benefits/FAQs are marked for replacement; Figma not readable, copy from the brief
- 2026-10-08: Interactive 404 page (render_404.py, src/404.json, src/404.css, editor JS in the shared template, SITE_BASE in build.py, audit check_404 with a GitHub-Pages-like local server). Decisions: the homepage gets #features and #industries anchors for the 404's links (there are no Features or Industries index pages); Pricing points at #pricing like the navbar, flagged because no pricing page exists; the Figma frames could not be read (the Figma connector is not authorized), so the copy comes from the brief
- 2026-10-08: Industry hero: colour-only deck, larger products (your changes, all eight pages): back cards lose their labels (the edges stay clickable), the progress line and the "Add text" step are gone (the text never sat perfectly on every product), the product photo grows from 72% to 96% of the card and may dip over the palette, and the story is now just the swatch click and tint (3.0s per card). With no option step the chip shows each card's own option statically; the unused "result" field is removed from the industry JSONs and the spec
- 2026-10-08: How it works: new step card colours (your four flat colours replace the gradients); strokes recomputed as darker tones of each colour at the same 1.25 contrast, keeping each colour's own saturation so they stay as muted as the fills. No dark-mode values were given, so the cards use the same colours in both themes, as before
- 2026-10-08: Industry pages: docs and cleanup. The kit's reference renderer and CSS are deleted (ported into render_industry.py and src/industry.css). The kit's beauty-cosmetics page is not added: Beauty & cosmetics is not an InkyBay industry (your call on 2026-10-08), so eight industry pages exist. Open: the demo store URL (#demo-store on every page) and every merchant named "Store name (draft)"
- 2026-10-08: Add industry page: Gadgets & electronics (built with stand-in images; needs: Phone case and charger images would make this page stronger.)
- 2026-10-08: Add industry page: Footwear & bags
- 2026-10-08: Add industry page: Gifts & promotional
- 2026-10-08: Add industry page: Printing & packaging (built with stand-in images; needs: More packaging products (boxes, labels, mailers) would make this page stronger.)
- 2026-10-08: Industry hero: fit the result text to the product. The audit caught "Studio Nine" spilling past the narrow notebook on printing-packaging; the deck now centres each card's text on the product's real outline (from the image's alpha) and shrinks it to 80% of the product's width, instead of shortening the copy
- 2026-10-08: Add industry page: Home & furniture
- 2026-10-08: Add industry page: Sports & teamwear
- 2026-10-08: Add industry page: Jewelry & accessories
- 2026-10-08: Industry hero: customizing deck (story, rotation, tabs, hover/focus pause, swipe, arrow keys, live region, reduced motion; shared on-screen observer extended to .ishow). Decisions: back-card blur is 0.3px per step (0.8px blurred the tab labels); the leave animation eases each half separately (an expo curve over the whole 0.6s hid the lift and blur within 100ms); the glass panel and palette are 92% white on dark pages so they stay light
- 2026-10-08: Industry page template (render_industry.py, src/industry.css, build.py writes site/industries/<slug>/, shared "Show more" JS, audit checks for industry JSON and the hero deck). Ported from the kit's reference onto the current codebase; the hero is the deck from docs/industry-hero-spec.md (static here, motion next commit). Back-card tabs follow the spec's 14px strip with 11px labels. Only fashion-apparel is built in this step
- 2026-10-08: Mobile menu sheet: balanced, easier to scan. Sub-items sat 8px left of their section labels (the compact-navbar padding beat the sheet rule and a generic ul rule removed the sub-list indent); now everything shares one left edge, sub-items get their menu icons and full-ink 16px titles in 48px rows, sections get 52px rows with hairlines, the current page is highlighted, and the sheet is an accordion so it stays short
- 2026-10-08: Remove Beauty & cosmetics (your call): the industry leaves src/industries/_index.json, so the Industries mega menu and its mobile sub-list list eight industries; its unused droplet icon is gone. This replaces the earlier "To fix later" note about Beauty & cosmetics images
- 2026-10-08: Wheel: one card per product (your call; replaces the one-card-per-industry rule). 25 static cards from src/products.json, labelled with the product and linking to its industry page, interleaved round-robin by industry with a build-time check that neighbours differ; the crossfade (JS, CSS, stagger) and the industries' products field are gone; cards return to the locked 232px/22px size now that labels are short; the step shrinks automatically if the product count would close the circle. Checked at 390/768/1440/1920px: 32.8px (20px on phones) gaps, no title cut off, no on-screen pops, 25 x next returns to the start, prev, pause and play work. To fix later: add Beauty & cosmetics product images (jar, lipstick, gift box) to src/assets/products/ and to products.json with industry beauty-cosmetics; their cards appear automatically
- 2026-10-07: Product copy matches the new products: advanced-product-setup wall heading "Apparel to wall clocks." (the pet bowl is gone), ready-made-templates "Frames, mugs and more." and its lead (no greeting card any more)
- 2026-10-07: Remove unused product images: card, drawstring, handbag, necklace, petbowl, phone, photo, pillow, pumpkin, puzzle, tote, wallart (each removed only after checking nothing references it: no image path in the repo, no product wall, zig-zag photo or industry uses it) and their src/products.json entries
- 2026-10-07: Feature pages use the new products: every removed product on the nine product walls and three zig-zag photos is swapped for a new one that fits the feature (walls keep their counts, no duplicates); unlimited-product-options' strap roll becomes Short/Long/Padded/None because a chain strap does not fit the backpack
- 2026-10-07: Industries wheel: nine industries from src/industries/_index.json (new products field), staggered product crossfades, links to industries/<slug>/. Cards show the industry title only: an examples line was tried and dropped (your call; at 14px it also broke the 16px text floor, so the audit failed with it). Cards grow to 256px (236px on tablets/phones) with 20px/18px titles so "Gadgets & electronics" and the other long titles stay on one line, also at 390px; the wrap-hide point moves to the loop edge because with nine cards it was visible at 1920px. Removed the unused .is-wide rule. To fix later: add Beauty & cosmetics product images (jar, lipstick, gift box) to src/assets/products/ and products.json, then list them in that industry's products (it shows the droplet icon until then)
- 2026-10-07: New product image library: 22 new products (renamed to lowercase, correctly spelled keys; duplicates T-shirt and mug2 dropped) plus mug, tee and socks re-processed the same way (trim, 82% fill, 600x600, WebP q82). Labels move from render_feature.py to src/products.json and become product names ("Mug", not "Drinkware"); the old products keep their old labels until they are removed. Noted: the mega menu promos inline cta-products.webp and hero-editor.webp on every page (~340 KB of base64), worth smaller promo thumbnails later
- 2026-10-07: Audit all mega menus (scripts/audit.py check_menus: every page, 1366 and 1440px, plus the 390px sheet; link counts come from nav.json, so new menus and items are covered automatically). Verified against a deliberately broken page: catches a cut-off description, a missing sheet link and Esc not closing
- 2026-10-07: Resources mega menu (groups layout, five new icons, external Help center with arrow-out icon, Live chat data-action hook, video promo from hero-editor.webp with a dark wash so it reads as a paused video). Footer Resources and Get help columns now come from nav.json (Contact kept as an extra Get help link). Fix found while testing: with all three sub-lists open the mobile sheet ran past the screen with no way to scroll; it now scrolls inside itself, and the wheel smooth-scroll leaves the sheet native
- 2026-10-07: Industries mega menu (nine industries from src/industries/_index.json, eight new icons, promo "Built for your kind of store" linking to resources/case-studies/). The cta-products image is near-square, so its promo uses object-position 50% 0% to keep the cap, colour picker and clipart panel whole. The footer Industries column is now generated from the same data (first five plus "All industries"), so no footer copy is hardcoded for it
- 2026-10-07: Data-driven mega menu component: src/nav.json renders the triggers, panels and mobile sub-lists; generic JS (one open at a time, instant swap between triggers, outside click/Esc). Features moved in with no visual change (before/after screenshots identical at 1440px, light and dark). Industries and Resources stay placeholders until their own commits. Menu links are now <root><path> everywhere (feature pages link to ../../features/<slug>/ instead of ../<slug>/), which replaces the old per-page link rule
- 2026-10-07: Hero showcase: Unlimited product options (photo heroes/unlimited-product-options.webp, mini UI options | Option added, No limit)
- 2026-10-07: Hero showcase: Quantity discounts (photo heroes/quantity-discounts.webp, mini UI tiers | Qty roll, 20% off)
- 2026-10-07: Hero showcase: Inventory management (photo heroes/inventory-management.webp, mini UI inventory | Stock roll, Unavailable)
- 2026-10-07: Hero showcase: Ready-made templates (photo heroes/ready-made-templates.webp, mini UI templates | Template applied, Text editable)
- 2026-10-07: Hero showcase: Smart add-on pricing (photo heroes/smart-add-on-pricing.webp, mini UI addons | Add-on roll, Total updated)
- 2026-10-07: Hero showcase: Multiple printing methods (photo heroes/multiple-printing-methods.webp, mini UI methods | Method roll, Thread colors: 6)
- 2026-10-07: Hero showcase: Font & clipart library (photo heroes/font-clipart-library.webp, mini UI library | Font roll, Clipart added)
- 2026-10-07: Hero showcase: Custom quote requests (photo heroes/custom-quote-requests.webp, mini UI quote | Design attached, Quote sent)
- 2026-10-07: Hero showcase: Advanced product setup (photo heroes/advanced-product-setup.webp, mini UI sides | Size roll, 4 print areas)
- 2026-10-07: Hero product photos: src/assets/heroes/<slug>.webp for all nine features, 1200x1200 (2x the hero size), quality 82, transparency kept, 54-83 KB each (converted from ~/Downloads/heroes/<slug>.png). Not used by any page until each hero is switched to the showcase
- 2026-10-07: Hero showcase layout (shared: render_feature.py, feature.css, once-only entrance JS in template.html, audit checks). Decisions: the comet ring leaves feature heroes (stays on the homepage hero, rating card and CTA card); square showcase so the 18em UI hangs below the product instead of covering it; no monospace in chip text ("Display" not "Mono"); docs wording "Unavailable" for inventory chips. To fix later: re-export ~/Downloads/heroes/inventory-management.png with the shelf tags in order S, M, L (no blank tags)
- 2026-10-07: Mega menu promo: new image (glowing InkyBay app icon with cursor), 720x489 WebP at quality 82, same file name. Subject measures centred in the 16:10 crop (50.5% x, 49.7% y), so no object-position override
- 2026-10-07: Mega menu promo: distinct surface in dark mode (#1E1714, top glow, 1px border; light mode unchanged). The border is on ::after, not the card, because the full-bleed image would cover an inset shadow
- 2026-10-07: Pages source switched to GitHub Actions; live site verified (homepage and feature pages load, mega menu, breadcrumb and logo links work between them)
- 2026-10-07: Document the new structure (README rewritten for site/, Actions deploy and local preview; playbook no longer points at the moved content/ drafts; Playwright setup uses python3 -m pip since bare pip is not always installed)
- 2026-10-07: Deploy to GitHub Pages with Actions (.github/workflows/pages.yml builds and deploys site/ on every push to main). Removed the root index.html redirect and .nojekyll: they served the old branch-based deploy and pointed at the untracked reference/
- 2026-10-07: Relative links for the new URL structure (mega menu, mobile sheet, logos, breadcrumb). Relative, not root-absolute, because GitHub Pages serves the site under /inkybay-website/; the breadcrumb now uses {{HOME}} like the logos
- 2026-10-07: Build to site/ with clean URLs (site/index.html, site/features/<slug>/index.html, site/404.html; reference/ and site/ ignored, reference/ untracked). audit.py reads site/ in this same commit so the audit checks the new build, not stale files; internal links are fixed in the next commit
- 2026-10-07: CLAUDE.md: rules for keeping docs in sync (rules section at the top, this change log seeded from git history)
- 2026-10-07: Add feature page: Unlimited product options
- 2026-10-07: Add feature page: Quantity discounts
- 2026-10-07: Add feature page: Inventory management
- 2026-10-07: Add feature page: Ready-made templates
- 2026-10-07: Add feature page: Smart add-on pricing
- 2026-10-07: Add feature page: Multiple printing methods
- 2026-10-07: Add feature page: Font & clipart library
- 2026-10-07: Add feature page: Custom quote requests
- 2026-10-07: Add feature playbook, audit script and draft content
- 2026-10-07: Mega menu: promo image, two-line menu copy, more spacing
- 2026-10-07: Mega menu, anchored looping feature visuals, dark How it works band, one-tone headings on tint
- 2026-10-07: Two-tone headings on the homepage; edge-to-edge product wall
- 2026-10-07: Feature template v2: Advanced product setup, two-tone headings, glow visuals, vertical product wall
- 2026-10-07: Feature page template, Live design editor page, one build for all pages
- 2026-10-06: FAQ heading: FAQs at the standard 56px H2
- 2026-10-05: How it works: first step uses the butter gradient
- 2026-10-05: How it works: four Figma gradients with matching strokes
- 2026-10-05: Why InkyBay glass keeps its light look in dark mode
- 2026-10-05: New backgrounds for Powerful customization and Built for complex products
- 2026-10-05: Why InkyBay glass cards fill the frame evenly with stronger contrast
- 2026-10-05: Head-centred avatars, even marquee separator, photo backgrounds with glass mini UIs in Why InkyBay
- 2026-10-05: Add merchants and shoppers text marquee between CTA and footer
- 2026-10-05: Soft centred ring glow with short trail, equal rail media boxes with larger UIs, no scaling on Why cards
- 2026-10-05: Smooth scroll, bounce-free navbar, always-compact mobile nav, blink-free image swaps, centred ring glow, drawn underline
- 2026-10-05: Add GitHub Pages entry point that opens the homepage reference
- 2026-10-05: Locked homepage design: reference build, template, assets, CLAUDE.md
