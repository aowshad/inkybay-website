# Industry hero v2: the customizing deck

The hero shows several products of the industry as a deck of cards. Each front card is customized live by a cursor
(text, colour, option) and only then hands over to the next card. The editor panel and palette stay put while the
products change, so the message is "one editor for everything you sell".

Inspired by a competitor's card deck (front card blurs away, next comes forward), but ours must be clearly different:
the deck rotates (the front card goes to the back, nothing is thrown away), every card is customized before it
leaves, and visitors can drive it. Never copy their layout, colours or timing.

It is different from the feature-page hero (dark showcase) and from the zig-zag visuals.

## Layout (inside .fhero__vis, square, about 560px at 1440)

```
                   ┌ Cap ─────────┐            back cards peek above the front card;
                 ┌ Baby onesie ───┐            each shows its label like a tab
               ┌ T-shirt ─────────┐
             ┌──────────────────────┐     ┌──────────────────────┐
             │ Hoodie        ━━━━── │     │ Customize your item  │  editor panel (static)
             │                      │     │  Add text        T   │  overlaps the deck's
             │      [ product ]     │     │  Upload image    ▣   │  right edge
             │      "Your name"     │     │  Change color    ◐   │
             │                      │     └──────────────────────┘
             │          [Size · L]  │
  ┌──────────┴───────┐──────────────┘
  │ ● ● ● ● palette  │                      palette (static) overlaps the deck's
  │ ● ● ● ●          │                      bottom-left corner
  └──────────────────┘
```

- **Stage**: light page background, one soft radial brand glow behind the deck (orange, about 0.18 opacity; a bit
  stronger in dark mode). No dark box, no orbit ring.
- **Deck**: 4 cards, portrait 4:5, radius 24, white surface, 1px `--line` border, soft shadow. Front card about 64% of
  the stage width. Back cards sit behind it: each one 14px higher, 4% narrower, slightly dimmer, so only their top
  strip with the label shows (the "tab").
- **Front card**: label top-left (16px, weight 500) with a thin progress line top-right (brand, fills over the card's
  time); the product photo centred (about 72% of the card); the option chip overlapping its bottom-right edge.
- **Editor panel** (right) and **palette** (bottom-left): frosted glass, light in both modes (same as Why InkyBay),
  both overlapping the deck's edges. They never move when cards change.
- **Cursor**: our own arrow (white, dark outline), about 22px.

## One card's story: 4.8s, then the deck rotates

| Time | What happens |
|---|---|
| 0.0s | New front card is settled. Cursor glides to action row 1, row highlights (brand tint). |
| 0.6s | Click (cursor scales 0.9 and back). The card's `result` text fades onto the product's print area (Geist 600, ink, about 9% of card width). |
| 1.6s | Cursor glides to the palette, clicks swatch `swatch`. Active ring moves there; the product tints toward that colour (soft multiply overlay, opacity about 0.35, masked by the product image's own alpha so the background never tints). |
| 2.8s | Cursor glides to action row 3, clicks. The chip updates to this card's `chip` text (rolls up). |
| 3.6s | Hold. Progress line completes. |
| 4.2s | Deck rotates (0.6s, `--ease-expo`): the front card lifts 12px, tilts back slightly, blurs to 10px and fades while it moves to the back of the stack; the next card un-blurs and grows forward into the front slot; tabs shift down one step. Result text and tint reset on the card that left. |

Loop through all cards forever, only while the hero is on screen (reuse the `mui-live` observer).

## Interaction
- Click (or Enter on) a back card's tab: the deck rotates to that card immediately and its story starts.
- Hover or keyboard focus on the deck pauses the loop; leaving resumes it.
- Phones: horizontal swipe on the deck goes to the next or previous card.
- Arrow keys left/right when the deck has focus. Tabs are buttons with `aria-label="Show <label>"`; the deck has
  `aria-roledescription="carousel"` and announces the front card's label politely.
- `prefers-reduced-motion`: no cursor, no blur, no auto-rotation. Show the first card customized (text, tint, chip on);
  tabs still switch cards instantly.

## Data (per industry JSON, `hero.stage`)

```json
"stage": {
  "actions": [{"label": "Add text", "icon": "type"}, {"label": "Upload image", "icon": "image"}, {"label": "Change color", "icon": "sliders"}],
  "swatches": ["#F4F1EE", "#2F2F2F", "#1F3A68", "#FF7500", "#E5380F", "#17A673", "#FFD982", "#BFE0FF"],
  "deck": [
    {"product": "hoodie", "label": "Hoodie", "result": "Your name", "swatch": 3, "chip": "Size · L"},
    {"product": "tee", "label": "T-shirt", "result": "RIVERS 10", "swatch": 2, "chip": "Size · M"}
  ]
}
```
3 to 5 cards per industry. Swatch is an index into `swatches`. Jewelry uses its 4 metal swatches.

## Mobile (under 600px)
The stage scales as one unit. Show 2 back tabs instead of 3, hide the palette's second row, keep the panel with its
rows on one line each. Nothing may overflow at 390px.

## Audit additions
- Panel, palette and chip each overlap the deck's edges (never detached).
- Result text sits inside the product's bounding box.
- Clicking each tab brings that card to the front; the loop advances on its own when not hovered.
- No horizontal overflow at 390px; only the tabs, chip and panel labels may be under 16px.
