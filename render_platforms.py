"""Render the platform pages from src/platforms.json: site/platforms/ (the overview) and site/platforms/<slug>/ (one per
platform). Logos are src/assets/platforms/<slug>.svg, one colour (currentColor), inlined so they take the brand colour
on white tiles and the ink colour in menus.

A live platform's page: hero (breadcrumb, logo lockup, H1, lead, Install on <name> + Try live demo, proof pill on
Shopify only, the hero video in the comet ring) [white], four steps [tint], every feature [white], what you need
[dark], industries [white], FAQs [tint]. A coming-soon platform: hero with a Coming soon badge and Join the waitlist,
the waitlist form [tint], every feature [white], FAQs [tint]. Styles in src/platforms.css (plus feature, hubs, forms
and partners CSS). The shell, CTA and footer come from the homepage.
"""
import json, re
from render_feature import ROOT, E, CHEV_R, ICON
from render_hubs import card as hub_card, ARROW

D = json.loads((ROOT / "src" / "platforms.json").read_text())
L = D["labels"]
PLATFORMS = D["platforms"]
assert all(p["status"] in ("live", "coming-soon") for p in PLATFORMS), "platforms.json: status is live or coming-soon"


def logo(slug, cls="plogo"):
    """The platform's logo as inline SVG (decorative: the name is always written next to it)."""
    svg = (ROOT / "src" / "assets" / "platforms" / f"{slug}.svg").read_text().strip()
    return re.sub(r'\s(role|aria-label)="[^"]*"', "", svg).replace("<svg ", f'<svg class="{cls}" aria-hidden="true" focusable="false" ', 1)


for _p in PLATFORMS:                                   # menu icons: the logo in one colour, like the other menu icons
    ICON["pl-" + _p["slug"]] = logo(_p["slug"], "plogo plogo--" + _p["slug"])


def nav_items():
    """The Resources menu's Platforms group (nav.json: {"title": "Platforms", "items_from": "platforms"})."""
    return [{"title": p["name"], "short": p["short"], "icon": "pl-" + p["slug"], "href": f'platforms/{p["slug"]}/',
             **({"badge": L["coming_soon"]} if p["status"] != "live" else {})} for p in PLATFORMS]


def group_items(g):
    """A nav.json group's items, expanding "items_from": "platforms"."""
    return nav_items() if g.get("items_from") == "platforms" else g["items"]


def fill(s, p):
    return s.replace("{name}", p["name"])


def tile(p, cls=""):
    return f'<span class="pltile{cls}" style="--pc:{p["color"]}">{logo(p["slug"])}</span>'


def badge(p):
    return f'<span class="plbadge">{E(L["coming_soon"])}</span>' if p["status"] != "live" else ""


def page(body, meta):
    home = (ROOT / "src" / "template.html").read_text()
    head = home[:home.index("<main>")]
    css = "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "hubs.css", "forms.css", "partners.css", "platforms.css"))
    head = head.replace("</style>", css + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(meta["title"])}</title>\n<meta name="description" content="{E(meta["description"])}">', head, count=1)
    return head + body + home[home.index("</main>") + len("</main>"):]


def heading(lines, id_):
    return (f'<h2 class="fsec__title" id="{id_}"><span class="h-line">{E(lines[0])}</span> '
            f'<span class="h-line h-muted">{E(lines[1])}</span></h2>')


def hero_video(home):
    """The homepage hero video in its comet-ring frame, with paths from the site root."""
    a = home.index('<div class="hero__media has-ring">')
    b = home.index("</button>", a); b = home.index("</div>", b) + 6; b = home.index("</div>", b) + 6
    return home[a:b].replace('"assets/video/', '"{{ROOT}}assets/video/')


def faqs(items):
    return "\n".join(f"""          <li class="qa{" is-open" if k == 0 else ""}">
            <h3><button class="qa__q" id="fq{k}" aria-expanded="{"true" if k == 0 else "false"}" aria-controls="fa{k}">{E(f["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
            <div class="qa__a" id="fa{k}" role="region" aria-labelledby="fq{k}"><div><p>{E(f["a"])}</p></div></div>
          </li>""" for k, f in enumerate(items))


