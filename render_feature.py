"""Render a feature page from src/features/<slug>.json.

The page reuses the homepage shell (head, CSS, navbar, CTA, crowd marquee, footer and JS) from
src/template.html, so every feature page stays in sync with the homepage. Only the <main> differs.
"""
import json, html, re, pathlib

ROOT = pathlib.Path(__file__).parent
E = lambda s: html.escape(s, quote=True)

P = lambda d: f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{d}</svg>'
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
    "chat": P('<path d="M5 4.5h14v11H9.5L5 19.5v-15z"/><path d="M9 9h6M9 12h4"/>'),
    "box": P('<path d="M3.5 7.5L12 3l8.5 4.5v9L12 21l-8.5-4.5v-9z"/><path d="M3.5 7.5L12 12l8.5-4.5M12 12v9"/>'),
    "percent": P('<path d="M19 5L5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/>'),
    "shirt": P('<path d="M8.5 3.5L3.5 6.5l2 3.6 2-1V20.5h9V9.1l2 1 2-3.6-5-3c-.4 1.4-1.8 2.4-3.5 2.4S8.9 4.9 8.5 3.5z"/>'),
    "gem": P('<path d="M6.5 4h11L21 9l-9 11L3 9l3.5-5z"/><path d="M3 9h18M9.5 4L8 9l4 11 4-11-1.5-5"/>'),
    "trophy": P('<path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20.5h7M10 17h4v3.5h-4z"/>'),
    "home": P('<path d="M4 10.5L12 4l8 6.5V20H4v-9.5z"/><path d="M10 20v-5.5h4V20"/>'),
    "package": P('<path d="M3.5 7.5L12 3l8.5 4.5v9L12 21l-8.5-4.5v-9z"/><path d="M3.5 7.5L12 12l8.5-4.5M12 12v9M7.8 5.3l8.4 4.5"/>'),
    "gift": P('<rect x="3.5" y="8" width="17" height="4" rx="1"/><path d="M5 12v8.5h14V12M12 8v12.5M12 8S10.6 4 8.2 4.4 8.6 8 12 8zM12 8s1.4-4 3.8-3.6S15.4 8 12 8z"/>'),
    "bag": P('<path d="M5 8h14l-1 12.5H6L5 8z"/><path d="M9 10V6.5a3 3 0 0 1 6 0V10"/>'),
    "pen": P('<path d="M4 20l1-4.5L15.5 5a2.1 2.1 0 0 1 3 3L8 18.5 4 20z"/><path d="M13.5 7l3 3"/>'),
    "chart": P('<path d="M4 20h16M7 16.5v-4M12 16.5V8M17 16.5V5"/>'),
    "play": P('<circle cx="12" cy="12" r="8.5"/><path d="M10.2 8.8v6.4l5-3.2-5-3.2z"/>'),
    "handshake": P('<path d="M2.5 11.5L6 8l3 1 2.5-1.5L14 8l3.5 0 4 3.5"/><path d="M6 8l-3.5 3.5 5.6 5.6c.8.8 2 .8 2.8 0L16 12c.7-.7.7-1.8 0-2.5L14 8M9 14.5l2-2M11.5 17l2-2"/>'),
    "book": P('<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v15H6.5A1.5 1.5 0 0 0 5 19.5v-15z"/><path d="M5 19.5A1.5 1.5 0 0 0 6.5 21H19v-3M9 7h6"/>'),
}
CHEV_R = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 4l4 4-4 4"/></svg>'
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
STAR = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.8l2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.2l-5.6 3 1.1-6.3L2.9 9.5l6.3-.9L12 2.8z"/></svg>'
PROD = {k: v["label"] for k, v in json.loads((ROOT / "src" / "products.json").read_text()).items()}   # product labels (src/products.json)


def mini_uis(home):
    """Pull the homepage mini-UI snippets, in page order, so feature pages reuse them unchanged."""
    main = home[home.index("<main>"):home.index("</main>")]
    out, i = [], 0
    while (i := main.find('<div class="mui-stage"', i)) >= 0:
        depth, j = 0, i
        while True:
            o, c = main.find("<div", j), main.find("</div>", j)
            if o != -1 and o < c:
                depth += 1; j = o + 4
            else:
                depth -= 1; j = c + 6
                if depth == 0:
                    break
        out.append(main[i:j]); i = j
    assert len(out) == 15, len(out)
    names = ["setup", "design", "files", "options", "methods", "inventory", "quote", "addons", "tiers",
             "library", "templates", None, "sides", None, "grow"]
    stage = {n: s for n, s in zip(names, out) if n}
    # inner <div class="mui"> only, for layouts that place cards themselves
    card = {n: re.sub(r'^<div class="mui-stage" aria-hidden="true">', "", s)[:-len("</div>")] for n, s in stage.items()}
    return card


