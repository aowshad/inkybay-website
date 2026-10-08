"""Render an industry page from src/industries/<slug>.json.

Same shell as the feature pages (homepage head, navbar, CTA, crowd marquee, footer and JS) and the same building
blocks (two-tone headings, chips, FAQ). Industry-only sections: the customizing-deck hero (docs/industry-hero-spec.md),
product cards, stats and the merchant showcase. Testimonials are the homepage reviews section, reused as is.
"""
import json, re
from render_feature import ROOT, E, ICON, CHEV_R, ARROW, heading

CURSOR = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3.5l13.5 8.2-6.1 1.3 3.6 6.6-2.6 1.4-3.6-6.6-4.8 4.1z" '
          'fill="#fff" stroke="#1B1F27" stroke-width="1.4" stroke-linejoin="round"/></svg>')


def deck(st):
    """The hero's customizing deck: product cards (front card labelled; back cards show only their edges), static editor
    panel and palette, and a cursor that recolours each front card."""
    cards = []
    for k, c in enumerate(st["deck"]):
        first = k == 0     # without JS (and with reduced motion) the first card shows its colour
        cards.append(
            f'<div class="icardx{" is-tint" if first else ""}"{" data-front" if first else ""} data-k="{k}" data-slot="{k}" data-swatch="{c["swatch"]}" '
            f'style="--slot:{k};--tint-c:{E(st["swatches"][c["swatch"]])}" role="group" aria-roledescription="slide" aria-label="{E(c["label"])}">'
            f'<button class="icardx__tab" type="button" aria-label="Show {E(c["label"])}" tabindex="-1"></button>'
            f'<span class="icardx__label">{E(c["label"])}</span>'
            f'<div class="icardx__media"><img class="icardx__img" src="{{{{IMG:products/{c["product"]}.webp}}}}" alt="" width="600" height="600" decoding="async">'
            f'<span class="icardx__tint" aria-hidden="true"></span></div>'
            f'<span class="icardx__chip chip">{E(c["chip"])}</span>'
            f'</div>')
    rows = "".join(f'<li class="ipanel__row" data-row="{k}"><span>{E(a["label"])}</span><span class="ipanel__icon">{ICON[a["icon"]]}</span></li>'
                   for k, a in enumerate(st["actions"]))
    on = st["deck"][0]["swatch"]
    sw = "".join(f'<li class="ipalette__sw{" is-on" if k == on else ""}" data-sw="{k}" style="--c:{E(c)}"></li>' for k, c in enumerate(st["swatches"]))
    return (f'<div class="ishow"><span class="ishow__glow" aria-hidden="true"></span>'
            f'<div class="ideck" tabindex="0" aria-roledescription="carousel" aria-label="Products you can customize">{"".join(cards)}</div>'
            f'<div class="ipanel" aria-hidden="true"><p class="ipanel__h">Customize your item</p><ul>{rows}</ul></div>'
            f'<ul class="ipalette" aria-hidden="true">{sw}</ul>'
            f'<span class="icursor" aria-hidden="true">{CURSOR}</span>'
            f'<p class="sr-only ishow__live" aria-live="polite"></p></div>')