def features_section(p):
    feats = json.loads((ROOT / "src" / "features" / "_index.json").read_text())["features"]
    hl = {"learn_more": L["learn_more"]}
    cards = [hub_card(f'{{{{ROOT}}}}features/{f["slug"]}/', f["title"], f["short"],
                      f'<img class="hubcard__photo" src="{{{{IMG:heroes/{f["slug"]}.webp}}}}" alt="" width="600" height="600" loading="lazy" decoding="async">', hl, " hubcard--dark")
             for f in feats]
    return f"""  <section class="fsec" aria-labelledby="pl-feat">
    <div class="container">
      <div class="fsec__head">{heading([fill(x, p) for x in L["features_heading"]], "pl-feat")}<p class="fsec__lead">{E(L["features_lead"])}</p></div>
      <ul class="hubgrid">
        {"".join(cards)}
      </ul>
    </div>
  </section>"""


def waitlist(p):
    w = D["waitlist"]; fl = w["fields"]
    err = lambda k: f'<span class="field__err" id="wl-{k}-err" aria-live="polite"></span>'
    req = lambda k: f'data-err="{E(fl[k]["error"])}" aria-describedby="wl-{k}-err"'
    others = "".join(f'<li><a class="plmini" href="{{{{ROOT}}}}platforms/{o["slug"]}/">{tile(o, " pltile--sm")}<span>{E(o["name"])}</span></a></li>'
                     for o in PLATFORMS if o["status"] == "live")
    return f"""  <section class="fsec fsec--tint pjoin" id="waitlist" aria-labelledby="pl-wait">
    <div class="container pjoin__grid">
      <div class="pjoin__intro">
        <h2 class="fsec__title" id="pl-wait">{E(w["heading"])}</h2>
        <p class="fsec__lead">{E(w["lead"])}</p>
        <p class="plothers__label">{E(L["other_platforms"])}</p>
        <ul class="plothers">{others}</ul>
      </div>
      <div class="pjoin__card">
        <form class="form" data-form="waitlist" data-endpoint="{{{{FORM_ENDPOINT}}}}" method="post" novalidate>
          <input type="hidden" name="form" value="waitlist"><input type="hidden" name="topic" value="{E(w["topic"])}">
          <div class="form__row">
            <label class="field"><span class="field__label">{E(fl["name"]["label"])}</span><input name="name" type="text" autocomplete="name" placeholder="{E(fl["name"]["placeholder"])}" required {req("name")}>{err("name")}</label>
            <label class="field"><span class="field__label">{E(fl["email"]["label"])}</span><input name="email" type="email" inputmode="email" autocomplete="email" placeholder="{E(fl["email"]["placeholder"])}" required {req("email")}>{err("email")}</label>
          </div>
          <div class="form__one">
            <label class="field"><span class="field__label">{E(fl["store"]["label"])} <span class="field__opt">({E(w["optional"])})</span></span><span class="field__prefix"><span aria-hidden="true">https://</span><input name="store" type="text" inputmode="url" autocomplete="url" placeholder="{E(fl["store"]["placeholder"])}" data-url {req("store")}></span>{err("store")}</label>
          </div>
          <div class="form__hp" aria-hidden="true"><label>Leave this empty<input name="_gotcha" type="text" tabindex="-1" autocomplete="off"></label></div>
          <label class="field field--check"><input name="consent" type="checkbox" required {req("consent")}><span>{E(fl["consent"]["label"])} <a href="{{{{ROOT}}}}privacy-policy/">{E(fl["consent"]["link"])}</a></span>{err("consent")}</label>
          <div class="form__foot"><button class="btn btn--primary form__submit" type="submit" data-sending="{E(w["sending"])}"><span class="btn__label" aria-hidden="true"><span data-text="{E(w["submit"])}">{E(w["submit"])}</span></span><span class="btn__icon" aria-hidden="true">{{{{BTN_ARROWS}}}}</span><span class="sr-only">{E(w["submit"])}</span></button>
            <p class="form__status" role="status" aria-live="polite" data-ok="{E(w["success"])}" data-fail="{E(w["error"])}" data-off="{E(w["not_connected"])}" data-fail-email="{E(w["fail_email"])}"></p></div>
        </form>
      </div>
    </div>
  </section>"""


