"""Render the 404 page from src/404.json: "the 404 is a design project" (no CTA section; the footer stays).

The "404" is a text layer on a product inside a mini InkyBay editor that visitors can move, resize, rotate, recolour
and retype (the shared JS in src/template.html drives it). GitHub Pages serves 404.html for any missing URL at any
depth, so every link on this page starts from SITE_BASE (passed in as `root`), never relative to the page's folder.
"""
import json, re
from render_feature import ROOT, E, ICON

CURSOR = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3.5l13.5 8.2-6.1 1.3 3.6 6.6-2.6 1.4-3.6-6.6-4.8 4.1z" '
          'fill="#fff" stroke="#1B1F27" stroke-width="1.4" stroke-linejoin="round"/></svg>')


def render(root):
    d = json.loads((ROOT / "src" / "404.json").read_text())
    home = (ROOT / "src" / "template.html").read_text()
    ed = d["editor"]

    tabs = "".join(f'<button class="ed__tab" type="button" role="tab" aria-selected="{"true" if k == 0 else "false"}" data-p="{k}">{E(p["label"])}</button>'
                   for k, p in enumerate(ed["products"]))
    imgs = "".join(f'<img class="ed__img{" is-on" if k == 0 else ""}" src="{{{{IMG:products/{p["product"]}.webp}}}}" alt="" width="600" height="600" decoding="async">'
                   for k, p in enumerate(ed["products"]))
    sw = "".join(f'<button class="ed__sw{" is-on" if k == 0 else ""}" type="button" aria-pressed="{"true" if k == 0 else "false"}" aria-label="{E(s["name"])}" '
                 f'data-c="{E(s["color"])}" style="--c:{E(s["color"])}"></button>' for k, s in enumerate(ed["swatches"]))
    wt = "".join(f'<button class="ed__wt" type="button" aria-pressed="{"true" if w["value"] == 700 else "false"}" data-w="{w["value"]}">{E(w["name"])}</button>'
                 for w in ed["weights"])
    areas = json.dumps([p["area"] for p in ed["products"]])
    a0 = ed["products"][0]["area"]
    editor = f"""<div class="ed" data-areas='{areas}' data-text="{E(ed["text"])}" data-max="{ed["max_chars"]}">
          <div class="ed__bar"><div class="ed__tabs" role="tablist" aria-label="Product">{tabs}</div><button class="ed__reset" type="button">Reset</button></div>
          <div class="ed__canvas" tabindex="0" role="application" aria-label="Design editor. Drag the 404 text, resize it from a corner, rotate it from the top handle. Arrow keys move, plus and minus resize, R rotates, Escape deselects.">
            <div class="ed__product">{imgs}
              <div class="ed__pa" style="--l:{a0[0]};--t:{a0[1]};--r:{a0[2]};--b:{a0[3]}">
                <div class="ed__layer" style="--x:.5;--y:.5;--s:.3;--rot:0deg;--c:{E(ed["swatches"][0]["color"])};--w:700">
                  <span class="ed__text" spellcheck="false">{E(ed["text"])}</span>
                  <span class="ed__h ed__h--nw" data-h="nw" aria-hidden="true"></span><span class="ed__h ed__h--ne" data-h="ne" aria-hidden="true"></span>
                  <span class="ed__h ed__h--sw" data-h="sw" aria-hidden="true"></span><span class="ed__h ed__h--se" data-h="se" aria-hidden="true"></span>
                  <span class="ed__rot" data-h="rot" aria-hidden="true"></span>
                </div>
              </div>
            </div>
            <span class="ed__warn" role="status">{E(ed["warning"])}</span>
            <span class="ed__cursor" aria-hidden="true">{CURSOR}</span>
            <span class="ed__hint" aria-hidden="true">{E(ed["hint"])}</span>
          </div>
          <div class="ed__tools"><div class="ed__sws" role="group" aria-label="Text colour">{sw}</div>
            <div class="ed__wts" role="group" aria-label="Font weight">{wt}</div><span class="ed__size" aria-hidden="true">Size 30%</span></div>
          <p class="sr-only ed__live" aria-live="polite"></p>
        </div>"""

    body = f"""<main>
  <!-- 404: the page is a design project -->
  <section class="e404" aria-labelledby="e404-title">
    <div class="container e404__grid">
      <div class="e404__text">
        <h1 class="e404__title" id="e404-title"><span class="h-line">{E(d["title"][0])}</span> <span class="h-line h-muted">{E(d["title"][1])}</span></h1>
        <p class="e404__lead">{E(d["lead"])}</p>
        <div class="e404__actions">{{{{BTN_PRIMARY:{d["button"]}|}}}}</div>
      </div>
      <div class="e404__vis">
        {editor}
      </div>
    </div>
  </section>
</main>"""

    head = home[:home.index("<main>")]
    head = head.replace("</style>", (ROOT / "src" / "404.css").read_text() + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(d["meta"]["title"])}</title>\n<meta name="robots" content="noindex">', head, count=1)
    tail = home[home.index("</main>") + len("</main>"):]
    cta_s = tail.index('<section class="cta"'); cta_e = tail.index("</section>", cta_s) + len("</section>")
    tail = tail[:cta_s] + tail[cta_e:]          # no CTA on the 404: the crowd marquee and footer stay
    return head + body + tail
