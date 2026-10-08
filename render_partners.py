"""Render the Partners page from src/partners.json (copy) and src/partners-directory.json (the list).

Same shell as the feature pages. The directory is filtered client-side (tabs with counts, search, "Show more"); the
partner form posts to FORM_ENDPOINT from the build config (shared with the Contact and newsletter forms) and says so
plainly when no endpoint is set.
"""
import json, re
from render_feature import ROOT, E, ICON, CHEV_R, heading

EXT = ('<svg class="ptr__ext" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
       'stroke-linejoin="round" aria-hidden="true"><path d="M6 4h6v6M12 4l-7.5 7.5"/></svg>')
TYPE_ICON = {"app": "layers", "service": "chat", "theme": "template", "other": "box"}


def monogram(name):
    words = [w for w in re.split(r"\s+", name) if w[:1].isalnum()]
    return "".join(w[0] for w in words[:2]).upper()


def render():
    c = json.loads((ROOT / "src" / "partners.json").read_text())
    partners = json.loads((ROOT / "src" / "partners-directory.json").read_text())["partners"]
    partners = sorted(partners, key=lambda p: not p.get("featured"))          # a featured partner comes first
    home = (ROOT / "src" / "template.html").read_text()
    types = {t["id"]: t for t in c["types"]}
    h, dr, f = c["hero"], c["directory"], c["form"]
    proof = home[home.index('<a class="proof"'):home.index("</a>", home.index('<a class="proof"')) + 4]

    # hero: partner tiles orbiting an InkyBay tile
    ring = "".join(f'<span class="porbit__tile mono mono--{k % 4}" style="--k:{k}">{E(monogram(p["name"]))}</span>' for k, p in enumerate(partners[:6]))
    chips = "".join(f'<span class="porbit__chip porbit__chip--{k + 1} chip{" chip--brand" if k else ""}">{E(t)}</span>' for k, t in enumerate(h["chips"]))
    orbit = (f'<div class="porbit" aria-hidden="true"><span class="porbit__glow"></span><div class="porbit__ring">{ring}</div>'
             f'<span class="porbit__core">{{{{LOGO_MARK}}}}</span>{chips}</div>')

    # directory
    tabs = (f'<button class="pdir__tab" type="button" role="tab" aria-selected="true" data-type="all">{E(dr["all"])} <span class="pdir__count">{len(partners)}</span></button>'
            + "".join(f'<button class="pdir__tab" type="button" role="tab" aria-selected="false" data-type="{t["id"]}">{E(t["label"])} '
                      f'<span class="pdir__count">{sum(p["type"] == t["id"] for p in partners)}</span></button>' for t in c["types"]))
    cards = "".join(
        f'<li class="ptr{" is-featured" if p.get("featured") else ""}" data-type="{E(p["type"])}" data-q="{E((p["name"] + " " + p["description"]).lower())}">'
        f'<span class="ptr__logo mono mono--{k % 4}" aria-hidden="true">{E(monogram(p["name"]))}</span>'
        f'<div class="ptr__head"><h3 class="ptr__name">{E(p["name"])}</h3><span class="ptr__badge">{E(types[p["type"]]["badge"])}</span></div>'
        f'<p class="ptr__text">{E(p["description"])}</p>'
        f'<a class="ptr__link" href="{E(p["url"])}" target="_blank" rel="noopener">{E(dr["learn_more"])}<span class="sr-only"> about {E(p["name"])} (opens in a new tab)</span>{EXT}</a></li>'
        for k, p in enumerate(partners))

    benefits = "".join(f'<li class="fben__item"><span class="fben__icon">{ICON[b["icon"]]}</span><h3>{E(b["title"])}</h3><p>{E(b["text"])}</p></li>' for b in c["benefits"])
    who = "".join(f'<li class="pwho__card"><span class="pwho__icon">{ICON[TYPE_ICON[w["type"]]]}</span><h3>{E(types[w["type"]]["label"])}</h3>'
                  f'<p class="pwho__for">{E(w["for"])}</p><p class="pwho__ex"><span>For example</span>{E(w["example"])}</p></li>' for w in c["who"])
    steps = "".join(f'<li class="pstep"><span class="pstep__num">{k + 1:02d}</span><h3>{E(s["title"])}</h3><p>{E(s["text"])}</p></li>' for k, s in enumerate(c["steps"]))
    opts = "".join(f'<option value="{E(o)}">{E(o)}</option>' for o in f["type_options"])
    err = lambda k: f'<span class="field__err" id="pf-{k}-err" aria-live="polite"></span>'
    faqs = "\n".join(f"""          <li class="qa{" is-open" if k == 0 else ""}">
            <h3><button class="qa__q" id="pq{k}" aria-expanded="{"true" if k == 0 else "false"}" aria-controls="pa{k}">{E(q["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
            <div class="qa__a" id="pa{k}" role="region" aria-labelledby="pq{k}"><div><p>{E(q["a"])}</p></div></div>
          </li>""" for k, q in enumerate(c["faqs"]))

    body = f"""<main>
  <!-- 1 · HERO -->
  <section class="fhero phero" aria-labelledby="p-title">
    <div class="container fhero__grid">
      <div class="fhero__text">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">Home</a>{CHEV_R}<a href="#">Resources</a>{CHEV_R}<span aria-current="page">Partners</span></nav>
        <h1 class="fhero__title" id="p-title"><span class="h-line">{E(h["title"][0])}</span> <span class="h-line h-muted">{E(h["title"][1])}</span></h1>
        <p class="fhero__lead">{E(h["lead"])}</p>
        <div class="fhero__actions">{{{{BTN_PRIMARY:{h["primary_cta"]}|#partner-form}}}}{{{{BTN_SECONDARY:{h["secondary_cta"]}|#directory}}}}</div>
        {proof}
      </div>
      <div class="fhero__vis">{orbit}</div>
    </div>
  </section>

  <!-- 2 · DIRECTORY (tint) -->
  <section class="fsec fsec--tint pdir" id="directory" aria-labelledby="p-dir">
    <div class="container">
      <div class="fsec__head fsec__head--center"><h2 class="fsec__title" id="p-dir">{E(dr["heading"])}</h2></div>
      <div class="pdir__bar">
        <div class="pdir__tabs" role="tablist" aria-label="Partner type">{tabs}</div>
        <label class="pdir__search"><span class="sr-only">{E(dr["search_label"])}</span><input type="search" placeholder="{E(dr["search_placeholder"])}" autocomplete="off"></label>
      </div>
      <ul class="pdir__grid" data-visible="{dr["visible"]}">{cards}</ul>
      <div class="pdir__empty" hidden><p class="pdir__empty-title">{E(dr["empty_title"])}</p><p>{E(dr["empty_text"])}</p><button class="btn btn--secondary pdir__clear" type="button">{E(dr["clear"])}</button></div>
      <div class="pdir__more"><button class="btn btn--secondary" type="button">{E(dr["show_more"])}</button></div>
      <p class="sr-only pdir__live" aria-live="polite"></p>
    </div>
  </section>

  <!-- 3 · WHY PARTNER (white) -->
  <section class="fsec" aria-labelledby="p-why">
    <div class="container">
      <div class="fsec__head">{heading(c["benefits_heading"], id_="p-why")}</div>
      <ul class="fben__grid">{benefits}</ul>
    </div>
  </section>

  <!-- 4 · WHO WE PARTNER WITH (dark) -->
  <section class="fsec fsec--dark" aria-labelledby="p-who">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading(c["who_heading"], id_="p-who")}</div>
      <ul class="pwho__grid">{who}</ul>
    </div>
  </section>

  <!-- 5 · HOW IT WORKS (white) -->
  <section class="fsec" aria-labelledby="p-steps">
    <div class="container">
      <div class="fsec__head">{heading(c["steps_heading"], id_="p-steps")}</div>
      <ol class="psteps">{steps}</ol>
    </div>
  </section>

  <!-- 6 · PARTNER FORM (tint) -->
  <section class="fsec fsec--tint" id="partner-form" aria-labelledby="p-form">
    <div class="container pform-wrap">
      <div class="fsec__head fsec__head--center"><h2 class="fsec__title" id="p-form">{E(f["heading"])}</h2><p class="fsec__lead">{E(f["lead"])}</p></div>
      <form class="form" data-form="partner" data-endpoint="{{{{FORM_ENDPOINT}}}}" method="post" novalidate>
        <p class="form__note" hidden>{E(f["not_connected"])}</p>
        <div class="form__row">
          <label class="field"><span class="field__label">{E(f["name"])}</span><input name="name" type="text" autocomplete="name" required data-err="{E(f["errors"]["name"])}" aria-describedby="pf-name-err">{err("name")}</label>
          <label class="field"><span class="field__label">{E(f["email"])}</span><input name="email" type="email" autocomplete="email" required data-err="{E(f["errors"]["email"])}" aria-describedby="pf-email-err">{err("email")}</label>
        </div>
        <div class="form__row">
          <label class="field"><span class="field__label">{E(f["website"])} <span class="field__opt">({E(f["optional"])})</span></span>
            <span class="field__prefix"><span aria-hidden="true">https://</span><input name="website" type="text" inputmode="url" autocomplete="url" data-url data-err="{E(f["errors"]["website"])}" aria-describedby="pf-website-err"></span>{err("website")}</label>
          <label class="field"><span class="field__label">{E(f["type"])}</span><select name="type" required data-err="{E(f["errors"]["type"])}" aria-describedby="pf-type-err"><option value="">{E(f["type_placeholder"])}</option>{opts}</select>{err("type")}</label>
        </div>
        <label class="field"><span class="field__label">{E(f["message"])}</span><textarea name="message" rows="5" required placeholder="{E(f["message_placeholder"])}" data-err="{E(f["errors"]["message"])}" aria-describedby="pf-message-err"></textarea>{err("message")}</label>
        <div class="form__hp" aria-hidden="true"><label>Leave this empty<input name="_gotcha" type="text" tabindex="-1" autocomplete="off"></label></div>
        <label class="field field--check"><input name="consent" type="checkbox" required data-err="{E(f["errors"]["consent"])}" aria-describedby="pf-consent-err"><span>{E(f["consent"])} <a href="#">{E(f["privacy"])}</a></span>{err("consent")}</label>
        <div class="form__foot"><button class="btn btn--primary form__submit" type="submit" data-sending="{E(f["sending"])}"><span class="btn__label" aria-hidden="true"><span data-text="{E(f["submit"])}">{E(f["submit"])}</span></span><span class="sr-only">{E(f["submit"])}</span></button>
          <p class="form__status" role="status" aria-live="polite" data-ok="{E(f["success"])}" data-fail="{E(f["error"])}" data-off="{E(f["not_connected"])}"></p></div>
      </form>
    </div>
  </section>

  <!-- 7 · FAQS (white) -->
  <section class="faq" aria-labelledby="faq-title">
    <div class="container faq__grid">
      <div class="faq__intro">
        <h2 class="faq__title" id="faq-title">FAQs</h2>
        <p class="faq__lead">Common questions about the partner program.</p>
        <div class="faq__help"><p>Still have questions?</p>{{{{BTN_SECONDARY:Talk to our team|#partner-form}}}}</div>
      </div>
      <ul class="faq__list">
{faqs}
      </ul>
    </div>
  </section>
</main>"""

    head = home[:home.index("<main>")]
    css = "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "forms.css", "partners.css"))
    head = head.replace("</style>", css + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(c["meta"]["title"])}</title>\n<meta name="description" content="{E(c["meta"]["description"])}">', head, count=1)
    tail = home[home.index("</main>") + len("</main>"):]
    return head + body + tail
