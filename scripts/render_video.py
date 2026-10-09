"""Render the hero video: src/video/hero-promo.html -> src/assets/video/hero-promo.{mp4,webm,webp}.

    python3 scripts/render_video.py                  # render, verify, encode (needs ffmpeg)
    python3 scripts/render_video.py --sheet out.png  # only 8 evenly spaced frames in one image (no ffmpeg needed)
    python3 scripts/render_video.py --check          # run the per-frame checks on all 300 frames (no ffmpeg needed)
    python3 scripts/render_video.py --frames DIR     # encode frames kept from a run whose encoding failed

Serves src/ over http, opens the page at 1920x1080 with deviceScaleFactor 2 (3840x2160) once the fonts, images and
print text are ready, and puts the film at each time with window.seek(t). Renders 60 fps, blends frame pairs into
30 fps (a touch of natural motion blur), downsizes to 1600x900 and checks every frame:
  - every text layer marked data-on-product stays on its product's alpha (sampled points of every word or letter),
  - nothing visible clips the canvas edge (products by their own outline, cards, chips, type, the logo),
  - the first and last frames differ by less than 1% (a seamless loop).
Failing frames are listed and nothing is encoded. Then: H.264 High yuv420p +faststart and VP9, 1600x900, no audio,
each under 2.5 MB (H.264 one pass at a CRF, since x264 cannot pair CRF with two passes; VP9 two-pass
constrained quality; the CRF is raised before anything else changes), and the poster (frame 0, WebP q82).
Temporary frames are deleted.
"""
import asyncio, functools, http.server, io, pathlib, shutil, subprocess, sys, tempfile, threading
from playwright.async_api import async_playwright
from PIL import Image, ImageChops, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "assets" / "video"
W, H, OW, OH = 1920, 1080, 1600, 900
FPS_IN, FPS_OUT, BUDGET = 60, 30, 2.5 * 1024 * 1024

CHECK_JS = """() => {
  const vis = el => { for (let e = el; e && e.nodeType === 1; e = e.parentElement) { const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < .02) return false; } return true; };
  const out = [], W = 1920, H = 1080;
  // text on products: sample each word or letter's centre and corners against the product's alpha
  document.querySelectorAll('.pt-text[data-on-product]').forEach(t => {
    if (!vis(t)) return;
    const prod = t.closest('.prod'), img = prod.querySelector('img'), r = img.getBoundingClientRect(), a = window.__alpha[img.src];
    t.querySelectorAll(':scope > span').forEach(w => {
      const units = w.querySelectorAll('.pt-ch').length ? w.querySelectorAll('.pt-ch') : [w];
      units.forEach(u => { const b = u.getBoundingClientRect(); if (b.width < 1) return;
        [[.5, .5], [.15, .25], [.85, .25], [.15, .75], [.85, .75]].forEach(([fx, fy]) => {
          const x = (b.left + b.width * fx - r.left) / r.width, y = (b.top + b.height * fy - r.top) / r.height;
          const v = a.d[Math.min(a.n - 1, Math.max(0, Math.round(y * (a.n - 1)))) * a.n + Math.min(a.n - 1, Math.max(0, Math.round(x * (a.n - 1))))];
          if (!(v > 242)) out.push('text off product: ' + (prod.id || prod.parentElement.dataset.cut) + ' "' + u.textContent + '" alpha ' + v);
        });
      });
    });
  });
  // nothing clips the canvas edge
  const edge = (name, b) => { if (b.right - b.left < 1) return; if (b.left < -0.5 || b.top < -0.5 || b.right > W + 0.5 || b.bottom > H + 0.5) out.push(name + ' clips the edge ' + [b.left, b.top, b.right, b.bottom].map(Math.round)); };
  document.querySelectorAll('.prod img').forEach(img => { if (!vis(img)) return;
    const r = img.getBoundingClientRect(), bb = window.__alpha[img.src].bbox;
    edge('product ' + img.src.split('/').pop(), { left: r.left + bb[0] * r.width, top: r.top + bb[1] * r.height, right: r.left + bb[2] * r.width, bottom: r.top + bb[3] * r.height }); });
  document.querySelectorAll('.card, .chip, .rail, .hero-word span, .line, .brand, .brand-line').forEach(e => { if (vis(e)) edge(e.id || e.className || e.textContent, e.getBoundingClientRect()); });
  return out;
}"""

