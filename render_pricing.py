"""Render the Pricing page from src/pricing.json (plans, prices and features from the Shopify App Store listing).

Same shell as the contact page: a centred hero with a Monthly / Yearly switch, four plan cards, an "Every plan starts
with" band on tint, FAQs, then the shared CTA, crowd marquee and footer. The switch is driven by the pricing JS in the
template; without JS the monthly prices show.
"""
import json, re
from render_feature import ROOT, E, ICON, CHEV_R

CHECK = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
         'aria-hidden="true"><path d="M3.5 8.5l3 3 6-7"/></svg>')


def money(v):
    return f"${v:,.2f}"


def render():
    d = json.loads((ROOT / "src" / "pricing.json").read_text())
    home = (ROOT / "src" / "template.html").read_text()
    L, t = d["labels"], d["toggle"]

    def card(p, k):
        if p.get("yearly"):
            y_month, y_note = money(p["yearly"] / 12), L["billed_yearly"].replace("{price}", money(p["yearly"]))
        else:
            y_month, y_note = money(p["monthly"]), L["monthly_only"]
        lead = f'<li class="prcard__lead">{E(p["lead_feature"])}</li>' if p.get("lead_feature") else ""
        feats = "".join(f"<li>{CHECK}<span>{E(f)}</span></li>" for f in p["features"])
        return f"""<li class="prcard" style="--k:{k}">
          <h2 class="prcard__name">{E(p["name"])}</h2>
          <p class="prcard__text">{E(p["text"])}</p>
          <p class="prcard__price"><span class="prcard__amt" data-monthly>{money(p["monthly"])}</span><span class="prcard__amt" data-yearly>{y_month}</span><span class="prcard__per">{E(L["per_month"])}</span></p>
          <p class="prcard__note"><span data-monthly>{E(L["billed_monthly"])}</span><span data-yearly>{E(y_note)}</span></p>
          {{{{BTN_PRIMARY:{L["cta"]}|{d["install_url"]}}}}}
          <p class="prcard__trial">{E(L["trial"])}</p>
          <div class="prcard__feats"><p class="prcard__label">{E(L["features"])}</p><ul>{lead}{feats}</ul></div>
        </li>"""

    includes = "".join(f'<li class="princl__item"><span class="princl__icon" aria-hidden="true">{ICON[i["icon"]]}</span>'
                       f'<h3 class="princl__title">{E(i["title"])}</h3><p class="princl__text">{E(i["text"])}</p></li>' for i in d["includes"]["items"])
    faqs = "\n".join(f"""          <li class="qa{" is-open" if k == 0 else ""}">
            <h3><button class="qa__q" id="pq{k}" aria-expanded="{"true" if k == 0 else "false"}" aria-controls="pa{k}">{E(q["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
            <div class="qa__a" id="pa{k}" role="region" aria-labelledby="pq{k}"><div><p>{E(q["a"])}</p></div></div>
          </li>""" for k, q in enumerate(d["faqs"]))

    body = f"""<main>
  <!-- 1 · HERO + PLANS (white) -->
  <section class="prhero" aria-labelledby="pr-title">
    <div class="container prhero__inner">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">Home</a>{CHEV_R}<span aria-current="page">Pricing</span></nav>
      <h1 class="prhero__title" id="pr-title"><span class="h-line">{E(d["hero"]["title"][0])}</span> <span class="h-line h-muted">{E(d["hero"]["title"][1])}</span></h1>
      <p class="prhero__lead">{E(d["hero"]["lead"])}</p>
      <div class="prtoggle" role="group" aria-label="{E(t["label"])}">
        <button type="button" data-period="monthly" aria-pressed="true">{E(t["monthly"])}</button>
        <button type="button" data-period="yearly" aria-pressed="false">{E(t["yearly"])}<span class="prtoggle__save">{E(t["save"])}</span></button>
      </div>
    </div>
    <div class="container">
      <ul class="prplans" data-period="monthly">
        {"".join(card(p, k) for k, p in enumerate(d["plans"]))}
      </ul>
    </div>
  </section>

  <!-- 2 · EVERY PLAN (tint) -->
  <section class="fsec fsec--tint princl" aria-labelledby="pr-incl">
    <div class="container">
      <h2 class="fsec__title princl__head" id="pr-incl">{E(d["includes"]["title"])}</h2>
      <ul class="princl__grid">{includes}</ul>
    </div>
  </section>

  <!-- 3 · FAQS (white) -->
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
    css = "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "pricing.css"))
    head = head.replace("</style>", css + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(d["meta"]["title"])}</title>\n<meta name="description" content="{E(d["meta"]["description"])}">', head, count=1)
    tail = home[home.index("</main>") + len("</main>"):]
    return head + body + tail
