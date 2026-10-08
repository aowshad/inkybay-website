"""Audit feature pages before committing.

    python3 scripts/audit.py <slug> [<slug> ...]     # check JSON + built page(s)
    python3 scripts/audit.py --all                   # the homepage, the 404, every feature page and every industry page

Exit code 0 = pass, 1 = fail. Never commit a page that fails.
Setup once:  pip install playwright && python3 -m playwright install chromium
"""
import json, re, sys, pathlib, asyncio

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from render_feature import ICON  # noqa: E402

MINI_UIS = {"setup", "design", "files", "options", "methods", "inventory", "quote", "addons", "tiers",
            "library", "templates", "sides", "grow"}
LIMITS = {  # field: (min items, max items, max chars per text) -- see CLAUDE.md "Writing a feature page"
    "benefits": (4, 4, 70), "details": (3, 3, 180), "capabilities": (8, 8, 45), "faqs": (3, 5, 200),
}
import os
FONTS_CSS = pathlib.Path(os.environ["AUDIT_FONTS_CSS"]).read_text() if os.environ.get("AUDIT_FONTS_CSS") else None
problems = []
def bad(slug, msg): problems.append(f"[{slug}] {msg}")


def check_json(slug):
    p = ROOT / "src" / "features" / f"{slug}.json"
    if not p.exists():
        return bad(slug, f"missing {p.relative_to(ROOT)}")
    d = json.loads(p.read_text())
    idx = {f["slug"]: f for f in json.loads((ROOT / "src/features/_index.json").read_text())["features"]}
    if slug not in idx: bad(slug, "not listed in _index.json")
    elif d["details_heading"] != idx[slug]["tagline"]: bad(slug, "details_heading must equal the tagline in _index.json")
    if len(d["hero"]["lead"]) > 260: bad(slug, "hero.lead over 260 chars")
    for key, (lo, hi, mx) in LIMITS.items():
        items = d.get(key, [])
        if not lo <= len(items) <= hi: bad(slug, f"{key}: {len(items)} items (need {lo}-{hi})")
        for it in items:
            txt = it.get("text") or it.get("a") or ""
            if len(txt) > mx: bad(slug, f"{key}: text over {mx} chars: {txt[:40]}...")
            if "icon" in it and it["icon"] not in ICON: bad(slug, f"{key}: unknown icon '{it['icon']}'")
            if "title" in it and len(it["title"]) > 40: bad(slug, f"{key}: title over 40 chars: {it['title']}")
    for r in d["details"]:
        if len(r["points"]) != 3: bad(slug, f"details '{r['title']}' needs exactly 3 points")
        if any(len(x) > 32 for x in r["points"]): bad(slug, f"details '{r['title']}' has a point over 32 chars")
        v = r["visual"]
        names = [v.get("ui"), v.get("back"), v.get("front")]
        for n in names:
            if n and n not in MINI_UIS: bad(slug, f"unknown mini-UI '{n}'")
        if v.get("image") and not (ROOT / f"src/assets/products/{v['image']}.webp").exists():
            bad(slug, f"missing product image '{v['image']}'")
    hv = d["hero"].get("visual")
    if hv and hv.get("layout") == "showcase":
        if hv.get("ui") not in MINI_UIS: bad(slug, f"hero: unknown mini-UI '{hv.get('ui')}'")
        if len(hv.get("chips", [])) > 2: bad(slug, "hero: up to 2 chips")
        if not (ROOT / f"src/assets/heroes/{hv.get('image')}.webp").exists(): bad(slug, f"hero: missing src/assets/heroes/{hv.get('image')}.webp")
    layouts = [r["visual"]["layout"] for r in d["details"]]
    if sorted(layouts) != ["product", "single", "stack"]: bad(slug, f"use each layout once (single, product, stack), got {layouts}")
    for h in ("details_heading", "capabilities_heading", "products_heading"):
        if len(d[h]) != 2: bad(slug, f"{h} must have exactly two lines")
    if any(len(x) > 24 for x in d["products_heading"]): bad(slug, "products_heading: keep each line within 24 chars (it sits in a half-width column)")
    if any(len(x) > 36 for x in d["capabilities_heading"]): bad(slug, "capabilities_heading: keep each line within 36 chars")
    known = json.loads((ROOT / "src/products.json").read_text())
    for prod in d["products"] + [r["visual"]["image"] for r in d["details"] if r["visual"].get("image")]:
        if not (ROOT / f"src/assets/products/{prod}.webp").exists(): bad(slug, f"missing product image '{prod}'")
        if prod not in known: bad(slug, f"product '{prod}' is not in src/products.json")
    if not 6 <= len(d["products"]) <= 14: bad(slug, "products: use 6-14")
    if "—" in json.dumps(d, ensure_ascii=False): bad(slug, "em dash found; use a comma or a full stop")
    return d


