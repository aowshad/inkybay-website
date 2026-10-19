"""Render the case studies from src/case-studies.json: the list (site/resources/case-studies/) and one story per
merchant (site/resources/case-studies/<slug>/).

The stories are real InkyBay merchants (from the customer stories on productsdesigner.com/clients and the Figma
design). Images live in src/assets/cases/<slug>/ (logo.webp on a white frame, body images at their own ratio).
List: hero (breadcrumb, two-tone H1, lead), then on tint a filter bar (search, Industry, Region, Clear filters, the
count) over 3-up cards (logo frame, location and industry, brand, one line, Read story / Visit store).
Story: breadcrumb, H1, lead, then the body (h2, paragraphs, checklists, images, quotes) beside a sticky sidebar
(logo, brand, industry, platform, location, products, app, Visit store); then three related stories.
A story: {"slug", "brand", "store", "country", "region", "industry", "products": [...], "summary", "title", "lead",
"body": [{"h"} | {"h3"} | {"p"} | {"ul": [...]} | {"img", "alt", "size": [w, h]} | {"quote", "by"?}]}; links in "p" and "ul"
are Markdown [text](url), bold is **text**. The build stops on an unknown industry or region, a duplicate slug or a missing image.
"""
import json, re, sys
from render_feature import ROOT, E, CHEV_R

ARROW = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
         'aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')
EXT = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
       'aria-hidden="true"><path d="M6 4h6v6M12 4l-7.5 7.5"/></svg>')
PIN = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
       'aria-hidden="true"><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/></svg>')
SEARCH = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">'
          '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>')
CHECK = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
         'aria-hidden="true"><path d="M3.5 8.5l3 3 6-7"/></svg>')
CHEV_D = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
          'aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>')


def data():
    d = json.loads((ROOT / "src" / "case-studies.json").read_text())
    ind = {i["slug"]: i["name"] for i in d["industries"]}
    reg = {r["slug"]: r["name"] for r in d["regions"]}
    seen = set()
    for c in d["cases"]:
        if c["slug"] in seen: sys.exit(f"src/case-studies.json: two stories share the slug '{c['slug']}'")
        seen.add(c["slug"])
        if c["industry"] not in ind: sys.exit(f"src/case-studies.json: '{c['brand']}' has unknown industry '{c['industry']}'")
        if c["region"] not in reg: sys.exit(f"src/case-studies.json: '{c['brand']}' has unknown region '{c['region']}'")
        imgs = [f'cases/{c["slug"]}/logo.webp'] + [b["img"] for b in c["body"] if "img" in b]
        for p in imgs:
            if not (ROOT / "src" / "assets" / p).exists(): sys.exit(f"src/case-studies.json: '{c['brand']}' needs src/assets/{p}")
    return d, ind, reg


