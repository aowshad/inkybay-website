"""Render the changelog from src/changelog.json: the list page (site/changelog/) and one detail page per entry
(site/changelog/<slug>/).

Same shell as the contact page. The list is a timeline (date on the left, a thin thread with a dot per entry, type
pills, the linked title and "Read update"); the details live only on each entry's own page: breadcrumb, date and
pills, H1, the text, the points (and an optional Markdown "body"), newer / older links and "All updates". Both end
with the feature-request card, then the shared CTA, crowd marquee and footer.
Add a release by adding an entry: {"date": "YYYY-MM-DD", "title", "types": [new|improved|fixed|announcement], "text",
"items"?, "body"?, "slug"?} plus a one-line "summary" shown as the subheading (the slug defaults to the title). The build stops on a bad date, an unknown type or a
duplicate slug.
"""
import datetime, json, re, sys
from render_feature import ROOT, E, CHEV_R

ARROW = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
         'aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')
BACK = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true"><path d="M13 8H3M7 4L3 8l4 4"/></svg>')


def data():
    d = json.loads((ROOT / "src" / "changelog.json").read_text())
    T, out, seen = d["types"], [], set()
    for e in d["entries"]:
        try: day = datetime.date.fromisoformat(e["date"])
        except (KeyError, ValueError): sys.exit(f"src/changelog.json: '{e.get('title')}' needs a date as YYYY-MM-DD")
        if not e.get("summary"): sys.exit(f"src/changelog.json: '{e['title']}' needs a one-line \"summary\" (the subheading)")
        bad = [t for t in e.get("types", []) if t not in T]
        if bad or not e.get("types"): sys.exit(f"src/changelog.json: '{e['title']}' has unknown or missing types {bad} (use {list(T)})")
        slug = e.get("slug") or re.sub(r"[^a-z0-9]+", "-", e["title"].lower()).strip("-")
        if slug in seen: sys.exit(f"src/changelog.json: two entries share the slug '{slug}' (set a \"slug\" on one of them)")
        seen.add(slug); out.append(dict(e, day=day, slug=slug))
    out.sort(key=lambda e: e["day"], reverse=True)
    return d, out


def date_label(day):
    return f'{day.strftime("%B")} {day.day}, {day.year}'


def pills(e, T):
    return "".join(f'<span class="chl__pill chl__pill--{t}">{E(T[t])}</span>' for t in e["types"])


def page(d, body, title, desc):
    home = (ROOT / "src" / "template.html").read_text()
    head = home[:home.index("<main>")]
    head = head.replace("</style>", "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "changelog.css")) + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(title)}</title>\n<meta name="description" content="{E(desc)}">', head, count=1)
    return head + body + home[home.index("</main>") + len("</main>"):]


def request(L):
    return f"""<div class="chl__request">
        <div><h2 class="chl__request-title">{E(L["request_title"])}</h2><p class="chl__request-text">{E(L["request_text"])}</p></div>
        {{{{BTN_SECONDARY:{L["request_cta"]}|contact/}}}}
      </div>"""


def render():
    """The list: date, pills and the linked title of every entry; no details."""
    d, entries = data()
    L, T = d["labels"], d["types"]
    rows = "".join(f"""<li class="chl__entry">
          <time class="chl__date" datetime="{e["day"].isoformat()}">{date_label(e["day"])}</time>
          <article class="chl__body" aria-labelledby="chl-{e["slug"]}">
            <div class="chl__pills">{pills(e, T)}</div>
            <h2 class="chl__title" id="chl-{e["slug"]}"><a href="{e["slug"]}/">{E(e["title"])}</a></h2>
            <p class="chl__sub">{E(e["summary"])}</p>
            <a class="chl__more" href="{e["slug"]}/">{E(L["read"])}<span class="sr-only">: {E(e["title"])}</span>{ARROW}</a>
          </article>
        </li>""" for e in entries)
    body = f"""<main>
  <section class="chlhero" aria-labelledby="chl-title">
    <div class="container">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(L["home"])}</a>{CHEV_R}<span aria-current="page">{E(d["hero"]["title"])}</span></nav>
      <h1 class="chlhero__title" id="chl-title">{E(d["hero"]["title"])}</h1>
      <p class="chlhero__lead">{E(d["hero"]["lead"])}</p>
    </div>
  </section>
  <section class="chl" aria-label="{E(d["hero"]["title"])}">
    <div class="container">
      <ol class="chl__list">
        {rows}
      </ol>
      {request(L)}
    </div>
  </section>
</main>"""
    return page(d, body, d["meta"]["title"], d["meta"]["description"])


def slugs():
    return [e["slug"] for e in data()[1]]


def render_entry(slug):
    """One entry's own page: everything the list leaves out."""
    d, entries = data()
    L, T = d["labels"], d["types"]
    i = next(k for k, e in enumerate(entries) if e["slug"] == slug)
    e = entries[i]; newer = entries[i - 1] if i > 0 else None; older = entries[i + 1] if i + 1 < len(entries) else None
    items = (f'<h2 class="chld__label">{E(L["in_this_update"])}</h2><ul class="chld__items">' + "".join(f"<li>{E(x)}</li>" for x in e["items"]) + "</ul>") if e.get("items") else ""
    extra = ""
    if e.get("body"):
        import render_blog
        extra = f'<div class="chld__md">{render_blog.md_html(e["body"])[0]}</div>'
    pn = '<nav class="chld__pn" aria-label="More updates">' + (
        f'<a class="chld__pnl chld__pnl--newer" href="../{newer["slug"]}/"><span>{E(L["newer"])}</span>{E(newer["title"])}</a>' if newer else "<span></span>") + (
        f'<a class="chld__pnl chld__pnl--older" href="../{older["slug"]}/"><span>{E(L["older"])}</span>{E(older["title"])}</a>' if older else "<span></span>") + "</nav>"
    SEP = '<span class="chld__sep" aria-hidden="true"></span>'
    body = f"""<main>
  <article class="chld" aria-labelledby="chld-title">
    <div class="container">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(L["home"])}</a>{CHEV_R}<a href="../">{E(d["hero"]["title"])}</a>{CHEV_R}<span aria-current="page">{E(e["title"])}</span></nav>
      <div class="chld__meta"><time datetime="{e["day"].isoformat()}">{date_label(e["day"])}</time>{SEP}<div class="chl__pills">{pills(e, T)}</div></div>
      <h1 class="chld__title" id="chld-title">{E(e["title"])}</h1>
      <p class="chld__sub">{E(e["summary"])}</p>
      <p class="chld__lead">{E(e["text"])}</p>
      {items}{extra}
      {pn}
      <a class="chld__back" href="../">{BACK}{E(L["back"])}</a>
      {request(L)}
    </div>
  </article>
</main>"""
    desc = e["summary"] if len(e["summary"]) <= 158 else e["text"]
    desc = desc if len(desc) <= 158 else desc[:157].rsplit(" ", 1)[0] + "…"   # meta description length
    return page(d, body, f'{e["title"]} | {d["meta"]["title"]}', desc)
