"""Check the measured print areas (src/video/print-areas.json) and render a debug sheet.

    python3 scripts/check_print_areas.py [out.png]

1. Every pixel inside each quad must sit on the product (alpha > 0.95).
2. "Your name" is placed with src/video/print-text.js (fit-to-box, matrix3d, curve, alpha mask, print look) and the
   rendered text must stay inside the quad. The sheet shows each product with its quad in editor blue.
Exit code 0 = pass.
"""
import json, sys, base64, pathlib, asyncio
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
AREAS = {k: v for k, v in json.loads((ROOT / "src/video/print-areas.json").read_text()).items() if not k.startswith("_")}


def inside(x, y, q):
    s = None
    for i in range(4):
        (x1, y1), (x2, y2) = q[i], q[(i + 1) % 4]; c = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if c:
            if s is None: s = c > 0
            elif (c > 0) != s: return False
    return True


def alpha_check():
    bad = []
    for name, a in AREAS.items():
        im = Image.open(ROOT / f"src/assets/products/{name}.webp").convert("RGBA"); W, H = im.size; al = im.getchannel("A")
        xs = [p[0] for p in a["quad"]]; ys = [p[1] for p in a["quad"]]; n = off = 0
        for y in range(int(min(ys) * H), int(max(ys) * H) + 1):
            for x in range(int(min(xs) * W), int(max(xs) * W) + 1):
                if inside(x / W, y / H, a["quad"]):
                    n += 1
                    if al.getpixel((min(x, W - 1), min(y, H - 1))) <= 242: off += 1
        print(f"  {name:9} {n} quad pixels, {off} not on the product")
        if off: bad.append(name)
    return bad


async def render(out):
    from playwright.async_api import async_playwright
    js = (ROOT / "src/video/print-text.js").read_text()
    tiles = "".join(f'<div class="tile"><div class="stage" data-name="{n}"><img src="data:image/webp;base64,{base64.b64encode((ROOT / f"src/assets/products/{n}.webp").read_bytes()).decode()}">'
                    f'<svg class="quad" viewBox="0 0 1 1" preserveAspectRatio="none"><polygon points="{" ".join(f"{x},{y}" for x, y in a["quad"])}" fill="none" stroke="#1C8CF0" stroke-width="0.004"/></svg></div><p>{n}</p></div>'
                    for n, a in AREAS.items())
    html = f"""<!doctype html><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Geist:wght@600;700&display=swap" rel="stylesheet">
<style>body{{margin:0;background:#fff;font:14px Inter,sans-serif;display:flex;gap:16px;padding:16px}}.tile{{text-align:center}}
.stage{{position:relative;width:480px;height:480px;background:#F2F0ED;border-radius:12px;overflow:hidden}}.stage img{{position:absolute;inset:0;width:100%;height:100%}}
.quad{{position:absolute;inset:0;width:100%;height:100%;z-index:3}}</style>{tiles}<script>{js}</script>"""
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 5 * 496 + 16, "height": 540}, device_scale_factor=2)
        await pg.set_content(html); await pg.evaluate("Promise.all([document.fonts.load('700 20px Geist'), document.fonts.load('600 20px Geist')]).then(() => document.fonts.ready)"); await pg.wait_for_timeout(300)
        res = await pg.evaluate("""(areas)=>[...document.querySelectorAll('.stage')].map(st=>{const n=st.dataset.name;
            const r=PrintText.place(st, areas[n], 'Your name', {image: st.querySelector('img').src, color:'#E5380F'});
            const sr=st.getBoundingClientRect(), tr=st.querySelector('.pt-text').getBoundingClientRect(), q=areas[n].quad.map(p=>[sr.left+p[0]*sr.width, sr.top+p[1]*sr.height]);
            const xs=q.map(p=>p[0]), ys=q.map(p=>p[1]);
            return {name:n, fontPx:Math.round(r.fontPx*10)/10, textInQuadBox: tr.left>=Math.min(...xs)-1 && tr.right<=Math.max(...xs)+1 && tr.top>=Math.min(...ys)-1 && tr.bottom<=Math.max(...ys)+1}})""", AREAS)
        await pg.wait_for_timeout(200); await pg.screenshot(path=str(out)); await b.close()
    return res


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "print-areas-debug.png"
    print("alpha under every quad:"); bad = alpha_check()
    res = asyncio.run(render(out))
    for r in res:
        print(f"  {r['name']:9} 'Your name' at {r['fontPx']}px (on a 480px product), inside its quad: {r['textInQuadBox']}")
        if not r["textInQuadBox"]: bad.append(r["name"])
    print("debug sheet:", out)
    if bad: print("FAIL:", bad); sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
