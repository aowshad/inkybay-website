"""Render site/brand-assets/ from src/brand-assets.json: the InkyBay logos, colours, typeface and usage guidelines for
partners, affiliates and press (structure after shopify.com/brand-assets, in our design system).

Sections: hero [white] (breadcrumb, two-tone H1, lead, Download brand kit + Read the guidelines, the agreement note, an
"On this page" pill row; a preview card with both lockups and the palette), Logos [tint], Colors [white, click to copy],
Typography [tint, a Poppins specimen and the type scale], Usage guidelines [white: clear space, minimum size, picking a
version, don'ts, writing our name, trademark use], then a help card and the shared CTA and footer.
Files live in src/assets/brand-kit/ (logos as SVG and 2048px PNG, the kit ZIP, colors.css and colors.json); Poppins is
self-hosted (src/assets/fonts/poppins-*-latin.woff2) and loaded on this page only. Styles in src/brand.css.
"""
import json, re
from render_feature import ROOT, E, CHEV_R, ICON

D = json.loads((ROOT / "src" / "brand-assets.json").read_text())
DL = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
      'aria-hidden="true"><path d="M8 2.5v8M4.5 7L8 10.5 11.5 7M3 13.5h10"/></svg>')
YES = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
       'aria-hidden="true"><path d="M3.5 8.3l3 3 6-6.6"/></svg>')
NO = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
      '<path d="M4.5 4.5l7 7M11.5 4.5l-7 7"/></svg>')


def img(file, ext="svg", cls="", w=149, h=40, alt=""):
    return (f'<img class="{cls}" src="{{{{IMG:brand-kit/{file}.{ext}}}}}" alt="{E(alt)}" width="{w}" height="{h}" '
            f'loading="lazy" decoding="async">')


def dl(path, label, name=None):
    """A download link for a file under src/assets/brand-kit/ (saved under its own name)."""
    name = name or path.rsplit("/", 1)[-1]
    return f'<a class="bdl" href="{{{{IMG:{path}}}}}" download="{E(name)}">{DL}<span>{E(label)}</span></a>'


def rgb(hexs):
    h = hexs.lstrip("#")
    return ", ".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def heading(t, id_):
    if isinstance(t, list):
        return f'<h2 class="fsec__title" id="{id_}"><span class="h-line">{E(t[0])}</span> <span class="h-line h-muted">{E(t[1])}</span></h2>'
    return f'<h2 class="fsec__title" id="{id_}">{E(t)}</h2>'


