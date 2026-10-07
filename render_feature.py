"""Render a feature page from features/<slug>.json using the homepage shell (head, nav, CTA, footer, JS)."""
import json, html, re, pathlib

ROOT = pathlib.Path(__file__).parent

def render(slug):
    d = json.load(open(ROOT / "src" / "features" / f"{slug}.json"))
    home = open(ROOT / "src" / "template.html").read()
    E = lambda s: html.escape(s, quote=True)

    # ---- reuse homepage mini-UI snippets (by position in the homepage markup)
    main = home[home.index("<main>"):home.index("</main>")]
    stages, i = [], 0
    while True:
        i = main.find('<div class="mui-stage"', i)
        if i < 0: break
        depth, j = 0, i
        while True:
            o, c = main.find("<div", j), main.find("</div>", j)
            if o != -1 and o < c: depth += 1; j = o + 4
            else:
                depth -= 1; j = c + 6
                if depth == 0: break
        stages.append(main[i:j]); i = j
    assert len(stages) == 15, len(stages)
    UI = {"setup": stages[0], "design": stages[1], "files": stages[2], "options": stages[3], "methods": stages[4],
          "inventory": stages[5], "quote": stages[6], "addons": stages[7], "tiers": stages[8], "library": stages[9],
          "templates": stages[10], "sides": stages[12], "grow": stages[14]}

    P = lambda d_: f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d_}</svg>'
    ICON = {
     "wand": P('<path d="M5 19l9-9"/><path d="M14 4l1 2.5 2.5 1-2.5 1L14 11l-1-2.5-2.5-1 2.5-1L14 4z"/>'),
     "eye": P('<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>'),
     "layers": P('<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>'),
     "file": P('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z"/><path d="M14 3v5h5M9 14l2 2 4-4"/>'),
     "type": P('<path d="M5 6V4h14v2M12 4v16M9 20h6"/>'),
     "image": P('<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M20.5 16l-5-5-8.5 8.5"/>'),
     "star": P('<path d="M12 3l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8-4.3-4.1 5.9-.8L12 3z"/>'),
     "qr": P('<rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><path d="M14 14h2v2h-2zM18 18h2v2h-2zM14 18h2M18 14h2"/>'),
     "hash": P('<path d="M5 9h14M5 15h14M10 4L8 20M16 4l-2 16"/>'),
     "template": P('<rect x="3.5" y="3.5" width="17" height="17" rx="2"/><path d="M3.5 9h17M9 9v11.5"/>'),
     "phone": P('<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>'),
     "save": P('<path d="M6 3.5h9l3.5 3.5v13H5.5v-16.5z"/><path d="M8.5 3.5v5h6v-5M8.5 20.5v-6h7v6"/>'),
     "sliders": P('<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>'),
     "tag": P('<path d="M3.5 12.5l8-8H20v8.5l-8 8-8.5-8.5z"/><circle cx="15.5" cy="8.5" r="1.5"/>'),
     "printer": P('<path d="M7 9V4h10v5"/><rect x="3.5" y="9" width="17" height="8" rx="2"/><path d="M7 14h10v6H7z"/>'),
    }
    CHEV_R = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 4l4 4-4 4"/></svg>'
    ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
    STAR = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.8l2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.2l-5.6 3 1.1-6.3L2.9 9.5l6.3-.9L12 2.8z"/></svg>'
    PROD = {"socks":"Apparel","mug":"Drinkware","pillow":"Home decor","wallart":"Wall art","photo":"Photo gifts","necklace":"Jewelry",
            "handbag":"Accessories","tote":"Bags & totes","drawstring":"Packaging","petbowl":"Pet products","phone":"Phone cases",
            "puzzle":"Toys & puzzles","pumpkin":"Seasonal","card":"Cards & prints"}

    h = d["hero"]
    stars5 = f'<span class="stars" role="img" aria-label="5 out of 5 stars" style="--fill:100%"><span class="stars__row stars__base" aria-hidden="true">{STAR*5}</span><span class="stars__fill" aria-hidden="true"><span class="stars__row">{STAR*5}</span></span></span>'
    proof = home[home.index('<a class="proof"'):home.index('</a>', home.index('<a class="proof"'))+4]

    def card(it, tag="li"):
        return f'<{tag} class="fcardx"><span class="ficon">{ICON[it["icon"]]}</span><h3>{E(it["title"])}</h3><p>{E(it["text"])}</p></{tag}>'

    rows = "\n".join(f"""        <div class="frow">
              <div class="frow__text">
                <h3 class="frow__title">{E(r["title"])}</h3>
                <p>{E(r["text"])}</p>
                <ul class="ticks">{''.join(f'<li>{E(p)}</li>' for p in r["points"])}</ul>
              </div>
              <div class="frow__vis"><div class="fvis">{UI[r["visual"]]}</div></div>
            </div>""" for r in d["details"])

    faqs = "\n".join(f"""          <li class="qa{' is-open' if k==0 else ''}">
                <h3><button class="qa__q" id="fq{k}" aria-expanded="{'true' if k==0 else 'false'}" aria-controls="fa{k}">{E(f["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
                <div class="qa__a" id="fa{k}" role="region" aria-labelledby="fq{k}"><div><p>{E(f["a"])}</p></div></div>
              </li>""" for k,f in enumerate(d["faqs"]))

    body = f"""<main>
      <!-- 1 · HERO -->
      <section class="fhero" aria-labelledby="f-title">
        <div class="container fhero__grid">
          <div class="fhero__text">
            <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a>{CHEV_R}<a href="#">Features</a>{CHEV_R}<span aria-current="page">{E(d["nav_label"])}</span></nav>
            <h1 class="fhero__title" id="f-title">{E(h["title"])}</h1>
            <p class="fhero__lead">{E(h["lead"])}</p>
            <div class="fhero__actions">{{{{BTN_PRIMARY:{h["primary_cta"]}}}}}{{{{BTN_SECONDARY:{h["secondary_cta"]}}}}}</div>
            {proof}
          </div>
          <div class="fhero__vis">
            <div class="hero__media has-ring"><span class="ring-glow" aria-hidden="true"><i></i></span><span class="ring" aria-hidden="true"></span>
              <div class="hero__screen"><img src="{{{{EDITOR}}}}" width="2240" height="1836" alt="{E(h["visual"]["alt"])}" decoding="async" fetchpriority="high"></div>
            </div>
          </div>
        </div>
      </section>

      <!-- 2 · BENEFITS -->
      <section class="fben" aria-label="Benefits">
        <div class="container"><ul class="fben__grid">{''.join(card(b) for b in d["benefits"])}</ul></div>
      </section>

      <!-- 3 · DETAILS + 4 · QUOTE (one tint band) -->
      <section class="fsec fsec--tint" aria-labelledby="f-details">
        <div class="container">
          <div class="fsec__head fsec__head--center"><h2 class="fsec__title" id="f-details">How it works</h2></div>
          <div class="frows">
    {rows}
          </div>
          <div class="fquote">
            <article class="story">
              {stars5}
              <p class="story__quote">{E(d["quote"]["text"])}</p>
              <div class="story__foot"><div class="story__who"><span class="story__avatar" aria-hidden="true">{E(d["quote"]["initials"])}</span><div><div class="story__name">{E(d["quote"]["name"])}</div><div class="story__where">{E(d["quote"]["location"])}</div></div></div><a class="story__link" href="#">See full case study {ARROW}</a></div>
            </article>
          </div>
        </div>
      </section>

      <!-- 5 · CAPABILITIES -->
      <section class="fsec" aria-labelledby="f-cap">
        <div class="container">
          <div class="fsec__head fsec__head--center"><h2 class="fsec__title" id="f-cap">Everything in the editor</h2></div>
          <ul class="fcap__grid">{''.join(card(c) for c in d["capabilities"])}</ul>
        </div>
      </section>

      <!-- 6 · WORKS WITH -->
      <section class="fsec fsec--tint" aria-labelledby="f-prod">
        <div class="container">
          <div class="fsec__head fsec__head--center"><h2 class="fsec__title" id="f-prod">Works with every product</h2></div>
          <ul class="fprod__grid">{''.join(f'<li class="fprod"><a href="#"><span class="fprod__img"><img src="{{{{IMG:products/{p}.webp}}}}" alt="" width="440" height="440" loading="lazy"></span>{E(PROD[p])}</a></li>' for p in d["products"])}</ul>
        </div>
      </section>

      <!-- 7 · FAQS -->
      <section class="faq" aria-labelledby="faq-title">
        <div class="container faq__grid">
          <div class="faq__intro">
            <h2 class="faq__title" id="faq-title">FAQs</h2>
            <p class="faq__lead">Common questions about the {E(d["nav_label"].lower())}.</p>
            <div class="faq__help"><p>Still have questions?</p>{{{{BTN_SECONDARY:Talk to our team}}}}</div>
          </div>
          <ul class="faq__list">
    {faqs}
          </ul>
        </div>
      </section>

      <!-- 8 · RELATED -->
      <section class="fsec fsec--tint frel" aria-labelledby="f-rel">
        <div class="container">
          <div class="fsec__head fsec__head--center"><h2 class="fsec__title" id="f-rel">Explore more features</h2></div>
          <ul class="frel__grid">{''.join(f'<li><a class="fcardx" href="{E(r["slug"])}.html"><span class="ficon">{ICON[r["icon"]]}</span><h3>{E(r["title"])}</h3><p>{E(r["text"])}</p><span class="more">Learn more {ARROW}</span></a></li>' for r in d["related"])}</ul>
        </div>
      </section>
    </main>"""

    head = home[:home.index("<main>")]
    head = head.replace("</style>", open(ROOT / "src" / "feature.css").read() + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(d["meta"]["title"])}</title>\n<meta name="description" content="{E(d["meta"]["description"])}">', head, count=1)
    tail = home[home.index("</main>") + len("</main>"):]
    return head + body + tail

