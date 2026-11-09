"""Render the three overview pages from src/hubs.json (copy) and the data the menus already use:
site/features/ (every feature in src/features/_index.json), site/industries/ (every industry in
src/industries/_index.json that has a page) and site/resources/ (the Resources menu groups in src/nav.json).

Each page: a hero (breadcrumb, two-tone H1, lead; Features and Industries add Start free trial and Try live demo),
then on tint the cards. Features: the feature's hero photo on the warm dark stage, title, short line, Learn more.
Industries: up to three of the industry's products on a light stage, title, short line, Learn more. Resources: one
group per menu group, cards with the menu icon, title and short line (external items open in a new tab, Live chat
keeps its data-action). Styles in src/hubs.css; the shell, CTA and footer come from the homepage.
"""
import json, re
from render_feature import ROOT, E, CHEV_R, ICON

ARROW = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
         'aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')
EXT = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
       'aria-hidden="true"><path d="M6 4h6v6M12 4l-7.5 7.5"/></svg>')


def load(name):
    return json.loads((ROOT / "src" / name).read_text())


def page(body, meta):
    home = (ROOT / "src" / "template.html").read_text()
    head = home[:home.index("<main>")]
    head = head.replace("</style>", "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "hubs.css")) + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(meta["title"])}</title>\n<meta name="description" content="{E(meta["description"])}">', head, count=1)
    return head + body + home[home.index("</main>") + len("</main>"):]


def hero(key, h, L, actions=True):
    btns = ('<div class="fhero__actions">{{BTN_PRIMARY:Start free trial|{{LINK:app_store}}}}'
            '{{BTN_SECONDARY:Try live demo|{{LINK:demo_store}}}}</div>') if actions else ""
    return f"""  <section class="hubhero" aria-labelledby="hub-title">
    <div class="container hubhero__intro">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(L["home"])}</a>{CHEV_R}<span aria-current="page">{E(h["crumb"])}</span></nav>
      <h1 class="hubhero__title" id="hub-title"><span class="h-line">{E(h["title"][0])}</span> <span class="h-line h-muted">{E(h["title"][1])}</span></h1>
      <p class="hubhero__lead">{E(h["lead"])}</p>
      {btns}
    </div>
  </section>"""


def card(href, title, text, media, L, cls=""):
    return f"""<li class="hubcard{cls}">
          <div class="hubcard__media" aria-hidden="true">{media}</div>
          <div class="hubcard__body">
            <h3 class="hubcard__title"><a href="{href}">{E(title)}</a></h3>
            <p class="hubcard__text">{E(text)}</p>
            <span class="hubcard__more" aria-hidden="true">{E(L["learn_more"])}{ARROW}</span>
          </div>
        </li>"""


def grid(h, cards, cls=""):
    return f"""  <section class="fsec fsec--tint" aria-labelledby="hub-list">
    <div class="container">
      <h2 class="sr-only" id="hub-list">{E(h["list_title"])}</h2>
      <ul class="hubgrid{cls}">
        {"".join(cards)}
      </ul>
    </div>
  </section>"""


def features():
    d, L = load("hubs.json"), load("hubs.json")["labels"]
    h = d["features"]
    cards = [card(f'{f["slug"]}/', f["title"], f["short"],
                  f'<img class="hubcard__photo" src="{{{{IMG:heroes/{f["slug"]}.webp}}}}" alt="" width="600" height="600" loading="lazy" decoding="async">', L, " hubcard--dark")
             for f in load("features/_index.json")["features"]]
    return page(f"<main>\n{hero('features', h, L)}\n{grid(h, cards)}\n</main>", h["meta"])


def industries():
    d, L = load("hubs.json"), load("hubs.json")["labels"]
    h = d["industries"]
    prods = load("products.json")
    cards = []
    for ind in load("industries/_index.json")["industries"]:
        if not (ROOT / "src" / "industries" / f'{ind["slug"]}.json').exists(): continue
        names = [n for n, p in prods.items() if p.get("industry") == ind["slug"]][:3]
        imgs = "".join(f'<img class="hubcard__prod" src="{{{{IMG:products/{n}.webp}}}}" alt="" width="600" height="600" loading="lazy" decoding="async">' for n in names)
        cards.append(card(f'{ind["slug"]}/', ind["title"], ind["short"], f'<span class="hubcard__prods" data-n="{len(names)}">{imgs}</span>', L))
    return page(f"<main>\n{hero('industries', h, L)}\n{grid(h, cards, ' hubgrid--4')}\n</main>", h["meta"])


def resources():
    d, L = load("hubs.json"), load("hubs.json")["labels"]
    h = d["resources"]
    menu = next(m for m in load("nav.json")["menus"] if m["id"] == "resources")
    groups = []
    for k, g in enumerate(menu["groups"]):
        items = []
        for i in g["items"]:
            ext = i.get("external")
            href = i["href"] if "href" in i else f'{i["slug"]}/'
            if not href.startswith(("#", "http")): href = "{{ROOT}}" + href
            attrs = (' target="_blank" rel="noopener"' if ext else "") + (f' data-action="{E(i["action"])}"' if i.get("action") else "")
            sr = f'<span class="sr-only"> ({E(L["new_tab"])})</span>' if ext else ""
            items.append(f"""<li class="hubres">
            <span class="hubres__icon" aria-hidden="true">{ICON[i["icon"]]}</span>
            <h3 class="hubres__title"><a href="{E(href)}"{attrs}>{E(i["title"])}{sr}</a></h3>
            <p class="hubres__text">{E(i["short"])}</p>
            <span class="hubres__go" aria-hidden="true">{EXT if ext else ARROW}</span>
          </li>""")
        groups.append(f"""<div class="hubgroup">
        <h2 class="hubgroup__title" id="hub-g{k}">{E(g["title"])}</h2>
        <ul class="hubres__list" aria-labelledby="hub-g{k}">
          {"".join(items)}
        </ul>
      </div>""")
    body = f"""<main>
{hero('resources', h, L, actions=False)}
  <section class="fsec fsec--tint">
    <div class="container hubgroups">
      {"".join(groups)}
    </div>
  </section>
</main>"""
    return page(body, h["meta"])