async def check_page(slug, d):
    from playwright.async_api import async_playwright
    path = page_path(slug)
    if not path.exists():
        return bad(slug, f"not built: run python3 build.py ({path.relative_to(ROOT)})")
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for scheme in ("light", "dark"):
            for w in (390, 768, 1440):
                pg = await b.new_page(viewport={"width": w, "height": 900}, color_scheme=scheme)
                if FONTS_CSS:  # offline runs only: serve Geist/Inter locally instead of Google Fonts
                    await pg.route("**/fonts.googleapis.com/**", lambda rt: rt.fulfill(status=200, content_type="text/css", body=FONTS_CSS))
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                await pg.goto(path.as_uri()); await pg.wait_for_timeout(800)
                h = await pg.evaluate("document.body.scrollHeight")
                for y in range(0, h, 500):
                    await pg.evaluate(f"window.scrollTo(0,{y})"); await pg.wait_for_timeout(40)
                await pg.wait_for_timeout(600)
                for k in range(await pg.locator("h2.h-anim").count()):   # bring every heading on screen once
                    await pg.locator("h2.h-anim").nth(k).scroll_into_view_if_needed(); await pg.wait_for_timeout(120)
                await pg.wait_for_timeout(900)
                r = await pg.evaluate("""(()=>{const W=document.documentElement.clientWidth;
                  const small=[...document.querySelectorAll('main p, main li, main a, main button')].filter(el=>!el.closest('.mui,.crumbs,.fcomp,.icardx__tab,.icardx__chip,.ipanel,.ipalette,.ed')
                    && el.textContent.trim() && parseFloat(getComputedStyle(el).fontSize)<16).map(el=>el.className||el.tagName);
                  const anim=[...document.querySelectorAll('h2.h-anim')], shown=anim.filter(x=>x.classList.contains('is-in')).length;
                  return {overflow: document.documentElement.scrollWidth > W, small:[...new Set(small)].slice(0,4), reveal:[shown, anim.length]}})()""")
                tag = f"{scheme} {w}px"
                if errs: bad(slug, f"{tag}: JS errors {errs[:2]}")
                if r["overflow"]: bad(slug, f"{tag}: horizontal overflow")
                if r["small"]: bad(slug, f"{tag}: text under 16px: {r['small']}")
                if r["reveal"][0] != r["reveal"][1]: bad(slug, f"{tag}: {r['reveal'][1]-r['reveal'][0]} headings did not reveal")
                if d and w == 1440 and scheme == "light":
                    # attachments overlap the main card's edge (checked once each row is on screen)
                    for k in range(len(d["details"])):
                        await pg.locator(".frow").nth(k).scroll_into_view_if_needed(); await pg.wait_for_timeout(1500)
                        ok = await pg.evaluate(f"""(()=>{{const a=document.querySelectorAll('.fanchor')[{k}]; if(!a) return true; const r=a.getBoundingClientRect();
                          return [...a.querySelectorAll(':scope > .att')].every(t=>{{const q=t.getBoundingClientRect();
                            const touch=!(q.right<r.left||q.left>r.right||q.bottom<r.top||q.top>r.bottom), inside=q.left>=r.left&&q.right<=r.right&&q.top>=r.top&&q.bottom<=r.bottom; return touch&&!inside}})}})()""")
                        if not ok: bad(slug, f"row {k+1}: a chip/badge does not overlap the card edge")
                    n = await pg.evaluate("document.querySelectorAll('.vwall .pcard:not([aria-hidden])').length")
                    if n < len(d["products"]): bad(slug, f"product wall shows {n} of {len(d['products'])} products")
                    lines = await pg.evaluate("""[...document.querySelectorAll('h2 .h-line:not(.h-inline)')].map(l=>Math.round(l.getBoundingClientRect().height/parseFloat(getComputedStyle(l.parentNode).lineHeight)))""")
                    if any(x > 1 for x in lines): bad(slug, f"1440px: a two-tone heading line wraps ({lines}); shorten it")
                if d and d["hero"].get("visual", {}).get("layout") == "showcase":
                    # hero showcase: the photo loads; the UI and every chip overlap the photo's or the stage's edge
                    await pg.evaluate("window.scrollTo(0,0)"); await pg.wait_for_timeout(2200)
                    h = await pg.evaluate("""(()=>{const box=e=>e.getBoundingClientRect(), img=document.querySelector('.fshow__img');
                      const edge=(q,r)=>{const touch=!(q.right<r.left||q.left>r.right||q.bottom<r.top||q.top>r.bottom), inside=q.left>=r.left&&q.right<=r.right&&q.top>=r.top&&q.bottom<=r.bottom; return touch&&!inside};
                      const P=box(document.querySelector('.fshow__photo')), S=box(document.querySelector('.fshow__stage'));
                      const bad=[...document.querySelectorAll('.fshow__ui, .fshow__chip')].filter(e=>getComputedStyle(e).display!=='none').filter(e=>!(edge(box(e),P)||edge(box(e),S))).map(e=>e.className);
                      return {loaded: !!img && img.complete && img.naturalWidth > 0, bad}})()""")
                    if not h["loaded"]: bad(slug, f"{tag}: hero image did not load")
                    if h["bad"]: bad(slug, f"{tag}: hero {h['bad']} does not overlap the photo or stage edge")
                await pg.close()
        await check_menus(b, slug, path)
        if slug in industry_slugs(): await check_industry_hero(b, slug, path)
        if slug == "404": await check_404(b)
        if slug == "partners": await check_partners(b, path)
        if slug == "contact": await check_contact(b, path)
        await b.close()