def md(s):
    """Escape, then turn Markdown links into real ones (external links open in a new tab)."""
    def link(m):
        t, u = m.group(1), m.group(2)
        ext = u.startswith("http")
        return f'<a href="{u}"' + (' target="_blank" rel="noopener"' if ext else "") + f">{t}</a>"
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", E(s))
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def page(body, title, desc):
    home = (ROOT / "src" / "template.html").read_text()
    head = home[:home.index("<main>")]
    head = head.replace("</style>", "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "cases.css")) + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(title)}</title>\n<meta name="description" content="{E(desc)}">', head, count=1)
    return head + body + home[home.index("</main>") + len("</main>"):]


def card(c, L, ind, href):
    """One story card; href is the story's URL relative to the page."""
    return f"""<li class="cscard" data-industry="{c["industry"]}" data-region="{c["region"]}" data-name="{E(c["brand"].lower())}">
          <a class="cscard__logo" href="{href}" tabindex="-1" aria-hidden="true"><img src="{{{{IMG:cases/{c["slug"]}/logo.webp}}}}" alt="" loading="lazy" decoding="async"></a>
          <div class="cscard__meta"><span class="cscard__loc">{PIN}{E(c["country"])}</span><span class="cscard__ind">{E(ind[c["industry"]])}</span></div>
          <h3 class="cscard__title"><a href="{href}">{E(c["brand"])}</a></h3>
          <p class="cscard__text">{E(c["summary"])}</p>
          <div class="cscard__actions">
            <a class="cscard__more" href="{href}">{E(L["read"])}<span class="sr-only">: {E(c["brand"])}</span>{ARROW}</a>
            <a class="cscard__store" href="{E(c["store"])}" target="_blank" rel="noopener">{E(L["visit"])}<span class="sr-only"> {E(c["brand"])} ({E(L["new_tab"])})</span>{EXT}</a>
          </div>
        </li>"""


def render():
    d, ind, reg = data()
    L, H, cases = d["labels"], d["hero"], d["cases"]
    used_i = [s for s in ind if any(c["industry"] == s for c in cases)]
    used_r = [s for s in reg if any(c["region"] == s for c in cases)]
    opt = lambda items, names: "".join(f'<option value="{s}">{E(names[s])}</option>' for s in items)
    count = L["count"].replace("{n}", f'<span data-cs-n>{len(cases)}</span>').replace("{total}", str(len(cases)))
    body = f"""<main>
  <section class="cshero" aria-labelledby="cs-title">
    <div class="container">
      <div class="cshero__intro">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(L["home"])}</a>{CHEV_R}<span>{E(L["resources"])}</span>{CHEV_R}<span aria-current="page">{E(L["crumb"])}</span></nav>
        <h1 class="cshero__title" id="cs-title"><span class="h-line">{E(H["title"][0])}</span> <span class="h-line h-muted">{E(H["title"][1])}</span></h1>
        <p class="cshero__lead">{E(H["lead"])}</p>
      </div>
    </div>
  </section>
  <section class="fsec fsec--tint cslib" aria-labelledby="cs-all">
    <div class="container">
      <h2 class="sr-only" id="cs-all">{E(L["all"])}</h2>
      <form class="csbar" role="search" data-cs-filter>
        <label class="csbar__sel"><span class="sr-only">{E(L["industry"])}</span><select name="industry"><option value="">{E(L["industry_all"])}</option>{opt(used_i, ind)}</select>{CHEV_D}</label>
        <label class="csbar__sel"><span class="sr-only">{E(L["region"])}</span><select name="region"><option value="">{E(L["region_all"])}</option>{opt(used_r, reg)}</select>{CHEV_D}</label>
        <button class="csbar__clear" type="reset" hidden>{E(L["clear"])}</button>
        <label class="csbar__search"><span class="sr-only">{E(L["search"])}</span>{SEARCH}<input type="search" name="q" placeholder="{E(L["search"])}" autocomplete="off"></label>
      </form>
      <p class="csbar__count" aria-live="polite">{count}</p>
      <ul class="csgrid">
        {"".join(card(c, L, ind, f'{c["slug"]}/') for c in cases)}
      </ul>
      <div class="csempty" hidden>
        <p class="csempty__title">{E(L["empty_title"])}</p>
        <p class="csempty__text">{E(L["empty_text"])}</p>
        <button class="csempty__btn" type="button" data-cs-clear>{E(L["clear"])}</button>
      </div>
    </div>
  </section>
</main>"""
    return page(body, d["meta"]["title"], d["meta"]["description"])


def slugs():
    return [c["slug"] for c in data()[0]["cases"]]


def block(b):
    if "h" in b: return f'<h2 id="{re.sub(r"[^a-z0-9]+", "-", b["h"].lower()).strip("-")}">{E(b["h"])}</h2>'
    if "h3" in b: return f"<h3>{E(b['h3'])}</h3>"
    if "p" in b: return f"<p>{md(b['p'])}</p>"
    if "ul" in b: return '<ul class="cscheck">' + "".join(f'<li><span class="cscheck__i">{CHECK}</span><span>{md(x)}</span></li>' for x in b["ul"]) + "</ul>"
    if "img" in b:
        dim = f' width="{b["size"][0]}" height="{b["size"][1]}"' if b.get("size") else ""
        return f'<figure class="csd__fig"><img src="{{{{IMG:{b["img"]}}}}}" alt="{E(b["alt"])}"{dim} loading="lazy" decoding="async"></figure>'
    if "quote" in b:
        by = f'<figcaption>{E(b["by"])}</figcaption>' if b.get("by") else ""
        return f'<figure class="csd__quote"><blockquote><p>{E(b["quote"])}</p></blockquote>{by}</figure>'
    sys.exit(f"src/case-studies.json: unknown block {b}")


def render_case(slug):
    d, ind, reg = data()
    L, cases = d["labels"], d["cases"]
    c = next(x for x in cases if x["slug"] == slug)
    facts = [(L["f_industry"], E(ind[c["industry"]])), (L["f_platform"], E(L["platform"])), (L["f_location"], E(c["country"])),
             (L["f_products"], E(", ".join(c["products"][:1] + [p[0].lower() + p[1:] for p in c["products"][1:]]))), (L["f_app"], f'<a href="{{{{HOME}}}}">{E(L["app"])}</a>')]
    dl = "".join(f"<div><dt>{E(k)}</dt><dd>{v}</dd></div>" for k, v in facts if v)
    # related: same industry first, then the rest in list order
    rel = [x for x in cases if x["slug"] != slug and x["industry"] == c["industry"]] + [x for x in cases if x["slug"] != slug and x["industry"] != c["industry"]]
    related = "".join(card(x, L, ind, f'../{x["slug"]}/') for x in rel[:3])
    body = f"""<main>
  <article class="csd" aria-labelledby="csd-title">
    <div class="container csd__grid">
      <header class="csd__head">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(L["home"])}</a>{CHEV_R}<a href="../">{E(L["crumb"])}</a>{CHEV_R}<span aria-current="page">{E(c["brand"])}</span></nav>
        <h1 class="csd__title" id="csd-title">{E(c["title"])}</h1>
        <p class="csd__lead">{E(c["lead"])}</p>
      </header>
        <aside class="csside" aria-label="{E(L["about"]).replace("{brand}", E(c["brand"]))}">
          <div class="csside__logo"><img src="{{{{IMG:cases/{c["slug"]}/logo.webp}}}}" alt="{E(c["brand"])}" decoding="async"></div>
          <p class="csside__brand">{E(c["brand"])}</p>
          <dl class="csside__facts">{dl}</dl>
          {{{{BTN_PRIMARY:{L["visit"]}|{c["store"]}}}}}
        </aside>
        <div class="csd__body">
          {"".join(block(b) for b in c["body"])}
        </div>
    </div>
  </article>
  <section class="fsec fsec--tint csrel" aria-labelledby="csrel-title">
    <div class="container">
      <div class="csrel__head">
        <h2 class="fsec__title" id="csrel-title">{E(L["related"])}</h2>
        <a class="cscard__more" href="../">{E(L["all_link"])}{ARROW}</a>
      </div>
      <ul class="csgrid">
        {related}
      </ul>
    </div>
  </section>
</main>"""
    desc = c["summary"] if len(c["summary"]) <= 158 else c["summary"][:157].rsplit(" ", 1)[0] + "…"
    return page(body, f'{c["brand"]}: {c["title"]} | {d["meta"]["short"]}', desc)
