"""Render the Affiliate program page (site/affiliate/) from src/affiliate.json.

Structure inspired by Shopify's affiliate page, in the InkyBay kit: a centred hero with four audience cards (a product
on the warm dark stage), an optional earnings calculator (only when "commission" is set in the JSON), the benefits on
a dark band, the kinds of sellers to refer with three facts, "Start earning today" (steps and the application form,
the Partners page's layout) and FAQs, then the shared CTA and footer. No commission rate, payout or cookie window is
stated anywhere until the terms exist.
"""
import json, re
from render_feature import ROOT, E, ICON, CHEV_R, heading


def render():
    d = json.loads((ROOT / "src" / "affiliate.json").read_text())
    home = (ROOT / "src" / "template.html").read_text()
    h, ap, f = d["hero"], d["apply"], d["apply"]["form"]
    fl, er = f["fields"], f["errors"]
    err = lambda k: f'<span class="field__err" id="af-{k}-err" aria-live="polite"></span>'

    audiences = "".join(f"""<li class="aaud">
          <img class="aaud__img" src="{{{{IMG:products/{a["product"]}.webp}}}}" alt="" width="600" height="600" decoding="async"{' loading="lazy"' if k > 1 else ""}>
          <div class="aaud__text"><h2 class="aaud__title">{E(a["title"])}</h2><p>{E(a["text"])}</p></div>
        </li>""" for k, a in enumerate(d["audiences"]))

    calc = ""
    if d.get("commission"):
        c, cl = d["commission"], d["calculator"]
        per = c["amount"] if c["model"] == "flat" else c["price"] * c["rate"] / 100 * c["months"]
        calc = f"""<div class="acalc" data-per="{per:.2f}">
        <h2 class="fsec__title acalc__title">{E(cl["title"])}</h2>
        <div class="acalc__card">
          <label class="acalc__label" for="acalc-n">{E(cl["referrals"])} <output class="acalc__n" for="acalc-n">10</output></label>
          <input class="acalc__range" id="acalc-n" type="range" min="1" max="100" value="10">
          <p class="acalc__out"><span>{E(cl["per_year"])}</span><strong class="acalc__sum">$0</strong></p>
          <p class="acalc__note">{E(cl["note"])}</p>
        </div>
      </div>"""

    benefits = "".join(f'<li class="fben__item"><span class="fben__icon">{ICON[b["icon"]]}</span><h3>{E(b["title"])}</h3><p>{E(b["text"])}</p></li>' for b in d["benefits"])
    sellers = "".join(f'<li class="asell"><h3 class="asell__title">{E(s["title"])}</h3><p class="asell__text">{E(s["text"])}</p></li>' for s in d["sellers"])
    facts = "".join(f'<li class="afact"><strong>{E(x["value"])}</strong><span>{E(x["label"])}</span></li>' for x in d["facts"])
    steps = "".join(f'<li class="pstep"><span class="pstep__num">{k + 1}</span><div><h3>{E(s)}</h3></div></li>' for k, s in enumerate(ap["steps"]))
    options = "".join(f'<option>{E(o)}</option>' for o in fl["type"]["options"])
    faqs = "\n".join(f"""          <li class="qa{" is-open" if k == 0 else ""}">
            <h3><button class="qa__q" id="aq{k}" aria-expanded="{"true" if k == 0 else "false"}" aria-controls="aa{k}">{E(q["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
            <div class="qa__a" id="aa{k}" role="region" aria-labelledby="aq{k}"><div><p>{E(q["a"])}</p></div></div>
          </li>""" for k, q in enumerate(d["faqs"]))

    body = f"""<main>
  <!-- 1 · HERO + AUDIENCES (white) -->
  <section class="ahero" aria-labelledby="a-title">
    <div class="container">
      <div class="ahero__intro">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">Home</a>{CHEV_R}<span>Resources</span>{CHEV_R}<span aria-current="page">Affiliate program</span></nav>
        <h1 class="ahero__title" id="a-title"><span class="h-line">{E(h["title"][0])}</span> <span class="h-line h-muted">{E(h["title"][1])}</span></h1>
        <p class="ahero__lead">{E(h["lead"])}</p>
        <div class="ahero__actions">{{{{BTN_PRIMARY:{h["primary"]}|#apply}}}}{{{{BTN_SECONDARY:{h["secondary"]}|#apply}}}}</div>
      </div>
      <ul class="aauds">{audiences}</ul>
    </div>
  </section>

  <!-- 2 · (CALCULATOR) + BENEFITS (dark) -->
  <section class="fsec fsec--dark abenefits" aria-labelledby="a-why">
    <div class="container">
      {calc}
      <div class="fsec__head">{heading(d["benefits_heading"], id_="a-why")}</div>
      <ul class="fben__grid">{benefits}</ul>
    </div>
  </section>

  <!-- 3 · SELLERS (white) -->
  <section class="fsec asellers" aria-labelledby="a-sell">
    <div class="container">
      <h2 class="fsec__title" id="a-sell">{E(d["sellers_heading"])}</h2>
      <ul class="asell__list">{sellers}</ul>
      <h3 class="afacts__title">{E(d["facts_title"])}</h3>
      <ul class="afacts">{facts}</ul>
    </div>
  </section>

  <!-- 4 · START EARNING TODAY (tint): steps on the left, the application form on the right -->
  <section class="fsec fsec--tint pjoin" id="apply" aria-labelledby="a-apply">
    <div class="container pjoin__grid">
      <div class="pjoin__intro">
        <h2 class="fsec__title" id="a-apply">{E(ap["heading"])}</h2>
        <p class="fsec__lead">{E(ap["lead"])}</p>
        <ol class="psteps">{steps}</ol>
        <p class="pjoin__trust">{ICON["handshake"]}<span>{E(ap["partner_note"])} <a href="{{{{ROOT}}}}partners/">{E(ap["partner_link"])}</a>.</span></p>
      </div>
      <div class="pjoin__card">
        <form class="form" data-form="{E(f["type"])}" data-endpoint="{{{{FORM_ENDPOINT}}}}" method="post" novalidate>
          <input type="hidden" name="form" value="{E(f["type"])}">
          <div class="form__row">
            <label class="field"><span class="field__label">{E(fl["name"]["label"])}</span><input name="name" type="text" autocomplete="name" placeholder="{E(fl["name"]["placeholder"])}" required data-err="{E(er["name"])}" aria-describedby="af-name-err">{err("name")}</label>
            <label class="field"><span class="field__label">{E(fl["email"]["label"])}</span><input name="email" type="email" inputmode="email" autocomplete="email" placeholder="{E(fl["email"]["placeholder"])}" required data-err="{E(er["email"])}" aria-describedby="af-email-err">{err("email")}</label>
          </div>
          <div class="form__one">
            <label class="field"><span class="field__label">{E(fl["url"]["label"])}</span>
              <span class="field__prefix"><span aria-hidden="true">https://</span><input name="website" type="text" inputmode="url" autocomplete="url" placeholder="{E(fl["url"]["placeholder"])}" required data-url data-err="{E(er["url"])}" aria-describedby="af-url-err"></span>{err("url")}</label>
          </div>
          <div class="form__one">
            <label class="field"><span class="field__label">{E(fl["type"]["label"])}</span><select name="promotion" required data-err="{E(er["type"])}" aria-describedby="af-type-err"><option value="">{E(fl["type"]["placeholder"])}</option>{options}</select>{err("type")}</label>
          </div>
          <label class="field"><span class="field__label">{E(fl["message"]["label"])}</span><textarea name="message" rows="4" placeholder="{E(fl["message"]["placeholder"])}"></textarea></label>
          <div class="form__hp" aria-hidden="true"><label>Leave this empty<input name="_gotcha" type="text" tabindex="-1" autocomplete="off"></label></div>
          <label class="field field--check"><input name="consent" type="checkbox" required data-err="{E(er["consent"])}" aria-describedby="af-consent-err"><span>{E(fl["consent"])} <a href="{{{{ROOT}}}}privacy-policy/">{E(fl["privacy"])}</a></span>{err("consent")}</label>
          <div class="form__foot"><button class="btn btn--primary form__submit" type="submit" data-sending="{E(f["sending"])}"><span class="btn__label" aria-hidden="true"><span data-text="{E(f["submit"])}">{E(f["submit"])}</span></span><span class="btn__icon" aria-hidden="true">{{{{BTN_ARROWS}}}}</span><span class="sr-only">{E(f["submit"])}</span></button>
            <p class="form__status" role="status" aria-live="polite" data-ok="{E(f["success"])}" data-fail="{E(f["error"])}" data-off="{E(f["not_connected"])}" data-fail-email="{E(f["fail_email"])}"></p></div>
        </form>
      </div>
    </div>
  </section>

  <!-- 5 · FAQS (white) -->
  <section class="faq" aria-labelledby="faq-title">
    <div class="container faq__grid">
      <div class="faq__intro">
        <h2 class="faq__title" id="faq-title">FAQs</h2>
        <p class="faq__lead">{E(d["faqs_lead"])}</p>
      </div>
      <ul class="faq__list">
{faqs}
      </ul>
    </div>
  </section>
</main>"""
    head = home[:home.index("<main>")]
    head = head.replace("</style>", "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "forms.css", "partners.css", "affiliate.css")) + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(d["meta"]["title"])}</title>\n<meta name="description" content="{E(d["meta"]["description"])}">', head, count=1)
    return head + body + home[home.index("</main>") + len("</main>"):]
