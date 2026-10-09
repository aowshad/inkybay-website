"""Render the Contact page from src/contact.json (topics, fields, channels, offices, FAQs).

Same shell as the feature pages. The form uses the shared form handler (FORM_ENDPOINT from the build config); the
topic chips, the copy button and the office clocks are driven by the contact JS in the template.
"""
import json, re, html as _html
from urllib.parse import quote_plus
from render_feature import ROOT, E, ICON, CHEV_R, heading

EXT = ('<svg class="cch__ext" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
       'stroke-linejoin="round" aria-hidden="true"><path d="M6 4h6v6M12 4l-7.5 7.5"/></svg>')
COPY = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true"><rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5V6a1.5 1.5 0 0 0-1.5-1.5H6A1.5 1.5 0 0 0 4.5 6v8A1.5 1.5 0 0 0 6 15.5h2.5"/></svg>')
CHECK = ('<svg class="cdone__check" viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="24" fill="none" stroke-width="2.5"/>'
         '<path d="M15 27l7 7 15-15" fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')
FLAGS = {
    "us": '<svg class="coff__flag" viewBox="0 0 28 20" role="img" aria-label="United States flag"><rect width="28" height="20" fill="#fff"/><rect y="0.000" width="28" height="1.538" fill="#B22234"/><rect y="3.077" width="28" height="1.538" fill="#B22234"/><rect y="6.154" width="28" height="1.538" fill="#B22234"/><rect y="9.231" width="28" height="1.538" fill="#B22234"/><rect y="12.308" width="28" height="1.538" fill="#B22234"/><rect y="15.385" width="28" height="1.538" fill="#B22234"/><rect y="18.462" width="28" height="1.538" fill="#B22234"/><rect width="11.2" height="10.77" fill="#3C3B6E"/><circle cx="1.40" cy="1.20" r=".42" fill="#fff"/><circle cx="3.50" cy="1.20" r=".42" fill="#fff"/><circle cx="5.60" cy="1.20" r=".42" fill="#fff"/><circle cx="7.70" cy="1.20" r=".42" fill="#fff"/><circle cx="9.80" cy="1.20" r=".42" fill="#fff"/><circle cx="2.35" cy="3.30" r=".42" fill="#fff"/><circle cx="4.45" cy="3.30" r=".42" fill="#fff"/><circle cx="6.55" cy="3.30" r=".42" fill="#fff"/><circle cx="8.65" cy="3.30" r=".42" fill="#fff"/><circle cx="1.40" cy="5.40" r=".42" fill="#fff"/><circle cx="3.50" cy="5.40" r=".42" fill="#fff"/><circle cx="5.60" cy="5.40" r=".42" fill="#fff"/><circle cx="7.70" cy="5.40" r=".42" fill="#fff"/><circle cx="9.80" cy="5.40" r=".42" fill="#fff"/><circle cx="2.35" cy="7.50" r=".42" fill="#fff"/><circle cx="4.45" cy="7.50" r=".42" fill="#fff"/><circle cx="6.55" cy="7.50" r=".42" fill="#fff"/><circle cx="8.65" cy="7.50" r=".42" fill="#fff"/><circle cx="1.40" cy="9.60" r=".42" fill="#fff"/><circle cx="3.50" cy="9.60" r=".42" fill="#fff"/><circle cx="5.60" cy="9.60" r=".42" fill="#fff"/><circle cx="7.70" cy="9.60" r=".42" fill="#fff"/><circle cx="9.80" cy="9.60" r=".42" fill="#fff"/></svg>',
    "bd": '<svg class="coff__flag" viewBox="0 0 28 20" role="img" aria-label="Bangladesh flag"><rect width="28" height="20" fill="#006A4E"/><circle cx="12.6" cy="10" r="5.6" fill="#F42A41"/></svg>',
}
ARC_H = ('<svg class="carc__svg carc__svg--h" viewBox="0 0 160 120" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="carc-g" x1="0" x2="1" y1="0" y2="0">'
         '<stop offset="0" stop-color="#FF7500"/><stop offset="1" stop-color="#E5380F"/></linearGradient></defs>'
         '<path class="carc__path" d="M4 80 C 50 6, 110 6, 156 80" fill="none" stroke="url(#carc-g)" stroke-width="2" stroke-dasharray="5 7" stroke-linecap="round"/>'
         '<circle class="carc__dot" r="5" cx="80" cy="25"/></svg>')
ARC_V = ('<svg class="carc__svg carc__svg--v" viewBox="0 0 120 100" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="carc-gv" x1="0" x2="0" y1="0" y2="1">'
         '<stop offset="0" stop-color="#FF7500"/><stop offset="1" stop-color="#E5380F"/></linearGradient></defs>'
         '<path class="carc__path" d="M60 2 C 6 30, 6 70, 60 98" fill="none" stroke="url(#carc-gv)" stroke-width="2" stroke-dasharray="5 7" stroke-linecap="round"/>'
         '<circle class="carc__dot" r="5" cx="20" cy="50"/></svg>')


