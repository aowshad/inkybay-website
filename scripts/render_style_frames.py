"""Render the hero video style frames: src/video/style-frames.html -> src/video/style-frames/<id>.png (1920x1080).

    python3 scripts/render_style_frames.py [contact-sheet.png]

Serves src/ over http (the page fetches print-areas.json), waits for the fonts and the print text, renders each
.stage at 2x and downsizes to 1920x1080 for crisp edges. With an argument it also writes the three side by side.
"""
import asyncio, functools, http.server, pathlib, sys, threading
from playwright.async_api import async_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "video" / "style-frames"
IDS = ["open", "editor", "order"]


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = functools.partial(Quiet, directory=str(ROOT / "src"))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    srv = serve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(f"http://127.0.0.1:{srv.server_port}/video/style-frames.html", wait_until="networkidle", timeout=90000)
        await pg.evaluate("window.framesReady.then(() => document.fonts.ready)")
        for i in IDS:
            tmp = OUT / f"{i}@2x.png"
            await pg.locator(f"#{i}").screenshot(path=str(tmp))
            Image.open(tmp).convert("RGB").resize((1920, 1080), Image.LANCZOS).save(OUT / f"{i}.png", optimize=True)
            tmp.unlink()
        await b.close()
    srv.shutdown()
    if errs:
        sys.exit("page errors: " + "; ".join(errs))
    if len(sys.argv) > 1:
        ims = [Image.open(OUT / f"{i}.png") for i in IDS]
        sheet = Image.new("RGB", (1920 * 3 + 80, 1080), (210, 210, 210))
        for k, im in enumerate(ims):
            sheet.paste(im, (k * 1960, 0))
        sheet.save(sys.argv[1])
    print("ok -> " + ", ".join(str((OUT / f"{i}.png").relative_to(ROOT)) for i in IDS))


asyncio.run(main())