def render(slug):
    d = json.loads((ROOT / "src" / "industries" / f"{slug}.json").read_text())
    home = (ROOT / "src" / "template.html").read_text()
    h = d["hero"]
    proof = home[home.index('<a class="proof"'):home.index("</a>", home.index('<a class="proof"')) + 4]
    rv_s = home.index('<section class="reviews"'); rv_e = home.index("</section>", rv_s) + len("</section>")
    reviews = home[rv_s:rv_e]          # the homepage reviews section: same markup, same shared JS

    def pcard(p):
        return (f'<li class="ipcard"><div class="ipcard__img"><img src="{{{{IMG:products/{p["image"]}.webp}}}}" alt="" width="600" height="600" loading="lazy" decoding="async"></div>'
                f'<h3 class="ipcard__name">{E(p["name"])}</h3></li>')

    def stat(s_):
        cls = "istats__num" + ("" if "." in s_["value"] else " stat__num")    # the shared count-up runs on whole numbers only
        return f'<li><span class="{cls}">{E(s_["value"])}<span>{E(s_["suffix"])}</span></span><span class="istats__label">{E(s_["label"])}</span></li>'

    shown = d.get("merchants_visible", 4)

    def mcard(m, k):
        extra = " is-extra" if k >= shown else ""
        return (f'<li class="imcard{extra}"><div class="imcard__preview" aria-hidden="true"><div class="imwin"><div class="imwin__bar"><i></i><i></i><i></i><span class="imwin__url"></span></div>'
                f'<div class="imwin__shot"><img src="{{{{IMG:products/{m["preview"]}.webp}}}}" alt="" width="600" height="600" loading="lazy" decoding="async">'
                f'<div class="imwin__lines"><b></b><s></s><s></s><u></u></div></div></div></div>'
                f'<div class="imcard__body"><div class="imcard__head"><span class="imcard__name">{E(m["name"])}</span><span class="imcard__where">{E(m["country"])}</span></div>'
                f'<p class="imcard__quote">{E(m["quote"])}</p>'
                f'<a class="story__link" href="{E(m["url"])}">Visit store {ARROW}</a></div></li>')

    more = (f'<div class="imer__more"><button class="btn btn--secondary" type="button" data-show-more aria-controls="imer-grid">Show more stores</button></div>'
            if len(d["merchants"]) > shown else "")
    faqs = "\n".join(f"""          <li class="qa{" is-open" if k == 0 else ""}">
            <h3><button class="qa__q" id="iq{k}" aria-expanded="{"true" if k == 0 else "false"}" aria-controls="ia{k}">{E(f["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
            <div class="qa__a" id="ia{k}" role="region" aria-labelledby="iq{k}"><div><p>{E(f["a"])}</p></div></div>
          </li>""" for k, f in enumerate(d["faqs"]))
    cta = d["products_cta"]

    body = f"""<main>
  <!-- 1 · HERO: the customizing deck (docs/industry-hero-spec.md) -->
  <section class="fhero ihero" aria-labelledby="i-title">
    <div class="container fhero__grid">
      <div class="fhero__text">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">Home</a>{CHEV_R}<a href="#">Industries</a>{CHEV_R}<span aria-current="page">{E(d["nav_label"])}</span></nav>
        <h1 class="fhero__title" id="i-title">{E(h["title"])}</h1>
        <p class="fhero__lead">{E(h["lead"])}</p>
        <div class="fhero__actions">{{{{BTN_PRIMARY:{h["primary_cta"]}}}}}{{{{BTN_SECONDARY:{h["secondary_cta"]}}}}}</div>
        {proof}
      </div>
      <div class="fhero__vis">{deck(h["stage"])}</div>
    </div>
  </section>

  <!-- 2 · PRODUCTS (tint) -->
  <section class="fsec fsec--tint" aria-labelledby="i-prod">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading(d["products_heading"], id_="i-prod")}</div>
      <ul class="iprod__grid">{"".join(pcard(p) for p in d["products"])}</ul>
      <div class="iprod__cta"><p>{E(cta["text"])}</p>{{{{BTN_PRIMARY:{cta["label"]}|{cta["href"]}}}}}</div>
    </div>
  </section>

  <!-- 3 · STATS (white) -->
  <section class="fsec" aria-labelledby="i-stats">
    <div class="container istats">
      <div class="istats__text">{heading(d["stats_heading"], id_="i-stats")}<p class="fsec__lead">{E(d["stats_lead"])}</p></div>
      <ul class="istats__list">{"".join(stat(s_) for s_ in d["stats"])}</ul>
    </div>
  </section>

  <!-- 4 · MERCHANTS (dark) -->
  <section class="fsec fsec--dark imer" aria-labelledby="i-mer">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading(d["merchants_heading"], id_="i-mer")}</div>
      <ul class="imer__grid" id="imer-grid">{"".join(mcard(m, k) for k, m in enumerate(d["merchants"]))}</ul>
      {more}
    </div>
  </section>

  <!-- 5 · TESTIMONIALS (tint): the homepage reviews section -->
  {reviews}

  <!-- 6 · FAQS (white) -->
  <section class="faq" aria-labelledby="faq-title">
    <div class="container faq__grid">
      <div class="faq__intro">
        <h2 class="faq__title" id="faq-title">FAQs</h2>
        <p class="faq__lead">Common questions from {E(d["nav_label"].lower())} stores.</p>
        <div class="faq__help"><p>Still have questions?</p>{{{{BTN_SECONDARY:Talk to our team}}}}</div>
      </div>
      <ul class="faq__list">
{faqs}
      </ul>
    </div>
  </section>
</main>"""

    head = home[:home.index("<main>")]
    css = (ROOT / "src" / "feature.css").read_text() + (ROOT / "src" / "industry.css").read_text()
    head = head.replace("</style>", css + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(d["meta"]["title"])}</title>\n<meta name="description" content="{E(d["meta"]["description"])}">', head, count=1)
    tail = home[home.index("</main>") + len("</main>"):]
    return head + body + tail