def heading(lines, tag="h2", cls="fsec__title", id_=""):
    first, second = lines
    return (f'<{tag} class="{cls}" id="{id_}"><span class="h-line">{E(first)}</span> '
            f'<span class="h-line h-muted">{E(second)}</span></{tag}>')


def chip(c, cls="chip"):
    """A chip is a string, or {"label": "Size", "roll": ["S", "M", "L", "XL"]} for a value that cycles."""
    if isinstance(c, dict):
        roll = "".join(f"<i>{E(x)}</i>" for x in c["roll"] + c["roll"][:1])
        return f'<span class="{cls}">{E(c["label"])} · <span class="roll"><span>{roll}</span></span></span>'
    return f'<span class="{cls}">{E(c)}</span>'


def visual(v, ui):
    """Three reusable layouts. Attachments sit inside the anchor (the main card's box), so they always
    overlap its edges; --d staggers their entrance."""
    glow = '<span class="fvis__glow" aria-hidden="true"><i></i><i></i><i></i></span>'
    if v["layout"] == "single":
        comp = (f'<div class="fcomp fcomp--single"><div class="fanchor">{ui[v["ui"]]}'
                f'<span class="att att--tl" style="--d:.35s">{chip(v["chip"])}</span>'
                f'<span class="att att--br" style="--d:.6s">{chip(v["badge"], "chip chip--brand")}</span></div></div>')
    elif v["layout"] == "product":
        tiles = "".join(f'<span class="tile" style="--k:{k}"><i style="--c:{c}"></i></span>' for k, c in enumerate(v["colors"]))
        comp = (f'<div class="fcomp fcomp--product"><div class="fanchor fanchor--photo">'
                f'<div class="fphoto"><img src="{{{{IMG:products/{v["image"]}.webp}}}}" alt="" width="400" height="400" loading="lazy"></div>'
                f'<span class="att att--tl" style="--d:.35s">{chip(v["chips"][0])}</span>'
                f'<span class="att att--r" style="--d:.55s"><span class="tiles">{tiles}</span></span>'
                f'<span class="att att--bl" style="--d:.75s">{chip(v["chips"][1])}</span></div></div>')
    else:  # stack
        comp = (f'<div class="fcomp fcomp--stack"><div class="fstack-back">{ui[v["back"]]}</div>'
                f'<div class="fanchor fstack-front">{ui[v["front"]]}'
                f'<span class="att att--tl" style="--d:.45s">{chip(v["badge"], "chip chip--brand")}</span></div></div>')
    return f'<div class="fvis" aria-hidden="true">{glow}{comp}</div>'


def hero_visual(h, ui):
    """Hero visual. {"layout": "showcase", "image": "<slug>", "ui": "<mini-ui>", "chips": [up to 2]} puts a product photo
    on a dark framed stage with one key mini UI and chips breaking its edges. Without a showcase (no hero.visual, or
    {"type": "image"}) the hero shows the editor screenshot with the comet ring."""
    v = h.get("visual") or {"type": "image"}
    if v.get("layout") != "showcase":
        return (f'<div class="hero__media has-ring"><span class="ring-glow" aria-hidden="true"><i></i></span><span class="ring" aria-hidden="true"></span>\n'
                f'          <div class="hero__screen"><img src="{{{{EDITOR}}}}" width="2240" height="1836" alt="{E(h["visual_alt"])}" decoding="async" fetchpriority="high"></div>\n'
                f'        </div>')
    assert len(v.get("chips", [])) <= 2, "showcase: up to 2 chips"
    chips = "".join(f'<span class="fshow__chip fshow__chip--{k + 1}" style="--d:{.9 + k * .25:.2f}s">{chip(c, "chip chip--brand" if k else "chip")}</span>'
                    for k, c in enumerate(v.get("chips", [])))
    return (f'<div class="fshow" aria-hidden="true"><div class="fshow__stage"></div>'
            f'<div class="fshow__photo"><img class="fshow__img" src="{{{{IMG:heroes/{v["image"]}.webp}}}}" alt="" width="1200" height="1200" decoding="async" fetchpriority="high"></div>'
            f'<div class="fshow__ui">{ui[v["ui"]]}</div>{chips}</div>')


