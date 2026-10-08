# Prompt: build the industry pages (eight; Beauty & cosmetics was dropped)

Copy this kit's folders into the repo first (see the chat), then paste this into Claude Code.

```
Build the nine industry pages. Read CLAUDE.md first and follow its rules
(doc + change log in the same commit, build + audit PASS, one commit per
step, authored as me, never force-push).

Inputs (already copied into the repo):
- src/industries/<slug>.json for all nine (content, hero stage, products,
  stats, merchants, FAQs). Keep them as the single source of copy.
- docs/industry-hero-spec.md: the hero design you must implement exactly.
- render_industry.reference.py and src/industry.reference.css: a working
  reference of the page from the design chat. It was built on an OLDER
  template, so do not copy it blindly: port its sections onto the current
  render_feature.py, build.py (site/ output, relative links), nav.json and
  shared JS. Delete the two reference files in the last step.

STEP 1 - Industry template (shared)
Create render_industry.py and src/industry.css on the current codebase.
Sections, in order (backgrounds in brackets):
  1 Hero [white]: breadcrumb Home > Industries > <title>, H1, lead, two
    buttons, proof pill, and the "customizing deck" from
    docs/industry-hero-spec.md (NOT the feature-page dark showcase).
  2 Products [tint]: two-tone heading (renders one tone on tint, as per
    the rule), grid 4-up of product cards: image + name only, no tags.
    Below: the products_cta text and a primary button to products_cta.href.
  3 Stats [white]: heading + lead left, three stats right as a vertical
    list with hairlines. Whole numbers count up once; decimals stay
    static. Hover a row: a soft light sweeps across its digits left to
    right (1.1s, ease-in-out), the "+" keeps its brand colour.
  4 Merchants [dark]: two cards per row (one on phones). Card: store
    preview window, store name + country, quote, "Visit store" link. No
    avatar, no category. Show the first merchants_visible cards; a
    "Show more stores" button reveals the rest (move its JS into the
    shared template, no inline onclick).
  5 Testimonials [tint]: the homepage reviews section, same markup and
    shared JS (reuse it, do not copy-paste a second implementation).
  6 FAQs [white].
  7 CTA, crowd marquee, footer [dark]: from the homepage.
Output: site/industries/<slug>/index.html. Mega menu and wheel links to
industries/<slug>/ must now resolve. Extend scripts/audit.py with the
hero-spec checks. Build only fashion-apparel in this step; audit must PASS.
Commit: "Industry page template".

STEP 2 - Hero: the customizing deck
Implement docs/industry-hero-spec.md fully: the 4-card deck with label
tabs, the per-card story (cursor clicks text, then a swatch, then the
last action; result text, masked tint, chip update), the rotating
transition (front card lifts, tilts, blurs and goes to the back; next
card un-blurs forward), tab clicks, hover/focus pause, swipe, arrow
keys, reduced motion and mobile. Panel and palette stay static.
Show me 1440px and 390px screenshots of the fashion-apparel hero in
light and dark, plus four frames: after the text click, after the
swatch click, mid-rotation, and the next card settled.
Commit: "Industry hero: customizing deck".

STEP 3 - The nine pages, one commit each, in this order:
  fashion-apparel, jewelry-accessories, sports-teamwear, home-furniture,
  printing-packaging, gifts-promotional, footwear-bags,
  gadgets-electronics
For each: build, audit <slug> must PASS. If a JSON has "needs_images",
build it anyway with the listed stand-ins and tell me what is missing.
Commit per page: "Add industry page: <Title>".

STEP 4 - Wrap up
- Delete render_industry.reference.py and src/industry.reference.css.
- Update CLAUDE.md: an "Industry pages" section (sections, JSON schema,
  hero spec summary, products and merchants rules) and the change log.
- audit --all must PASS. Push, confirm the Pages deploy, show
  git log --oneline -14 and one image with all nine heroes at 1440px.

Flag, do not guess: the demo store URL (products_cta.href is
"#demo-store"), and every merchant marked "Store name (draft)".
```


---

## If the hero v1 ("editor stage") is already built

Paste this instead of the prompt above:

```
The industry hero changes from the v1 "editor stage" to the v2
"customizing deck". docs/industry-hero-spec.md and the hero.stage data in
every src/industries/<slug>.json have been replaced (copied in from the
new kit). Follow CLAUDE.md rules.

1. Re-implement the hero to the new spec (remove the orbit ring and tool
   buttons; add the deck, tabs, per-card story, rotation, interaction).
   Keep the shared parts that still apply (glass panel, palette, cursor,
   masked tint, chip). Update scripts/audit.py with the new checks.
   Show the same screenshots and four frames as in the spec.
   Commit: "Industry hero: customizing deck".
2. Rebuild all nine industry pages; audit --all must PASS.
   Commit: "Industry pages use the deck hero".
3. Update CLAUDE.md (Industry pages section + change log), push.
```
