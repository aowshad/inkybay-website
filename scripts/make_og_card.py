"""Make the social share card: src/assets/brand/og-card.jpg (1200x630), used as og:image / twitter:image on every page
without its own image. Copy comes from src/site.json ("social"); the look follows the hero video (warm ground, one
brand glow, the 3D logo, Geist 600).

    python3 scripts/make_og_card.py
"""
import asyncio, base64, json, pathlib
from playwright.async_api import async_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
A = ROOT / "src" / "assets"


def data(p, kind):
    return f"data:{kind};base64," + base64.b64encode((A / p).read_bytes()).decode()


async def main():
    s = json.loads((ROOT / "src" / "site.json").read_text())["social"]
    html = f"""<style>
      @font-face {{ font-family: Geist; src: url({data('fonts/geist-latin.woff2', 'font/woff2')}); font-weight: 400 700; }}
      @font-face {{ font-family: Inter; src: url({data('fonts/inter-latin.woff2', 'font/woff2')}); font-weight: 400 700; }}
      html, body {{ margin: 0; }}
      .c {{ position: relative; width: 1200px; height: 630px; overflow: hidden; background: linear-gradient(160deg, #FFF7F0, #FFFFFF 70%); font-family: Inter; }}
      .g {{ position: absolute; width: 900px; height: 900px; right: -220px; top: -260px; border-radius: 50%;
           background: radial-gradient(circle, rgba(255,117,0,.22), rgba(255,117,0,0) 65%); }}
      .t {{ position: absolute; left: 80px; top: 50%; transform: translateY(-50%); width: 640px; }}
      h1 {{ margin: 0; font: 600 64px/1.05 Geist; letter-spacing: -.035em; color: #1B1714; }}
      p {{ margin: 28px 0 0; font: 500 28px/1.3 Inter; color: #6E6660; }}
      img {{ position: absolute; right: 90px; top: 50%; width: 360px; transform: translateY(-50%) rotate(-4deg); filter: drop-shadow(0 30px 40px rgba(120,30,10,.3)); }}
    </style><div class="c"><div class="g"></div><div class="t"><h1>{s['headline']}</h1><p>{s['line']}</p></div><img src="{data('brand/inkybay-3d.webp', 'image/webp')}"></div>"""
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=2)
        await pg.set_content(html); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        tmp = A / "brand" / "og-card@2x.png"; await pg.screenshot(path=str(tmp)); await b.close()
    Image.open(tmp).convert("RGB").resize((1200, 630), Image.LANCZOS).save(A / "brand" / "og-card.jpg", "JPEG", quality=88, optimize=True, progressive=True)
    tmp.unlink(); print("ok -> src/assets/brand/og-card.jpg")


asyncio.run(main())