def render(slug):
    d = json.loads((ROOT / "src" / "features" / f"{slug}.json").read_text())
    home = (ROOT / "src" / "template.html").read_text()
    ui = mini_uis(home)
    h = d["hero"]
    proof = home[home.index('<a class="proof"'):home.index("</a>", home.index('<a class="proof"')) + 4]
    stars5 = (f'<span class="stars" role="img" aria-label="5 out of 5 stars" style="--fill:100%"><span class="stars__row stars__base" aria-hidden="true">{STAR * 5}</span>'
              f'<span class="stars__fill" aria-hidden="true"><span class="stars__row">{STAR * 5}</span></span></span>')

    benefits = "".join(f'<li class="fben__item"><span class="fben__icon">{ICON[b["icon"]]}</span><h3>{E(b["title"])}</h3><p>{E(b["text"])}</p></li>' for b in d["benefits"])
    rows = "\n".join(f"""        <div class="frow">
          <div class="frow__text">
            <h3 class="frow__title">{E(r["title"])}</h3>
            <p>{E(r["text"])}</p>
            <ul class="ticks">{"".join(f"<li>{E(p)}</li>" for p in r["points"])}</ul>
          </div>
          <div class="frow__vis">{visual(r["visual"], ui)}</div>
        </div>""" for r in d["details"])
    caps = "".join(f'<li class="fcardx"><span class="ficon">{ICON[c["icon"]]}</span><h3>{E(c["title"])}</h3><p>{E(c["text"])}</p></li>' for c in d["capabilities"])
    card = lambda p: (f'<a class="pcard" href="#"><span class="pcard__img"><img src="{{{{IMG:products/{p}.webp}}}}" alt="" width="440" height="440" loading="lazy"></span>'
                      f'<span class="pcard__name">{E(PROD[p])}{ARROW}</span></a>')
    cols = [d["products"][i::3] for i in range(3)]          # round-robin into three columns
    vwall = "".join(f'<div class="vcol"><div class="vtrack">{"".join(card(p) for p in c)}</div></div>' for c in cols)
    faqs = "\n".join(f"""          <li class="qa{" is-open" if k == 0 else ""}">
            <h3><button class="qa__q" id="fq{k}" aria-expanded="{"true" if k == 0 else "false"}" aria-controls="fa{k}">{E(f["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
            <div class="qa__a" id="fa{k}" role="region" aria-labelledby="fq{k}"><div><p>{E(f["a"])}</p></div></div>
          </li>""" for k, f in enumerate(d["faqs"]))

    body = f"""<main>
  <!-- 1 · HERO -->
  <section class="fhero" aria-labelledby="f-title">
    <div class="container fhero__grid">
      <div class="fhero__text">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">Home</a>{CHEV_R}<a href="#">Features</a>{CHEV_R}<span aria-current="page">{E(d["nav_label"])}</span></nav>
        <h1 class="fhero__title" id="f-title">{E(h["title"])}</h1>
        <p class="fhero__lead">{E(h["lead"])}</p>
        <div class="fhero__actions">{{{{BTN_PRIMARY:{h["primary_cta"]}}}}}{{{{BTN_SECONDARY:{h["secondary_cta"]}}}}}</div>
        {proof}
      </div>
      <div class="fhero__vis">
        {hero_visual(h, ui)}
      </div>
    </div>
  </section>

  <!-- 2 · BENEFITS -->
  <section class="fben" aria-label="Benefits">
    <div class="container"><ul class="fben__grid">{benefits}</ul></div>
  </section>

  <!-- 3 · HOW IT WORKS (zig-zag) + 4 · QUOTE, one dark band -->
  <section class="fsec fsec--dark" aria-labelledby="f-details">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading(d["details_heading"], id_="f-details")}</div>
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
  <section class="fsec fsec--tint" aria-labelledby="f-cap">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading(d["capabilities_heading"], id_="f-cap")}</div>
      <ul class="fcap__grid">{caps}</ul>
    </div>
  </section>

  <!-- 6 · WORKS WITH (vertical product wall; any number of products) -->
  <section class="fsec fsec--wall" aria-labelledby="f-prod">
    <div class="container fprod">
      <div class="fprod__text">
        <div class="fsec__head">{heading(d["products_heading"], id_="f-prod")}<p class="fsec__lead">{E(d["products_lead"])}</p></div>
        {{{{BTN_SECONDARY:Browse industries}}}}
      </div>
      <div class="vwall" aria-label="Products">{vwall}</div>
    </div>
  </section>

  <!-- 7 · FAQS -->
  <section class="faq faq--tint" aria-labelledby="faq-title">
    <div class="container faq__grid">
      <div class="faq__intro">
        <h2 class="faq__title" id="faq-title">FAQs</h2>
        <p class="faq__lead">Common questions about {E(d["nav_label"].lower())}.</p>
        <div class="faq__help"><p>Still have questions?</p>{{{{BTN_SECONDARY:Talk to our team}}}}</div>
      </div>
      <ul class="faq__list">
{faqs}
      </ul>
    </div>
  </section>
</main>"""

    head = home[:home.index("<main>")]
    head = head.replace("</style>", (ROOT / "src" / "feature.css").read_text() + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(d["meta"]["title"])}</title>\n<meta name="description" content="{E(d["meta"]["description"])}">', head, count=1)
    tail = home[home.index("</main>") + len("</main>"):]
    return head + body + tail