def industry_slugs():
    """Industries in _index.json that have a page (src/industries/<slug>.json)."""
    idx = json.loads((ROOT / "src/industries/_index.json").read_text())["industries"]
    return [i["slug"] for i in idx if (ROOT / f"src/industries/{i['slug']}.json").exists()]


def page_path(slug):
    if slug == "homepage": return ROOT / "site/index.html"
    if slug == "404": return ROOT / "site/404.html"
    if slug == "partners": return ROOT / "site/partners/index.html"
    if slug == "contact": return ROOT / "site/contact/index.html"
    if slug in industry_slugs(): return ROOT / f"site/industries/{slug}/index.html"
    return ROOT / f"site/features/{slug}/index.html"


def check_industry_json(slug):
    """Industry page content (src/industries/<slug>.json): see CLAUDE.md "Industry pages"."""
    d = json.loads((ROOT / f"src/industries/{slug}.json").read_text())
    known = json.loads((ROOT / "src/products.json").read_text())
    for k in ("hero", "products_heading", "products", "products_cta", "stats_heading", "stats_lead", "stats", "merchants_heading", "merchants", "faqs"):
        if k not in d: bad(slug, f"missing '{k}'")
    st = d["hero"]["stage"]
    if not 3 <= len(st["deck"]) <= 5: bad(slug, f"hero deck: {len(st['deck'])} cards (need 3-5)")
    if len(st["actions"]) != 3: bad(slug, "hero: exactly 3 panel actions")
    for a in st["actions"]:
        if a["icon"] not in ICON: bad(slug, f"hero: unknown icon '{a['icon']}'")
    for c in st["deck"]:
        if not 0 <= c["swatch"] < len(st["swatches"]): bad(slug, f"hero: '{c['label']}' swatch {c['swatch']} out of range")
    imgs = [c["product"] for c in st["deck"]] + [p["image"] for p in d["products"]] + [m["preview"] for m in d["merchants"]]
    for i in imgs:
        if i not in known or not (ROOT / f"src/assets/products/{i}.webp").exists(): bad(slug, f"product image '{i}' is not in src/products.json")
    if len(d["stats"]) != 3: bad(slug, "stats: exactly 3")
    if not 3 <= len(d["faqs"]) <= 5: bad(slug, "faqs: 3-5")
    for f in d["faqs"]:
        if len(f["a"]) > 200: bad(slug, f"faq answer over 200 chars: {f['a'][:40]}...")
    for h in ("products_heading", "stats_heading", "merchants_heading"):
        if len(d[h]) != 2: bad(slug, f"{h} must have exactly two lines")
    if "—" in json.dumps(d, ensure_ascii=False): bad(slug, "em dash found; use a comma or a full stop")
    return d