ALPHA_JS = """async () => {   // each product image's alpha at 400x400 plus its outline's bounding box, for the checks
  window.__alpha = {};
  for (const img of document.querySelectorAll('.prod img')) {
    const n = 400, c = document.createElement('canvas'); c.width = c.height = n; const g = c.getContext('2d'); g.drawImage(img, 0, 0, n, n);
    const px = g.getImageData(0, 0, n, n).data, d = new Uint8Array(n * n); let x0 = n, y0 = n, x1 = 0, y1 = 0;
    for (let i = 0; i < n * n; i++) { d[i] = px[i * 4 + 3]; if (d[i] > 8) { const x = i % n, y = (i / n) | 0; x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); } }
    window.__alpha[img.src] = { n, d, bbox: [x0 / n, y0 / n, (x1 + 1) / n, (y1 + 1) / n] };
  }
}"""


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT / "src")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


async def open_film(p, srv):
    b = await p.chromium.launch()
    pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(f"http://127.0.0.1:{srv.server_port}/video/hero-promo.html?render", wait_until="networkidle", timeout=120000)
    await pg.evaluate("window.ready.then(() => document.fonts.ready)")
    await pg.evaluate(ALPHA_JS)
    if errs:
        sys.exit("page errors: " + "; ".join(errs))
    return b, pg


async def frame(pg, t):
    await pg.evaluate(f"window.seek({t})")
    png = await pg.screenshot(clip={"x": 0, "y": 0, "width": W, "height": H}, animations="allow")
    return Image.open(io.BytesIO(png)).convert("RGB")