def render():
    h, lg, co, ty, us, hp = D["hero"], D["logos"], D["colors"], D["type"], D["usage"], D["help"]
    sw = "".join(f'<i style="background:{c["hex"]}"></i>' for c in co["items"])
    toc = "".join(f'<a class="btoc-pill" href="#{a}">{E(t)}</a>' for a, t in h["toc"])
    hero = f"""  <section class="fhero bhero" aria-labelledby="b-title">
    <div class="container fhero__grid">
      <div class="fhero__text">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(D["crumbs"][0])}</a>{CHEV_R}<a href="{{{{ROOT}}}}resources/">{E(D["crumbs"][1])}</a>{CHEV_R}<span aria-current="page">{E(D["crumbs"][2])}</span></nav>
        <h1 class="fhero__title" id="b-title">{E(h["title"])}</h1>
        <p class="fhero__lead">{E(h["lead"])}</p>
        <div class="fhero__actions"><a class="btn btn--primary" href="{{{{IMG:{h["kit"]}}}}}" download="inkybay-brand-kit.zip" aria-label="{E(h["primary"])}"><span class="btn__label" aria-hidden="true"><span data-text="{E(h["primary"])}">{E(h["primary"])}</span></span><span class="btn__icon" aria-hidden="true">{{{{BTN_ARROWS}}}}</span></a>{{{{BTN_SECONDARY:{h["secondary"]}|#usage}}}}</div>
        <p class="bhero__meta">{E(h["kit_meta"])}</p>
        <p class="bhero__note">{E(h["note"])}</p>
      </div>
      <div class="fhero__vis">
        <div class="bpreview" aria-hidden="true">
          <div class="bpreview__light">{img("inkybay-full-light-bg", cls="bpreview__logo")}</div>
          <div class="bpreview__dark">{img("inkybay-full-dark-bg", cls="bpreview__logo")}<span class="bpreview__sw">{sw}</span></div>
        </div>
      </div>
    </div>
    <div class="container"><nav class="btoc" aria-label="{E(h["toc_label"])}"><span class="btoc__label">{E(h["toc_label"])}</span>{toc}</nav></div>
  </section>"""

    cards = "".join(f"""<li class="blogo">
          <div class="blogo__stage blogo__stage--{l["stage"]}">{img(l["file"], cls="blogo__img blogo__img--" + ("icon" if l["w"] == l["h"] else "full"), w=l["w"], h=l["h"], alt=f'InkyBay {l["name"].lower()}, {l["variant"].lower()}')}</div>
          <div class="blogo__body">
            <h3 class="blogo__title">{E(l["name"])} <span class="blogo__variant">{E(l["variant"])}</span></h3>
            <p class="blogo__text">{E(l["text"])}</p>
            <div class="blogo__dl">{dl(f'brand-kit/{l["file"]}.svg', lg["svg"])}{dl(f'brand-kit/{l["file"]}.png', lg["png"])}</div>
          </div>
        </li>""" for l in lg["items"])
    logos = f"""  <section class="fsec fsec--tint" id="logos" aria-labelledby="b-logos">
    <div class="container">
      <div class="bhead-row"><div class="fsec__head bhead">{heading(lg["title"], "b-logos")}<p class="fsec__lead">{E(lg["lead"])}</p></div>{dl(h["kit"], lg["all"] + " (ZIP)", "inkybay-brand-kit.zip")}</div>
      <ul class="blogos">{cards}</ul>
    </div>
  </section>"""

    def swatch(c):
        return (f'<li><button class="bswatch cch__copy" type="button" data-copy="{c["hex"]}" data-copied="{E(co["copied"])}" aria-label="{E(co["copy"])} {E(c["name"])} {c["hex"]}">'
                f'<span class="bswatch__chip" style="background:{c["hex"]}"></span>'
                f'<span class="bswatch__body"><span class="bswatch__name">{E(c["name"])}</span><span class="bswatch__role">{E(c["role"])}</span>'
                f'<span class="bswatch__val">{c["hex"]}<span class="cch__copied" aria-live="polite"></span></span><span class="bswatch__val">RGB {rgb(c["hex"])}</span></span></button></li>')
    g = co["gradient"]
    grad = (f'<li class="bgrad"><button class="bswatch bswatch--grad cch__copy" type="button" data-copy="{E(g["css"])}" data-copied="{E(co["copied"])}" aria-label="{E(co["copy"])} {E(g["name"])}">'
            f'<span class="bswatch__chip" style="background:{g["css"]}"></span>'
            f'<span class="bswatch__body"><span class="bswatch__name">{E(g["name"])}</span><span class="bswatch__role">{E(g["role"])}</span>'
            f'<span class="bswatch__val">{" → ".join(g["stops"])}<span class="cch__copied" aria-live="polite"></span></span><span class="bswatch__val">45°, {g["stops"][0]} 0%, {g["stops"][1]} 58%</span></span></button></li>')
    colors = f"""  <section class="fsec" id="colors" aria-labelledby="b-colors">
    <div class="container">
      <div class="fsec__head bhead">{heading(co["title"], "b-colors")}<p class="fsec__lead">{E(co["lead"])}</p></div>
      <ul class="bswatches">{grad}{"".join(swatch(c) for c in co["items"])}</ul>
      <div class="bmore"><span class="bmore__label">{E(co["downloads_label"])}</span>{"".join(dl(p, n) for p, n in co["downloads"])}</div>
    </div>
  </section>"""

    weights = "".join(f'<li><span class="bpop" style="font-weight:{w}">Aa</span><span class="bweight">{E(n)} {w}</span></li>' for n, w in ty["weights"])
    rows = "".join(f'<li class="bscale__row"><span class="bscale__meta"><span class="bscale__name">{E(r["name"])}</span><span>{r["size"]} / {r["lh"]} · {r["weight"]}</span></span>'
                   f'<span class="bpop bscale__sample" aria-hidden="true" style="font-size:{r["size"]}px;line-height:{r["lh"]}px;font-weight:{r["weight"]}">{E(r["sample"])}</span></li>' for r in ty["scale"])
    typo = f"""  <section class="fsec fsec--tint" id="typography" aria-labelledby="b-type">
    <div class="container">
      <div class="fsec__head bhead">{heading(ty["title"], "b-type")}<p class="fsec__lead">{E(ty["lead"])}</p></div>
      <div class="btype">
        <div class="btype__spec">
          <span class="bpop btype__aa" aria-hidden="true">Aa</span>
          <div><p class="btype__family bpop">{E(ty["family"])}</p><p class="btype__role">{E(ty["role"])}</p></div>
          <p class="bpop btype__sample">{E(ty["sample"])}</p>
          <ul class="bweights">{weights}</ul>
          <a class="bdl" href="{E(ty["get_href"])}" target="_blank" rel="noopener">{E(ty["get"])}<span class="sr-only"> (opens in a new tab)</span></a>
        </div>
        <div class="btype__scale"><p class="bscale__label">{E(ty["scale_label"])}</p><ul class="bscale">{rows}</ul></div>
      </div>
    </div>
  </section>"""

    cl, mn, vs, dn, nm, ru = us["clear"], us["min"], us["versions"], us["donts"], us["name"], us["rules"]
    clear = f"""<div class="bguide">
        <div class="bguide__text"><h3 class="bguide__title">{E(cl["title"])}</h3><p>{E(cl["text"])}</p></div>
        <figure class="bclear" aria-hidden="true"><div class="bclear__box">{img("inkybay-full-light-bg", cls="bclear__logo")}<i class="bx bx--t">X</i><i class="bx bx--r">X</i><i class="bx bx--b">X</i><i class="bx bx--l">X</i></div></figure>
      </div>"""
    mins = "".join(f'<li class="bmin__item"><div class="bmin__stage">{img(m["file"], cls="", w=m["px"], h=round(m["px"] * (40 / 149 if m["px"] > 40 else 1)))}</div>'
                   f'<p class="bmin__name">{E(m["name"])}</p><p class="bmin__val"><span>{E(mn["digital"])}</span>{E(m["digital"])}</p><p class="bmin__val"><span>{E(mn["print"])}</span>{E(m["print"])}</p></li>' for m in mn["items"])
    minsize = f"""<div class="bguide">
        <div class="bguide__text"><h3 class="bguide__title">{E(mn["title"])}</h3><p>{E(mn["text"])}</p></div>
        <ul class="bmin">{mins}</ul>
      </div>"""
    vers = "".join(f'<li class="bver"><div class="bver__stage bver__stage--{v["stage"]}">{img(v["file"], cls="bver__img" + (" bver__img--icon" if "icon" in v["file"] else ""), w=40 if "icon" in v["file"] else 149, h=40)}</div>'
                   f'<p class="bver__title"><span class="byes">{YES}</span>{E(v["title"])}</p><p class="bver__text">{E(v["text"])}</p></li>' for v in vs["items"])
    donts = "".join(f'<li class="bdont"><div class="bdont__stage bdont__stage--{x["fx"]}" aria-hidden="true">'
                    f'{img("inkybay-full-light-bg" if x["fx"] not in ("contrast",) else "inkybay-full-light-bg", cls="bdont__img")}'
                    f'{"<span class=bdont__crowd>Free shipping on every order</span>" if x["fx"] == "crowd" else ""}</div>'
                    f'<p class="bdont__text"><span class="bno">{NO}<span class="sr-only">{E(dn["label"])}: </span></span>{E(x["text"])}</p></li>' for x in dn["items"])
    name = f"""<div class="bguide">
        <div class="bguide__text"><h3 class="bguide__title">{E(nm["title"])}</h3><p>{E(nm["text"])}</p></div>
        <div class="bname">
          <div class="bname__col bname__col--ok"><p class="bname__label"><span class="byes">{YES}</span>{E(nm["right_label"])}</p><ul>{"".join(f"<li>{E(w)}</li>" for w in nm["right"])}</ul></div>
          <div class="bname__col bname__col--no"><p class="bname__label"><span class="bno">{NO}</span>{E(nm["wrong_label"])}</p><ul>{"".join(f"<li>{E(w)}</li>" for w in nm["wrong"])}</ul></div>
        </div>
      </div>"""
    rules = "".join(f"<li>{E(r)}</li>" for r in ru["items"])
    usage = f"""  <section class="fsec" id="usage" aria-labelledby="b-usage">
    <div class="container">
      <div class="fsec__head bhead">{heading(us["title"], "b-usage")}<p class="fsec__lead">{E(us["lead"])}</p></div>
      {clear}
      {minsize}
      <div class="bguide bguide--stack"><h3 class="bguide__title">{E(vs["title"])}</h3><ul class="bvers">{vers}</ul></div>
      <div class="bguide bguide--stack"><h3 class="bguide__title">{E(dn["title"])}</h3><ul class="bdonts">{donts}</ul></div>
      {name}
      <div class="bguide">
        <div class="bguide__text"><h3 class="bguide__title">{E(ru["title"])}</h3></div>
        <ol class="brules">{rules}</ol>
      </div>
      <div class="bhelp">
        <div><h3 class="bhelp__title">{E(hp["title"])}</h3><p>{E(hp["text"])}</p></div>
        <div class="bhelp__actions">{{{{BTN_PRIMARY:{hp["email"]}|mailto:{hp["email"]}}}}}{{{{BTN_SECONDARY:{hp["contact"]}|contact/}}}}</div>
      </div>
    </div>
  </section>"""

    home = (ROOT / "src" / "template.html").read_text()
    head = home[:home.index("<main>")]
    head = head.replace("</style>", "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "brand.css")) + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(D["meta"]["title"])}</title>\n<meta name="description" content="{E(D["meta"]["description"])}">', head, count=1)
    body = "<main>\n" + "\n".join([hero, logos, colors, typo, usage]) + "\n</main>"
    return head + body + home[home.index("</main>") + len("</main>"):]
