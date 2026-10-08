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
  404.html                copy of the homepage for now
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
src/assets/               logos/, products/, people/, photos/, brand/ (SVG), heroes/ (feature hero photos), hero-editor.webp, cta-products.webp
src/products.json         product library: {"<name>": {"label", "industry"}} for every src/assets/products/<name>.webp
build.py                  python3 build.py  ->  regenerates site/ (homepage, 404, every feature page)
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
82% of the frame (so every product reads at the same size). Keys are lowercase and hyphenated (`water-bottle`). Every
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
9. **How it works**: heading left, CTA right. Each step card has its own Figma gradient (butter #FFFDD1, peach #FFD8B4, sky #BBEBFC, butter #FFFDD1, fading to white bottom-right) with a matching darker stroke of equal contrast. Hovered step widens (JS-controlled active state so crossing gaps never collapses the row). Scenes scale to the card, centred geometrically before scaling.
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
- `site/404.html` is a copy of the homepage with relative links, so its links only work when it is served from the
  site root; give it root-safe links when it becomes a real 404 page.
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
  promo is the video visual; footer: "Resources" = Learn + Grow, "Get help" = Get help + Contact).
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
  internal link with `/`): every link is `<root><path>`, where `<root>` is `""` on the homepage and `../../` on a
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

**Industry hero: the customizing deck** (`docs/industry-hero-spec.md`, data in `hero.stage`): 3-5 product cards
(4:5, radius 24, white in both themes) stacked so each back card is 14px higher and 4% narrower and shows its label as
a tab (11px). The editor panel (right) and palette (bottom-left) are frosted glass, light in both themes (more opaque
on a dark page), and never move. Each front card's story runs 4.8s: the cursor clicks the first action (the `result`
text appears on the product), a swatch (a multiply tint masked by the product image's own alpha, opacity .35), then the
third action (the chip rolls to `chip`); the progress line fills; then the deck rotates (0.6s): the front card lifts
12px, tilts back, blurs to 10px and fades while it moves to the back (each half of that animation eases on its own so
it stays visible), and the next card sharpens forward (back cards carry a slight 0.3px-per-step blur that keeps the tabs
readable). Runs only while on screen (the shared `.mui-live` observer) and pauses on hover or focus. Tabs (buttons,
"Show <label>"), arrow keys and swipe change cards; the deck is an `aria-roledescription="carousel"` with a polite live
region. Phones: two back tabs, one palette row. Reduced motion and no JS: no cursor, blur or rotation; the first card
is shown customized and tabs switch instantly. The audit checks the JSON and that the panel, palette and chip overlap the front card and the result text sits
inside the product's bounding box (from the image's alpha), that the deck advances on its own and that every visible tab
brings its card to the front.

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
