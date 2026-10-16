"""Render the Changelog page from src/changelog.json (entries newest first, labels and type names).

Same shell as the contact page: a hero, then a timeline (a thin thread with a dot per entry; the date on the left,
type pills, title, text and points on the right), a feature-request card, and the shared CTA, crowd marquee and footer.
Add a release by adding an entry: {"date": "YYYY-MM-DD", "title", "types": [new|improved|fixed|announcement], "text",
"items"?}. The build stops on a bad date or an unknown type.
"""
import datetime, json, re, sys
from render_feature import ROOT, E, CHEV_R


def render():
    d = json.loads((ROOT / "src" / "changelog.json").read_text())
    home = (ROOT / "src" / "template.html").read_text()
    L, T = d["labels"], d["types"]
    entries = []
    for e in d["entries"]:
        try: day = datetime.date.fromisoformat(e["date"])
        except (KeyError, ValueError): sys.exit(f"src/changelog.json: '{e.get('title')}' needs a date as YYYY-MM-DD")
        bad = [t for t in e.get("types", []) if t not in T]
        if bad or not e.get("types"): sys.exit(f"src/changelog.json: '{e['title']}' has unknown or missing types {bad} (use {list(T)})")
        entries.append((day, e))
    entries.sort(key=lambda x: x[0], reverse=True)

    def entry(day, e):
        anchor = f'{day.isoformat()}-' + re.sub(r"[^a-z0-9]+", "-", e["title"].lower()).strip("-")
        pills = "".join(f'<span class="chl__pill chl__pill--{t}">{E(T[t])}</span>' for t in e["types"])
        items = ("<ul class=\"chl__items\">" + "".join(f"<li>{E(i)}</li>" for i in e["items"]) + "</ul>") if e.get("items") else ""
        return f"""<li class="chl__entry" id="{anchor}">
          <time class="chl__date" datetime="{day.isoformat()}">{day.strftime("%B")} {day.day}, {day.year}</time>
          <article class="chl__body" aria-labelledby="{anchor}-t">
            <div class="chl__pills">{pills}</div>
            <h2 class="chl__title" id="{anchor}-t"><a href="#{anchor}">{E(e["title"])}</a></h2>
            <p class="chl__text">{E(e["text"])}</p>
            {items}
          </article>
        </li>"""

    body = f"""<main>
  <section class="chlhero" aria-labelledby="chl-title">
    <div class="container chl__wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">{E(L["home"])}</a>{CHEV_R}<span aria-current="page">{E(d["hero"]["title"])}</span></nav>
      <h1 class="chlhero__title" id="chl-title">{E(d["hero"]["title"])}</h1>
      <p class="chlhero__lead">{E(d["hero"]["lead"])}</p>
    </div>
  </section>
  <section class="chl" aria-label="{E(d["hero"]["title"])}">
    <div class="container chl__wrap">
      <ol class="chl__list">
        {"".join(entry(day, e) for day, e in entries)}
      </ol>
      <div class="chl__request">
        <div><h2 class="chl__request-title">{E(L["request_title"])}</h2><p class="chl__request-text">{E(L["request_text"])}</p></div>
        {{{{BTN_SECONDARY:{L["request_cta"]}|contact/}}}}
      </div>
    </div>
  </section>
</main>"""

    head = home[:home.index("<main>")]
    head = head.replace("</style>", "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "changelog.css")) + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(d["meta"]["title"])}</title>\n<meta name="description" content="{E(d["meta"]["description"])}">', head, count=1)
    tail = home[home.index("</main>") + len("</main>"):]
    return head + body + tail
