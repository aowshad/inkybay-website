# InkyBay website — Claude Code guide

The homepage is **designed and locked**. `reference/homepage.html` is the source of truth for look and behaviour.
When building the full site, extract tokens and components from it first, rebuild the homepage in the chosen
stack until it matches the reference, and only then create new pages. Do not reinvent the look on page 2.

## Repo layout

```
reference/homepage.html   single-file build of the locked homepage (open in a browser)
src/template.html         the same page with {{TOKENS}} for buttons, brand SVGs and images
src/assets/               logos/, products/, people/, photos/, brand/ (SVG), hero-editor.webp, cta-products.webp
build.py                  python3 build.py  ->  regenerates reference/homepage.html
```

## Locked kit (do not add new values; extend the scale only if a real need appears)

**Layout**: 1440 frame, 1248 container, `--margin` 96 (fluid, 20 min), 12 columns, `--gutter` 32 (fluid).
**Rhythm**: `--section-y` 120 desktop / 80 phones (every section's top and bottom padding).
`--head-gap` 64 / 40 (section heading block to its content).
**Type**: Geist for headings only, Inter for everything else. **No monospace anywhere.**
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
- **Image swaps** (features, why): the new frame fades in on top while the old stays fully opaque until covered. No scale, no blink.
- **Comet ring** (`.has-ring` + `.ring` + `.ring-glow > i`): 1px light with a short trail (~60deg), 8s per lap. The glow is a 3px
  masked stroke inside a wrapper that blurs it (7px) AFTER masking, so the halo is soft and centred on the line. Never mask after blurring.
  Used on the hero editor, the rating card and the CTA card. Content that should sit above the light gets `z-index: 4`.
- **Mini UI** (`.mui-stage > .mui`): em-based product snippets used as section visuals; scale with the host via container
  queries; one quiet loop each; animate only while on screen (`.mui-live`).
- **Heading reveal**: plain-text h2s are split into words by JS and rise out of a blur once on entering the viewport.

## Section order and behaviour

1. **Hero**: proof pill (star icon, 4.6, 169 reviews; "App Store" hidden under 480px), word-by-word headline landing, editor screenshot with comet ring.
2. **Logos**: marquee inside the container with edge fades; second set cloned by JS; pauses on hover.
3. **Features**: "customization" is always a selected layer; swatches auto-cycle every 2s and are clickable; ring is the active swatch's own box-shadow (always concentric). Left list auto-advances (7s progress line). Mobile heading: "Everything you need / for product / customization + swatches".
4. **Industries** (always dark): 14 product cards on an arc; titles never wrap (wide products use `.is-wide`). Radius is computed at the card's bottom edge so neighbours never touch (32.8px gap). 1.6 deg/s. Pause/play plus prev/next steps. Flat track on phones.
5. **Reveal**: in-flow statement; words sharpen with a 5-word soft edge as it passes through the viewport.
6. **Feature rail** ("Customize without limits"): pinned; vertical scroll drives the horizontal track 1:1; cards always 16:10, one full plus half the next; title one line, description reserves two lines, so every media box is identical; progress bar, no numbers. Native swipe rail under 960px.
7. **Case study** (tint band shared with Reviews): story card plus three stats that count up once. The "See full case study"
   underline draws left to right on hover (0.8s ease-in-out).
8. **Reviews**: infinite loop with clones, autoplay 5s driven by a JS clock (not CSS animationend; that skipped under load), dots only, drag/swipe, pauses on hover, keyboard focus, drag or offscreen. All cards equal height.
9. **How it works**: heading left, CTA right. Hovered step widens (JS-controlled active state so crossing gaps never collapses the row). Scenes scale to the card, centred geometrically before scaling.
10. **Why InkyBay** (tint): image left, stacked cards right (each tucks 18px under the next); active card gets a glow stroke only (no scaling or widening); each frame has its own nature photo (`photos/why-1..4`) with a frosted-glass mini UI on top (light and dark variants) that fills ~79% of the frame with an equal margin on all sides (`--pad: 6cqmin`); its main area (canvas, chart, file list) grows to fill; chart bars are white with the last one brand; the active side tab is solid brand with white text; progress hairline is aligned to the card's edges and centred in its bottom margin; click or 6s auto-advance.
11. **FAQ**: sticky intro left, single-open accordion right; white cards, orange only on the open one.
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
- Stats (10,000+ merchants, 50,000+ products daily, 169 reviews) and the 4.6 rating must match the live App Store listing.
- Fonts load from Google Fonts in the reference; self-host Geist and Inter in production.

## Suggested next steps

1. Pick the stack (Next.js + CSS modules or Tailwind with these tokens as theme values).
2. Port tokens, then Button, Navbar, Ring, Mini UI, heading reveal.
3. Rebuild the homepage section by section and diff it visually against `reference/homepage.html`.
4. Start the inner pages (Features, Industries, Pricing, Resources) with the same kit.
