"""Render the Video tutorials page (site/resources/video-tutorials/) from src/videos.json.

The videos are InkyBay's own YouTube tutorials (the channel listed on docs.inkybay.com). Thumbnails are self-hosted
(src/assets/videos/<id>.webp), so nothing loads from YouTube until a visitor presses play; then the video plays in a
dialog through YouTube's privacy-enhanced player (youtube-nocookie.com). Every play link is a real YouTube link, so
without JS it simply opens YouTube. Sections: hero (two-tone H1, lead, Subscribe on YouTube), a featured "Start here"
video, the library on tint (category tabs with counts, 3-up cards), a help card, then the shared CTA and footer.
"""
import json, re, sys
from render_feature import ROOT, E, CHEV_R

PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.5 5.9v12.2c0 .8.9 1.3 1.6.8l9.1-6.1c.6-.4.6-1.3 0-1.7l-9.1-6.1c-.7-.4-1.6 0-1.6.9z" fill="currentColor"/></svg>'
CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>'
EXT = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 4h6v6M12 4l-7.5 7.5"/></svg>'


def clock(s):
    return f"{s // 60}:{s % 60:02d}"


def render():
    d = json.loads((ROOT / "src" / "videos.json").read_text())
    home = (ROOT / "src" / "template.html").read_text()
    L, cats = d["labels"], {c["slug"]: c["name"] for c in d["categories"]}
    vids = d["videos"]
    for v in vids:
        if v["category"] not in cats: sys.exit(f"src/videos.json: '{v['title']}' has unknown category '{v['category']}'")
        if not (ROOT / "src" / "assets" / "videos" / f'{v["id"]}.webp').exists(): sys.exit(f"src/videos.json: no thumbnail src/assets/videos/{v['id']}.webp")
    watch = lambda v: f'https://www.youtube.com/watch?v={v["id"]}'
    mins = lambda v: f'{max(1, round(v["seconds"] / 60))} {L["minutes"]}'

    def card(v):
        return f"""<li class="vcard" data-cat="{v["category"]}">
          <a class="vcard__thumb" href="{watch(v)}" data-video="{v["id"]}" data-title="{E(v["title"])}" aria-label="{E(L["play"])}: {E(v["title"])} ({mins(v)})">
            <img src="{{{{IMG:videos/{v["id"]}.webp}}}}" alt="" width="960" height="540" loading="lazy" decoding="async">
            <span class="vcard__play" aria-hidden="true">{PLAY}</span><span class="vcard__dur" aria-hidden="true">{clock(v["seconds"])}</span>
          </a>
          <span class="vcard__cat">{E(cats[v["category"]])}</span>
          <h3 class="vcard__title"><a href="{watch(v)}" data-video="{v["id"]}" data-title="{E(v["title"])}">{E(v["title"])}</a></h3>
        </li>"""

    f = next(v for v in vids if v["id"] == d["featured"]["id"])
    count = lambda n: (L["count_one"] if n == 1 else L["count_many"]).replace("{n}", str(n))
    tabs = (f'<button type="button" class="vtab" data-cat="all" aria-pressed="true">{E(L["all"])} <span>{len(vids)}</span></button>'
            + "".join(f'<button type="button" class="vtab" data-cat="{s}" aria-pressed="false">{E(n)} <span>{sum(v["category"] == s for v in vids)}</span></button>' for s, n in cats.items()))
    body = f"""<main class="vpage">
  <!-- 1 · HERO + START HERE (white) -->
  <section class="vhero" aria-labelledby="v-title">
    <div class="container">
      <div class="vhero__intro">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="{{{{HOME}}}}">Home</a>{CHEV_R}<span>Resources</span>{CHEV_R}<span aria-current="page">{E(d["hero"]["title"][0])}</span></nav>
        <h1 class="vhero__title" id="v-title"><span class="h-line">{E(d["hero"]["title"][0])}</span> <span class="h-line h-muted">{E(d["hero"]["title"][1])}</span></h1>
        <p class="vhero__lead">{E(d["hero"]["lead"])}</p>
        <div class="vhero__actions"><a class="vlink" href="{d["channel_url"]}" target="_blank" rel="noopener">{E(d["hero"]["channel_cta"])}{EXT}</a><span class="vhero__count">{count(len(vids))}</span></div>
      </div>
      <article class="vfeat" aria-labelledby="v-feat">
        <a class="vfeat__thumb" href="{watch(f)}" data-video="{f["id"]}" data-title="{E(f["title"])}" aria-label="{E(L["play"])}: {E(f["title"])} ({mins(f)})">
          <img src="{{{{IMG:videos/{f["id"]}.webp}}}}" alt="" width="960" height="540" fetchpriority="high" decoding="async">
          <span class="vcard__play vcard__play--lg" aria-hidden="true">{PLAY}</span><span class="vcard__dur" aria-hidden="true">{clock(f["seconds"])}</span>
        </a>
        <div class="vfeat__text">
          <p class="vfeat__label">{E(d["featured"]["label"])}</p>
          <h2 class="vfeat__title" id="v-feat">{E(f["title"])}</h2>
          <p class="vfeat__meta">{E(cats[f["category"]])} · {mins(f)}</p>
          <p class="vfeat__body">{E(d["featured"]["text"])}</p>
          <a class="btn btn--primary vfeat__btn" href="{watch(f)}" data-video="{f["id"]}" data-title="{E(f["title"])}" aria-label="{E(d["featured"]["cta"])}: {E(f["title"])}"><span class="btn__label" aria-hidden="true"><span data-text="{E(d["featured"]["cta"])}">{E(d["featured"]["cta"])}</span></span><span class="btn__icon" aria-hidden="true">{{{{BTN_ARROWS}}}}</span></a>
        </div>
      </article>
    </div>
  </section>

  <!-- 2 · LIBRARY (tint) -->
  <section class="fsec fsec--tint vlib" aria-labelledby="v-lib">
    <div class="container">
      <h2 class="fsec__title vlib__title" id="v-lib">All tutorials</h2>
      <div class="vtabs" role="group" aria-label="{E(L["filter"])}">{tabs}</div>
      <ul class="vgrid">{"".join(card(v) for v in vids)}</ul>
    </div>
  </section>

  <!-- 3 · HELP (white) -->
  <section class="vhelp-sec">
    <div class="container">
      <div class="vhelp">
        <div><h2 class="vhelp__title">{E(L["help_title"])}</h2><p class="vhelp__text">{E(L["help_text"])}</p></div>
        <div class="vhelp__actions"><a class="vlink" href="{d["help_url"]}" target="_blank" rel="noopener">{E(L["help_cta"])}{EXT}</a>{{{{BTN_SECONDARY:{L["contact_cta"]}|contact/}}}}</div>
      </div>
    </div>
  </section>

  <dialog class="vmodal" aria-labelledby="vmodal-title">
    <div class="vmodal__box">
      <div class="vmodal__frame"></div>
      <div class="vmodal__bar"><p class="vmodal__title" id="vmodal-title"></p>
        <a class="vlink vmodal__yt" href="#" target="_blank" rel="noopener">{E(L["on_youtube"])}{EXT}</a>
        <button class="vmodal__close" type="button" autofocus aria-label="{E(L["close"])}">{CLOSE}</button></div>
    </div>
  </dialog>
</main>"""
    head = home[:home.index("<main>")]
    head = head.replace("</style>", "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "videos.css")) + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f'<title>{E(d["meta"]["title"])}</title>\n<meta name="description" content="{E(d["meta"]["description"])}">', head, count=1)
    return head + body + home[home.index("</main>") + len("</main>"):]
