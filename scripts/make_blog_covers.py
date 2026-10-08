"""Generate the demo blog covers: 1600x1000 (16:10), a soft brand gradient with one product, no text.

    python3 scripts/make_blog_covers.py          # writes src/assets/blog/<slug>.webp for posts with cover_product

Real posts can use any 16:10 image instead; this is only for demo content.
"""
import pathlib, re, math
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1600, 1000
TINTS = [((255, 241, 228), (255, 214, 182)), ((255, 236, 226), (252, 200, 182)), ((255, 244, 222), (255, 220, 160)), ((253, 238, 232), (247, 205, 190))]


def cover(product, k):
    a, b = TINTS[k % len(TINTS)]
    img = Image.new("RGB", (W, H), a); d = ImageDraw.Draw(img)
    for y in range(H):                                   # diagonal-ish vertical blend, light top-left to warm bottom-right
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(round(a[i] + (b[i] - a[i]) * t * .85) for i in range(3)))
    glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse([W * .22, H * .12, W * .78, H * .92], fill=170)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), img, glow)
    p = Image.open(ROOT / f"src/assets/products/{product}.webp").convert("RGBA")
    size = int(H * .82); p = p.resize((size, size), Image.LANCZOS)
    shadow = Image.new("RGBA", p.size, (0, 0, 0, 0)); shadow.putalpha(p.getchannel("A").point(lambda v: int(v * .22)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    x, y = (W - size) // 2, (H - size) // 2 + 10
    base = img.convert("RGBA"); base.alpha_composite(Image.new("RGBA", shadow.size, (90, 40, 10, 0)), (0, 0))
    sh = Image.new("RGBA", p.size, (90, 40, 10, 255)); sh.putalpha(shadow.getchannel("A")); base.alpha_composite(sh, (x, y + 30))
    base.alpha_composite(p, (x, y))
    return base.convert("RGB")


def main():
    out = ROOT / "src/assets/blog"; out.mkdir(parents=True, exist_ok=True)
    posts = sorted((ROOT / "src/blog/posts").glob("*.md"))
    for k, f in enumerate(posts):
        fm = f.read_text().split("---")[1]
        prod = re.search(r"^cover_product:\s*(\S+)", fm, re.M); thumb = re.search(r"^thumbnail:\s*(\S+)", fm, re.M)
        if not prod or not thumb: continue
        cover(prod.group(1), k).save(out / thumb.group(1), "WEBP", quality=82, method=6)
        print("cover ->", thumb.group(1))


if __name__ == "__main__":
    main()