def render(root):
    c = json.loads((ROOT / "src" / "contact.json").read_text())
    home = (ROOT / "src" / "template.html").read_text()
    f, fl = c["form"], c["form"]["fields"]

    def chan(ch):
        if ch["id"] == "email":
            action = (f'<a class="cch__detail" href="{E(ch["href"])}">{E(ch["detail"])}</a>'
                      f'<button class="cch__copy" type="button" data-copy="{E(ch["detail"])}" data-copied="{E(ch["copied"])}" aria-label="{E(ch["copy"])}">{COPY}<span class="cch__copied" aria-live="polite"></span></button>')
        elif ch.get("action"):
            action = f'<a class="cch__detail" href="#" data-action="{E(ch["action"])}">{E(ch["detail"])}</a>'
        else:
            action = f'<a class="cch__detail" href="{E(ch["href"])}" target="_blank" rel="noopener">{E(ch["detail"])}{EXT}</a>'
        return (f'<li class="cch__row"><span class="cch__icon">{ICON[ch["icon"]]}</span><div class="cch__body"><span class="cch__title">{E(ch["title"])}</span>'
                f'<div class="cch__act">{action}</div></div></li>')

    err = lambda k: f'<span class="field__err" id="cf-{k}-err" aria-live="polite"></span>'
    req = lambda k: f'data-err="{E(fl[k]["error"])}" aria-describedby="cf-{k}-err"'
    fx = lambda key, inner, hidden=False: f'<div class="cfx{" is-hidden" if hidden else ""}" data-f="{key}"><div class="cfx__in">{inner}</div></div>'
    o = f'<span class="field__opt">({E(f["optional"])})</span>'

    h = f["help"]
    helps = "".join(f'<option value="{E(o["label"])}" data-message="{E(o["message"])}"{" data-partner" if o.get("partner") else ""}>{E(o["label"])}</option>' for o in h["options"])
    fi = fl["file"]
    form = f"""<div class="ccard">
          <form class="form cform" data-form="contact" data-endpoint="{{{{FORM_ENDPOINT}}}}" method="post" enctype="multipart/form-data" novalidate>
            <div class="form__row">
              <label class="field"><span class="field__label">{E(fl["name"]["label"])}</span><input name="name" type="text" autocomplete="name" required {req("name")}>{err("name")}</label>
              <label class="field"><span class="field__label">{E(fl["email"]["label"])}</span><input name="email" type="email" inputmode="email" autocomplete="email" required {req("email")}>{err("email")}</label>
            </div>
            <div class="form__one">
              <label class="field"><span class="field__label">{E(fl["store"]["label"])} {o}</span><span class="field__prefix"><span aria-hidden="true">https://</span><input name="store" type="text" inputmode="url" autocomplete="url" data-url {req("store")}></span>{err("store")}</label>
            </div>
            <div class="form__row">
              <label class="field"><span class="field__label">{E(h["label"])}</span><select name="topic" required data-err="{E(h["error"])}" aria-describedby="cf-topic-err"><option value="">{E(h["placeholder"])}</option>{helps}</select>{err("topic")}</label>
              <div class="field cfile"><span class="field__label" id="cf-file-label">{E(fi["label"])} {o}</span>
                <label class="cfile__box"><input class="cfile__input" name="attachment" type="file" accept="{E(fi["accept"])}" data-maxsize="{fi["max_mb"] * 1024 * 1024}" data-err="{E(fi["error"])}" aria-labelledby="cf-file-label" aria-describedby="cf-file-hint cf-file-err">
                  <span class="cfile__btn">{ICON["file"]}<span class="cfile__name" data-empty="{E(fi["button"])}">{E(fi["button"])}</span></span><button class="cfile__clear" type="button" aria-label="Remove file" hidden>×</button></label>
                <span class="cfile__hint" id="cf-file-hint">{E(fi["hint"])}</span>{err("file")}</div>
            </div>
            <div class="cfx" data-f="partner" hidden><div class="cfx__in">{f'<div class="cpartner"><p>{E(f["partner_note"])}</p><a class="btn btn--secondary" href="{E(root + f["partner_href"])}">{E(f["partner_button"])}</a></div>'}</div></div>
            <label class="field"><span class="field__label cform__msg-label">{E(fl["message"]["label"])}<span class="cform__count" aria-hidden="true">0 / {fl["message"]["max"]}</span></span><textarea name="message" rows="5" maxlength="{fl["message"]["max"]}" required placeholder="{E(f["default_placeholder"])}" data-default-placeholder="{E(f["default_placeholder"])}" {req("message")}></textarea>{err("message")}</label>
            <div class="form__hp" aria-hidden="true"><label>Leave this empty<input name="_gotcha" type="text" tabindex="-1" autocomplete="off"></label></div>
            <label class="field field--check"><input name="consent" type="checkbox" required {req("consent")}><span>{E(fl["consent"]["label"])} <a href="#">{E(fl["consent"]["link"])}</a></span>{err("consent")}</label>
            <div class="form__foot"><button class="btn btn--primary form__submit" type="submit" data-sending="{E(f["sending"])}"><span class="btn__label" aria-hidden="true"><span data-text="{E(f["submit"])}">{E(f["submit"])}</span></span><span class="btn__icon" aria-hidden="true">{{{{BTN_ARROWS}}}}</span><span class="sr-only">{E(f["submit"])}</span></button>
              <p class="form__status" role="status" aria-live="polite" data-ok="" data-fail="{E(f["error"])}" data-fail-email="{E(f["error_email"])}" data-off="{E(f["not_connected"])}"></p></div>
          </form>
          <template class="form__done"><div class="cdone" tabindex="-1">{CHECK}<h2 class="cdone__title">{E(f["success_title"])}</h2><p class="cdone__next">{E(f["success_next"]["text"])}</p>
            <button class="cdone__again" type="button">{E(f["success_again"])}</button></div></template>
        </div>"""

    def office(o_, k):
        maps = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(o_["address"])
        h = o_["hours"]
        return (f'<li class="coff" data-tz="{E(o_["tz"])}" data-days="{",".join(map(str, h["days"]))}" data-open="{E(h["open"])}" data-close="{E(h["close"])}">'
                f'<div class="coff__head"><h3>{FLAGS.get(o_.get("flag"), "")}{E(o_["name"])}</h3><span class="coff__role">{E(o_["role"])}</span></div>'
                f'<div class="coff__clock"><span class="coff__time" aria-live="off">--:--</span><span class="coff__tz">{E(c["offices_labels"]["local"])} · {E(o_["tz"].split("/")[-1].replace("_", " "))}</span>'
                f'<span class="coff__badge" data-open-label="{E(c["offices_labels"]["open"])}" data-closed-label="{E(c["offices_labels"]["closed"])}"></span></div>'
                f'<a class="coff__line" href="{E(maps)}" target="_blank" rel="noopener" aria-label="{E(o_["address"])} ({E(c["offices_labels"]["map"])}, opens in a new tab)">{E(o_["address"])}{EXT}</a>'
                f'<a class="coff__line" href="tel:{E(o_["tel"])}">{E(o_["phone"])}</a></li>')
    offices = c["offices"]
    faqs = "\n".join(f"""          <li class="qa{" is-open" if k == 0 else ""}">
            <h3><button class="qa__q" id="cq{k}" aria-expanded="{"true" if k == 0 else "false"}" aria-controls="ca{k}">{E(q["q"])}<span class="qa__icon" aria-hidden="true"></span></button></h3>
            <div class="qa__a" id="ca{k}" role="region" aria-labelledby="cq{k}"><div><p>{E(q["a"])}</p></div></div>
          </li>""" for k, q in enumerate(c["faqs"]))

    body = f"""<main>
  <!-- 1 · HERO + FORM (white) -->
  <section class="chero" aria-labelledby="c-title">
    <div class="container chero__grid">
      <div class="chero__intro">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">Home</a>{CHEV_R}<span aria-current="page">Contact</span></nav>
        <h1 class="chero__title" id="c-title"><span class="h-line">{E(c["hero"]["title"][0])}</span> <span class="h-line h-muted">{E(c["hero"]["title"][1])}</span></h1>
        <p class="chero__lead">{E(c["hero"]["lead"])}</p>
      </div>
      <div class="chero__form">{form}</div>
      <div class="chero__side">
        <ul class="cch">{"".join(chan(ch) for ch in c["channels"])}</ul>
        <p class="chero__note"><span class="chero__note-dot" aria-hidden="true"></span>{E(c["response_note"]["text"])}</p>
      </div>
    </div>
  </section>

  <!-- 2 · OFFICES (dark) -->
  <section class="fsec fsec--dark coffices" aria-labelledby="c-off">
    <div class="container">
      <div class="fsec__head fsec__head--center">{heading(c["offices_heading"], id_="c-off")}</div>
      <ul class="coffices__grid">{office(offices[0], 0)}<li class="carc" aria-hidden="true">{ARC_H}{ARC_V}</li>{office(offices[1], 1)}</ul>
    </div>
  </section>

  <!-- 3 · FAQS (white) -->
  <section class="faq" aria-labelledby="faq-title">
    <div class="container faq__grid">
      <div class="faq__intro">
        <h2 class="faq__title" id="faq-title">FAQs</h2>
        <p class="faq__lead">Common questions about getting in touch.</p>
      </div>
      <ul class="faq__list">
{faqs}
      </ul>
    </div>
  </section>
</main>"""

    head = home[:home.index("<main>")]
    css = "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "forms.css", "contact.css"))
    head = head.replace("</style>", css + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(c["meta"]["title"])}</title>\n<meta name="description" content="{E(c["meta"]["description"])}">', head, count=1)
    tail = home[home.index("</main>") + len("</main>"):]
    return head + body + tail