async def check_industry_hero(b, slug, path):
    """The customizing deck (docs/industry-hero-spec.md): panel, palette and chip overlap the front card's edges."""
    for w in (1440, 390):
        pg = await b.new_page(viewport={"width": w, "height": 900})
        await pg.emulate_media(reduced_motion="reduce")      # the settled, coloured first card
        await pg.goto(path.as_uri()); await pg.wait_for_timeout(700)
        r = await pg.evaluate("""(async()=>{const box=e=>e.getBoundingClientRect();
          const edge=(q,r)=>{const touch=!(q.right<r.left||q.left>r.right||q.bottom<r.top||q.top>r.bottom), inside=q.left>=r.left&&q.right<=r.right&&q.top>=r.top&&q.bottom<=r.bottom; return touch&&!inside};
          const front=document.querySelector('.icardx[data-front]'); if(!front) return {missing:true};
          const C=box(front), out=[];
          for (const [name, el] of [['panel', document.querySelector('.ipanel')], ['palette', document.querySelector('.ipalette')], ['chip', front.querySelector('.icardx__chip')]])
            if (!el || !edge(box(el), C)) out.push(name);
          return {detached: out, overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth}})()""")
        if r.get("missing"): bad(slug, f"hero {w}px: no front card"); await pg.close(); continue
        if r["detached"]: bad(slug, f"hero {w}px: {r['detached']} do not overlap the front card's edge")
        if r["overflow"]: bad(slug, f"hero {w}px: horizontal overflow")
        await pg.close()
    # interaction (motion on): the loop advances on its own when not hovered; each tab brings its card to the front
    pg = await b.new_page(viewport={"width": 1440, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(path.as_uri()); await pg.mouse.move(4, 896)
    FRONT = "document.querySelector('.icardx[data-front]').getAttribute('aria-label')"
    first = await pg.evaluate(FRONT)
    try:
        await pg.wait_for_function(f"{FRONT} !== {json.dumps(first)}", timeout=8000)
    except Exception:
        bad(slug, "hero: the deck does not advance on its own")
    labels = await pg.evaluate("[...document.querySelectorAll('.icardx')].map(c=>c.getAttribute('aria-label'))")
    for k, lab in enumerate(labels):
        tab = pg.locator(f'.icardx[data-k="{k}"] .icardx__tab')
        if await pg.evaluate(FRONT) == lab: continue
        if not await tab.is_visible(): continue
        await tab.click(); await pg.wait_for_timeout(700)
        if await pg.evaluate(FRONT) != lab: bad(slug, f"hero: clicking the '{lab}' tab does not bring it to the front")
    if errs: bad(slug, f"hero: JS errors {errs[:2]}")
    await pg.close()


async def check_contact(b, path):
    """Contact: each topic changes the placeholder and the visible fields; required fields block submit with errors;
    the copy button works; both office clocks show a time and a badge; links in the page resolve; no overflow at 390."""
    slug = "contact"
    for w in (1440, 390):
        ctx = await b.new_context(viewport={"width": w, "height": 900}, permissions=["clipboard-read", "clipboard-write"])
        pg = await ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(path.as_uri()); await pg.wait_for_timeout(500)
        S = """(()=>({ph:document.querySelector('[name="message"]').placeholder, topic:document.querySelector('[name="topic"]').value,
              hidden:[...document.querySelectorAll('.cform .cfx.is-hidden')].map(e=>e.dataset.f).sort()}))()"""
        base = await pg.evaluate(S)
        if base["hidden"] != ["best_time", "partner"]: bad(slug, f"{w}px: default state should show every field but 'Best time to talk' ({base['hidden']})")
        seen = set()
        for t in await pg.evaluate("[...document.querySelectorAll('.ctopic')].map(c=>c.dataset.topic)"):
            await pg.click(f'.ctopic[data-topic="{t}"]'); await pg.wait_for_timeout(420); st = await pg.evaluate(S)
            if t == "partners":
                if "fields" not in st["hidden"] or "partner" in st["hidden"]: bad(slug, f"{w}px: Partnerships does not swap the form for the partner note")
                continue
            seen.add(st["ph"])
            if st["ph"] == base["ph"] or not st["topic"]: bad(slug, f"{w}px: topic '{t}' does not change the placeholder / topic value")
            if t == "demo" and "best_time" in st["hidden"]: bad(slug, f"{w}px: Book a demo does not show 'Best time to talk'")
            if t == "billing" and "using" not in st["hidden"]: bad(slug, f"{w}px: Billing does not hide 'I'm using'")
        if len(seen) < 4: bad(slug, f"{w}px: topics do not each have their own placeholder")
        await pg.click('.ctopic[data-topic="setup"]'); await pg.wait_for_timeout(400)
        await pg.locator(".cform .form__submit").scroll_into_view_if_needed(); await pg.click(".cform .form__submit"); await pg.wait_for_timeout(200)
        f = await pg.evaluate("""(()=>({invalid:document.querySelectorAll('.cform .field.is-invalid').length, focused:document.activeElement && document.activeElement.getAttribute('aria-invalid'),
            status:document.querySelector('.cform .form__status').textContent}))()""")
        if f["invalid"] < 4 or f["focused"] != "true" or f["status"]: bad(slug, f"{w}px: an empty submit is not blocked with inline errors and focus on the first ({f})")
        await pg.locator(".cch__copy").scroll_into_view_if_needed(); await pg.click(".cch__copy"); await pg.wait_for_timeout(250)
        if not (await pg.text_content(".cch__copied")).strip(): bad(slug, f"{w}px: the copy button does not confirm")
        if w == 1440:
            try:
                if (await pg.evaluate("navigator.clipboard.readText()")) != await pg.get_attribute(".cch__copy", "data-copy"): bad(slug, "the copy button does not copy the address")
            except Exception: pass
        clocks = await pg.evaluate("[...document.querySelectorAll('.coff')].map(o=>[o.querySelector('.coff__time').textContent, o.querySelector('.coff__badge').textContent])")
        if len(clocks) != 2 or any(not __import__('re').match(r"^\d{1,2}:\d{2}\s?[AP]M$", t) or not b_ for t, b_ in clocks): bad(slug, f"{w}px: office clocks or badges missing ({clocks})")
        links = await pg.evaluate("""[...document.querySelectorAll('main a[href]')].map(a=>a.getAttribute('href')).filter(h=>!/^(#|https?:|mailto:|tel:)/.test(h))""")
        for h in links:
            t = (path.parent / h.split("#")[0]).resolve(); t = t / "index.html" if h.split("#")[0].endswith("/") else t
            if not t.exists(): bad(slug, f"{w}px: link {h} does not resolve")
        if await pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"): bad(slug, f"{w}px: horizontal overflow")
        if errs: bad(slug, f"{w}px: JS errors {errs[:2]}")
        await ctx.close()


async def check_partners(b, path):
    """Partners: tabs and search change the visible cards and counts; "Show more" reveals the rest; the form blocks an
    empty submit with inline errors; external links open in a new tab; no overflow at 390px."""
    slug = "partners"
    for w in (1440, 390):
        pg = await b.new_page(viewport={"width": w, "height": 900}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(path.as_uri()); await pg.wait_for_timeout(400)
        S = """(()=>{const v=[...document.querySelectorAll('.ptr')].filter(c=>!c.hidden);
          return {shown:v.length, types:[...new Set(v.map(c=>c.dataset.type))], more:!document.querySelector('.pdir__more').hidden,
                  empty:!document.querySelector('.pdir__empty').hidden,
                  counts:Object.fromEntries([...document.querySelectorAll('.pdir__tab')].map(t=>[t.dataset.type, +t.querySelector('.pdir__count').textContent]))}})()"""
        total = await pg.evaluate("document.querySelectorAll('.ptr').length"); vis = int(await pg.evaluate("+document.querySelector('.pdir__grid').dataset.visible"))
        st = await pg.evaluate(S)
        if total > vis and (st["shown"] != vis or not st["more"]): bad(slug, f"{w}px: expected {vis} cards and 'Show more' at first, got {st['shown']}")
        await pg.click(".pdir__more button"); st = await pg.evaluate(S)
        if st["shown"] != total or st["more"]: bad(slug, f"{w}px: 'Show more' does not reveal all {total} partners")
        await pg.click('.pdir__tab[data-type="theme"]'); st = await pg.evaluate(S)
        if st["types"] != ["theme"] or st["shown"] != st["counts"]["theme"]: bad(slug, f"{w}px: the Theme providers tab does not filter the cards ({st})")
        await pg.click('.pdir__tab[data-type="all"]'); await pg.fill(".pdir__search input", "agency"); st = await pg.evaluate(S)
        if not 0 < st["shown"] < total or st["counts"]["all"] != st["shown"]: bad(slug, f"{w}px: search does not filter cards and counts ({st})")
        await pg.fill(".pdir__search input", "zzzz-no-match"); st = await pg.evaluate(S)
        if st["shown"] or not st["empty"]: bad(slug, f"{w}px: no empty state when nothing matches")
        await pg.click(".pdir__clear"); st = await pg.evaluate(S)
        if st["empty"] or st["counts"]["all"] != total: bad(slug, f"{w}px: 'Clear filters' does not reset the directory")
        ext = await pg.evaluate("""[...document.querySelectorAll('main a[href^="http"]')].filter(a=>a.target!=='_blank'||!/noopener/.test(a.rel)).map(a=>a.href)""")
        if ext: bad(slug, f"{w}px: external links without target=_blank rel=noopener: {ext[:2]}")
        await pg.locator(".form__submit").scroll_into_view_if_needed(); await pg.click(".form__submit"); await pg.wait_for_timeout(200)
        f = await pg.evaluate("""(()=>({invalid:document.querySelectorAll('.form .field.is-invalid').length, errs:[...document.querySelectorAll('.form .field__err')].filter(e=>e.textContent.trim()).length,
            status:document.querySelector('.form__status').textContent}))()""")
        if f["invalid"] < 4 or f["errs"] < 4 or f["status"]: bad(slug, f"{w}px: an empty submit is not blocked with inline errors ({f})")
        if await pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"): bad(slug, f"{w}px: horizontal overflow")
        if errs: bad(slug, f"{w}px: JS errors {errs[:2]}")
        await pg.close()


def serve_site():
    """A local stand-in for GitHub Pages: site/ under SITE_BASE, and 404.html (status 404) for any missing path."""
    import http.server, threading, os
    base = os.environ.get("SITE_BASE", "/inkybay-website/"); site = ROOT / "site"
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            path = self.path.split("?")[0].split("#")[0]; f = None
            if path.startswith(base):
                f = site / path[len(base):]
                if f.is_dir(): f = f / "index.html"
            ok = f is not None and f.is_file()
            body = (f if ok else site / "404.html").read_bytes()
            self.send_response(200 if ok else 404); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}{base}"


async def check_404(b):
    """The interactive 404: served at any depth with working links; the layer drags and resizes; the warning shows
    when it leaves the print area and clears when it is back; nothing overflows at 390px."""
    srv, base = serve_site(); slug = "404"
    try:
        hrefs = None
        for depth in ("nope/", "a/b/c", "x/y/z/w.html"):
            pg = await b.new_page(viewport={"width": 1440, "height": 900})
            r = await pg.goto(base + depth)
            if r.status != 404 or not await pg.locator(".ed").count(): bad(slug, f"{depth}: missing URL does not show the 404 editor (status {r.status})")
            links = await pg.evaluate("""[...document.querySelectorAll('a[href]')].filter(a=>!a.getAttribute('href').startsWith('#')).map(a=>a.href).filter(h=>h.startsWith(location.origin))""")
            srcs = await pg.evaluate("""[...document.querySelectorAll('[src]')].map(e=>e.getAttribute('src')).filter(s=>!/^(data:|https?:)/.test(s))""")
            if srcs: bad(slug, f"{depth}: relative asset paths {srcs[:2]}")
            if any(not l.startswith(base) for l in links): bad(slug, f"{depth}: a link leaves SITE_BASE: {[l for l in links if not l.startswith(base)][:2]}")
            if hrefs is None: hrefs = sorted(set(links))
            elif sorted(set(links)) != hrefs: bad(slug, f"{depth}: links differ by depth (relative links)")
            await pg.close()
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        for u in sorted({h.split("#")[0] for h in hrefs or []}):
            target = ROOT / "site" / u[len(base):]
            if target.is_dir(): target = target / "index.html"
            if target.is_file():
                st = (await pg.request.get(u)).status
                if st != 200: bad(slug, f"link {u[len(base)-1:]} returns {st}")
        await pg.close()
        for w in (1440, 390):
            pg = await b.new_page(viewport={"width": w, "height": 900})
            await pg.add_init_script("try{localStorage.setItem('ib404-hinted','1')}catch(e){}")
            await pg.goto(base + "nope/"); await pg.locator(".ed__canvas").scroll_into_view_if_needed(); await pg.wait_for_timeout(500)
            v = lambda k: pg.evaluate(f"parseFloat(getComputedStyle(document.querySelector('.ed__layer')).getPropertyValue('--{k}'))")
            async def drag(sel, dx, dy):
                bx = await pg.locator(sel).bounding_box(); x, y = bx["x"] + bx["width"] / 2, bx["y"] + bx["height"] / 2
                await pg.mouse.move(x, y); await pg.mouse.down()
                for k in range(1, 9): await pg.mouse.move(x + dx * k / 8, y + dy * k / 8)
                await pg.mouse.up(); await pg.wait_for_timeout(350)
            x0 = await v("x"); await drag(".ed__text", 24, 8)
            if abs(await v("x") - x0) < .01: bad(slug, f"{w}px: dragging the layer does not move it")
            s0 = await v("s"); await drag(".ed__h--se", 20, 14)
            if await v("s") <= s0: bad(slug, f"{w}px: dragging a corner handle does not resize the layer")
            await pg.click(".ed__reset"); await pg.wait_for_timeout(300)     # back to the start size before the out-and-back test
            pw = (await pg.locator(".ed__pa").bounding_box())["width"]
            await drag(".ed__text", pw * .9, 0)
            out = await pg.evaluate("[document.querySelector('.ed').classList.contains('is-out'), +getComputedStyle(document.querySelector('.ed__warn')).opacity]")
            if not (out[0] and out[1] > .9): bad(slug, f"{w}px: the 'Outside print area' warning does not show when the layer leaves the print area")
            await drag(".ed__text", -pw * .9, 0)
            if await pg.evaluate("document.querySelector('.ed').classList.contains('is-out')"): bad(slug, f"{w}px: the warning does not clear when the layer is back inside")
            if await pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"): bad(slug, f"{w}px: horizontal overflow")
            await pg.close()
    finally:
        srv.shutdown()


def nav_expected():
    """{menu id: number of links} from src/nav.json (grid items from their index file, or the sum of group items)."""
    out = {}
    for m in json.loads((ROOT / "src/nav.json").read_text())["menus"]:
        if m["layout"] == "groups": out[m["id"]] = sum(len(g["items"]) for g in m["groups"])
        elif "items_from" in m: out[m["id"]] = len(next(v for v in json.loads((ROOT / m["items_from"]).read_text()).values() if isinstance(v, list)))
        else: out[m["id"]] = len(m.get("items", []))
    return out


async def check_menus(b, slug, path):
    """Every mega menu at 1366 and 1440px: opens alone, nothing cut off, promo image loads, Esc and outside click close.
    At 390px: every menu's sub-list opens in the mobile sheet with the right number of links."""
    exp = nav_expected()
    for w in (1366, 1440):
        pg = await b.new_page(viewport={"width": w, "height": 900}); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(path.as_uri()); await pg.wait_for_timeout(500)
        tag = f"menus {w}px"
        for mid in exp:
            t = pg.locator(f"#nav-{mid}")
            if not await t.count(): bad(slug, f"{tag}: no trigger #nav-{mid}"); continue
            if await t.get_attribute("aria-controls") != f"mega-{mid}": bad(slug, f"{tag}: #nav-{mid} has no aria-controls=mega-{mid}")
            await t.click(); await pg.wait_for_timeout(450)    # opens directly, even while another menu is open
            r = await pg.evaluate(f"""(()=>{{const m=document.getElementById('mega-{mid}');
              const open=[...document.querySelectorAll('.mega[data-open="true"]')].map(x=>x.id);
              const cut=[...m.querySelectorAll('.mega__desc')].filter(x=>x.scrollHeight>x.clientHeight+1).map(x=>x.textContent);
              const imgs=[...m.querySelectorAll('.mega__promo img')], promo=getComputedStyle(m.querySelector('.mega__promo')).display!=='none';
              return {{open, cut, imgs: imgs.length, loaded: imgs.every(i=>i.complete&&i.naturalWidth>0), promo,
                       expanded: document.getElementById('nav-{mid}').getAttribute('aria-expanded')}}}})()""")
            if r["open"] != [f"mega-{mid}"]: bad(slug, f"{tag}: opening {mid} leaves open {r['open']} (need exactly mega-{mid})")
            if r["expanded"] != "true": bad(slug, f"{tag}: #nav-{mid} aria-expanded is not true when open")
            if r["cut"]: bad(slug, f"{tag}: {mid} description cut off (two lines max): {r['cut'][:2]}")
            if r["promo"] and (not r["imgs"] or not r["loaded"]): bad(slug, f"{tag}: {mid} promo image did not load")
        mid = next(iter(exp))
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("[[...document.querySelectorAll('.mega[data-open=\"true\"]')].length, document.activeElement && document.activeElement.id]")
        if r[0]: bad(slug, f"{tag}: Esc does not close the open menu")
        await pg.click(f"#nav-{mid}"); await pg.wait_for_timeout(400)
        await pg.mouse.click(4, 896); await pg.wait_for_timeout(300)
        if await pg.evaluate("document.querySelectorAll('.mega[data-open=\"true\"]').length"): bad(slug, f"{tag}: outside click does not close the menu")
        if errs: bad(slug, f"{tag}: JS errors {errs[:2]}")
        await pg.close()
    pg = await b.new_page(viewport={"width": 390, "height": 844})
    await pg.goto(path.as_uri()); await pg.wait_for_timeout(500)
    await pg.click(".nav__toggle"); await pg.wait_for_timeout(400)
    for mid, n in exp.items():
        t = pg.locator(f'.sheet-toggle[aria-controls="sheet-{mid}"]')
        if not await t.count(): bad(slug, f"menus 390px: no sheet toggle for {mid}"); continue
        await t.click(); await pg.wait_for_timeout(550)
        r = await pg.evaluate(f"""(()=>{{const u=document.getElementById('sheet-{mid}'), h=u.getBoundingClientRect().height;
          return {{links: u.querySelectorAll('a').length, open: h > 0 && h >= u.scrollHeight - 1}}}})()""")
        if not r["open"]: bad(slug, f"menus 390px: {mid} sub-list does not open fully in the sheet")
        if r["links"] != n: bad(slug, f"menus 390px: {mid} sub-list has {r['links']} links, nav.json has {n}")
    await pg.close()


def main():
    args = sys.argv[1:]
    if args == ["--all"]:
        args = ["homepage", "404", "partners", "contact"] + sorted(x.stem for x in (ROOT / "src/features").glob("*.json") if not x.name.startswith("_")) + industry_slugs()
    if not args:
        print(__doc__); sys.exit(1)
    for slug in args:
        if slug in ("404", "partners", "contact"):
            asyncio.run(check_page(slug, None))
        elif slug in industry_slugs():
            check_industry_json(slug); asyncio.run(check_page(slug, None))
        else:
            d = None if slug == "homepage" else check_json(slug)
            asyncio.run(check_page(slug, d))
    if problems:
        print("FAIL\n  " + "\n  ".join(problems)); sys.exit(1)
    print(f"PASS: {', '.join(args)}")


if __name__ == "__main__":
    main()
