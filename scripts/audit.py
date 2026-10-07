"""Audit feature pages before committing.

    python3 scripts/audit.py <slug> [<slug> ...]     # check JSON + built page(s)
    python3 scripts/audit.py --all                   # every page in src/features + the homepage

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
    for prod in d["products"]:
        if not (ROOT / f"src/assets/products/{prod}.webp").exists(): bad(slug, f"missing product image '{prod}'")
    if not 6 <= len(d["products"]) <= 14: bad(slug, "products: use 6-14")
    if "—" in json.dumps(d, ensure_ascii=False): bad(slug, "em dash found; use a comma or a full stop")
    return d


async def check_page(slug, d):
    from playwright.async_api import async_playwright
    path = ROOT / "site" / ("index.html" if slug == "homepage" else f"features/{slug}/index.html")
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
                  const small=[...document.querySelectorAll('main p, main li, main a, main button')].filter(el=>!el.closest('.mui,.crumbs,.fcomp')
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
                if w == 1440 and scheme == "light":
                    await pg.evaluate("window.scrollTo(0,0)"); await pg.wait_for_timeout(300)
                    await pg.click("#nav-features"); await pg.wait_for_timeout(500)
                    t = await pg.evaluate("[...document.querySelectorAll('.mega__desc')].some(x=>x.scrollHeight>x.clientHeight+1)")
                    if t: bad(slug, "mega menu: a description is cut off; shorten its 'short' text in _index.json")
                await pg.close()
        await b.close()


def main():
    args = sys.argv[1:]
    if args == ["--all"]:
        args = ["homepage"] + sorted(x.stem for x in (ROOT / "src/features").glob("*.json") if not x.name.startswith("_"))
    if not args:
        print(__doc__); sys.exit(1)
    for slug in args:
        d = None if slug == "homepage" else check_json(slug)
        asyncio.run(check_page(slug, d))
    if problems:
        print("FAIL\n  " + "\n  ".join(problems)); sys.exit(1)
    print(f"PASS: {', '.join(args)}")


if __name__ == "__main__":
    main()