async def sheet(path, n=8):
    srv = serve()
    async with async_playwright() as p:
        b, pg = await open_film(p, srv)
        tw, th = 960, 540; times = [10 * k / n for k in range(n)]
        out = Image.new("RGB", (tw * 4 + 36, th * ((n + 3) // 4) + 12 * ((n - 1) // 4)), (230, 230, 230))
        problems = []
        for k, t in enumerate(times):
            im = (await frame(pg, t)).resize((tw, th), Image.LANCZOS)
            out.paste(im, ((k % 4) * (tw + 12), (k // 4) * (th + 12)))
            problems += [f"t={t:.2f}s: {x}" for x in await pg.evaluate(CHECK_JS)]
        out.save(path); await b.close()
    srv.shutdown()
    print("frames at " + ", ".join(f"{t:.2f}s" for t in times) + f" -> {path}")
    print("\n".join(problems) if problems else "checks: PASS")


def encode(frames_dir, n):
    """H.264 is one pass at a CRF (x264 cannot combine CRF with two passes); VP9 is two-pass constrained quality.
    Either way the CRF goes up until the file is under the budget."""
    OUT.mkdir(parents=True, exist_ok=True)
    src = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS_OUT), "-i", str(frames_dir / "f%04d.png")]
    def h264(crf):
        dst = OUT / "hero-promo.mp4"
        subprocess.run(src + ["-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-preset", "veryslow", "-tune", "film",
                              "-crf", str(crf), "-movflags", "+faststart", "-an", str(dst)], check=True)
        return dst.stat().st_size
    def vp9(crf):
        dst = OUT / "hero-promo.webm"; log = str(frames_dir / "vp9")
        a = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-b:v", "0", "-crf", str(crf), "-row-mt", "1", "-deadline", "good", "-cpu-used", "1", "-an", "-passlogfile", log]
        subprocess.run(src + a + ["-pass", "1", "-f", "null", "-"], check=True)
        subprocess.run(src + a + ["-pass", "2", str(dst)], check=True)
        return dst.stat().st_size
    results = {}
    for name, fn, crf in [("hero-promo.mp4", h264, 20), ("hero-promo.webm", vp9, 32)]:
        size = fn(crf)
        while size > BUDGET and crf < 51:                    # raise CRF before anything else changes
            crf += 2; size = fn(crf)
        results[name] = (size, crf)
    return results


async def render(reuse=None):
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is missing. Install it with:  brew install ffmpeg   then run this again.")
    tmp = pathlib.Path(reuse) if reuse else pathlib.Path(tempfile.mkdtemp(prefix="hero-video-"))
    problems, n = [], int(10 * FPS_OUT)
    if not (reuse and len(list(tmp.glob("f*.png"))) == n):
        srv = serve()
        async with async_playwright() as p:
            b, pg = await open_film(p, srv)
            for k in range(0, 2 * n, 2):                       # two 60 fps frames blend into one 30 fps frame
                a, c = await frame(pg, k / FPS_IN), await frame(pg, (k + 1) / FPS_IN)
                problems += [f"frame {k // 2} ({k / FPS_IN:.2f}s): {x}" for x in await pg.evaluate(CHECK_JS)]
                Image.blend(a, c, .5).resize((OW, OH), Image.LANCZOS).save(tmp / f"f{k // 2:04d}.png")
            await b.close()
        srv.shutdown()
    first, last = Image.open(tmp / "f0000.png"), Image.open(tmp / f"f{n - 1:04d}.png")
    diff = sum(ImageStat.Stat(ImageChops.difference(first, last)).mean) / 3 / 255
    if diff >= .01:
        problems.append(f"loop: first and last frames differ by {diff:.2%}")
    if problems:
        sys.exit("NOT ENCODED, failing frames:\n  " + "\n  ".join(problems))
    try:
        res = encode(tmp, n)
    except subprocess.CalledProcessError as e:
        sys.exit(f"encoding failed ({e}); the frames are kept in {tmp} (rerun with --frames {tmp})")
    first.save(OUT / "hero-promo.webp", "WEBP", quality=82, method=6)
    for name, (size, crf) in res.items():
        print(f"ok -> src/assets/video/{name}  {size / 1024 / 1024:.2f} MB  (CRF {crf})")
    print(f"ok -> src/assets/video/hero-promo.webp  {(OUT / 'hero-promo.webp').stat().st_size / 1024:.0f} KB   loop diff {diff:.3%}")
    shutil.rmtree(tmp, ignore_errors=True)                 # temporary frames go once the files are written


async def check():
    """Every 30 fps frame through the checks (geometry only, so 1x is enough), plus the loop."""
    srv = serve(); problems = []
    async with async_playwright() as p:
        b, pg = await open_film(p, srv)
        for k in range(10 * FPS_OUT):
            await pg.evaluate(f"window.seek({k / FPS_OUT})")
            problems += [f"frame {k} ({k / FPS_OUT:.2f}s): {x}" for x in await pg.evaluate(CHECK_JS)]
        first, last = await frame(pg, 0), await frame(pg, 10 - 1 / FPS_IN)
        diff = sum(ImageStat.Stat(ImageChops.difference(first, last)).mean) / 3 / 255
        if diff >= .01: problems.append(f"loop: first and last frames differ by {diff:.2%}")
        await b.close()
    srv.shutdown()
    print("\n".join(problems) if problems else f"checks: PASS (300 frames, loop diff {diff:.3%})")


if __name__ == "__main__":
    if "--check" in sys.argv:
        asyncio.run(check())
    elif "--sheet" in sys.argv:
        asyncio.run(sheet(sys.argv[sys.argv.index("--sheet") + 1]))
    else:
        asyncio.run(render(sys.argv[sys.argv.index("--frames") + 1] if "--frames" in sys.argv else None))
