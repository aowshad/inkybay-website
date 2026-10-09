"""Generate the demo blog covers: 1600x1000 (16:10), a background image with one product, no text.

    python3 scripts/make_blog_covers.py                    # background: src/assets/blog/_bg.webp
    python3 scripts/make_blog_covers.py --bg other.webp    # any image in src/assets/blog/ (or a path)
    python3 scripts/make_blog_covers.py --sheet grid.png   # also writes a contact sheet and prints the checks

Writes src/assets/blog/<thumbnail> for every post with a cover_product. The background is cover-fitted (it may be
cropped, the product never is). The product is trimmed to its own outline and scaled so it fits a square 62% of the
frame height (tall products are 620px high, wide ones 620px wide, so all read the same size), centred, and gets a soft shadow drawn from its own alpha.
Real posts can use any 16:10 image instead; this is only for demo content.
"""
import argparse, pathlib, re
from PIL import Image, ImageFilter, ImageOps, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOG = ROOT / "src/assets/blog"
W, H = 1600, 1000
BACKGROUND = "_bg.webp"          # the default background (src/assets/blog/_bg.webp)
PRODUCT = .62                    # the product's outline fits a square of 62% of the frame height


def background(name):
    p = pathlib.Path(name); p = p if p.is_absolute() or p.exists() else BLOG / name
    return ImageOps.fit(Image.open(p).convert("RGB"), (W, H), Image.LANCZOS)   # cover-fit, centred crop


def cover(product, bg):
    img = bg.convert("RGBA")
    p = Image.open(ROOT / f"src/assets/products/{product}.webp").convert("RGBA")
    p = p.crop(p.getchannel("A").getbbox())                                 # trim to the product's outline
    k = H * PRODUCT / max(p.width, p.height)                                 # wide and tall products read the same size
    p = p.resize((round(p.width * k), round(p.height * k)), Image.LANCZOS)
    x, y = (W - p.width) // 2, (H - p.height) // 2
    pad = 80                                                                 # soft shadow that follows the shape
    sh = Image.new("RGBA", (p.width + 2 * pad, p.height + 2 * pad), (0, 0, 0, 0))
    a = Image.new("L", sh.size, 0); a.paste(p.getchannel("A").point(lambda v: int(v * .5)), (pad, pad))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(26)))
    img.alpha_composite(sh, (x - pad, y - pad + 26))
    img.alpha_composite(p, (x, y))
    return img.convert("RGB"), (x, y, x + p.width, y + p.height), p


def lum(rgb):
    return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--bg", default=BACKGROUND); ap.add_argument("--sheet")
    args = ap.parse_args()
    bg = background(args.bg)
    posts = sorted((ROOT / "src/blog/posts").glob("*.md")); made = []
    for f in posts:
        fm = f.read_text().split("---")[1]
        prod = re.search(r"^cover_product:\s*(\S+)", fm, re.M); thumb = re.search(r"^thumbnail:\s*(\S+)", fm, re.M)
        if not prod or not thumb: continue
        im, box, p = cover(prod.group(1), bg)
        im.save(BLOG / thumb.group(1), "WEBP", quality=85, method=6)
        # checks: 16:10, a clear margin on every side, and contrast between the product and the background around it
        m = min(box[0], box[1], W - box[2], H - box[3])
        prod_l = ImageStat.Stat(p.convert("RGB"), p.getchannel("A").point(lambda v: 255 if v > 200 else 0)).mean
        ring = Image.new("L", (W, H), 0); ring.paste(255, (max(0, box[0] - 60), max(0, box[1] - 60), min(W, box[2] + 60), min(H, box[3] + 60)))
        ring.paste(0, box); bg_l = ImageStat.Stat(bg, ring).mean
        L1, L2 = sorted([(lum(prod_l) / 255) + .05, (lum(bg_l) / 255) + .05])
        made.append((thumb.group(1), prod.group(1), im.size, m, round(L2 / L1, 2)))
        print(f"cover -> {thumb.group(1):48} {prod.group(1):12} {im.size[0]}x{im.size[1]}  margin {m}px  contrast {L2 / L1:.2f}")
    assert all(s == (W, H) for _, _, s, _, _ in made), "a cover is not 1600x1000"
    if args.sheet:
        cols = 4; tw, th = 400, 250; rows = -(-len(made) // cols)
        sheet = Image.new("RGB", (cols * tw + (cols - 1) * 12, rows * th + (rows - 1) * 12), (240, 240, 240))
        for i, (name, *_ ) in enumerate(made):
            sheet.paste(Image.open(BLOG / name).resize((tw, th), Image.LANCZOS), ((i % cols) * (tw + 12), (i // cols) * (th + 12)))
        sheet.save(args.sheet)


if __name__ == "__main__":
    main()