def render(slug):
    p = next(x for x in PLATFORMS if x["slug"] == slug)
    home = (ROOT / "src" / "template.html").read_text()
    live = p["status"] == "live"
    if live:
        assert p["install"], f"platforms.json: {slug} is live but has no install link"
        acts = (f'{{{{BTN_PRIMARY:{fill(L["install"], p)}|{p["install"]}}}}}'
                f'{{{{BTN_SECONDARY:{L["demo"]}|{p["demo"]}}}}}')
    else:
        acts = f'{{{{BTN_PRIMARY:{L["waitlist_cta"]}|#waitlist}}}}{{{{BTN_SECONDARY:{L["demo"]}|{p["demo"]}}}}}'
    proof = ""
    if p.get("rating"):
        a = home.index('<a class="proof"'); proof = home[a:home.index("</a>", a) + 4]
    hero = f"""  <section class="fhero plhero" aria-labelledby="pl-title">
    <div class="container fhero__grid">
      <div class="fhero__text">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(L["home"])}</a>{CHEV_R}<a href="{{{{ROOT}}}}platforms/">{E(L["crumb"])}</a>{CHEV_R}<span aria-current="page">{E(p["name"])}</span></nav>
        <div class="pllock" aria-hidden="true"><span class="pllock__mark">{{{{LOGO_MARK}}}}</span><span class="pllock__link"></span>{tile(p)}</div>
        {badge(p)}
        <h1 class="fhero__title" id="pl-title">Product customizer for {E(p["name"])}</h1>
        <p class="fhero__lead">{E(p["lead"])}</p>
        <div class="fhero__actions">{acts}</div>
        {proof}
      </div>
      <div class="fhero__vis">
        {hero_video(home)}
      </div>
    </div>
  </section>"""
    secs = [hero]
    if live:
        steps = "".join(f'<li class="fcardx"><span class="ficon">{ICON[s["icon"]]}</span><span class="plstep__num">{k + 1:02d}</span><h3>{E(s["title"])}</h3><p>{E(s["text"])}</p></li>'
                        for k, s in enumerate(p["steps"]))
        secs.append(f"""  <section class="fsec fsec--tint" aria-labelledby="pl-steps">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading([fill(x, p) for x in L["steps_heading"]], "pl-steps")}</div>
      <ol class="fcap__grid plsteps">{steps}</ol>
    </div>
  </section>""")
    else:
        secs.append(waitlist(p))
    secs.append(features_section(p))
    if live:
        req = "".join(f'<li class="fben__item"><span class="fben__icon">{ICON[r["icon"]]}</span><h3>{E(r["title"])}</h3><p>{E(r["text"])}</p></li>' for r in p["requirements"])
        inds = json.loads((ROOT / "src" / "industries" / "_index.json").read_text())["industries"]
        pills = "".join(f'<li><a class="plind" href="{{{{ROOT}}}}industries/{i["slug"]}/"><span class="plind__icon">{ICON[i["icon"]]}</span>{E(i["title"])}</a></li>'
                        for i in inds if (ROOT / "src" / "industries" / f'{i["slug"]}.json').exists())
        secs.append(f"""  <section class="fsec fsec--dark" aria-labelledby="pl-req">
    <div class="container">
      <div class="fsec__head">{heading(L["req_heading"], "pl-req")}</div>
      <ul class="fben__grid plreq">{req}</ul>
    </div>
  </section>
  <section class="fsec plinds" aria-labelledby="pl-ind">
    <div class="container">
      <h2 class="plinds__title" id="pl-ind">{E(L["industries_heading"])}</h2>
      <ul class="plinds__list">{pills}</ul>
    </div>
  </section>""")
    secs.append(f"""  <section class="faq faq--tint" aria-labelledby="faq-title">
    <div class="container faq__grid">
      <div class="faq__intro">
        <h2 class="faq__title" id="faq-title">FAQs</h2>
        <p class="faq__lead">{E(fill(L["faqs_lead"], p))}</p>
        <div class="faq__help"><p>{E(L["still"])}</p>{{{{BTN_SECONDARY:{L["talk"]}|contact/}}}}</div>
      </div>
      <ul class="faq__list">
{faqs(p["faqs"])}
      </ul>
    </div>
  </section>""")
    out = page("<main>\n" + "\n".join(secs) + "\n</main>", p["meta"])
    shop = "{{BTN_PRIMARY:Install on Shopify|{{LINK:app_store}}}}"      # the shared CTA installs this page's platform
    assert shop in out, "template CTA changed: update render_platforms.render"
    mine = (f'{{{{BTN_PRIMARY:{fill(L["install"], p)}|{p["install"]}}}}}' if live else f'{{{{BTN_PRIMARY:{L["waitlist_cta"]}|#waitlist}}}}')
    return out.replace(shop, mine)


