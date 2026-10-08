"""Audit feature pages before committing.

    python3 scripts/audit.py <slug> [<slug> ...]     # check JSON + built page(s)
    python3 scripts/audit.py --all                   # the homepage, every feature page and every industry page

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
                  const small=[...document.querySelectorAll('main p, main li, main a, main button')].filter(el=>!el.closest('.mui,.crumbs,.fcomp,.icardx__tab,.icardx__chip,.ipanel,.ipalette')
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
        await b.close()


def industry_slugs():
    """Industries in _index.json that have a page (src/industries/<slug>.json)."""
    idx = json.loads((ROOT / "src/industries/_index.json").read_text())["industries"]
    return [i["slug"] for i in idx if (ROOT / f"src/industries/{i['slug']}.json").exists()]


def page_path(slug):
    if slug == "homepage": return ROOT / "site/index.html"
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
    """The customizing deck (docs/industry-hero-spec.md): panel, palette and chip overlap the front card's edges;
    the result text sits inside the product's bounding box (from the image's alpha)."""
    for w in (1440, 390):
        pg = await b.new_page(viewport={"width": w, "height": 900})
        await pg.emulate_media(reduced_motion="reduce")      # the settled, customized first card
        await pg.goto(path.as_uri()); await pg.wait_for_timeout(700)
        r = await pg.evaluate("""(async()=>{const box=e=>e.getBoundingClientRect();
          const edge=(q,r)=>{const touch=!(q.right<r.left||q.left>r.right||q.bottom<r.top||q.top>r.bottom), inside=q.left>=r.left&&q.right<=r.right&&q.top>=r.top&&q.bottom<=r.bottom; return touch&&!inside};
          const front=document.querySelector('.icardx[data-front]'); if(!front) return {missing:true};
          const C=box(front), out=[];
          for (const [name, el] of [['panel', document.querySelector('.ipanel')], ['palette', document.querySelector('.ipalette')], ['chip', front.querySelector('.icardx__chip')]])
            if (!el || !edge(box(el), C)) out.push(name);
          const img=front.querySelector('.icardx__img'); await img.decode().catch(()=>{});
          const cv=document.createElement('canvas'); cv.width=img.naturalWidth; cv.height=img.naturalHeight; const g=cv.getContext('2d'); g.drawImage(img,0,0);
          const a=g.getImageData(0,0,cv.width,cv.height).data; let x0=1e9,y0=1e9,x1=-1,y1=-1;
          for(let y=0;y<cv.height;y+=2) for(let x=0;x<cv.width;x+=2){ if(a[(y*cv.width+x)*4+3]>40){ if(x<x0)x0=x; if(x>x1)x1=x; if(y<y0)y0=y; if(y>y1)y1=y; } }
          const I=box(img), sx=I.width/cv.width, sy=I.height/cv.height, P={left:I.left+x0*sx, right:I.left+x1*sx, top:I.top+y0*sy, bottom:I.top+y1*sy};
          const T=box(front.querySelector('.icardx__text'));
          const textIn = T.width>0 && T.left>=P.left-1 && T.right<=P.right+1 && T.top>=P.top-1 && T.bottom<=P.bottom+1;
          return {detached: out, textIn, overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth}})()""")
        if r.get("missing"): bad(slug, f"hero {w}px: no front card"); await pg.close(); continue
        if r["detached"]: bad(slug, f"hero {w}px: {r['detached']} do not overlap the front card's edge")
        if not r["textIn"]: bad(slug, f"hero {w}px: result text is not inside the product's bounding box")
        if r["overflow"]: bad(slug, f"hero {w}px: horizontal overflow")
        await pg.close()


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
        args = ["homepage"] + sorted(x.stem for x in (ROOT / "src/features").glob("*.json") if not x.name.startswith("_")) + industry_slugs()
    if not args:
        print(__doc__); sys.exit(1)
    for slug in args:
        if slug in industry_slugs():
            check_industry_json(slug); asyncio.run(check_page(slug, None))
        else:
            d = None if slug == "homepage" else check_json(slug)
            asyncio.run(check_page(slug, d))
    if problems:
        print("FAIL\n  " + "\n  ".join(problems)); sys.exit(1)
    print(f"PASS: {', '.join(args)}")


if __name__ == "__main__":
    main()
