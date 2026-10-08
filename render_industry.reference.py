"""Render an industry page from src/industries/<slug>.json.

Same shell as the feature pages (homepage head, navbar, CTA, footer, JS) and the same building blocks
(two-tone headings, zig-zag visuals, chips, mini UIs, FAQ). Industry-only sections: hero stage,
product cards and the merchant showcase.
"""
import json, re
from render_feature import ROOT, E, ICON, CHEV_R, ARROW, STAR, mini_uis, heading, visual, chip


def render(slug):
    d = json.loads((ROOT / "src" / "industries" / f"{slug}.json").read_text())
    feats = {f["slug"]: f for f in json.loads((ROOT / "src" / "features" / "_index.json").read_text())["features"]}
    home = (ROOT / "src" / "template.html").read_text()
    ui = mini_uis(home)
    rv_s = home.index('<section class="reviews"'); rv_e = home.index("</section>", rv_s) + len("</section>")
    reviews = "<!-- 6 · TESTIMONIALS (from the homepage, same markup and shared JS) -->\n  " + home[rv_s:rv_e]
    h = d["hero"]
    proof = home[home.index('<a class="proof"'):home.index("</a>", home.index('<a class="proof"')) + 4]

    st = h["stage"]
    stage = (f'<div class="fvis istage" aria-hidden="true"><div class="fcomp"><div class="fanchor fanchor--photo">'
             f'<div class="istage__img"><img src="{{{{IMG:products/{st["main"]}.webp}}}}" alt="" width="600" height="600"></div>'
             f'<span class="att att--tl" style="--d:.35s">{chip(st["chips"][0])}</span>'
             f'<span class="att att--br" style="--d:.6s">{chip(st["chips"][1], "chip chip--brand")}</span></div></div></div>')


    def pcard(p):
        img = f'<img src="{{{{IMG:products/{p["image"]}.webp}}}}" alt="" width="600" height="600" loading="lazy">'
        return f'<li class="ipcard"><div class="ipcard__img">{img}</div><div class="ipcard__body"><h3 class="ipcard__name">{E(p["name"])}</h3></div></li>'

    def mcard(m, k):
        extra = " is-extra" if k >= d.get("merchants_visible", 4) else ""
        return (f'<li class="imcard{extra}"><div class="imcard__preview" aria-hidden="true"><div class="imwin"><div class="imwin__bar"><i></i><i></i><i></i><span class="imwin__url"></span></div>'
                f'<div class="imwin__shot"><img src="{{{{IMG:products/{m["preview"]}.webp}}}}" alt="" width="600" height="600" loading="lazy">'
                f'<div class="imwin__lines"><b></b><s></s><s></s><u></u></div></div></div></div>'
                f'<div class="imcard__body"><div class="imcard__head"><span class="imcard__name">{E(m["name"])}</span><span class="imcard__where">{E(m["country"])}</span></div>'
                f'<p class="imcard__quote">{E(m["quote"])}</p>'
                f'<a class="story__link" href="{E(m["url"])}">Visit store {ARROW}</a></div></li>')

    def stat(s_):
        cls = "istats__num stat__num" if "." not in s_["value"] else "istats__num"   # count-up handles whole numbers only
        return f'<li><span class="{cls}">{E(s_["value"])}<span>{E(s_["suffix"])}</span></span><span class="istats__label">{E(s_["label"])}</span></li>'

    faqs = "\n".join(f"""          <li class="qa{" is-open" if k == 0 else ""}">
            <h3><button class="qa__q" id="iq{k}" aria-expanded="{"true" if k == 0 else "false"}" aria-controls="ia{k}">{E(f["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
            <div class="qa__a" id="ia{k}" role="region" aria-labelledby="iq{k}"><div><p>{E(f["a"])}</p></div></div>
          </li>""" for k, f in enumerate(d["faqs"]))

    body = f"""<main>
  <!-- 1 · HERO -->
  <section class="fhero" aria-labelledby="i-title">
    <div class="container fhero__grid">
      <div class="fhero__text">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="../../">Home</a>{CHEV_R}<a href="#">Industries</a>{CHEV_R}<span aria-current="page">{E(d["nav_label"])}</span></nav>
        <h1 class="fhero__title" id="i-title">{E(h["title"])}</h1>
        <p class="fhero__lead">{E(h["lead"])}</p>
        <div class="fhero__actions">{{{{BTN_PRIMARY:{h["primary_cta"]}}}}}{{{{BTN_SECONDARY:{h["secondary_cta"]}}}}}</div>
        {proof}
      </div>
      <div class="fhero__vis">{stage}</div>
    </div>
  </section>

  <!-- 3 · PRODUCTS (tint) -->
  <section class="fsec fsec--tint" aria-labelledby="i-prod">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading(d["products_heading"], id_="i-prod")}</div>
      <ul class="iprod__grid">{"".join(pcard(p) for p in d["products"])}</ul>
      <div class="iprod__cta"><p>{E(d["products_cta"]["text"])}</p>{{{{BTN_PRIMARY:{d["products_cta"]["label"]}}}}}</div>
    </div>
  </section>

  <!-- 4 · STATS (white) -->
  <section class="fsec" aria-labelledby="i-stats">
    <div class="container istats">
      <div class="istats__text">{heading(d["stats_heading"], id_="i-stats")}<p class="fsec__lead">{E(d["stats_lead"])}</p></div>
      <ul class="istats__list">{"".join(stat(s_) for s_ in d["stats"])}</ul>
    </div>
  </section>

  <!-- 5 · MERCHANTS (dark) -->
  <section class="fsec fsec--dark imer" aria-labelledby="i-mer">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading(d["merchants_heading"], id_="i-mer")}</div>
      <ul class="imer__grid">{"".join(mcard(m, k) for k, m in enumerate(d["merchants"]))}</ul>
      {'<div class="imer__more"><button class="btn btn--secondary" type="button" onclick="this.closest(\'.imer\').classList.add(\'is-all\')">Show more stores</button></div>' if len(d["merchants"]) > d.get("merchants_visible", 4) else ''}
    </div>
  </section>

  {reviews}

  <!-- 7 · FAQS -->
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
