"""Legal pages (Privacy policy, Terms of service): src/legal/<slug>.md -> site/<slug>/.

Each page is Markdown with front matter (title, slug, description, updated, effective, summary bullets), rendered with
the blog article's pipeline and layout (render_blog.md_html, shell, contents sidebar), so it looks and behaves like an
article: breadcrumb, H1, a meta row, an "In short" card, numbered sections with copy-link anchors, a sticky contents
list on desktop (a disclosure on phones), and a questions card that links to the contact page and the other page.
Labels live in src/legal/legal.json.
"""
import json, math, re
import render_blog as RB
from render_feature import ROOT, E, CHEV_R

LEGAL = ROOT / "src" / "legal"
CFG = json.loads((LEGAL / "legal.json").read_text())
L = CFG["labels"]
SEP = '<span class="bmeta__sep" aria-hidden="true"></span>'


def load(slug):
    path = LEGAL / f"{slug}.md"
    meta, body = RB.front_matter(path.read_text(), path)
    for k in ("title", "slug", "description", "updated", "effective", "summary"):
        if not meta.get(k): RB.fail(f"{path.name}: missing '{k}' in the front matter")
    if meta["slug"] != slug: RB.fail(f"{path.name}: slug '{meta['slug']}' must match the file name")
    html, toc = RB.md_html(body)
    meta["html"], meta["toc"], meta["minutes"] = html, toc, max(1, math.ceil(len(re.sub(r"<[^>]+>", " ", html).split()) / 225))
    return meta


def render(slug, home):
    p = load(slug); others = [load(s) for s in CFG["pages"] if s != slug]
    toc_items = "".join(f'<li data-sec="{t["id"]}"><a href="#{t["id"]}">{E(t["name"])}</a>'
                        + (("<ol class=\"btoc__sub\">" + "".join(f'<li><a href="#{c["id"]}">{E(c["name"])}</a></li>' for c in t["children"]) + "</ol>") if t["children"] else "")
                        + "</li>" for t in p["toc"])
    toc = f'<ol class="btoc__list">{toc_items}</ol>'
    meta = (f'<div class="bmeta"><span>{E(L["updated"])} <time datetime="{p["updated"]}">{RB.fmt_date(p["updated"])}</time></span>{SEP}'
            f'<span>{E(L["effective"])} <time datetime="{p["effective"]}">{RB.fmt_date(p["effective"])}</time></span>{SEP}<span>{p["minutes"]} {E(L["minutes"])}</span></div>')
    summary = "".join(f"<li>{E(s)}</li>" for s in p["summary"])
    also = " · ".join(f'<a href="../{o["slug"]}/">{E(o["title"])}</a>' for o in others)
    body = f"""<div class="bprogress" aria-hidden="true"><i></i></div>
  <article class="bart blegal" aria-labelledby="l-title">
    <div class="container bart__grid">
      <div class="bart__main">
        <header class="bart__head">
          <nav class="crumbs" aria-label="Breadcrumb"><a href="../">{E(L["home"])}</a>{CHEV_R}<span aria-current="page">{E(p["title"])}</span></nav>
          <h1 class="bart__title" id="l-title">{E(p["title"])}</h1>
          {meta}
        </header>
        <aside class="bcall lsum" aria-labelledby="l-sum"><p class="bcall__title" id="l-sum">{E(L["summary"])}</p><ul>{summary}</ul></aside>
        <details class="btoc btoc--inline"><summary>{E(L["toc"])}</summary><nav aria-label="Table of contents">{toc}</nav></details>
        <div class="bbody">{p["html"]}</div>
        <footer class="lfoot">
          <div class="lfoot__card">
            <div><h2 class="lfoot__title">{E(L["questions_title"])}</h2><p class="lfoot__text">{E(L["questions_text"])}</p></div>
            {{{{BTN_SECONDARY:{L["contact"]}|contact/}}}}
          </div>
          <p class="lfoot__also">{E(L["also"])}: {also}</p>
        </footer>
      </div>
      <aside class="bart__side" aria-label="{E(L["toc"])}">
        <nav class="btoc btoc--side" aria-label="Table of contents"><p class="btoc__title">{E(L["toc"])}</p><div class="btoc__track">{toc}<span class="btoc__ind" aria-hidden="true"></span></div></nav>
      </aside>
    </div>
  </article>"""
    return RB.shell(home, body, f'{p["title"]} | InkyBay', p["description"], "")