def render_index():
    x = D["index"]
    cards = "".join(f"""<li class="hubcard plcard">
          <div class="hubcard__media plcard__media" aria-hidden="true">{tile(p, " pltile--lg")}</div>
          <div class="hubcard__body">
            <h3 class="hubcard__title"><a href="{p["slug"]}/">{E(p["name"])}</a>{badge(p)}</h3>
            <p class="hubcard__text">{E(p["short"])}</p>
            <span class="hubcard__more" aria-hidden="true">{E(L["learn_more"])}{ARROW}</span>
          </div>
        </li>""" for p in PLATFORMS)
    body = f"""<main>
  <section class="hubhero" aria-labelledby="hub-title">
    <div class="container hubhero__intro">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(L["home"])}</a>{CHEV_R}<span aria-current="page">{E(L["crumb"])}</span></nav>
      <h1 class="hubhero__title" id="hub-title"><span class="h-line">{E(x["title"][0])}</span> <span class="h-line h-muted">{E(x["title"][1])}</span></h1>
      <p class="hubhero__lead">{E(x["lead"])}</p>
    </div>
  </section>
  <section class="fsec fsec--tint" aria-labelledby="hub-list">
    <div class="container">
      <h2 class="sr-only" id="hub-list">{E(L["crumb"])}</h2>
      <ul class="hubgrid hubgrid--4">
        {cards}
      </ul>
    </div>
  </section>
</main>"""
    return page(body, x["meta"])


def bridge(root):
    """The homepage integrations section ({{INTEGRATIONS}}): the platforms on white tiles either side of the InkyBay
    hub, each joined to it by a wire in its own colour (template.html: .bridge CSS and JS). Every tile links to its
    platform page. The markup is the final state (wires drawn, logos in colour); the JS arms it and connects the live
    platforms one by one. A coming-soon platform keeps a dashed wire and a Coming soon chip."""
    h = D["home"]
    half = (len(PLATFORMS) + 1) // 2
    def tile(p):
        soon = p["status"] != "live"
        state = L["coming_soon"] if soon else L["live"]
        chip = f'<span class="bridge__soon">{E(L["coming_soon"])}</span>' if soon else ""
        return (f'<li><a class="bridge__tile" href="{root}platforms/{p["slug"]}/" data-slug="{p["slug"]}" data-status="{p["status"]}" '
                f'style="--pc:{p["color"]};--pcd:{p["color_dark"]}"><span class="bridge__box">{logo(p["slug"])}</span>'
                f'<span class="bridge__name">{E(p["name"])}<span class="sr-only">, {E(state.lower())}</span></span>{chip}</a></li>')
    grads = "".join(f'<linearGradient id="bw-{p["slug"]}" gradientUnits="userSpaceOnUse"><stop offset="0" class="bridge__s0" style="--pc:{p["color"]};--pcd:{p["color_dark"]}"/>'
                    f'<stop offset="1" class="bridge__s1"/></linearGradient>' for p in PLATFORMS)
    wires = "".join(f'<g class="bridge__g" data-slug="{p["slug"]}" data-status="{p["status"]}" style="--pc:{p["color"]};--pcd:{p["color_dark"]}">'
                    f'<path class="bridge__base"/><path class="bridge__wire" pathLength="1" stroke="url(#bw-{p["slug"]})"/>'
                    f'<path class="bridge__comet" pathLength="1" stroke="url(#bw-{p["slug"]})" filter="url(#bridge-glow)"/></g>' for p in PLATFORMS)
    return f"""<div class="bridge" data-bridge>
        <svg class="bridge__wires" aria-hidden="true" focusable="false"><defs>{grads}<filter id="bridge-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>{wires}</svg>
        <ul class="bridge__side">{"".join(tile(p) for p in PLATFORMS[:half])}</ul>
        <div class="bridge__hub" aria-hidden="true"><span class="bridge__ring"></span><span class="bridge__pulse"></span><span class="bridge__core">{{{{LOGO_MARK}}}}</span></div>
        <ul class="bridge__side bridge__side--r">{"".join(tile(p) for p in PLATFORMS[half:])}</ul>
      </div>"""


def home_section():
    h = D["home"]
    return f"""<!-- ===== SECTION 08a · PLATFORMS (src/platforms.json, render_platforms.bridge) ===== -->
  <section class="integ" aria-labelledby="integ-title">
    <div class="container">
      <div class="integ__head">
        <h2 class="integ__title" id="integ-title"><span class="h-line h-inline">{E(h["title"][0])}</span> <span class="h-line h-inline h-muted">{E(h["title"][1])}</span></h2>
        <p class="integ__lead">{E(h["lead"])}</p>
      </div>
      {{{{INTEGRATIONS}}}}
      <div class="integ__foot">{{{{BTN_SECONDARY:{h["cta"]}|platforms/}}}}</div>
    </div>
  </section>"""
